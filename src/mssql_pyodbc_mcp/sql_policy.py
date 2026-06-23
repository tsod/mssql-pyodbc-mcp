from __future__ import annotations

import re

from .errors import ToolError


BLOCKED_KEYWORDS = {
    "alter",
    "backup",
    "begin",
    "bulk",
    "create",
    "delete",
    "drop",
    "exec",
    "execute",
    "grant",
    "insert",
    "merge",
    "reconfigure",
    "restore",
    "revoke",
    "truncate",
    "update",
}


def validate_read_only_sql(sql: str) -> str:
    normalized = _strip_leading_comments(sql).strip()
    if not normalized:
        raise ToolError("SQL_REJECTED", "SQL cannot be empty.")

    if _has_statement_separator(normalized):
        raise ToolError("SQL_REJECTED", "Multiple statements are not allowed.")

    first_word = _first_word(normalized)
    if first_word not in {"select", "with"}:
        raise ToolError("SQL_REJECTED", "Only SELECT and CTE read queries are allowed.")

    scan_text = _remove_string_literals_and_comments(normalized).lower()
    tokens = set(re.findall(r"\b[a-z_][a-z0-9_]*\b", scan_text))
    blocked = sorted(tokens.intersection(BLOCKED_KEYWORDS))
    if blocked:
        raise ToolError("SQL_REJECTED", "SQL contains blocked keyword(s).", {"blocked": blocked})

    return normalized


def _first_word(sql: str) -> str:
    match = re.match(r"([A-Za-z_][A-Za-z0-9_]*)", sql)
    return match.group(1).lower() if match else ""


def _strip_leading_comments(sql: str) -> str:
    text = sql.lstrip()
    changed = True
    while changed:
        changed = False
        if text.startswith("--"):
            _, sep, rest = text.partition("\n")
            text = rest if sep else ""
            changed = True
        elif text.startswith("/*"):
            end = text.find("*/")
            if end < 0:
                raise ToolError("SQL_REJECTED", "Unclosed block comment.")
            text = text[end + 2 :].lstrip()
            changed = True
    return text


def _has_statement_separator(sql: str) -> bool:
    return ";" in _remove_string_literals_and_comments(sql).rstrip(";")


def _remove_string_literals_and_comments(sql: str) -> str:
    result: list[str] = []
    i = 0
    in_single_quote = False
    in_bracket_identifier = False
    while i < len(sql):
        char = sql[i]
        nxt = sql[i + 1] if i + 1 < len(sql) else ""

        if in_single_quote:
            if char == "'" and nxt == "'":
                i += 2
                continue
            if char == "'":
                in_single_quote = False
            i += 1
            continue

        if in_bracket_identifier:
            if char == "]":
                in_bracket_identifier = False
            i += 1
            continue

        if char == "'":
            in_single_quote = True
            i += 1
            continue
        if char == "[":
            in_bracket_identifier = True
            i += 1
            continue
        if char == "-" and nxt == "-":
            end = sql.find("\n", i + 2)
            i = len(sql) if end < 0 else end + 1
            continue
        if char == "/" and nxt == "*":
            end = sql.find("*/", i + 2)
            if end < 0:
                raise ToolError("SQL_REJECTED", "Unclosed block comment.")
            i = end + 2
            continue

        result.append(char)
        i += 1

    if in_single_quote:
        raise ToolError("SQL_REJECTED", "Unclosed string literal.")
    if in_bracket_identifier:
        raise ToolError("SQL_REJECTED", "Unclosed bracket identifier.")

    return "".join(result)
