# Impact Analysis

## Project
- Name: mssql-pyodbc-mcp
- CR: CR-001
- Change: Add support for a second MSSQL DB profile.

## PM Summary
- Current product supports one environment-derived MSSQL database.
- This change adds a second optional profile while preserving existing single-profile configuration and tool behavior.
- MCP callers will select a configured profile with an optional `db` argument.
- If `db` is omitted, tools use `default`.

## SA Analysis

### Requirement Understanding
- Users need one MCP server/runtime to access two configured MSSQL databases.
- Existing read-only behavior, result limits, and secret redaction remain mandatory.
- Backward compatibility matters: existing single-DB env setup should keep working.

### Business Rules
- Supported profile names are fixed as `default` and `secondary`.
- The `default` profile is required and maps to the existing `MSSQL_*` variables.
- The `secondary` profile is optional and maps to `MSSQL_SECONDARY_*` variables.
- A caller may pass `db="<configured database name>"` to select a target; `db="default"` and `db="secondary"` remain accepted as internal profile selectors.
- Omitting `db` is equivalent to `db="default"`.
- Calling `secondary` when it is not configured returns a safe configuration error.
- All profiles use SQL username/password authentication.
- All profiles are read-only at the application policy layer.

### Workflow Rules
- Agent starts MCP server using environment variables.
- Agent may call `test_connection()` for default or `test_connection(db="<MSSQL_SECONDARY_DATABASE value>")` for the second DB.
- Agent uses the same target selection pattern for table listing, schema inspection, and query execution.
- Tool responses include the selected `db` profile name in safe response metadata.

### Edge Cases
- Missing default required variables.
- Partial secondary variables are configured.
- Invalid selected profile name.
- Secondary is omitted and caller selects `secondary`.
- Both profiles point to the same database.
- Query includes cross-database SQL references.
- Query is unsafe regardless of selected profile.

### Acceptance Considerations
- Existing tests for the default profile continue to pass.
- New tests cover explicit secondary selection.
- New tests cover invalid and missing secondary profile errors.
- Documentation clearly describes the secondary environment variables and selector.

## SD Analysis

### Affected Modules
- `src/mssql_pyodbc_mcp/config.py`
  - Add profile-aware config loading.
  - Keep `DatabaseConfig` as the single-profile connection model.
- `src/mssql_pyodbc_mcp/service.py`
  - Resolve the selected profile and build a `DatabaseClient` for that profile.
  - Add optional `db` parameters to service methods.
- `src/mssql_pyodbc_mcp/server.py`
  - Expose optional `db` argument on MCP tools.
- `scripts/check_mcp_tools.py`
  - Optionally accept a profile argument for live checks.
- Tests
  - Add profile parsing and service selection coverage.
- Docs
  - Update README and env example.

### Data Model Impact
- Add a lightweight `DatabaseProfiles` holder or equivalent mapping.
- Keep connection handling single-profile per `DatabaseClient`.
- Add `profile` to `DatabaseConfig` so safe identity can include `db`.

### API Impact
- Existing:
  - `test_connection()`
  - `list_tables()`
  - `describe_table(table_name)`
  - `query(sql)`
- Updated:
  - `test_connection(db: str = "default")`
  - `list_tables(db: str = "default")`
  - `describe_table(table_name: str, db: str = "default")`
  - `query(sql: str, db: str = "default")`
- Tool response safe metadata should include `db` for connection and query-target clarity.

### Technical Risks
- MCP clients may not expose optional arguments ergonomically; defaults preserve old behavior.
- Partial secondary config must not leak password values in error details.
- Fixed two-profile support is simpler but may need expansion later.
- Cross-database SQL references are difficult to detect reliably; leave enforcement to SQL Server permissions and existing read-only SQL policy for this CR.

## Main Spec Updates Needed
- `docs/specs/system-spec.md`: update scope, requirements, business rules, API summary, risks, acceptance criteria.
- `docs/specs/api-spec.md`: add `db` input and secondary env vars.
- `docs/specs/domain-model.md`: add profile-aware model.
- `README.md`: document secondary profile usage.
- `scripts/mssql-pyodbc-mcp.env.example`: add commented secondary variables.

## Decisions
- Support exactly two profiles for CR-001: `default` and `secondary`.
- Use optional `db` selector in existing tools.
- Default selector value is `default`.
- Secondary profile is optional.
- Do not add profile-management tools.
- Do not implement cross-database SQL parsing beyond existing read-only validation.

## Ready for PG
- Yes

## Blockers
- None.
