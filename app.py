import os
import re
import base64
import tempfile
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import snowflake.connector
from snowflake.core import Root
from dotenv import load_dotenv
import cortex_chat

load_dotenv()

ACCOUNT = os.getenv("ACCOUNT")
HOST = os.getenv("HOST")
USER = os.getenv("SNOWFLAKE_USER")
ROLE = os.getenv("SNOWFLAKE_ROLE")
WAREHOUSE = os.getenv("WAREHOUSE")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
AGENT_ENDPOINT = os.getenv("AGENT_ENDPOINT")
PAT = os.getenv("PAT")

DEBUG = False

def log(msg, end='\n'):
    """Print with flush for real-time output."""
    print(msg, end=end, flush=True)

# Initialize Slack app
app = App(token=SLACK_BOT_TOKEN)

# Global storage for planning steps data
planning_steps_data = {}

@app.message(re.compile(r"^(clear history|forget|reset|new conversation)$", re.IGNORECASE))
def handle_clear_history(message, say):
    """Handle requests to clear conversation history."""
    try:
        channel_id = message.get('channel')
        if CORTEX_APP:
            CORTEX_APP.clear_history(channel_id)
            say("🗑️ Conversation history cleared! I'll start fresh with no memory of our previous conversation.")
        else:
            say("❌ Agent not initialized.")
    except Exception as e:
        say(f"❌ Error clearing history: {e}")

@app.event("app_mention")
def handle_app_mention(event, say, client, body):
    """Handle direct mentions of the bot."""
    handle_message_event(event, say, client, body)

@app.message(re.compile(".*"))
def handle_direct_message(message, say, client, body):
    """Handle direct messages to the bot."""
    # Only respond to direct messages (not in channels unless mentioned)
    if message.get('channel_type') == 'im':
        handle_message_event(message, say, client, body)

def handle_message_event(event, say, client, body):
    """Main handler for processing user messages with Cortex Agent."""
    try:
        user_message = event.get('text', '').strip()
        if not user_message:
            return
        
        # Remove bot mention if present
        user_message = re.sub(r'<@\w+>', '', user_message).strip()
        
        if not user_message:
            say("👋 Hi! Ask me any question about your data and I'll help you analyze it using Snowflake Cortex.")
            return
        
        # Initialize Cortex chat if not available
        global CORTEX_APP
        if not CORTEX_APP:
            say("❌ Cortex Agent not initialized. Please check your configuration.")
            return
        
        # Set up Slack communication for real-time updates
        CORTEX_APP.set_slack_say_function(say)
        CORTEX_APP.set_slack_app(app, event.get('channel'))
        
        say(
            text="🚀 Starting Cortex Agent...",
            blocks=[
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": ":snowflake: *Snowflake Cortex Agent* is processing your request...\n_You'll see real-time updates as the agent works!_",
                    }
                },
                {
                    "type": "divider"
                },
            ]
        )
        
        # Get response with real-time streaming
        response = CORTEX_APP.chat(user_message)
        
        # Display final response
        display_agent_response(response, say)
        
    except Exception as e:
        error_info = f"{type(e).__name__} at line {e.__traceback__.tb_lineno} of {__file__}: {e}"
        print(f"❌ Error in handle_message_event: {error_info}")
        say(f"❌ Sorry, there was an error processing your message: {str(e)}")

@app.action("show_planning_details")
def handle_planning_details_toggle(ack, body, say):
    """Handle planning details show/hide toggle."""
    ack()
    
    try:
        # Get the current button value to determine action
        action_value = body["actions"][0]["value"]
        message_ts = body["message"]["ts"]
        channel_id = body["channel"]["id"]
        
        # Get timeline or fallback to separate arrays
        try:
            timeline = getattr(CORTEX_APP, 'timeline', [])
            # Fallback to separate arrays if timeline not available
            if not timeline:
                steps = getattr(CORTEX_APP, 'planning_steps', [])
                thinking_steps = getattr(CORTEX_APP, 'thinking_steps', [])
            else:
                steps = []
                thinking_steps = []
        except:
            timeline = []
            steps = planning_steps_data.get('steps', [])
            thinking_steps = []
        
        if action_value == "show":
            # Show detailed planning steps with verification and SQL info
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*🤔 Thinking...* ✅ *Completed!*"
                    }
                }
            ]
            
            # Add planning steps and thinking content in chronological order
            combined_steps = []
            
            if timeline:
                # Use chronological timeline for proper ordering
                for event in timeline:
                    if event['type'] == 'status':
                        combined_steps.append(f" {event['content']}")
                    elif event['type'] == 'thinking':
                        combined_steps.append(f" {event['content']}")
            else:
                # Fallback to separate arrays (old behavior)
                # Add status steps
                if steps:
                    for step in steps:
                        combined_steps.append(f" {step}")
                
                # Add thinking steps without truncation for full content display
                if thinking_steps:
                    for thinking in thinking_steps:
                        # Don't truncate thinking content - users want to see complete thoughts
                        combined_steps.append(f" {thinking}")
            
            if combined_steps:
                # Build the text but ensure it doesn't exceed Slack's 3000 character limit
                header = "*Thinking Steps:*\n"
                max_content_length = 2950 - len(header)  # Leave room for header and safety margin
                
                steps_text = ""
                truncated = False
                
                for i, step in enumerate(combined_steps):
                    step_line = f"• {step}\n"
                    if len(steps_text) + len(step_line) <= max_content_length:
                        steps_text += step_line
                    else:
                        truncated = True
                        break
                
                # Remove trailing newline
                steps_text = steps_text.rstrip('\n')
                
                # Add truncation notice if needed
                if truncated:
                    remaining_count = len(combined_steps) - i
                    steps_text += f"\n\n_... and {remaining_count} more items (truncated for display)_"
                
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{header}{steps_text}"
                    }
                })
            
            # Add SQL information with actual queries and verification status
            try:
                sql_queries = getattr(CORTEX_APP, 'sql_queries', [])
                verified_query_used = getattr(CORTEX_APP, 'verified_query_used', False)
                
                if sql_queries:
                    num_queries = len(sql_queries)
                    blocks.extend([
                        {"type": "divider"},
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*💾 SQL Queries:*\nCortex Analyst used {num_queries} SQL {'query' if num_queries == 1 else 'queries'}"
                            }
                        }
                    ])
                    
                    # Add each SQL query with its code and verification status
                    for i, sql_query in enumerate(sql_queries, 1):
                        # Determine if this query is verified (assume first/only query is verified if verified_query_used is True)
                        is_verified = verified_query_used and (i == 1 or num_queries == 1)
                        
                        # Create query header with verification status
                        query_header = f"*💾 SQL Query {i}:*"
                        if is_verified:
                            query_header += " :verified: Answer accuracy verified by agent owner"
                        
                        # Truncate SQL if too long for Slack
                        if len(sql_query) > 2800:
                            displayed_sql = sql_query[:2800] + "...\n-- (SQL truncated for display)"
                        else:
                            displayed_sql = sql_query
                        
                        blocks.extend([
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": query_header
                                }
                            },
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": f"```sql\n{displayed_sql}\n```"
                                }
                            }
                        ])
                        
                        # Add separator between queries (except for the last one)
                        if i < len(sql_queries):
                            blocks.append({"type": "divider"})
                    
                    # Add context after all queries
                    blocks.append({
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": "ℹ️ All SQL queries were already executed by Cortex during analysis. Results are included in the response above."
                            }
                        ]
                    })
            except:
                pass  # Skip SQL if not available
            
            # Add hide button
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🔽 Hide Details"
                        },
                        "action_id": "show_planning_details",
                        "value": "hide"
                    }
                ]
            })
        else:  # action_value == "hide"
            # Hide detailed planning steps (show summary)
            if timeline:
                step_count = len(timeline)
            else:
                step_count = (len(steps) if steps else 0) + (len(thinking_steps) if thinking_steps else 0)
            
            # Check what additional info is available
            additional_info = []
            try:
                has_verification = getattr(CORTEX_APP, 'verification_info', {}) or getattr(CORTEX_APP, 'verified_query_used', False)
                sql_queries = getattr(CORTEX_APP, 'sql_queries', [])
                
                if has_verification and sql_queries:
                    # Combine verification and SQL info
                    query_count = len(sql_queries)
                    additional_info.append(f":verified: answer accuracy verified by agent owner for {query_count} SQL {'query' if query_count == 1 else 'queries'}")
                elif has_verification:
                    # Only verification info
                    additional_info.append(":verified: answer accuracy verified by agent owner")
                elif sql_queries:
                    # Only SQL queries
                    query_count = len(sql_queries)
                    additional_info.append(f"{query_count} SQL {'query' if query_count == 1 else 'queries'}")
            except:
                pass
            
            summary_text = f"_Finished {step_count} steps"
            if additional_info:
                summary_text += f" • Includes {' and '.join(additional_info)}"
            summary_text += "_"
            
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*🤔 Thinking...* ✅ *Completed!*\n\n{summary_text}"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "📋 Show Details"
                            },
                            "action_id": "show_planning_details",
                            "value": "show"
                        }
                    ]
                }
            ]
        
        # Update the message
        app.client.chat_update(
            channel=channel_id,
            ts=message_ts,
            text="🤔 Planning details",
            blocks=blocks
        )
        
    except Exception as e:
        # Fallback message
        say(f"❌ Error toggling planning details: {e}")

def format_markdown_table_for_slack(text):
    """Convert markdown tables to Slack-friendly code block tables."""
    import re
    
    def format_table(match):
        table_text = match.group(0)
        lines = table_text.strip().split('\n')
        
        # Parse the table
        rows = []
        for line in lines:
            # Skip separator lines (|---|---|)
            if re.match(r'^\|[\s\-:]+\|$', line.replace('|', '|').strip()):
                continue
            # Extract cells
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            if cells:
                rows.append(cells)
        
        if not rows:
            return table_text
        
        # Calculate column widths
        num_cols = max(len(row) for row in rows)
        col_widths = [0] * num_cols
        for row in rows:
            for i, cell in enumerate(row):
                if i < num_cols:
                    col_widths[i] = max(col_widths[i], len(cell))
        
        # Format as aligned table
        formatted_lines = []
        for i, row in enumerate(rows):
            formatted_cells = []
            for j, cell in enumerate(row):
                width = col_widths[j] if j < len(col_widths) else len(cell)
                formatted_cells.append(cell.ljust(width))
            formatted_lines.append(' | '.join(formatted_cells))
            
            # Add separator after header
            if i == 0:
                separator = '-+-'.join('-' * w for w in col_widths)
                formatted_lines.append(separator)
        
        return '```\n' + '\n'.join(formatted_lines) + '\n```'
    
    # Match markdown tables (lines starting with |)
    table_pattern = r'(\|[^\n]+\|\n)+'
    text = re.sub(table_pattern, format_table, text)
    
    return text

def format_key_value_data_for_slack(text):
    """Format key-value bullet points into a cleaner table-like format."""
    import re
    
    # Find sections with consistent key-value patterns like "- **Key:** Value"
    kv_pattern = r'- \*\*([^*]+)\*\*:?\s*([^\n]+)'
    
    lines = text.split('\n')
    formatted_lines = []
    kv_block = []
    
    for line in lines:
        match = re.match(kv_pattern, line.strip())
        if match:
            key, value = match.groups()
            kv_block.append((key.strip(), value.strip()))
        else:
            # Output accumulated key-value block as table
            if len(kv_block) >= 3:  # Only format if we have 3+ items
                # Calculate widths
                max_key = max(len(k) for k, v in kv_block)
                table_lines = ['```']
                for key, value in kv_block:
                    table_lines.append(f'{key.ljust(max_key)} : {value}')
                table_lines.append('```')
                formatted_lines.append('\n'.join(table_lines))
                kv_block = []
            elif kv_block:
                # Not enough items, output as-is
                for key, value in kv_block:
                    formatted_lines.append(f'- *{key}:* {value}')
                kv_block = []
            formatted_lines.append(line)
    
    # Handle remaining block
    if len(kv_block) >= 3:
        max_key = max(len(k) for k, v in kv_block)
        table_lines = ['```']
        for key, value in kv_block:
            table_lines.append(f'{key.ljust(max_key)} : {value}')
        table_lines.append('```')
        formatted_lines.append('\n'.join(table_lines))
    elif kv_block:
        for key, value in kv_block:
            formatted_lines.append(f'- *{key}:* {value}')
    
    return '\n'.join(formatted_lines)

def format_text_for_slack(text):
    """Convert markdown formatting to Slack's mrkdwn format."""
    if not text:
        return text
    
    try:
        import re
        
        # First, convert markdown tables to code block tables
        text = format_markdown_table_for_slack(text)
        
        # Format key-value bullet points into table-like format
        text = format_key_value_data_for_slack(text)
        
        # Convert **bold** to *bold* for Slack
        # Replace **text** with *text* (bold)
        text = re.sub(r'\*\*(.*?)\*\*', r'*\1*', text)
        
        # Replace __text__ with *text* (alternative bold syntax)
        text = re.sub(r'__(.*?)__', r'*\1*', text)
        
        # Replace *text* with _text_ (italics) - but only single asterisks
        # This is tricky because we don't want to mess with our bold conversion
        # So we'll handle this carefully by looking for single asterisks not preceded/followed by another asterisk
        text = re.sub(r'(?<!\*)\*(?!\*)([^*]+?)(?<!\*)\*(?!\*)', r'_\1_', text)
        
        return text
        
    except Exception as e:
        print(f"❌ Error formatting text: {e}")
        return text

def display_result_set_in_slack(result_set, say, table_number=1):
    """Display a result set as a formatted table in Slack."""
    try:
        if not result_set:
            return
        
        # Debug log the structure
        if DEBUG:
            log(f"📊 Result set type: {type(result_set)}")
            if isinstance(result_set, dict):
                log(f"📊 Result set keys: {result_set.keys()}")
        
        # Extract data and columns from the new structure
        columns = None
        data = result_set
        
        # Handle dict structure with 'data' and 'columns'
        if isinstance(result_set, dict):
            if 'data' in result_set:
                data = result_set['data']
                columns = result_set.get('columns')
            elif 'rows' in result_set:
                data = result_set['rows']
                columns = result_set.get('columns')
            else:
                # It's a single row dict
                data = [result_set]
        
        if not data:
            log(f"⚠️ No data in result set")
            return
        
        # Handle dict data with nested structure (e.g., {0: {...}, 1: {...}})
        if isinstance(data, dict):
            if DEBUG:
                log(f"📊 Data is dict with keys: {list(data.keys())[:5]}...")
            # Check if it's indexed by numbers (row indices)
            if all(isinstance(k, (int, str)) for k in data.keys()):
                try:
                    # Try to convert to list of values
                    if all(str(k).isdigit() for k in data.keys()):
                        # Keys are row indices like 0, 1, 2...
                        sorted_keys = sorted(data.keys(), key=lambda x: int(x))
                        data = [data[k] for k in sorted_keys]
                    else:
                        # Keys might be column names - transpose to row format
                        first_val = next(iter(data.values()))
                        if isinstance(first_val, dict):
                            # Format: {col1: {0: val, 1: val}, col2: {0: val, 1: val}}
                            row_indices = set()
                            for col_data in data.values():
                                if isinstance(col_data, dict):
                                    row_indices.update(col_data.keys())
                            sorted_indices = sorted(row_indices, key=lambda x: int(x) if str(x).isdigit() else x)
                            data = [
                                {col: data[col].get(idx) for col in data.keys()}
                                for idx in sorted_indices
                            ]
                        else:
                            # Single row with column names as keys
                            data = [data]
                except Exception as e:
                    log(f"⚠️ Error converting dict to list: {e}")
                    data = [data]
            
        if not isinstance(data, list) or len(data) == 0:
            log(f"⚠️ Result set data is not a valid list after conversion: {type(data)}")
            return
        
        # Handle list of lists (row data without headers)
        if isinstance(data[0], list):
            if columns:
                # Use provided column names
                data = [
                    {col: val for col, val in zip(columns, row)}
                    for row in data
                ]
            else:
                # Use generic column names
                data = [
                    {f"col_{i}": val for i, val in enumerate(row)}
                    for row in data
                ]
        
        # Ensure first item is a dict
        if not isinstance(data[0], dict):
            log(f"⚠️ Result set rows are not dicts: {type(data[0])}")
            return
        
        # Get column headers from first row
        headers = list(data[0].keys())
        result_set = data  # Use processed data for the rest of the function
        
        # Limit columns if too many (Slack has width limits)
        max_cols = 8
        if len(headers) > max_cols:
            headers = headers[:max_cols]
            truncated_cols = True
        else:
            truncated_cols = False
        
        # Calculate column widths (max 20 chars per column for Slack)
        col_widths = {}
        for header in headers:
            col_widths[header] = min(20, max(len(str(header)[:20]), 
                max(len(str(row.get(header, ''))[:20]) for row in result_set[:10])))
        
        # Build table with size checking
        max_table_chars = 2700  # Leave room for code block and header
        
        def build_table(headers, result_set, max_rows):
            header_row = ' | '.join(str(h)[:col_widths[h]].ljust(col_widths[h]) for h in headers)
            separator = '-+-'.join('-' * col_widths[h] for h in headers)
            
            data_rows = []
            for row in result_set[:max_rows]:
                row_str = ' | '.join(str(row.get(h, ''))[:col_widths[h]].ljust(col_widths[h]) for h in headers)
                data_rows.append(row_str)
            
            table = f"{header_row}\n{separator}\n" + '\n'.join(data_rows)
            return table, len(data_rows)
        
        # Try progressively fewer rows until it fits
        for max_rows in [10, 8, 5, 3]:
            table_text, rows_shown = build_table(headers, result_set, max_rows)
            if len(table_text) <= max_table_chars:
                break
        
        # Add truncation notices
        notices = []
        if len(result_set) > rows_shown:
            notices.append(f"{len(result_set) - rows_shown} more rows")
        if truncated_cols:
            notices.append(f"{len(data[0].keys()) - max_cols} more columns")
        if notices:
            table_text += f"\n\n... and {', '.join(notices)}"
        
        # Final safety check - if still too long, truncate text
        if len(table_text) > max_table_chars:
            table_text = table_text[:max_table_chars] + "\n... (truncated)"
        
        say(
            text=f"📊 Query Results Table {table_number}",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*📊 Query Results (Table {table_number}):*"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"```\n{table_text}\n```"
                    }
                }
            ]
        )
        
    except Exception as e:
        import traceback
        log(f"❌ Error displaying result set: {e}")
        log(f"   Traceback: {traceback.format_exc()}")
        say(f"⚠️ Could not display table {table_number}: {str(e)}")

def improve_chart_spec(chart_spec):
    """Improve chart specification for better visualization.
    
    Args:
        chart_spec: Vega-Lite chart specification (dict)
        
    Returns:
        dict: Improved chart specification
    """
    import copy
    spec = copy.deepcopy(chart_spec)
    
    try:
        # Define proper day order (Monday first)
        day_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        # Define proper hour order
        hour_order = list(range(24))
        
        # Process encoding if it exists
        if 'encoding' in spec:
            enc = spec['encoding']
            
            # Fix X axis sorting
            if 'x' in enc:
                x_field = enc['x'].get('field', '').upper()
                if 'DAY' in x_field or 'WEEK' in x_field:
                    enc['x']['sort'] = day_order
                elif 'HOUR' in x_field:
                    enc['x']['sort'] = hour_order
                if 'axis' not in enc['x']:
                    enc['x']['axis'] = {}
                enc['x']['axis']['labelAngle'] = 0
            
            # Fix Y axis sorting
            if 'y' in enc:
                y_field = enc['y'].get('field', '').upper()
                if 'DAY' in y_field or 'WEEK' in y_field:
                    enc['y']['sort'] = day_order
                elif 'HOUR' in y_field:
                    enc['y']['sort'] = hour_order
        
        # Set reasonable dimensions if not specified
        if 'width' not in spec:
            spec['width'] = 500
        if 'height' not in spec:
            spec['height'] = 400
            
        # Add config for better styling
        if 'config' not in spec:
            spec['config'] = {}
        spec['config']['view'] = {'stroke': 'transparent'}
        spec['config']['axis'] = {
            'domainColor': '#888',
            'tickColor': '#888',
            'labelFontSize': 11,
            'titleFontSize': 13
        }
        spec['config']['legend'] = {
            'titleFontSize': 12,
            'labelFontSize': 11
        }
        spec['config']['title'] = {
            'fontSize': 16,
            'fontWeight': 'bold'
        }
        
        return spec
        
    except Exception:
        return chart_spec

def render_vega_chart_to_image(chart_spec):
    """Render a Vega-Lite chart specification to a PNG image.
    
    Args:
        chart_spec: Vega-Lite chart specification (dict)
        
    Returns:
        bytes: PNG image data, or None if rendering fails
    """
    try:
        # Improve the chart spec before rendering
        improved_spec = improve_chart_spec(chart_spec)
        
        if DEBUG:
            log(f"📊 Rendering chart with vl-convert...")
        
        # Try using vl-convert if available (best option)
        try:
            import vl_convert as vlc
            result = vlc.vegalite_to_png(improved_spec, scale=2)
            if DEBUG:
                log(f"📊 vl-convert success! Image size: {len(result)} bytes")
            return result
        except ImportError as e:
            log(f"⚠️ vl-convert not available: {e}")
        except Exception as e:
            log(f"⚠️ vl-convert error: {e}")
        
        # Try using altair if available
        try:
            import altair as alt
            import io
            chart = alt.Chart.from_dict(improved_spec)
            buf = io.BytesIO()
            chart.save(buf, format='png')
            buf.seek(0)
            return buf.read()
        except ImportError as e:
            log(f"⚠️ altair not available: {e}")
        except Exception as e:
            log(f"⚠️ altair error: {e}")
        
        return None
        
    except Exception as e:
        log(f"❌ Chart rendering failed: {e}")
        return None

def display_chart_in_slack(chart_data, say, slack_app, chart_number=1):
    """Display a chart image in Slack.
    
    Args:
        chart_data: Dictionary or list containing chart info (image_base64, image_url, chart_url, chart_spec, etc.)
        say: Slack say function
        slack_app: Slack app instance for file uploads
        chart_number: Chart number for labeling
    """
    try:
        # Handle list of charts - process each one
        if isinstance(chart_data, list):
            for i, chart_item in enumerate(chart_data):
                display_chart_in_slack(chart_item, say, slack_app, chart_number + i)
            return
        
        # Handle string chart data (base64 or URL)
        if isinstance(chart_data, str):
            log(f"📊 Chart data is string, length={len(chart_data)}, starts with: {chart_data[:50]}...")
            if chart_data.startswith('data:image') or chart_data.startswith('iVBOR'):
                # It's a base64 image
                chart_data = {'image_base64': chart_data}
            elif chart_data.startswith('http'):
                # It's a URL
                chart_data = {'image_url': chart_data}
            elif chart_data.startswith('{') or chart_data.startswith('['):
                # It might be JSON string - try to parse it
                try:
                    import json
                    parsed = json.loads(chart_data)
                    chart_data = parsed if isinstance(parsed, dict) else {'spec': parsed}
                    log(f"📊 Parsed JSON chart data: {type(chart_data)}")
                except:
                    log(f"⚠️ Failed to parse chart data as JSON")
                    return
            else:
                log(f"⚠️ Chart data is string but not recognized format: {chart_data[:100]}...")
                return
        
        # Ensure chart_data is a dict
        if not isinstance(chart_data, dict):
            log(f"⚠️ Chart data is not a dict: {type(chart_data)}")
            return
        
        # Handle base64 encoded image
        if chart_data.get('image_base64'):
            image_data = chart_data['image_base64']
            
            # Remove data URI prefix if present
            if image_data.startswith('data:image'):
                # Extract base64 part after the comma
                image_data = image_data.split(',', 1)[1]
            
            # Decode base64 to bytes
            image_bytes = base64.b64decode(image_data)
            
            # Upload to Slack using files_upload_v2
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                tmp_file.write(image_bytes)
                tmp_file_path = tmp_file.name
            
            try:
                # Get channel from the app
                channel_id = getattr(slack_app, '_channel_id', None)
                if channel_id:
                    slack_app.client.files_upload_v2(
                        channel=channel_id,
                        file=tmp_file_path,
                        filename=f"chart_{chart_number}.png",
                        title=f"📊 Chart {chart_number}",
                        initial_comment=f"*📊 Generated Visualization*"
                    )
            finally:
                # Clean up temp file
                import os as os_module
                if os_module.path.exists(tmp_file_path):
                    os_module.remove(tmp_file_path)
            return
        
        # Handle image URL
        image_url = chart_data.get('image_url') or chart_data.get('chart_url') or chart_data.get('url')
        if image_url:
            say(
                text=f"📊 Chart {chart_number}",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*📊 Generated Visualization (Chart {chart_number})*"
                        }
                    },
                    {
                        "type": "image",
                        "image_url": image_url,
                        "alt_text": f"Chart {chart_number}"
                    }
                ]
            )
            return
        
        # Handle direct image bytes (already decoded)
        if chart_data.get('image'):
            image_content = chart_data['image']
            if isinstance(image_content, bytes):
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                    tmp_file.write(image_content)
                    tmp_file_path = tmp_file.name
                
                try:
                    channel_id = getattr(slack_app, '_channel_id', None)
                    if channel_id:
                        slack_app.client.files_upload_v2(
                            channel=channel_id,
                            file=tmp_file_path,
                            filename=f"chart_{chart_number}.png",
                            title=f"📊 Chart {chart_number}",
                            initial_comment=f"*📊 Generated Visualization*"
                        )
                finally:
                    import os as os_module
                    if os_module.path.exists(tmp_file_path):
                        os_module.remove(tmp_file_path)
                return
        
        # Handle Vega-Lite chart specification (from response.chart events)
        # Check for wrapped format: {'type': 'chart_spec', 'spec': {...}}
        # Or raw Vega-Lite format: {'title': '...', 'mark': '...', 'encoding': {...}, ...}
        chart_spec = None
        
        if chart_data.get('type') == 'chart_spec' and chart_data.get('spec'):
            chart_spec = chart_data['spec']
        elif any(key in chart_data for key in ['$schema', 'mark', 'encoding', 'data', 'layer', 'vconcat', 'hconcat']):
            # This is a raw Vega-Lite spec
            chart_spec = chart_data
            log(f"📊 Detected raw Vega-Lite spec with keys: {list(chart_data.keys())[:5]}")
        
        if chart_spec:
            # Extract chart title from spec if available
            chart_title = chart_spec.get('title', '')
            if isinstance(chart_title, dict):
                chart_title = chart_title.get('text', '')
            if not chart_title:
                chart_title = "Visualization"
            
            image_bytes = render_vega_chart_to_image(chart_spec)
            
            if image_bytes:
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                    tmp_file.write(image_bytes)
                    tmp_file_path = tmp_file.name
                
                try:
                    channel_id = getattr(slack_app, '_channel_id', None)
                    if channel_id:
                        slack_app.client.files_upload_v2(
                            channel=channel_id,
                            file=tmp_file_path,
                            filename=f"chart_{chart_number}.png",
                            title=f"📊 {chart_title}",
                            initial_comment=f"*📊 {chart_title}*"
                        )
                finally:
                    import os as os_module
                    if os_module.path.exists(tmp_file_path):
                        os_module.remove(tmp_file_path)
                return
            else:
                # Can't render - show a message about the chart spec
                say(
                    text=f"📊 Chart {chart_number} specification received",
                    blocks=[
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*📊 Chart {chart_number}* was generated as a Vega-Lite specification.\n\n_To render this chart, install `vl-convert-python`:_\n```pip install vl-convert-python```"
                            }
                        }
                    ]
                )
                return
        
        # If we have chart data but couldn't display it
        say(f"📊 A chart was generated but couldn't be rendered. Please install `vl-convert-python` for chart support.")
        
    except Exception as e:
        say(f"⚠️ Chart couldn't be displayed: {str(e)}")

def split_text_for_slack(text, max_length=2900):
    """Split long text into chunks that fit Slack's 3000 char limit."""
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    # Split by paragraphs first (double newline)
    paragraphs = text.split('\n\n')
    
    for para in paragraphs:
        # If single paragraph is too long, split by lines
        if len(para) > max_length:
            lines = para.split('\n')
            for line in lines:
                if len(current_chunk) + len(line) + 2 <= max_length:
                    current_chunk += line + '\n'
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = line + '\n'
        elif len(current_chunk) + len(para) + 2 <= max_length:
            current_chunk += para + '\n\n'
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para + '\n\n'
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks if chunks else [text[:max_length] + "..."]

def display_agent_response(content, say):
    """Enhanced response display with SQL execution and improved formatting."""
    try:
        
        # Display the final agent response text
        if content.get('text'):
            formatted_text = format_text_for_slack(content['text'])
            
            # Split long responses into multiple messages
            text_chunks = split_text_for_slack(formatted_text)
            
            for i, chunk in enumerate(text_chunks):
                if i == 0:
                    # First chunk gets the header
                    say(
                        text="🎯 Final Response",
                        blocks=[
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": f"*🎯 Snowflake Cortex Agent Response:*\n{chunk}"
                                }
                            }
                        ]
                    )
                else:
                    # Continuation chunks
                    say(
                        text="Response continued...",
                        blocks=[
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": chunk
                                }
                            }
                        ]
                    )
        
        # Store verification and SQL info for planning section (moved from main display)
        if content.get('verification_info') or content.get('verified_query_used'):
            CORTEX_APP.verification_info = content.get('verification_info', {})
            CORTEX_APP.verified_query_used = content.get('verified_query_used', False)
        
        if content.get('sql_queries'):
            CORTEX_APP.sql_queries = content['sql_queries']
        
        # Display citations if present
        if content.get('citations') and content['citations']:
            formatted_citations = format_text_for_slack(content['citations'])
            say(
                text="📚 Citations",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*📚 Citations:*\n_{formatted_citations}_"
                        }
                    }
                ]
            )
        
        # Display suggestions if present
        if content.get('suggestions'):
            # Format each suggestion individually 
            formatted_suggestions = [format_text_for_slack(suggestion) for suggestion in content['suggestions'][:3]]
            suggestions_text = "\n".join(f"• {suggestion}" for suggestion in formatted_suggestions)
            say(
                text="💡 Suggestions",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*💡 Follow-up Suggestions:*\n{suggestions_text}"
                        }
                    }
                ]
            )
        
        # Display charts if present
        charts = content.get('charts', [])
        if not charts:
            # Also check CORTEX_APP for charts
            try:
                charts = getattr(CORTEX_APP, 'charts', [])
            except:
                pass
        
        # Debug: Log chart info
        if DEBUG:
            print(f"📊 Charts in response: {len(charts) if charts else 0}")
            if charts:
                for i, chart in enumerate(charts):
                    print(f"   Chart {i+1}: {type(chart)} - keys: {chart.keys() if isinstance(chart, dict) else 'N/A'}")
        
        if charts:
            for i, chart in enumerate(charts):
                display_chart_in_slack(chart, say, app, i + 1)
        elif DEBUG:
            log("📊 No charts received from Cortex Agent")
        
        # Display result sets (tabular data) if present
        result_sets = content.get('result_sets', [])
        if DEBUG:
            log(f"📊 Result sets count: {len(result_sets) if result_sets else 0}")
            if result_sets:
                for i, rs in enumerate(result_sets):
                    log(f"   Result set {i+1}: type={type(rs)}, len={len(rs) if hasattr(rs, '__len__') else 'N/A'}")
        
        if result_sets:
            for i, result_set in enumerate(result_sets):
                if result_set:
                    display_result_set_in_slack(result_set, say, i + 1)
        elif DEBUG:
            log("📊 No result_sets received from Cortex Agent")
            
    except Exception as e:
        error_info = f"{type(e).__name__} at line {e.__traceback__.tb_lineno} of {__file__}: {e}"
        print(f"❌ Error in display_agent_response: {error_info}")
        say(
            text="❌ Display error",
            blocks=[{
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"❌ *Error displaying response*\n```{error_info}```"
                }
            }]
        )

def get_snowflake_connection():
    """Create Snowflake connection using PAT authentication."""
    try:
        log("🔗 Attempting Snowflake connection with PAT authentication...")
        
        # Get account from host if not set
        account = ACCOUNT
        if not account:
            if HOST:
                account = HOST.split('.')[0]
                print(f"   📋 Extracted account from host: {account}")
        
        # Try PAT authentication first
        try:
            # Debug: Print credentials being used
            if DEBUG:
                print(f"   📋 Connection credentials:")
                print(f"      USER:      {USER}")
                print(f"      ACCOUNT:   {account}")
                print(f"      WAREHOUSE: {WAREHOUSE}")
                print(f"      ROLE:      {ROLE}")
                print(f"      PAT:       {PAT[:20] if PAT else 'NOT SET'}...{PAT[-10:] if PAT else ''}")
            
            conn = snowflake.connector.connect(
                user=USER,
                password=PAT,
                account=account,
                warehouse=WAREHOUSE,
                role=ROLE
            )
            
            # Test connection
            cursor = conn.cursor()
            cursor.execute("SELECT CURRENT_VERSION()")
            result = cursor.fetchone()
            cursor.close()
            
            log(f"   ✅ PAT authentication successful! Snowflake version: {result[0]}")
            return conn
            
        except Exception as pat_error:
            log(f"   ❌ PAT authentication failed: {pat_error}")
            return None
                
    except Exception as e:
        print(f"   ❌ Failed to connect to Snowflake: {e}")
        return None

def init():
    """Initialize Snowflake connection and Cortex chat."""
    conn = get_snowflake_connection()

    cortex_app = cortex_chat.CortexChat(
        AGENT_ENDPOINT, 
        PAT
    )

    log("🚀 Initialization complete")
    return conn, cortex_app

# Start app
if __name__ == "__main__":
    CONN, CORTEX_APP = init()
    if CONN:
        Root = Root(CONN)
        SocketModeHandler(app, SLACK_APP_TOKEN).start()
