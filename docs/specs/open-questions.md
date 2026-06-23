# Open Questions

- Confirm final default for `MSSQL_DRIVER`. Proposed: `ODBC Driver 18 for SQL Server`.
- Confirm final default for `MSSQL_PORT`. Proposed: `1433`.
- Confirm final default for `MSSQL_TRUST_SERVER_CERTIFICATE`. Proposed: `yes` for local/dev convenience, with README warning for production.
- Decide whether `describe_table` should require schema-qualified names or allow unqualified names with ambiguity handling.
- Decide whether query row limiting should use cursor fetch limit only, SQL wrapping, or both.
- Decide the exact MCP error response shape after selecting the Python MCP library.
- Decide whether SQL validation should use a parser dependency or a conservative custom validator for first release.
