# Snowflake Cortex Agent - Sample Prompts

A collection of detailed, actionable prompts for the Snowflake Data Engineer Assistant.

---

## 📊 Query Performance Analysis

### 1. Slow Query Investigation
```
Show me the top 10 longest-running queries from the last 7 days, including the execution time, user, warehouse, query text, bytes scanned, and compilation time.

Display the results in a tabular form here in Slack and create a bar chart showing execution times by query.

Analyze which queries need optimization and provide specific recommendations for each (e.g., clustering keys, warehouse sizing, query rewriting).

Send the detailed report to my email
```

### 2. Cache Efficiency Analysis
```
Find all queries from the last 14 days that scanned more than 10GB of data but had less than 50% cache hit rate.

Show me the query_id, user, warehouse, bytes_scanned, cache_hit_percentage, and execution_time in a table.

Create a scatter plot showing bytes_scanned vs cache_hit_rate to identify patterns.

Provide recommendations on how to improve cache utilization for these queries.

Email the analysis to my email
```

### 3. Failed Query Analysis
```
List all failed queries from the last 7 days with their error messages, user, warehouse, query text, and timestamp.

Group the failures by error type and show the count for each in a table and pie chart.

Identify the root causes and suggest fixes for the top 3 most common errors.

Send the error report to my email
```

### 4. User Query Patterns
```
Analyze query patterns by user for the last 30 days, showing total queries, average execution time, total bytes scanned, and credits consumed per user.

Display in a table sorted by credits consumed and create a bar chart of the top 10 users.

Identify users with inefficient query patterns and provide specific recommendations.

Email the user analysis to my email
```

### 5. Peak Load Analysis
```
Show me query execution patterns by hour of day and day of week for the last 30 days.

Create a heatmap visualization showing when our Snowflake environment is busiest.

Display the top 5 peak hours with query counts, average execution time, and warehouse utilization.

Recommend optimal scheduling windows for heavy batch jobs.

Send the load analysis to my email
```

---

## 💰 Warehouse Cost Management

### 6. Credit Consumption Deep Dive
```
Show me the credit consumption breakdown by warehouse for the last 30 days, including compute credits, cloud services credits, and total cost.

Display as a table and create a stacked bar chart showing the cost breakdown over time (weekly).

Identify warehouses with abnormally high cloud services charges and explain why this might be happening.

Provide cost optimization recommendations with expected savings.

Email the cost analysis to my email
```

### 7. Month-over-Month Cost Comparison
```
Compare warehouse costs between this month and last month, showing the change in credits consumed, percentage increase/decrease, and top cost drivers.

Create a comparison table and a side-by-side bar chart for visualization.

Identify the reasons for significant cost changes and suggest corrective actions.

Send the cost comparison report to my email
```

### 8. Warehouse Rightsizing Analysis
```
Analyze warehouse utilization patterns for the last 30 days, including average query load, peak usage times, idle time percentage, and auto-suspend settings.

Show the data in a table and create a heatmap showing usage by hour and day of week.

Recommend optimal warehouse sizes and auto-suspend configurations for each warehouse.

Calculate potential cost savings from implementing these changes.

Email the rightsizing recommendations to my email
```

### 9. Cost Anomaly Detection
```
Identify any unusual cost spikes or anomalies in the last 14 days compared to historical patterns.

Show me dates with significant cost deviations, the warehouses involved, and the queries that caused them.

Display in a table and create a line chart showing daily costs with anomalies highlighted.

Investigate root causes and suggest preventive measures.

Send the anomaly report to my email
```

### 10. Warehouse Efficiency Ranking
```
Rank all warehouses by cost efficiency for the last 30 days, showing credits consumed, queries executed, total bytes processed, and cost per GB processed.

Display in a table sorted by efficiency score and create a bar chart comparison.

Identify the least efficient warehouses and provide specific optimization strategies.

Email the efficiency ranking to my email
```

---

## 🗄️ Table Storage Analytics

### 11. Storage Growth Analysis
```
Show me the top 20 largest tables in my account with their current size, row count, creation date, last modified date, and monthly growth rate.

Display in a table and create a bar chart of the largest tables by size.

Identify tables that are growing rapidly and may need attention (partitioning, archival, clustering).

Provide storage optimization recommendations.

Send the storage report to my email
```

### 12. Clustering Effectiveness Audit
```
List all tables larger than 1GB that either lack clustering keys or have poor clustering effectiveness (depth > 5).

Show table name, database, schema, size, row count, current clustering key (if any), and clustering depth.

Create a scatter plot showing table size vs clustering depth.

Prioritize which tables would benefit most from clustering and provide specific clustering key recommendations.

Email the clustering audit to my email
```

### 13. Database Storage Distribution
```
Show me storage utilization by database and schema for the entire account.

Display hierarchically showing database > schema > total size, table count, and growth trend.

Create a treemap visualization showing storage distribution.

Identify databases or schemas that may need cleanup or archival policies.

Send the storage distribution report to my email
```

### 14. Stale Data Identification
```
Find tables that haven't been modified in the last 90 days but are larger than 100MB.

Show table name, database, schema, size, last modified date, and days since last update.

Display in a table sorted by size and create a bar chart.

Recommend which tables are candidates for archival or deletion.

Email the stale data report to my email
```

---

## ⚙️ Task Monitoring

### 15. ETL Pipeline Health Check
```
Show me all task execution history from the last 7 days, including task name, database, success/failure status, execution time, and error messages (if failed).

Calculate the success rate for each task and display in a table with a status indicator.

Create a bar chart showing task execution times and a separate chart for failure rates.

For tasks with failures, analyze the error patterns and suggest fixes.

Send the ETL health report to my email
```

### 16. Task Performance Trends
```
Analyze task execution trends over the last 30 days, showing average execution time, max execution time, and execution count per task.

Identify tasks whose execution time has increased significantly (>20%) week-over-week.

Display the data in a table and create a line chart showing execution time trends.

Provide recommendations for optimizing slow or degrading tasks.

Email the task performance analysis to my email
```

### 17. Task Failure Investigation
```
List all task failures from the last 14 days with detailed error messages, task name, database, timestamp, and run duration before failure.

Group failures by error type and show frequency.

Display in a table and create a bar chart of failures by task.

Provide root cause analysis and specific fixes for recurring failures.

Send the failure investigation to my email
```

### 18. Task Scheduling Optimization
```
Analyze task scheduling patterns and resource contention for the last 30 days.

Identify tasks that run concurrently and may be competing for resources.

Show task overlaps in a table and create a timeline visualization.

Recommend optimal scheduling adjustments to reduce contention and improve performance.

Email the scheduling optimization plan to my email
```

---

## 🏢 Organizational & Chargeback Analysis

### 19. Team Cost Allocation
```
Show me the credit consumption breakdown by team/business unit for the last quarter, including warehouse usage, storage costs, and total spend.

Display in a table grouped by team and create a pie chart showing cost distribution.

Identify teams with the highest cost growth and analyze the drivers.

Suggest cost optimization opportunities for each team.

Email the chargeback report to my email
```

### 20. Application Resource Usage
```
Analyze Snowflake resource usage by application tag for the last 30 days, showing query count, compute credits, bytes scanned, and average query time.

Create a table and bar chart comparing applications.

Identify applications with inefficient resource usage patterns (high credits, low throughput).

Provide application-specific optimization recommendations.

Send the application usage report to my email
```

### 21. Cost Center Trending
```
Show me cost trends by cost center over the last 6 months, including monthly credits, month-over-month change, and budget variance.

Display in a table and create a multi-line chart showing trends for top 5 cost centers.

Identify cost centers exceeding budget and analyze the causes.

Provide forecasts for next month based on current trends.

Email the cost center report to my email
```

---

## 🔍 Comprehensive Analysis

### 22. Full Infrastructure Health Check
```
Perform a comprehensive health check of our Snowflake environment covering:

1. Query Performance: Top 10 slowest queries, failed queries, and cache efficiency
2. Cost Analysis: Credit consumption trends, warehouse costs, and anomalies
3. Storage: Largest tables, growth trends, and clustering effectiveness
4. Tasks: ETL success rates and performance trends

Display each section in separate tables with relevant charts.

Prioritize issues by impact (High/Medium/Low) and provide actionable recommendations with expected ROI.

Create an executive summary at the top.

Email the full health check report to my email
```

### 23. Cost Optimization Roadmap
```
Identify all cost optimization opportunities in our Snowflake environment by analyzing:

1. Underutilized warehouses (idle time > 50%)
2. Oversized warehouses (avg utilization < 30%)
3. Queries without partition pruning (full table scans)
4. Tables without clustering that would benefit from it
5. Long-running tasks that could be optimized

Show each category in a table with estimated savings potential.

Create a summary chart showing total potential savings by category.

Provide specific implementation steps for the top 5 highest-impact optimizations.

Send the optimization roadmap to my email
```

### 24. Weekly Performance Report
```
Generate a weekly performance report for the last 7 days including:

1. Query Statistics: Total queries, avg execution time, failed queries, top users
2. Warehouse Metrics: Total credits consumed, busiest warehouses, cost trends
3. Notable Changes: Significant increases in cost or query times vs previous week
4. Alerts: Any concerning patterns or anomalies detected

Display key metrics in tables and create trend charts for credits and query times.

Highlight items requiring immediate attention.

Email the weekly report to my email
```

### 25. Executive Dashboard Summary
```
Create an executive summary dashboard showing:

1. Total credits consumed this month vs last month with % change
2. Top 5 most expensive warehouses
3. Query success rate and average response time
4. Storage growth trend
5. Top 3 cost optimization opportunities with potential savings

Display all metrics in a clean table format with status indicators (green/yellow/red).

Create summary charts for key trends.

Provide 3 key action items for leadership attention.

Email the executive summary to my email
```

---

## 🚀 Quick Prompts

### Simple Queries
```
Show me credit consumption for the last 7 days by warehouse.
```

```
What are the top 5 slowest queries today?
```

```
List all failed tasks from yesterday.
```

```
Show storage size for all databases.
```

### With Visualization
```
Show me daily credit consumption for the last 30 days and create a line chart.
```

```
Display warehouse utilization by hour in a heatmap.
```

```
Create a bar chart of top 10 largest tables.
```

### With Analysis
```
Analyze why our costs increased last week and suggest fixes.
```

```
Find queries that would benefit from clustering and explain why.
```

```
Identify performance bottlenecks in our ETL pipelines.
```

---

## 📝 Prompt Building Template

```
[ACTION] me [WHAT] from [TIME PERIOD], including [COLUMNS/METRICS].

Display the results in [FORMAT] and [VISUALIZATION TYPE].

[ANALYSIS REQUEST] and provide [RECOMMENDATIONS TYPE].

Send/Email to [EMAIL ADDRESS].
```

### Example Variables:
- **ACTION**: Show, List, Find, Analyze, Compare, Identify
- **TIME PERIOD**: last 7/14/30 days, this week/month/quarter, yesterday
- **FORMAT**: tabular form, grouped by X, sorted by Y
- **VISUALIZATION**: bar chart, line chart, pie chart, heatmap, scatter plot
- **ANALYSIS**: Identify patterns, Find root causes, Prioritize issues
- **RECOMMENDATIONS**: optimization suggestions, cost savings, best practices

---

*Last updated: December 2024*

