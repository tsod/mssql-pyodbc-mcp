# Implementation Plan

## Suggested Milestones

1. Project scaffold and developer setup
2. Core DB configuration and connection layer
3. Tool implementation
4. Safety, serialization, and tests
5. MCP client documentation and handoff readiness

## Build Order

- Initialize Python package structure.
- Add dependency metadata for the selected MCP Python library, pyodbc, test runner, and lint/type tools as appropriate.
- Add README with environment variables, ODBC driver prerequisite notes, and Codex MCP configuration example.
- Implement `DatabaseConfig` loader:
  - Read required environment variables.
  - Apply documented defaults where approved.
  - Return safe missing/invalid configuration errors.
- Implement connection factory:
  - Build pyodbc connection string without exposing secrets.
  - Apply connection timeout.
  - Support SQL username/password authentication only.
- Implement metadata repository:
  - `list_tables`
  - `describe_table`
- Implement SQL policy:
  - Allow SELECT and CTE-style read queries.
  - Reject write, DDL, EXEC, and multi-statement input.
  - Normalize comments/whitespace enough to avoid obvious bypasses.
- Implement query execution:
  - Execute validated SQL.
  - Fetch at most 100 rows.
  - Return `truncated` when more rows are available or when using a limit strategy that can detect it.
  - Convert DB values to JSON-safe values.
- Register MCP tools:
  - `test_connection`
  - `list_tables`
  - `describe_table`
  - `query`
- Add tests:
  - Environment config validation.
  - SQL allow/block policy.
  - Result serialization.
  - Tool-level behavior with mocked pyodbc connections.
- Add optional integration test instructions requiring real MSSQL env vars.

## Risks and Mitigations

- SQL validation bypass risk:
  - Mitigation: combine conservative validation, single-statement enforcement, DB read-only account recommendation, and tests for common bypasses.
- Driver installation variability:
  - Mitigation: document ODBC Driver 18 setup and allow driver override through `MSSQL_DRIVER`.
- Result serialization failures:
  - Mitigation: centralize value conversion and test common DB types.
- Long-running queries:
  - Mitigation: set finite timeout and document that this is an inspection tool, not a reporting engine.
- Ambiguous table names:
  - Mitigation: support schema-qualified names and return clear ambiguity errors for unqualified matches.

## Testing Focus

- Missing environment variable reporting.
- Password and connection string redaction.
- Successful and failed connection checks.
- Table listing query shape.
- Schema description query shape.
- SELECT validation with:
  - simple SELECT
  - CTE
  - JOIN
  - GROUP BY
  - ORDER BY
  - blocked INSERT/UPDATE/DELETE
  - blocked DDL
  - blocked EXEC
  - multiple statement attempts
- 100-row maximum behavior.
- JSON serialization for NULL, datetime, decimal, bytes, and normal scalar values.

## PG Handoff

- PM planning is sufficient for PG to scaffold and implement the first release.
- PG should resolve open questions by choosing conservative defaults and documenting them unless the user provides different preferences before implementation.
