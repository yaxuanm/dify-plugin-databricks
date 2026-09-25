from __future__ import annotations

import re
from typing import Tuple


ALLOWED_SQL_TYPES = {
    "SELECT",
    "INSERT",
    "UPDATE",
    "DELETE",
    "MERGE",
    "CREATE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "SHOW",
    "DESCRIBE",
}


BLOCKED_PATTERNS = [
    (r"\bGRANT\b", "Privilege management statements are blocked."),
    (r"\bREVOKE\b", "Privilege management statements are blocked."),
    (r"\bCREATE\s+USER\b", "User management statements are blocked."),
    (r"\bALTER\s+USER\b", "User management statements are blocked."),
    (r"\bDROP\s+USER\b", "User management statements are blocked."),
    (r"\bCREATE\s+GROUP\b", "Group management statements are blocked."),
    (r"\bDROP\s+GROUP\b", "Group management statements are blocked."),
    (r"\bALTER\s+GROUP\b", "Group management statements are blocked."),
    (r"\bCALL\b", "Procedure calls are blocked for safety."),
]


def validate_sql_query(sql_query: str, declared_sql_type: str) -> Tuple[bool, str]:
    sql = (sql_query or "").strip()
    if not sql:
        return False, "SQL query is required."

    normalized_type = (declared_sql_type or "SELECT").upper().strip()
    if normalized_type not in ALLOWED_SQL_TYPES:
        return False, "Unsupported SQL type: %s." % normalized_type

    if _has_multiple_statements(sql):
        return False, "Multiple SQL statements are not allowed."

    for pattern, message in BLOCKED_PATTERNS:
        if re.search(pattern, sql, re.IGNORECASE):
            return False, message

    actual_type = _detect_sql_type(sql)
    if not actual_type:
        return False, "Could not determine SQL statement type."

    if actual_type != normalized_type:
        if not (actual_type == "WITH" and normalized_type in {"SELECT", "INSERT", "UPDATE", "DELETE", "MERGE"}):
            return False, "Declared SQL type %s does not match the query." % normalized_type

    return True, ""


def _has_multiple_statements(sql: str) -> bool:
    stripped = sql.strip()
    body = stripped[:-1] if stripped.endswith(";") else stripped
    return ";" in body


def _detect_sql_type(sql: str) -> str:
    upper = sql.lstrip().upper()
    match = re.match(r"^(SELECT|INSERT|UPDATE|DELETE|MERGE|CREATE|DROP|ALTER|TRUNCATE|SHOW|DESCRIBE|WITH)\b", upper)
    return match.group(1) if match else ""
