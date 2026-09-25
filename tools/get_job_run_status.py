from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.invoke_message import InvokeMessage
from dify_plugin.entities.tool import ToolInvokeMessage

from lib.databricks_client import DatabricksAPIError, DatabricksClient, DatabricksClientError


class GetJobRunStatusTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            client = DatabricksClient(
                host=self.runtime.credentials["databricks_host"],
                token=self.runtime.credentials["databricks_token"],
            )
            result = client.get_job_run_status(run_id=int(tool_parameters["run_id"]))

            yield self.create_log_message(
                label="Databricks run status fetched",
                data={
                    "run_id": result["run_id"],
                    "life_cycle_state": result["life_cycle_state"],
                    "result_state": result["result_state"],
                },
                status=InvokeMessage.LogMessage.LogStatus.SUCCESS,
            )
            yield self.create_json_message(result)
            yield self.create_text_message(
                "Run %s is %s / %s." % (
                    result["run_id"],
                    result["life_cycle_state"],
                    result["result_state"] or "UNKNOWN",
                )
            )
        except (DatabricksAPIError, DatabricksClientError, ValueError) as exc:
            yield self.create_log_message(
                label="Databricks run status failed",
                data={"error": str(exc)},
                status=InvokeMessage.LogMessage.LogStatus.ERROR,
            )
            yield self.create_text_message("Failed to get Databricks run status: %s" % exc)
