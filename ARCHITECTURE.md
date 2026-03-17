# Slack + Snowflake Cortex Agent Architecture

This document provides a comprehensive overview of how the Slack bot integrates with Snowflake Cortex Agents to provide AI-powered data analysis and visualization.

---

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Data Flow Sequence](#data-flow-sequence)
3. [Low-Level Component Diagram](#low-level-component-diagram)
4. [File Structure](#file-structure)
5. [Key Functions Reference](#key-functions-reference)
6. [SSE Event Types](#sse-event-types)

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           SLACK + CORTEX AGENT FLOW                             │
└─────────────────────────────────────────────────────────────────────────────────┘

    ┌──────────┐         ┌──────────────┐         ┌─────────────────────┐
    │          │         │              │         │                     │
    │  SLACK   │◄───────►│  SLACK BOT   │◄───────►│  SNOWFLAKE CORTEX   │
    │  USER    │         │   (app.py)   │         │      AGENT API      │
    │          │         │              │         │                     │
    └──────────┘         └──────────────┘         └─────────────────────┘
         │                      │                           │
         │                      │                           │
    1. User sends          2. Bot processes           3. Agent uses tools:
       message                message                    • Cortex Analyst (SQL)
       (DM or @mention)                                  • Cortex Search
                                                         • Data to Chart
         │                      │                           │
         │                      │                           │
         ▼                      ▼                           ▼
    ┌──────────┐         ┌──────────────┐         ┌─────────────────────┐
    │          │         │              │         │                     │
    │  User    │◄────────│  Bot shows   │◄────────│  Agent returns:     │
    │  sees    │         │  response    │         │  • Text response    │
    │  result  │         │  + tables    │         │  • Result sets      │
    │          │         │  + charts    │         │  • Charts (Vega)    │
    └──────────┘         └──────────────┘         └─────────────────────┘
```

### Components Overview

| Component | Description |
|-----------|-------------|
| **Slack User** | End user interacting via Slack (DM or channel mention) |
| **Slack Bot (app.py)** | Python application using Slack Bolt framework |
| **Cortex Agent API** | Snowflake REST API for AI agent interactions |
| **Cortex Analyst** | SQL generation and execution tool |
| **Cortex Search** | Document/knowledge search tool |
| **Data to Chart** | Visualization generation tool (Vega-Lite) |

---

## Data Flow Sequence

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           REQUEST/RESPONSE SEQUENCE                               │
└──────────────────────────────────────────────────────────────────────────────────┘

   SLACK USER          SLACK BOT           CORTEX CHAT         CORTEX AGENT API
       │                   │                    │                      │
       │  1. Send message  │                    │                      │
       │──────────────────►│                    │                      │
       │                   │                    │                      │
       │                   │  2. chat(query)    │                      │
       │                   │───────────────────►│                      │
       │                   │                    │                      │
       │                   │                    │  3. POST /agents/:run│
       │                   │                    │─────────────────────►│
       │                   │                    │     (with history)   │
       │                   │                    │                      │
       │                   │                    │  4. SSE Stream       │
       │  5. "Thinking..." │◄───────────────────│◄─────────────────────│
       │◄──────────────────│   (real-time)      │  response.status     │
       │                   │                    │  response.thinking   │
       │                   │                    │                      │
       │                   │                    │  5. Tool executions  │
       │                   │                    │◄─────────────────────│
       │                   │                    │  • Cortex Analyst    │
       │                   │                    │  • Cortex Search     │
       │                   │                    │  • data_to_chart     │
       │                   │                    │                      │
       │                   │                    │  6. Final response   │
       │                   │                    │◄─────────────────────│
       │                   │                    │  response.text       │
       │                   │                    │  response.tool_result│
       │                   │                    │  response.chart      │
       │                   │                    │                      │
       │                   │  7. Return summary │                      │
       │                   │◄───────────────────│                      │
       │                   │  {text, charts,    │                      │
       │                   │   result_sets...}  │                      │
       │                   │                    │                      │
       │  8. Display       │                    │                      │
       │◄──────────────────│                    │                      │
       │  • Text response  │                    │                      │
       │  • Data tables    │                    │                      │
       │  • Rendered chart │                    │                      │
       │  • Suggestions    │                    │                      │
       │                   │                    │                      │
       ▼                   ▼                    ▼                      ▼
```

### Step-by-Step Flow

1. **User Input**: User sends a message via Slack DM or @mentions the bot
2. **Message Handling**: `app.py` receives the event and calls `handle_message_event()`
3. **Agent Request**: `CortexChat.chat()` sends request to Snowflake with conversation history
4. **SSE Streaming**: Agent streams responses via Server-Sent Events
5. **Real-time Updates**: Bot updates Slack UI with "Thinking..." status
6. **Tool Execution**: Agent uses tools (SQL, Search, Charts) as needed
7. **Response Parsing**: `CortexResponseParser` extracts text, charts, result sets, etc.
8. **Display**: Bot renders tables, charts and displays final response in Slack

---

## Low-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   app.py                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         SLACK EVENT HANDLERS                             │    │
│  │                                                                          │    │
│  │  @app.event("app_mention")     @app.message(".*")                       │    │
│  │       │                              │                                   │    │
│  │       └──────────┬───────────────────┘                                   │    │
│  │                  ▼                                                       │    │
│  │    ┌─────────────────────────────┐                                      │    │
│  │    │  handle_message_event()     │  ◄── Main entry point                │    │
│  │    │  • Extract user message     │                                      │    │
│  │    │  • Remove @mention          │                                      │    │
│  │    │  • Set up Slack comms       │                                      │    │
│  │    └─────────────┬───────────────┘                                      │    │
│  │                  │                                                       │    │
│  │                  ▼                                                       │    │
│  │    ┌─────────────────────────────┐                                      │    │
│  │    │  CORTEX_APP.chat(message)   │  ──► Call Cortex Agent               │    │
│  │    └─────────────┬───────────────┘                                      │    │
│  │                  │                                                       │    │
│  │                  ▼                                                       │    │
│  │    ┌─────────────────────────────┐                                      │    │
│  │    │  display_agent_response()   │  ◄── Format & display response       │    │
│  │    │  • Show text response       │                                      │    │
│  │    │  • Show citations           │                                      │    │
│  │    │  • Show suggestions         │                                      │    │
│  │    │  • Display result tables    │                                      │    │
│  │    │  • Display charts           │                                      │    │
│  │    └─────────────┬───────────────┘                                      │    │
│  │                  │                                                       │    │
│  │         ┌───────┴────────┐                                              │    │
│  │         ▼                ▼                                              │    │
│  │  ┌────────────────┐  ┌────────────────────┐                            │    │
│  │  │display_result_ │  │display_chart_in_   │                            │    │
│  │  │set_in_slack()  │  │slack()             │                            │    │
│  │  │• Format tables │  │• Render Vega-Lite  │                            │    │
│  │  │• Column names  │  │• Upload PNG        │                            │    │
│  │  └────────────────┘  └────────────────────┘                            │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         HELPER FUNCTIONS                                 │    │
│  │                                                                          │    │
│  │  • format_text_for_slack()          - Convert markdown to Slack format  │    │
│  │  • format_markdown_table_for_slack()- Convert MD tables to code blocks  │    │
│  │  • format_key_value_data_for_slack()- Format key-value bullet points    │    │
│  │  • split_text_for_slack()           - Split long messages (3000 limit)  │    │
│  │  • improve_chart_spec()             - Sort axes, add styling            │    │
│  │  • render_vega_chart_to_image()     - Vega-Lite → PNG                   │    │
│  │  • handle_planning_details_toggle() - Show/hide thinking steps          │    │
│  │  • get_snowflake_connection()       - PAT authentication                │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ CORTEX_APP.chat()
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                               cortex_chat.py                                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         class CortexChat                                 │    │
│  │                                                                          │    │
│  │  Attributes:                                                             │    │
│  │  • agent_url           - Snowflake Agent REST API endpoint              │    │
│  │  • pat                 - Programmatic Access Token                       │    │
│  │  • parser              - CortexResponseParser instance                   │    │
│  │  • conversation_history - Dict[channel_id → messages]                   │    │
│  │                                                                          │    │
│  │  ┌───────────────────────────────────────────────────────────────────┐  │    │
│  │  │  chat(query, channel_id)                                          │  │    │
│  │  │    │                                                              │  │    │
│  │  │    └──► _retrieve_response(query, channel_id)                     │  │    │
│  │  │              │                                                    │  │    │
│  │  │              │  1. Build conversation history                     │  │    │
│  │  │              │  2. Create HTTP POST request                       │  │    │
│  │  │              │  3. Stream SSE response                            │  │    │
│  │  │              │                                                    │  │    │
│  │  │              ▼                                                    │  │    │
│  │  │    ┌─────────────────────────────────────────────┐               │  │    │
│  │  │    │  PROCESS SSE EVENTS (Server-Sent Events)    │               │  │    │
│  │  │    │                                             │               │  │    │
│  │  │    │  • response.status    → Update Slack UI     │               │  │    │
│  │  │    │  • response.thinking  → Capture thinking    │               │  │    │
│  │  │    │  • response.chart     → Capture chart spec  │               │  │    │
│  │  │    │  • response.tool_result → SQL/Search data   │               │  │    │
│  │  │    │  • response.text      → Final answer        │               │  │    │
│  │  │    └─────────────────────────────────────────────┘               │  │    │
│  │  │              │                                                    │  │    │
│  │  │              ▼                                                    │  │    │
│  │  │    ┌─────────────────────────────────────────────┐               │  │    │
│  │  │    │  parser.parse_sse_response(response_lines)  │               │  │    │
│  │  │    │  parser.extract_summary(parsed_response)    │               │  │    │
│  │  │    └─────────────────────────────────────────────┘               │  │    │
│  │  │              │                                                    │  │    │
│  │  │              ▼                                                    │  │    │
│  │  │    ┌─────────────────────────────────────────────┐               │  │    │
│  │  │    │  Store in conversation_history              │               │  │    │
│  │  │    │  Return: {text, sql_queries, charts,        │               │  │    │
│  │  │    │          result_sets, ...}                  │               │  │    │
│  │  │    └─────────────────────────────────────────────┘               │  │    │
│  │  └───────────────────────────────────────────────────────────────────┘  │    │
│  │                                                                          │    │
│  │  Other Methods:                                                          │    │
│  │  • set_slack_say_function()  - Set Slack communication                  │    │
│  │  • set_slack_app()           - Set app for message updates              │    │
│  │  • clear_history()           - Clear conversation history               │    │
│  │  • _update_slack_with_thinking() - Real-time thinking updates           │    │
│  │  • _smart_truncate()         - Truncate text at word/sentence boundary  │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ parser.parse_sse_response()
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          cortex_response_parser.py                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                    class CortexResponseParser                            │    │
│  │                                                                          │    │
│  │  Data Classes:                                                           │    │
│  │  • ToolUse        - Represents tool invocation                          │    │
│  │  • ToolResult     - SQL, search results, charts, result_set             │    │
│  │  • ParsedMessage  - Role + content                                       │    │
│  │  • CortexResponse - Complete parsed response                             │    │
│  │                                                                          │    │
│  │  Methods:                                                                │    │
│  │  • parse_sse_response()    - Parse streaming SSE lines                  │    │
│  │  • parse_json_response()   - Parse non-streaming JSON                   │    │
│  │  • extract_summary()       - Extract text, SQL, charts, result_sets     │    │
│  │  • _process_sse_line()     - Process individual SSE line                │    │
│  │                                                                          │    │
│  │  Properties extracted:                                                   │    │
│  │  • final_text       - Agent's text response                             │    │
│  │  • sql_queries      - SQL executed by Cortex Analyst                    │    │
│  │  • search_results   - Results from Cortex Search                        │    │
│  │  • citations        - Source citations                                   │    │
│  │  • charts           - Vega-Lite chart specifications                    │    │
│  │  • result_sets      - Tabular data with column names                    │    │
│  │  • verification_info - Query verification status                        │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
sfguide-integrate-snowflake-cortex-agents-with-slack/
│
├── app.py                      # Main Slack bot application
│   ├── Event Handlers          # @app.message, @app.event
│   ├── handle_message_event()  # Process user messages
│   ├── display_agent_response()# Format & show responses
│   ├── display_result_set_in_slack() # Display tabular data
│   ├── display_chart_in_slack()# Render & upload charts
│   ├── improve_chart_spec()    # Enhance Vega-Lite specs
│   └── init()                  # Initialize connections
│
├── cortex_chat.py              # Cortex Agent communication
│   ├── CortexChat class
│   │   ├── chat()              # Main entry point
│   │   ├── _retrieve_response()# Stream SSE response
│   │   ├── conversation_history# Per-channel memory
│   │   └── clear_history()     # Reset conversation
│   └── Real-time Slack updates
│
├── cortex_response_parser.py   # Parse agent responses
│   ├── Data classes            # ToolUse, ToolResult, etc.
│   ├── parse_sse_response()    # Parse streaming events
│   ├── extract_summary()       # Extract key data
│   └── result_set extraction   # Parse Snowflake result format
│
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (not in git)
├── slack_bot.sh                # Startup script
└── ARCHITECTURE.md             # This file
```

---

## Key Functions Reference

### app.py

| Function | Description |
|----------|-------------|
| `handle_message_event(event, say, client, body)` | Main handler for user messages |
| `display_agent_response(content, say)` | Format and display agent response |
| `display_result_set_in_slack(result_set, say, table_number)` | Display tabular data with column names |
| `display_chart_in_slack(chart_data, say, slack_app, chart_number)` | Render and upload charts |
| `render_vega_chart_to_image(chart_spec)` | Convert Vega-Lite to PNG |
| `improve_chart_spec(chart_spec)` | Enhance chart with proper sorting/styling |
| `format_text_for_slack(text)` | Convert markdown to Slack mrkdwn |
| `format_markdown_table_for_slack(text)` | Convert MD tables to code blocks |
| `format_key_value_data_for_slack(text)` | Format bullet points as tables |
| `split_text_for_slack(text, max_length)` | Split long messages for Slack limit |
| `handle_planning_details_toggle(ack, body, say)` | Toggle thinking details visibility |
| `handle_clear_history(message, say)` | Clear conversation history |
| `get_snowflake_connection()` | Create Snowflake connection with PAT |
| `init()` | Initialize Snowflake and Cortex |

### cortex_chat.py

| Function | Description |
|----------|-------------|
| `CortexChat.__init__(agent_url, pat, ...)` | Initialize with agent endpoint and credentials |
| `chat(query, channel_id)` | Main entry point for agent interaction |
| `_retrieve_response(query, channel_id)` | Stream SSE response from agent |
| `set_slack_say_function(func)` | Set Slack communication function |
| `set_slack_app(app, channel_id)` | Set Slack app for message updates |
| `clear_history(channel_id)` | Clear conversation history |
| `_update_slack_with_thinking(...)` | Real-time thinking updates |
| `_smart_truncate(text, max_length)` | Truncate at word/sentence boundaries |

### cortex_response_parser.py

| Function | Description |
|----------|-------------|
| `parse_sse_response(sse_lines)` | Parse SSE streaming response |
| `parse_json_response(json_data)` | Parse non-streaming JSON |
| `extract_summary(response)` | Extract key data (text, SQL, charts, result_sets) |
| `_process_sse_line(line)` | Process individual SSE line |
| `ToolResult.sql_query` | Extract SQL from tool result |
| `ToolResult.chart_data` | Extract chart from tool result |
| `ToolResult.result_set` | Extract tabular data with columns |
| `CortexResponse.final_text` | Get final text response |
| `CortexResponse.charts` | Get all chart specifications |
| `CortexResponse.result_sets` | Get all result set data |

---

## SSE Event Types

The Cortex Agent API uses Server-Sent Events (SSE) for streaming responses:

| Event Type | Description | Data |
|------------|-------------|------|
| `response.status` | Agent status update | `{message: "Planning..."}` |
| `response.thinking` | Agent thinking content | `{text: "<thinking>...</thinking>"}` |
| `response.thinking.delta` | Streaming thinking | `{text: "partial..."}` |
| `response.tool_use` | Tool invocation | `{name: "cortex_analyst", input: {...}}` |
| `response.tool_result` | Tool execution result | `{content: [{json: {sql: "...", result_set: {...}}}]}` |
| `response.tool_result.status` | Tool status | `{message: "Executing SQL"}` |
| `response.text` | Final text response | `{text: "Here's your answer..."}` |
| `response.text.delta` | Streaming text | `{text: "partial..."}` |
| `response.chart` | Chart specification | `{chart_spec: {...}}` |
| `response` | Final response marker | Complete response object |

---

## Environment Variables

Required environment variables in `.env`:

```env
# Snowflake Configuration
ACCOUNT=your_account
HOST=your_account.snowflakecomputing.com
SNOWFLAKE_USER=your_username
SNOWFLAKE_ROLE=your_role
WAREHOUSE=your_warehouse

# Snowflake Cortex Agent
AGENT_ENDPOINT=https://your_account.snowflakecomputing.com/api/v2/databases/DB/schemas/SCHEMA/agents/AGENT:run
PAT=your_programmatic_access_token

# Slack Configuration
SLACK_APP_TOKEN=xapp-1-...
SLACK_BOT_TOKEN=xoxb-...
```

---

## Conversation History

The bot maintains conversation history per Slack channel:

```python
conversation_history = {
    "C123456": [
        {"role": "user", "content": [{"type": "text", "text": "Show me slow queries"}]},
        {"role": "assistant", "content": [{"type": "text", "text": "Here are..."}]},
        # ... up to 10 message pairs
    ]
}
```

To clear history, users can say:
- "clear history"
- "forget"
- "reset"
- "new conversation"

---

## Chart Rendering

Charts are rendered using the following pipeline:

```
Cortex Agent → Vega-Lite Spec → improve_chart_spec() → vl-convert → PNG → Slack Upload
```

Supported chart types:
- Heatmaps
- Bar charts
- Line charts
- Scatter plots
- Pie charts
- And any Vega-Lite compatible visualization

---

## Result Set Display

Tabular data from Cortex Analyst is displayed with:
- Column names extracted from `resultSetMetaData.rowType`
- Proper alignment in code blocks
- Truncation for large datasets (15 rows max displayed)
- Column width limiting (25 chars max per column)

Example output:
```
QUERY_ID   | EXECUTION_TIME | USER_NAME  | WAREHOUSE
-----------+----------------+------------+----------
01c0f51d.. | 9283869        | BOT_USER   | WH_SMALL
01c0f507.. | 9207151        | BOT_USER   | WH_SMALL
```

---

*Last updated: December 2024*
