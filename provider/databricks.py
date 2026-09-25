from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from lib.databricks_client import DatabricksAPIError, DatabricksClient, DatabricksClientError


class DatabricksProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            client = DatabricksClient(
                host=credentials.get("databricks_host", ""),
                token=credentials.get("databricks_token", ""),
            )
            client.validate_credentials(
                default_warehouse_id=credentials.get("warehouse_id") or credentials.get("default_warehouse_id")
            )
        except (DatabricksAPIError, DatabricksClientError) as exc:
            raise ToolProviderCredentialValidationError(str(exc))
        except Exception as exc:  # pragma: no cover - defensive fallback for plugin runtime
            raise ToolProviderCredentialValidationError("Failed to validate Databricks credentials: %s" % exc)
