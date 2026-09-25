from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.invoke_message import InvokeMessage
from dify_plugin.entities.tool import ToolInvokeMessage

from lib.databricks_client import DatabricksAPIError, DatabricksClient, DatabricksClientError, DatabricksTimeoutError
from lib.sql_validation import validate_sql_query


class ExecuteSQLStatementTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        sql_query = tool_parameters.get("sql_query", "")
        sql_type = tool_parameters.get("sql_type", "SELECT").upper()
        is_valid, error_message = validate_sql_query(sql_query, sql_type)
        if not is_valid:
            yield self.create_text_message("Databricks SQL blocked: %s" % error_message)
            yield self.create_json_message(
                {
                    "success": False,
                    "error": error_message,
                    "executed_sql": sql_query,
                    "row_count": 0,
                    "columns": [],
                    "rows": [],
                }
            )
            return

        try:
            client = DatabricksClient(
                host=self.runtime.credentials["databricks_host"],
                token=self.runtime.credentials["databricks_token"],
            )
            warehouse_id = tool_parameters.get("warehouse_id") or self.runtime.credentials.get("warehouse_id")
            result = client.execute_sql(
                statement=sql_query,
                warehouse_id=warehouse_id,
                catalog=tool_parameters.get("catalog") or self.runtime.credentials.get("catalog"),
                schema=tool_parameters.get("schema") or self.runtime.credentials.get("schema"),
                wait_timeout_seconds=15,
                poll_timeout_seconds=30,
                max_rows=int(tool_parameters.get("max_rows", 100)),
            )

            yield self.create_log_message(
                label="Databricks SQL executed",
                data={
                    "statement_id": result["statement_id"],
                    "row_count": result["row_count"],
                    "columns": result["columns"],
                },
                status=InvokeMessage.LogMessage.LogStatus.SUCCESS,
            )
            yield self.create_json_message(
                {
                    "success": True,
                    "statement_id": result["statement_id"],
                    "status": result["status"],
                    "columns": result["columns"],
                    "rows": result["rows"],
                    "row_count": result["row_count"],
                    "executed_sql": sql_query,
                }
            )
            yield self.create_text_message(result["summary"])
        except (DatabricksAPIError, DatabricksClientError, DatabricksTimeoutError) as exc:
            yield self.create_log_message(
                label="Databricks SQL failed",
                data={"error": str(exc)},
                status=InvokeMessage.LogMessage.LogStatus.ERROR,
            )
            yield self.create_text_message("Databricks SQL execution failed: %s" % exc)
            yield self.create_json_message(
                {
                    "success": False,
                    "error": str(exc),
                    "executed_sql": sql_query,
                    "row_count": 0,
                    "columns": [],
                    "rows": [],
                }
            )
