from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.invoke_message import InvokeMessage
from dify_plugin.entities.tool import ToolInvokeMessage

from lib.databricks_client import DatabricksAPIError, DatabricksClient, DatabricksClientError


class RunJobNowTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            client = DatabricksClient(
                host=self.runtime.credentials["databricks_host"],
                token=self.runtime.credentials["databricks_token"],
            )
            job_parameters = client.parse_json_object(
                tool_parameters.get("job_parameters_json", ""),
                "job_parameters_json",
            )
            result = client.run_job_now(
                job_id=int(tool_parameters["job_id"]),
                job_parameters=job_parameters or None,
                idempotency_token=tool_parameters.get("idempotency_token"),
            )

            yield self.create_log_message(
                label="Databricks job triggered",
                data={"job_id": result["job_id"], "run_id": result["run_id"]},
                status=InvokeMessage.LogMessage.LogStatus.SUCCESS,
            )
            yield self.create_json_message(result)
            yield self.create_text_message(
                "Triggered Databricks job %s. Run ID: %s." % (result["job_id"], result["run_id"])
            )
        except (DatabricksAPIError, DatabricksClientError, ValueError) as exc:
            yield self.create_log_message(
                label="Databricks job trigger failed",
                data={"error": str(exc)},
                status=InvokeMessage.LogMessage.LogStatus.ERROR,
            )
            yield self.create_text_message("Failed to trigger Databricks job: %s" % exc)
