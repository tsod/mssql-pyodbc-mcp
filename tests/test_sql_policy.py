import pytest

from mssql_pyodbc_mcp.errors import ToolError
from mssql_pyodbc_mcp.sql_policy import validate_read_only_sql


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM dbo.Users",
        "  -- comment\nSELECT TOP 10 id FROM dbo.Users ORDER BY id",
        "WITH cte AS (SELECT id FROM dbo.Users) SELECT * FROM cte",
        "SELECT a.id, count(*) FROM dbo.A a JOIN dbo.B b ON a.id = b.a_id GROUP BY a.id",
    ],
)
def test_allows_general_select_queries(sql):
    assert validate_read_only_sql(sql).lower().startswith(("select", "with"))


@pytest.mark.parametrize(
    "sql",
    [
        "",
        "INSERT INTO dbo.Users(id) VALUES (1)",
        "UPDATE dbo.Users SET name = 'x'",
        "DELETE FROM dbo.Users",
        "DROP TABLE dbo.Users",
        "EXEC dbo.DoThing",
        "SELECT * FROM dbo.Users; DELETE FROM dbo.Users",
        "BEGIN TRAN SELECT * FROM dbo.Users",
    ],
)
def test_rejects_blocked_sql(sql):
    with pytest.raises(ToolError):
        validate_read_only_sql(sql)


def test_does_not_reject_keywords_inside_string_literals_or_comments():
    sql = "SELECT 'delete' AS word -- update\nFROM dbo.Users"

    assert validate_read_only_sql(sql) == sql


def test_rejects_unclosed_block_comment():
    with pytest.raises(ToolError):
        validate_read_only_sql("/* comment")
