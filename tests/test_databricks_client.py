import unittest

from lib.databricks_client import DatabricksClient, DatabricksClientError


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=None):
        self.status_code = status_code
        self._payload = payload or {}
        if text is None:
            text = "" if payload is None else "payload"
        self.text = text

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, headers=None, timeout=None, **kwargs):
        self.calls.append(
            {
                "method": method,
                "url": url,
                "headers": headers or {},
                "timeout": timeout,
                "kwargs": kwargs,
            }
        )
        if not self.responses:
            raise AssertionError("No more fake responses configured.")
        return self.responses.pop(0)


class DatabricksClientTests(unittest.TestCase):
    def test_normalizes_host_without_scheme(self):
        client = DatabricksClient(host="dbc-123.cloud.databricks.com/", token="abc")
        self.assertEqual(client.host, "https://dbc-123.cloud.databricks.com")

    def test_rejects_missing_token(self):
        with self.assertRaises(DatabricksClientError):
            DatabricksClient(host="https://dbc-123.cloud.databricks.com", token="")

    def test_execute_sql_immediate_success(self):
        response = FakeResponse(
            payload={
                "statement_id": "stmt-1",
                "status": {"state": "SUCCEEDED"},
                "manifest": {
                    "schema": {
                        "columns": [
                            {"name": "customer"},
                            {"name": "revenue"},
                        ]
                    }
                },
                "result": {
                    "data_array": [
                        ["North", "100"],
                        ["South", "200"],
                    ]
                },
            }
        )
        session = FakeSession([response])
        client = DatabricksClient(
            host="https://dbc-123.cloud.databricks.com",
            token="abc",
            session=session,
        )

        result = client.execute_sql("select 1", warehouse_id="wh-1")

        self.assertEqual(result["statement_id"], "stmt-1")
        self.assertEqual(result["row_count"], 2)
        self.assertEqual(result["rows"][0]["customer"], "North")
        self.assertEqual(session.calls[0]["url"], "https://dbc-123.cloud.databricks.com/api/2.0/sql/statements/")

    def test_execute_sql_polls_until_success(self):
        submit = FakeResponse(payload={"statement_id": "stmt-2", "status": {"state": "PENDING"}})
        final = FakeResponse(
            payload={
                "statement_id": "stmt-2",
                "status": {"state": "SUCCEEDED"},
                "manifest": {"schema": {"columns": [{"name": "value"}]}},
                "result": {"data_array": [["ok"]]},
            }
        )
        session = FakeSession([submit, final])
        client = DatabricksClient(
            host="https://dbc-123.cloud.databricks.com",
            token="abc",
            session=session,
        )

        result = client.execute_sql(
            "select 1",
            warehouse_id="wh-1",
            wait_timeout_seconds=5,
            poll_timeout_seconds=5,
        )

        self.assertEqual(result["rows"][0]["value"], "ok")
        self.assertEqual(session.calls[1]["url"], "https://dbc-123.cloud.databricks.com/api/2.0/sql/statements/stmt-2")

    def test_execute_sql_fetches_next_chunk(self):
        initial = FakeResponse(
            payload={
                "statement_id": "stmt-3",
                "status": {"state": "SUCCEEDED"},
                "manifest": {"schema": {"columns": [{"name": "value"}]}},
                "result": {
                    "data_array": [["a"]],
                    "next_chunk_internal_link": "/api/2.0/sql/statements/stmt-3/result/chunks/1?row_offset=1",
                },
            }
        )
        chunk = FakeResponse(payload={"result": {"data_array": [["b"], ["c"]]}})
        session = FakeSession([initial, chunk])
        client = DatabricksClient(
            host="https://dbc-123.cloud.databricks.com",
            token="abc",
            session=session,
        )

        result = client.execute_sql("select 1", warehouse_id="wh-1", max_rows=3)

        self.assertEqual([row["value"] for row in result["rows"]], ["a", "b", "c"])

    def test_run_job_now_builds_expected_payload(self):
        session = FakeSession([FakeResponse(payload={"run_id": 123, "number_in_job": 4})])
        client = DatabricksClient(
            host="https://dbc-123.cloud.databricks.com",
            token="abc",
            session=session,
        )

        result = client.run_job_now(job_id=77, job_parameters={"region": "EMEA"}, idempotency_token="token-1")

        self.assertEqual(result["run_id"], 123)
        self.assertEqual(
            session.calls[0]["kwargs"]["json"],
            {"job_id": 77, "job_parameters": {"region": "EMEA"}, "idempotency_token": "token-1"},
        )

    def test_get_job_run_status_returns_state_fields(self):
        session = FakeSession(
            [
                FakeResponse(
                    payload={
                        "run_id": 456,
                        "job_id": 77,
                        "run_name": "nightly-etl",
                        "state": {
                            "life_cycle_state": "TERMINATED",
                            "result_state": "SUCCESS",
                            "state_message": "",
                        },
                    }
                )
            ]
        )
        client = DatabricksClient(
            host="https://dbc-123.cloud.databricks.com",
            token="abc",
            session=session,
        )

        result = client.get_job_run_status(run_id=456)

        self.assertEqual(result["life_cycle_state"], "TERMINATED")
        self.assertEqual(result["result_state"], "SUCCESS")

    def test_parse_json_object_rejects_non_object(self):
        with self.assertRaises(DatabricksClientError):
            DatabricksClient.parse_json_object('["not","an","object"]', "job_parameters_json")


if __name__ == "__main__":
    unittest.main()
