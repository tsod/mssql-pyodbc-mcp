from datetime import date, datetime, time
from decimal import Decimal

from mssql_pyodbc_mcp.serialization import to_json_safe


def test_common_sql_values_are_json_safe():
    assert to_json_safe(None) is None
    assert to_json_safe(Decimal("10.50")) == "10.50"
    assert to_json_safe(datetime(2026, 6, 23, 10, 5, 0)) == "2026-06-23T10:05:00"
    assert to_json_safe(date(2026, 6, 23)) == "2026-06-23"
    assert to_json_safe(time(10, 5, 0)) == "10:05:00"
    assert to_json_safe(b"abc") == "YWJj"
