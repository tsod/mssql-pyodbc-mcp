# Impact Analysis

## Project
- Name: mssql-pyodbc-mcp
- CR: CR-002
- Change: Add three named optional MSSQL DB profiles.

## PM Summary
- Current product supports one required `default` profile and one optional `secondary` profile.
- This change adds three optional named profiles:
  - `Tend`
  - `ProjectWorkTracker`
  - `TWNTaxiAD`
- Existing tool signatures stay compatible. The existing optional `db` selector expands to support the three new profile names.
- Existing `MSSQL_*`, `MSSQL_SECONDARY_*`, `db="default"`, omitted `db`, `db="secondary"`, and configured database-name selection must keep working.

## SA Analysis

### Requirement Understanding
- Users need the existing MSSQL MCP server to query three additional known databases.
- Each new DB target behaves like the existing secondary profile: optional configuration, selected per tool call, and read-only.
- This is a configuration/profile expansion, not a change to SQL permissions or query semantics.

### Business Rules
- Supported profile selectors after this CR:
  - `default`
  - `secondary`
  - `Tend`
  - `ProjectWorkTracker`
  - `TWNTaxiAD`
- Selectors should be case-insensitive for profile names.
- Callers may also select by configured database name for any configured profile.
- `default` remains required and maps to `MSSQL_*`.
- `secondary` remains optional and maps to `MSSQL_SECONDARY_*`.
- The new profiles are optional and map to:
  - `MSSQL_TEND_*`
  - `MSSQL_PROJECTWORKTRACKER_*`
  - `MSSQL_TWNTAXIAD_*`
- Selecting an unconfigured optional profile returns a safe `CONFIG_MISSING` error.
- Missing optional profiles must not prevent default or other configured profiles from working.
- All profiles use SQL username/password authentication and existing read-only enforcement.

### Workflow Rules
- Runtime environment defines any desired profile groups.
- Agent calls `test_connection(db="Tend")`, `list_tables(db="ProjectWorkTracker")`, `describe_table(..., db="TWNTaxiAD")`, or `query(..., db="Tend")`.
- Agent can still omit `db` to use default.
- Agent can still use `db="secondary"` for the CR-001 optional profile.

### Edge Cases
- Optional named profile selected but no env vars exist.
- Optional named profile is partially configured.
- Profile selector differs only by case, such as `tend`.
- Configured database name overlaps with a profile selector.
- Two configured profiles point to the same database name.
- Invalid port or trust flag in one optional profile.
- Unknown selector should report all valid fixed profile names plus configured database names without secrets.

### Acceptance Considerations
- Unit tests prove all three new profiles load from their expected env keys.
- Unit tests prove direct selectors and lowercase selectors route correctly.
- Unit tests prove configured database-name selection works for named profiles.
- Unit tests prove unconfigured or partial optional profile errors are safe.
- Existing default/secondary tests continue to pass.
- README and env example include the three new groups.

### Open Questions
- None blocking PM planning.

## SD Analysis

### Design Assumptions
- Keep the implementation environment-variable based.
- Keep `DatabaseConfig` as the concrete single-profile connection model.
- Add fixed profile metadata so new profiles are data-driven within code rather than implemented as repeated conditionals.
- Continue lazy config validation at tool execution time.

### Proposed Modules
- `src/mssql_pyodbc_mcp/config.py`
  - Expand supported profile metadata.
  - Add profile-to-env-prefix mapping for default, secondary, Tend, ProjectWorkTracker, and TWNTaxiAD.
  - Keep `resolve_profile`, `match_database_name`, `allowed_db_values`, and `env_key` behavior, generalized across all profiles.
- `src/mssql_pyodbc_mcp/service.py`
  - No interface change expected; it already passes `db` into `DatabaseConfig.from_env`.
- `src/mssql_pyodbc_mcp/server.py`
  - No tool signature change expected; the optional `db` argument already exists.
- Tests
  - Extend config and service coverage for named profile routing.
- Docs/specs
  - Update scope and environment variable references.

### Main Workflow
1. MCP client calls a tool with optional `db`.
2. Service passes `db` to `DatabaseConfig.from_env`.
3. Config resolves `db` by fixed profile selector or configured database name.
4. Config maps resolved profile to the correct environment variable group.
5. Connection factory opens a connection for that selected target.
6. Existing metadata/query logic runs unchanged.

### Data Model
- Add `DatabaseProfileDefinition` concept or equivalent metadata mapping:
  - profile id used in responses, such as `tend`
  - display selector, such as `Tend`
  - environment prefix, such as `MSSQL_TEND`
  - optional/required flag
- No database schema or persisted application data changes.

### API Draft
- Tool names and input fields remain unchanged.
- `db` valid values expand to:
  - `default`
  - `secondary`
  - `Tend`
  - `ProjectWorkTracker`
  - `TWNTaxiAD`
  - configured database names from any configured profile.
- Tool responses should continue returning safe `db`, `server`, and `database` metadata. The `db` value should be the resolved internal profile id.

### Technical Risks
- The current `env_key` implementation only supports default and secondary and must be generalized carefully.
- Allowed selector output may become confusing if profile names and database names overlap.
- Case normalization must preserve user-friendly docs while keeping deterministic internal ids.
- Adding fixed profiles through hard-coded branches would increase maintenance cost if more profiles are added later.

### Open Questions
- None blocking PM planning.

## Main Spec Updates Needed
- `docs/specs/system-spec.md`
- `docs/specs/api-spec.md`
- `docs/specs/domain-model.md`
- `README.md`
- `scripts/mssql-pyodbc-mcp.env.example`

## Decisions
- Support exactly three additional named optional profiles in CR-002: `Tend`, `ProjectWorkTracker`, and `TWNTaxiAD`.
- Keep existing `default` and `secondary` profiles unchanged.
- Use full uppercase environment variable prefixes:
  - `MSSQL_TEND`
  - `MSSQL_PROJECTWORKTRACKER`
  - `MSSQL_TWNTAXIAD`
- Accept direct profile selectors case-insensitively.
- Continue accepting configured database names as selectors.
- Do not add profile-management MCP tools.
- Do not change SQL validation, row limiting, authentication mode, or transport.

## Ready for PG
- Yes

## Blockers
- None.
