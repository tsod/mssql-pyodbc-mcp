# UI Proposal

## Main Screens

- No visual UI is planned for the first release.
- The user-facing interface is the MCP tool surface exposed to Codex and agents over stdio.

## Core User Flows

- Configure environment variables in the local MCP runtime.
- Start the MCP server from Codex or another MCP client.
- Call `test_connection` to verify DB access.
- Call `list_tables` to discover available tables.
- Call `describe_table` to inspect a selected table.
- Call `query` to run a read-only SELECT and inspect structured results.

## Interaction Notes

- Tool names should be explicit and predictable.
- Tool descriptions should clearly state read-only behavior and the 100-row limit.
- Error messages should be short, actionable, and safe for agent display.
- Returned structures should use stable field names so agents can reason over results.

## UX Risks

- If SQL rejection messages are too vague, agents may repeatedly retry invalid SQL.
- If missing environment variable errors do not list the missing keys, setup will be slow.
- If table names are not schema-qualified, agents may choose the wrong table when multiple schemas contain the same name.
- If row truncation is not explicit, agents may treat partial results as complete.
