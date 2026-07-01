# Snowflake Cortex Agent + Slack Bot

A Slack bot that integrates with Snowflake Cortex Agents to provide AI-powered data analysis, query performance insights, and cost optimization recommendations directly in Slack.

![Snowflake](https://img.shields.io/badge/Snowflake-29B5E8?style=flat&logo=snowflake&logoColor=white)
![Slack](https://img.shields.io/badge/Slack-4A154B?style=flat&logo=slack&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)

## About This Project

This project is built on top of the official [Snowflake Cortex Agents Quickstart Guide](https://www.snowflake.com/en/developers/guides/integrate-snowflake-cortex-agents-with-slack/) and extends it with additional enterprise-ready capabilities for a richer Slack experience.

### Features Added On Top of the Base Quickstart

| Feature | Description |
|---------|-------------|
| 📊 **Tabular Data Display** | Query results are displayed as beautifully formatted tables with column headers, automatic width calculation, and smart truncation for large datasets |
| 📈 **Chart/Graph Rendering** | Vega-Lite chart specifications from Cortex are rendered to PNG images and uploaded directly to Slack using `vl-convert-python` |
| 💬 **Conversation Memory** | Maintains conversation history per Slack channel, allowing follow-up questions with context (configurable history length) |
| ⚡ **Real-time Thinking Updates** | Live "Thinking..." status updates with collapsible details showing agent planning steps, tool usage, and reasoning |
| 🔍 **SQL Query Transparency** | Expandable "Show Details" button reveals the SQL queries executed by Cortex Analyst with verification status |
| 📝 **Smart Text Formatting** | Markdown-to-Slack conversion, table formatting, and automatic handling of Slack's 3000 character limit |
| 📚 **Citations Display** | Search results from Cortex Search are displayed with proper citations and source references |
| 💡 **Follow-up Suggestions** | Displays AI-generated follow-up question suggestions to guide users |
| 🗑️ **Clear History Command** | Users can reset conversation context with commands like `clear history`, `forget`, or `reset` |
| ✅ **Query Verification Badge** | Shows when Cortex Analyst used a verified query for answer accuracy |

## Core Features

- 🤖 **AI-Powered Analysis** - Natural language queries powered by Snowflake Cortex Agents
- 📊 **Tabular Data Display** - Query results displayed as formatted tables with column names
- 📈 **Chart Generation** - Vega-Lite charts rendered and uploaded to Slack
- 💬 **Conversation Memory** - Maintains context across messages per channel
- ⚡ **Real-time Updates** - Live "Thinking..." status updates during processing
- 🔍 **Query Optimization** - Automatic recommendations for slow queries

## Quick Start

### Prerequisites

- Python 3.11+
- Snowflake account with Cortex Agent configured
- Slack workspace with bot permissions

### Installation

1. **Clone the repository**
   ```bash
   git@github.com:hsg09/snowflake_slack_bot-slack_bot_with_graphs.git
   cd snowflake_slack_bot
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   
   Create a `.env` file:
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

5. **Run the bot**
   ```bash
   ./slack_bot.sh
   ```

## Usage

### In Slack

**Direct Message or @mention the bot:**

```
Show me the top 10 longest-running queries from the last 7 days
```

```
Analyze warehouse costs for this month and create a chart
```

```
Find failed queries from yesterday and suggest fixes
```

### Clear Conversation History

Say any of these to reset context:
- `clear history`
- `forget`
- `reset`
- `new conversation`

### Sample Prompts

See [SAMPLE_PROMPTS.md](SAMPLE_PROMPTS.md) for 25+ detailed prompt examples covering:
- Query Performance Analysis
- Warehouse Cost Management
- Table Storage Analytics
- Task Monitoring
- Organizational Chargeback

## Project Structure

```
├── app.py                    # Main Slack bot application
├── cortex_chat.py            # Cortex Agent communication
├── cortex_response_parser.py # Response parsing & extraction
├── slack_bot.sh              # Startup script
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (not in git)
├── ARCHITECTURE.md           # Technical architecture docs
├── SAMPLE_PROMPTS.md         # Example prompts
└── README.md                 # This file
```

## Architecture

```
┌──────────┐         ┌──────────────┐         ┌─────────────────────┐
│  SLACK   │◄───────►│  SLACK BOT   │◄───────►│  SNOWFLAKE CORTEX   │
│  USER    │         │   (app.py)   │         │      AGENT API      │
└──────────┘         └──────────────┘         └─────────────────────┘
                            │
                   ┌────────┴────────┐
                   ▼                 ▼
            ┌────────────┐    ┌────────────┐
            │   Tables   │    │   Charts   │
            │  (result   │    │  (Vega-    │
            │   sets)    │    │   Lite)    │
            └────────────┘    └────────────┘
```

For detailed architecture, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `ACCOUNT` | Snowflake account identifier |
| `HOST` | Snowflake host URL |
| `SNOWFLAKE_USER` | Snowflake username |
| `SNOWFLAKE_ROLE` | Snowflake role with Cortex access |
| `WAREHOUSE` | Default warehouse |
| `AGENT_ENDPOINT` | Cortex Agent REST API endpoint |
| `PAT` | Programmatic Access Token |
| `SLACK_APP_TOKEN` | Slack app-level token (xapp-...) |
| `SLACK_BOT_TOKEN` | Slack bot token (xoxb-...) |

### Slack App Setup

1. Create a new Slack app at [api.slack.com](https://api.slack.com/apps)
2. Enable **Socket Mode**
3. Add **Bot Token Scopes**:
   - `chat:write`
   - `files:write`
   - `im:history`
   - `im:read`
   - `app_mentions:read`
4. **Subscribe to Events**:
   - `message.im`
   - `app_mention`
5. Install to workspace and copy tokens

## Dependencies

```
slack_bolt          # Slack Bot Framework
snowflake-connector # Snowflake connectivity
requests            # HTTP client
python-dotenv       # Environment management
vl-convert-python   # Vega-Lite chart rendering
pandas              # Data manipulation
```

## Troubleshooting

### "Programmatic access token is invalid"
- Regenerate PAT in Snowflake UI
- Ensure PAT was created by the correct user

### "Role not granted to user"
- Grant the role: `GRANT ROLE role_name TO USER username;`

### Charts not rendering
- Install vl-convert: `pip install vl-convert-python`

### Table too long for Slack
- Tables auto-truncate to fit Slack's 3000 char limit
- Shows row/column counts that were truncated

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is based on the [Snowflake Cortex Agents Quickstart](https://quickstarts.snowflake.com/guide/integrate_snowflake_cortex_agents_with_slack/) with additional capabilities layered on top for production use.

## Resources

- [Snowflake Cortex Agents Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)
- [Slack Bolt for Python](https://slack.dev/bolt-python/)
- [Original Quickstart Guide](https://quickstarts.snowflake.com/guide/integrate_snowflake_cortex_agents_with_slack/)
- [Getting Started with Cortex Agents and Slack](https://www.snowflake.com/en/developers/guides/integrate-snowflake-cortex-agents-with-slack/)
- [Build Snowflake Cost Savings and Performance Agent in 5 Minutes](https://medium.com/snowflake/build-snowflake-cost-savings-and-performance-agent-in-5-minutes-854427c0fdd8)

---

*Built with ❄️ Snowflake Cortex and 💬 Slack*

