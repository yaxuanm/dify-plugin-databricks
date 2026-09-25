# Databricks SQL end-to-end test

This is a deliberately read-only Dify plugin test. It proves the installed plugin can authenticate to a non-production Databricks workspace, execute one SQL statement, poll the Statement Execution API, and return structured rows to a Dify workflow.

## Setup boundary

1. In a non-production Databricks workspace, run `sql/01_setup_demo_fixture.sql` in the Databricks SQL editor. It creates only the synthetic `demo_codex.contracts.contract_demo_account_snapshot` fixture.
2. Install the packaged plugin in local Dify and configure the provider through the Dify credential form. Do not save a host, token, warehouse ID, or other credential in this repository.
3. In Dify, create `Databricks E2E - SQL Read Only` with three nodes:
   `User Input -> Databricks Query -> Output`.
4. Configure `Databricks Query` to use `sql/02_read_only_plugin_check.sql`, set `sql_type` to `SELECT`, and leave the tool's `warehouse_id` empty when the provider default is configured.

## Success criteria

- Provider credential validation succeeds.
- The Dify trace shows a successful `databricks_sql_query` tool call.
- The tool output has `success: true`, `status: SUCCEEDED`, and `row_count: 4`.
- The four returned records have `high` or `medium` risk flags.

## Safety

- The fixture contains synthetic demo data only.
- The Dify invocation is a single `SELECT`; it does not invoke `run_job_now`.
- Run `run_job_now` only in a separate test with an explicitly approved disposable Job ID, because it creates a real Databricks run.
