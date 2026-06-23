# Change Request

## Project
- Name: mssql-pyodbc-mcp
- Existing Project Path: /mnt/d/AIProject/Workspaces/mssql-pyodbc-mcp
- Branch: cra/CR-001-multi-db-support

## Change Type
- New feature
- Configuration/API behavior change
- Documentation and test update

## Reason / Goal
- The current MCP server supports exactly one configured MSSQL database profile.
- The user wants to extend the tool so agent workflows can access one additional database from the same project/runtime.
- The change should preserve the existing read-only MSSQL inspection/query use case while allowing a second DB target to be configured and used safely.

## Current Behavior
- The project reads one DB profile from environment variables:
  - `MSSQL_SERVER`
  - `MSSQL_DATABASE`
  - `MSSQL_USER`
  - `MSSQL_PASSWORD`
  - `MSSQL_DRIVER`
  - `MSSQL_PORT`
  - `MSSQL_TRUST_SERVER_CERTIFICATE`
- MCP tools operate only against that one configured database:
  - `test_connection`
  - `list_tables`
  - `describe_table`
  - `query`
- Existing specs explicitly list multiple DB profiles as out of scope for the first release.

## Expected Behavior
- The MCP server can be configured with the existing DB plus one additional DB profile.
- Agents can select which configured DB target to use when checking connection, listing tables, describing a table, or running read-only queries.
- The original one-DB configuration path remains usable for backward compatibility unless PM/SD decide otherwise.
- Tool responses and errors clearly identify the selected DB target without exposing passwords or full connection strings.

## Scope
- In Scope:
  - Add support for two configured MSSQL DB profiles.
  - Define how MCP tool callers select the DB target.
  - Preserve read-only SQL validation and 100-row result limiting for all DB targets.
  - Update environment variable documentation, examples, specs, and tests.
  - Keep SQL username/password authentication.
- Out of Scope:
  - Arbitrary unlimited DB profiles unless PM/SD expands this CR.
  - Runtime creation, editing, or deletion of DB profiles through MCP tools.
  - Remote HTTP/SSE MCP hosting.
  - Windows Authentication / trusted connection.
  - Write operations, stored procedure execution, DDL, database administration, or cross-database transaction workflows.
  - UI or web dashboard.

## Affected Areas
- UI: None expected.
- API: Existing MCP tools likely need an optional DB selector input, or new DB-specific/listing tools may be introduced during design.
- Data: No application data persistence. Runtime DB configuration model must support a second profile.
- Workflow: Agent workflows must know how to choose the target DB before table inspection or querying.
- Tests: Configuration tests, service/tool behavior tests, SQL safety tests for selected targets, and backward compatibility tests.
- Docs: README, environment example, system spec, API spec, domain model, implementation plan, and open questions.
- Deployment: MCP runtime environment variables and user setup instructions need to describe the second DB.

## Non-Regression Requirements
- Existing single-DB environment configuration should continue to work unless explicitly deprecated.
- Existing tools must remain read-only.
- Existing password and connection-string redaction behavior must remain intact.
- `query` must still reject write, DDL, administrative, EXEC, and unsafe multi-statement patterns.
- Query results must still return at most 100 rows per call.
- Existing tests should continue to pass or be intentionally updated for the new API contract.

## Data / Content Impact
- No migration of project-owned data is expected.
- Existing real MSSQL databases are external systems and must not be mutated by this change.
- Additional DB credentials may be introduced through environment variables; documentation must avoid committing real secrets.

## Evidence
- Screenshots: N/A
- Error Messages: N/A
- Sample Data: N/A
- Reproduction Steps:
  1. Configure the current MCP server with one MSSQL DB.
  2. Start the stdio MCP server.
  3. Use `test_connection`, `list_tables`, `describe_table`, or `query`.
  4. Observe that all tools target only the single configured DB and there is no way to select another DB profile.
- References:
  - `docs/specs/system-spec.md` currently states one DB profile is in scope and multiple DB profiles are out of scope.
  - `docs/specs/api-spec.md` defines DB configuration as one set of `MSSQL_*` environment variables.
  - `docs/specs/domain-model.md` defines `DatabaseConfig` as a single environment-derived connection setting.

## Acceptance Signals
- A user can configure two MSSQL DB profiles in the runtime environment.
- An agent can call connection, metadata, and query tools against either configured DB target.
- Tool outputs identify the selected target DB safely.
- Existing one-DB setup remains functional.
- Unit tests cover both default/single profile compatibility and explicit second-profile targeting.
- README and env example explain how to configure and use the second DB.

## Constraints
- Keep the server local-first and stdio-based.
- Keep Python and pyodbc.
- Keep SQL account/password authentication.
- Do not expose passwords, full connection strings, or sensitive connection details in responses, logs, docs, or status files.
- Do not perform implementation in the CRA stage.

## Assumptions
- "再擴充一個DB" means support exactly one additional configured MSSQL database, for a total of two DB profiles.
- Both DB profiles use the same kind of SQL username/password authentication model.
- The second DB may have different server, database, user, password, driver, port, and trust-certificate settings.
- MCP clients can pass an additional selector field if PM/SD choose to update existing tool schemas.
- Backward compatibility with existing single-DB environment variables is desired.

## Open Questions
- Should the product support exactly two DB profiles, or should this CR generalize to named N-profile support?
- What should the DB selector look like to the MCP client: `db`, `profile`, `target`, or separate tool names?
- What should the default target be when the selector is omitted?
- Should both DB profiles be required at startup, or should the second profile be optional?
- Should profile names be fixed, such as `default` and `secondary`, or user-configurable?
- Are cross-database references inside a submitted SQL query allowed, rejected, or left to SQL Server permissions?
- Should `test_connection` test one selected DB at a time or all configured DBs by default?

## Ready for PM
- Yes

## CRA Notes
- The core change is clear enough to start PM impact analysis.
- Several API/configuration choices remain open and should be resolved during PM/SA/SD planning before implementation starts.
