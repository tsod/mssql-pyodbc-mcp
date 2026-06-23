# Domain Model

## Entities

### DatabaseConfig

- Purpose: Holds environment-derived DB connection settings for one selected DB target.
- Key Fields:
  - `profile`
  - `server`
  - `database`
  - `user`
  - `password`
  - `driver`
  - `port`
  - `trust_server_certificate`
- Relationships:
  - Used by `ConnectionFactory`.
  - Validated before DB operations.

### ConnectionCheck

- Purpose: Represents connection validation result.
- Key Fields:
  - `ok`
  - `db`
  - `message`
  - `server`
  - `database`
- Relationships:
  - Returned by `test_connection`.

### TableRef

- Purpose: Represents an accessible SQL Server user table.
- Key Fields:
  - `schema`
  - `name`
  - `full_name`
- Relationships:
  - Returned by `list_tables`.
  - Used as input context for `describe_table`.

### ColumnInfo

- Purpose: Represents simple table column metadata.
- Key Fields:
  - `column_name`
  - `data_type`
  - `nullable`
- Relationships:
  - Returned by `describe_table`.

### QueryRequest

- Purpose: Represents a submitted read-only SQL query.
- Key Fields:
  - `sql`
  - `db`
- Relationships:
  - Validated by SQL policy before execution.

### QueryResult

- Purpose: Represents structured query output for agents.
- Key Fields:
  - `columns`
  - `rows`
  - `row_count`
  - `truncated`
  - `max_rows`
- Relationships:
  - Returned by `query`.

### ToolError

- Purpose: Represents safe, structured error information.
- Key Fields:
  - `code`
  - `message`
  - `details`
- Relationships:
  - Returned or raised by all tools on invalid input, configuration, connection, or execution failure.

## State Model

- Stateless server process.
- Environment configuration is read at startup or per tool call.
- Tool calls resolve the selected DB target before creating a connection.
- DB connections are opened for tool execution or managed through a lightweight connection helper.
- No application state is persisted.

## Business Constraints

- Two configured DB targets are supported.
- `default` is required; the second target is optional.
- Callers may select by `default`, `secondary`, or the configured database name.
- Read-only operations only.
- Maximum query result size is 100 rows.
- SQL username/password authentication only.
- Error handling must avoid secret leakage.
