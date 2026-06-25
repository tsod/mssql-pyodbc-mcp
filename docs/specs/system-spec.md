# System Spec

## Product Summary

`mssql-pyodbc-mcp` is a local stdio MCP server that lets Codex and agent workflows inspect and query configured Microsoft SQL Server databases through Python and pyodbc. The server is read-only, environment-configured, and intended for local developer/agent runtime use.

## Goals

- Provide agent-accessible MSSQL metadata inspection and read-only querying.
- Let agents verify DB connectivity before running data operations.
- Keep the runtime small: one required default DB target plus supported optional named DB targets, stdio transport, SQL username/password authentication.
- Reduce accidental database mutation risk by rejecting non-read SQL and limiting query results.

## Scope

- Python MCP server using pyodbc.
- stdio transport for local Codex/agent usage.
- One required default MSSQL DB target and four optional MSSQL DB targets configured through environment variables.
- SQL username/password authentication only.
- MCP tools:
  - `test_connection`
  - `list_tables`
  - `describe_table`
  - `query`
- General SELECT support, including CTEs, joins, filters, grouping, ordering, and subqueries.
- Maximum query result size: 100 rows.
- Simple table schema inspection with column name, data type, and nullable flag.

## Out of Scope

- DB targets beyond the supported fixed profiles.
- Remote HTTP/SSE MCP hosting.
- Windows Authentication / trusted connection.
- INSERT, UPDATE, DELETE, MERGE, DDL, stored procedure execution, or database administration actions.
- UI, web dashboard, or query editor.
- Query history persistence.

## User Stories

- As a Codex user, I want to check whether the configured MSSQL database is reachable before asking an agent to query it.
- As an agent, I want to list user tables so I can discover available data.
- As an agent, I want to inspect a table's simple schema so I can compose valid SELECT queries.
- As an agent, I want to execute a SELECT query and receive structured column/row results.
- As a developer, I want write operations to be rejected so the MCP server does not mutate data.

## Functional Requirements

- The server must start as a stdio MCP server.
- The server must read DB configuration from environment variables:
  - `MSSQL_SERVER`
  - `MSSQL_DATABASE`
  - `MSSQL_USER`
  - `MSSQL_PASSWORD`
  - `MSSQL_DRIVER`
  - `MSSQL_PORT`
  - `MSSQL_TRUST_SERVER_CERTIFICATE`
- The server may also read optional DB configuration from `MSSQL_SECONDARY_*`, `MSSQL_TEND_*`, `MSSQL_PROJECTWORKTRACKER_*`, and `MSSQL_TWNTAXIAD_*` equivalents.
- `test_connection` must validate selected DB configuration and attempt a lightweight DB connection.
- `list_tables` must return user tables only for the selected DB target.
- `describe_table` must accept a table identifier and return simple column metadata for the selected DB target.
- `query` must accept arbitrary read-only SELECT SQL for the selected DB target and return no more than 100 rows.
- All MCP tools must accept an optional `db` selector with `default` as the default value; callers may pass supported profile selectors or the configured database name from any configured profile.
- Errors must be agent-readable and must not expose passwords or full sensitive connection strings.
- Missing environment variables must be reported clearly.

## Business Rules

- Only read-only behavior is allowed in the first release.
- `query` permits SELECT statements and common SELECT constructs.
- `INSERT`, `UPDATE`, `DELETE`, and other mutating or schema-changing statements must be rejected.
- Result sets must be limited to 100 rows even if the submitted SQL could return more.
- The configured DB account should be read-only where practical; application-level SQL blocking is not the only protection.
- The server supports one required default DB target and four optional DB targets.
- The `default` profile is required and uses `MSSQL_*` variables.
- The second profile is optional and uses `MSSQL_SECONDARY_*` variables.
- Three additional named profiles are optional and use `MSSQL_TEND_*`, `MSSQL_PROJECTWORKTRACKER_*`, and `MSSQL_TWNTAXIAD_*` variables.
- Agent-facing DB selection may use `default`, `secondary`, `Tend`, `ProjectWorkTracker`, `TWNTaxiAD`, or configured database names.
- Profile selectors are case-insensitive.
- Selecting an unknown or unconfigured DB target must return a safe configuration error.

## Edge Cases

- Required environment variable is missing or empty.
- Secondary profile is selected but not configured.
- Named optional profile is selected but not configured.
- Named optional profile is partially configured.
- Unknown DB selector is provided.
- ODBC driver is missing or misnamed.
- SQL Server is unreachable.
- Login fails.
- Target database does not exist or user lacks access.
- Query is empty or whitespace.
- Query starts with comments before a SELECT or CTE.
- Query uses blocked keywords or multiple statements.
- Query returns zero rows.
- Query returns more than 100 rows.
- Query returns non-JSON-native values such as decimal, datetime, bytes, UUID-like values, or NULL.
- `describe_table` receives an unknown table name or ambiguous unqualified table name.
- Table names include schema qualification such as `dbo.Users`.

## Domain Model

- `DatabaseConfig`: environment-derived connection settings for one selected profile.
- `DatabaseProfile`: internal profile selector such as `default`, `secondary`, `tend`, `projectworktracker`, or `twntaxiad`; callers may also select by configured database name.
- `ConnectionCheck`: result of validating configuration and opening a connection.
- `TableRef`: schema/name reference to a SQL Server user table.
- `ColumnInfo`: simple table column metadata.
- `QueryRequest`: read-only SQL submitted by an agent.
- `QueryResult`: column names, rows, count, and truncation metadata.
- `ToolError`: structured safe error returned to the MCP client.

## Data Model

- No application database is created by this project.
- The server reads SQL Server metadata from system catalog views such as `INFORMATION_SCHEMA` or `sys` views.
- Runtime data is transient and should not be persisted.

## API Spec

- The product exposes MCP tools rather than HTTP endpoints.
- Detailed tool contract is defined in `docs/specs/api-spec.md`.
- Tool responses should be JSON-serializable dictionaries/lists suitable for agent consumption.

## Workflow / State Transitions

1. MCP client starts the server over stdio.
2. Server loads and validates environment configuration lazily at tool execution time or startup.
3. Agent calls `test_connection` with optional `db`.
4. Agent calls `list_tables` with optional `db`.
5. Agent calls `describe_table` for relevant tables with optional `db`.
6. Agent calls `query` with SELECT SQL and optional `db`.
7. Server validates SQL, executes read-only query, fetches up to 100 rows, serializes results, and returns them.
8. On invalid configuration, blocked SQL, or DB errors, server returns safe structured errors.

## Non-functional Requirements

- Local-first execution through stdio.
- Clear error messages for agents.
- Passwords and sensitive connection string content must not appear in normal responses or logs.
- Query execution should use a finite timeout to avoid hanging agent workflows.
- Implementation should be testable without requiring a live MSSQL instance for core validation logic.
- Code should isolate SQL validation, configuration loading, connection creation, metadata queries, and MCP tool registration.

## Risks

- SQL validation with arbitrary SELECT support is difficult to make perfect using string checks alone.
- pyodbc and Microsoft ODBC driver installation differ by OS.
- Result serialization may fail for SQL Server-specific Python values unless normalized.
- `TOP`, comments, CTEs, and multiple statements can complicate row limiting and safety checks.
- DB permissions are external to the MCP server and may allow writes if application checks are bypassed.

## Implementation Plan

1. Scaffold Python package, dependency metadata, MCP server entrypoint, and README.
2. Implement environment configuration loader and connection factory.
3. Implement SQL validation and safe result serialization.
4. Implement `test_connection`, `list_tables`, `describe_table`, and `query` tool logic.
5. Add unit tests for configuration, SQL blocking, row limiting behavior, and serialization.
6. Add optional integration test documentation for a real MSSQL DB.

## Acceptance Criteria

- Codex can start the MCP server through stdio.
- `test_connection` returns success when valid selected MSSQL environment variables and DB access are present.
- `list_tables` returns user tables for any configured supported profile.
- `describe_table` returns `column_name`, `data_type`, and `nullable` for a selected table in any configured supported profile.
- `query` executes valid SELECT SQL against any configured supported profile and returns at most 100 rows.
- `query` supports common SELECT constructs including CTE, joins, filters, grouping, ordering, and subqueries.
- Attempts to run INSERT, UPDATE, DELETE, DDL, EXEC, or multiple mutating statements are rejected.
- Missing or invalid configuration returns safe, agent-readable errors.

## Open Questions

- None for the current implemented scope.
