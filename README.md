# Databricks Tools

This Dify tool plugin lets workflows interact with Databricks in two demo-friendly ways:

- execute SQL queries against a Databricks SQL warehouse
- trigger a Databricks Job and inspect its latest run status

## Included tools

- `execute_sql_statement`
- `run_job_now`
- `get_job_run_status`

## Credentials

Configure the provider with:

- `databricks_host`: your Databricks workspace host, for example `https://dbc-123456.cloud.databricks.com`
- `databricks_token`: a Databricks personal access token or another bearer token accepted by the workspace
- `warehouse_id` (optional): the default warehouse ID to use for SQL queries
- `catalog` (optional): the default catalog for SQL queries
- `schema` (optional): the default schema for SQL queries

## Databricks APIs used

- SQL Statement Execution API: `/api/2.0/sql/statements`
- Jobs API 2.0: `/api/2.0/jobs/run-now` and `/api/2.0/jobs/runs/get`

## Local testing

The core Databricks client is covered by unit tests that do not require live Databricks credentials:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Notes

- This plugin is designed as a workflow tool plugin, not a native knowledge datasource.
- For demo safety, the SQL tool blocks multi-statement queries and a set of high-risk privilege-management commands.
- The plugin follows the same high-level provider/tool separation pattern as the official Snowflake plugin, but uses Databricks REST APIs instead of a direct database connector.
