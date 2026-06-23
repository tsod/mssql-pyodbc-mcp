from __future__ import annotations

import os

import pyodbc


def main() -> int:
    required = ["MSSQL_SERVER", "MSSQL_DATABASE", "MSSQL_USER", "MSSQL_PASSWORD"]
    missing = [key for key in required if not os.environ.get(key)]
    if missing:
        print(f"Missing environment variables: {', '.join(missing)}")
        return 2

    driver = os.environ.get("MSSQL_DRIVER", "ODBC Driver 18 for SQL Server")
    print(f"Available drivers: {pyodbc.drivers()}")
    print(f"Using driver: {driver}")
    print(f"OPENSSL_CONF: {os.environ.get('OPENSSL_CONF', '(not set)')}")

    base = (
        f"DRIVER={{{driver}}};"
        f"SERVER={os.environ['MSSQL_SERVER']},{os.environ.get('MSSQL_PORT', '1433')};"
        f"DATABASE={os.environ['MSSQL_DATABASE']};"
        f"UID={os.environ['MSSQL_USER']};"
        f"PWD={os.environ['MSSQL_PASSWORD']};"
    )

    cases = [
        "Encrypt=no;TrustServerCertificate=yes;",
        "Encrypt=optional;TrustServerCertificate=yes;",
        "Encrypt=yes;TrustServerCertificate=yes;",
        "Encrypt=mandatory;TrustServerCertificate=yes;",
    ]

    for extra in cases:
        print("=" * 80)
        print(f"TRY {extra}")
        try:
            conn = pyodbc.connect(base + extra, timeout=5)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            print(f"OK {cursor.fetchone()[0]}")
            conn.close()
        except Exception as exc:
            print(f"FAIL {exc!r}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
