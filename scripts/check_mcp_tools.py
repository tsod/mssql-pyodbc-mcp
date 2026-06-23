from __future__ import annotations

import json
import sys
from typing import Any

from mssql_pyodbc_mcp.errors import ToolError
from mssql_pyodbc_mcp.service import MssqlToolService


def dump(title: str, payload: Any) -> None:
    print("=" * 80)
    print(title)
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


def quote_identifier(identifier: str) -> str:
    return "[" + identifier.replace("]", "]]") + "]"


def main() -> int:
    service = MssqlToolService()
    db = sys.argv[1] if len(sys.argv) > 1 else "default"

    try:
        dump(f"test_connection {db}", service.test_connection(db=db))

        table_result = service.list_tables(db=db)
        tables = table_result.get("tables", [])
        dump(
            "list_tables_first_10",
            {
                "ok": table_result.get("ok"),
                "table_count": len(tables),
                "tables": tables[:10],
            },
        )

        if not tables:
            print("No tables found; describe_table and query checks were skipped.")
            return 0

        first_table = tables[0]
        full_name = first_table["full_name"]
        dump(f"describe_table {db} {full_name}", service.describe_table(full_name, db=db))

        schema = quote_identifier(first_table["schema"])
        name = quote_identifier(first_table["name"])
        sql = f"SELECT TOP (5) * FROM {schema}.{name}"
        dump(f"query {db} {sql}", service.query(sql, db=db))
        return 0
    except ToolError as exc:
        dump("tool_error", exc.to_dict())
        return 1
    except Exception as exc:
        dump("unexpected_error", {"type": type(exc).__name__, "message": str(exc)})
        return 1


if __name__ == "__main__":
    sys.exit(main())
