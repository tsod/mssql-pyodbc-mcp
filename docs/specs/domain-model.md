# Domain Model

## Entities

### DatabaseProfile

- Purpose: Describes one supported DB target profile and its environment variable prefix.
- Key Fields:
  - `profile`
  - `display_name`
  - `env_prefix`
  - `required`
- Supported Profiles:
  - `default`: `MSSQL_*`, required
  - `global_business`: `MSSQL_GLOBAL_BUSINESS_*`, optional
  - `tend`: `MSSQL_TEND_*`, optional
  - `projectworktracker`: `MSSQL_PROJECTWORKTRACKER_*`, optional
  - `twntaxiad`: `MSSQL_TWNTAXIAD_*`, optional
  - `254global`: `MSSQL_254GLOBAL_*`, optional
  - `twntaxiad53`: `MSSQL_TWNTAXIAD53_*`, optional
- Relationships:
  - Used to resolve `db` selectors before creating `DatabaseConfig`.

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

- One required default DB target and six optional DB targets are supported.
- `default` is required; `global_business`, `tend`, `projectworktracker`, `twntaxiad`, `254global`, and `twntaxiad53` are optional.
- Callers may select by supported profile selector or configured database name.
- Profile selectors are case-insensitive.
- `secondary` is retired and must be rejected before configured database-name matching.
- Read-only operations only.
- Maximum query result size is 100 rows.
- SQL username/password authentication only.
- Error handling must avoid secret leakage.
