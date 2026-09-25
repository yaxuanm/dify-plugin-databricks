from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

import requests


TERMINAL_STATES = {"SUCCEEDED", "FAILED", "CANCELED", "CLOSED"}


class DatabricksClientError(Exception):
    """Base error for Databricks client failures."""


class DatabricksAPIError(DatabricksClientError):
    """Raised when Databricks returns an API error."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload or {}


class DatabricksTimeoutError(DatabricksClientError):
    """Raised when a Databricks operation does not finish in time."""


class DatabricksClient:
    def __init__(
        self,
        host: str,
        token: str,
        timeout: int = 30,
        session: Optional[requests.sessions.Session] = None,
    ) -> None:
        self.host = self._normalize_host(host)
        self.token = token.strip()
        self.timeout = timeout
        self.session = session or requests.Session()

        if not self.token:
            raise DatabricksClientError("Databricks token is required.")

    @staticmethod
    def _normalize_host(host: str) -> str:
        cleaned = (host or "").strip()
        if not cleaned:
            raise DatabricksClientError("Databricks host is required.")
        if not cleaned.startswith(("http://", "https://")):
            cleaned = "https://" + cleaned
        return cleaned.rstrip("/")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": "Bearer %s" % self.token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _build_url(self, path: str) -> str:
        if path.startswith(("http://", "https://")):
            return path
        return "%s%s" % (self.host, path)

    def _request(self, method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        headers = dict(self._headers())
        headers.update(kwargs.pop("headers", {}))
        response = self.session.request(
            method=method,
            url=self._build_url(path),
            headers=headers,
            timeout=kwargs.pop("timeout", self.timeout),
            **kwargs,
        )

        if response.status_code >= 400:
            payload = self._safe_json(response)
            message = self._extract_error_message(payload) or response.text or "Databricks API request failed."
            raise DatabricksAPIError(message, status_code=response.status_code, payload=payload)

        if not response.text:
            return {}
        return self._safe_json(response)

    @staticmethod
    def _safe_json(response: Any) -> Dict[str, Any]:
        try:
            return response.json()
        except Exception:
            return {}

    @staticmethod
    def _extract_error_message(payload: Dict[str, Any]) -> str:
        if not payload:
            return ""
        if isinstance(payload.get("message"), str):
            return payload["message"]
        status = payload.get("status") or {}
        if isinstance(status.get("error"), dict):
            if status["error"].get("message"):
                return str(status["error"]["message"])
        if isinstance(payload.get("error"), str):
            return payload["error"]
        if isinstance(payload.get("error"), dict) and payload["error"].get("message"):
            return str(payload["error"]["message"])
        return ""

    def list_sql_warehouses(self) -> Dict[str, Any]:
        return self._request("GET", "/api/2.0/sql/warehouses")

    def validate_credentials(self, default_warehouse_id: Optional[str] = None) -> None:
        if default_warehouse_id:
            self.execute_sql(
                statement="SELECT 1 AS ok",
                warehouse_id=default_warehouse_id,
                wait_timeout_seconds=5,
                poll_timeout_seconds=10,
                max_rows=1,
            )
            return
        self.list_sql_warehouses()

    def execute_sql(
        self,
        statement: str,
        warehouse_id: str,
        catalog: Optional[str] = None,
        schema: Optional[str] = None,
        wait_timeout_seconds: int = 15,
        poll_timeout_seconds: int = 30,
        max_rows: int = 100,
    ) -> Dict[str, Any]:
        if not statement or not statement.strip():
            raise DatabricksClientError("SQL statement is required.")
        if not warehouse_id or not warehouse_id.strip():
            raise DatabricksClientError("A Databricks warehouse_id is required.")

        payload: Dict[str, Any] = {
            "warehouse_id": warehouse_id.strip(),
            "statement": statement.strip(),
            "format": "JSON_ARRAY",
            "disposition": "INLINE",
            "wait_timeout": "%ss" % max(5, min(wait_timeout_seconds, 50)),
        }
        if catalog:
            payload["catalog"] = catalog.strip()
        if schema:
            payload["schema"] = schema.strip()

        response = self._request("POST", "/api/2.0/sql/statements/", json=payload)
        statement_id = response.get("statement_id")
        if not statement_id:
            raise DatabricksAPIError("Databricks did not return a statement_id.", payload=response)

        response = self._poll_statement(statement_id, response, poll_timeout_seconds)
        rows = self._collect_rows(response, max_rows=max_rows)
        status = response.get("status", {})
        state = status.get("state", "UNKNOWN")

        if state != "SUCCEEDED":
            raise DatabricksAPIError(
                self._extract_error_message(response) or "Statement did not succeed.",
                payload=response,
            )

        columns = self._extract_column_names(response)
        summary = "Returned %s row(s) across %s column(s)." % (len(rows), len(columns))
        return {
            "statement_id": statement_id,
            "status": state,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "summary": summary,
            "raw_response": response,
        }

    def _poll_statement(
        self,
        statement_id: str,
        initial_response: Dict[str, Any],
        poll_timeout_seconds: int,
        poll_interval_seconds: int = 2,
    ) -> Dict[str, Any]:
        response = initial_response
        started = time.time()
        while True:
            state = ((response.get("status") or {}).get("state") or "").upper()
            if state in TERMINAL_STATES:
                return response
            if time.time() - started >= poll_timeout_seconds:
                raise DatabricksTimeoutError(
                    "Statement %s did not finish within %s seconds." % (statement_id, poll_timeout_seconds)
                )
            time.sleep(poll_interval_seconds)
            response = self._request("GET", "/api/2.0/sql/statements/%s" % statement_id)

    def _collect_rows(self, response: Dict[str, Any], max_rows: int = 100) -> List[Dict[str, Any]]:
        column_names = self._extract_column_names(response)
        rows: List[Dict[str, Any]] = []
        rows.extend(self._rows_from_response(response, column_names))

        next_chunk = ((response.get("result") or {}).get("next_chunk_internal_link"))
        while next_chunk and len(rows) < max_rows:
            chunk_response = self._request("GET", next_chunk)
            rows.extend(self._rows_from_response(chunk_response, column_names))
            next_chunk = ((chunk_response.get("result") or {}).get("next_chunk_internal_link"))

        return rows[:max_rows]

    @staticmethod
    def _extract_column_names(response: Dict[str, Any]) -> List[str]:
        columns = (((response.get("manifest") or {}).get("schema") or {}).get("columns") or [])
        return [column.get("name", "column_%s" % index) for index, column in enumerate(columns)]

    @staticmethod
    def _rows_from_response(response: Dict[str, Any], column_names: List[str]) -> List[Dict[str, Any]]:
        data_array = ((response.get("result") or {}).get("data_array") or [])
        rows: List[Dict[str, Any]] = []
        for row in data_array:
            if isinstance(row, list):
                rows.append(dict(zip(column_names, row)))
            else:
                rows.append({"value": row})
        return rows

    def run_job_now(
        self,
        job_id: int,
        job_parameters: Optional[Dict[str, Any]] = None,
        idempotency_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"job_id": int(job_id)}
        if job_parameters:
            payload["job_parameters"] = job_parameters
        if idempotency_token:
            payload["idempotency_token"] = idempotency_token
        response = self._request("POST", "/api/2.0/jobs/run-now", json=payload)
        return {
            "job_id": int(job_id),
            "run_id": response.get("run_id"),
            "number_in_job": response.get("number_in_job"),
            "raw_response": response,
        }

    def get_job_run_status(self, run_id: int) -> Dict[str, Any]:
        response = self._request("GET", "/api/2.0/jobs/runs/get", params={"run_id": int(run_id)})
        state = response.get("state") or {}
        return {
            "run_id": int(run_id),
            "job_id": response.get("job_id"),
            "run_name": response.get("run_name"),
            "life_cycle_state": state.get("life_cycle_state"),
            "result_state": state.get("result_state"),
            "state_message": state.get("state_message"),
            "start_time": response.get("start_time"),
            "end_time": response.get("end_time"),
            "raw_response": response,
        }

    @staticmethod
    def parse_json_object(raw_value: str, field_name: str) -> Dict[str, Any]:
        value = (raw_value or "").strip()
        if not value:
            return {}
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise DatabricksClientError("%s must be valid JSON." % field_name) from exc
        if not isinstance(parsed, dict):
            raise DatabricksClientError("%s must decode to a JSON object." % field_name)
        return parsed
