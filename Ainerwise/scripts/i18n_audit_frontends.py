#!/usr/bin/env python3
"""Scan frontend source for user-facing text that is not obviously i18n-backed.

This is intentionally conservative: it reports candidates for review instead of
rewriting files. Use it before/after localization work to keep small cards,
subtitles, demo copy, and admin labels from slipping through.
"""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

DEFAULT_ROOTS = [
    "frontend-pc",
    "frontend-h5",
    "frontend-admin",
    "frontend",
    "modules/procurement/pc",
    "modules/procurement/h5",
    "modules/procurement/admin/src",
]

SKIP_DIRS = {
    ".git",
    ".nuxt",
    ".output",
    "dist",
    "node_modules",
    "coverage",
    ".cache",
}

TEXT_RE = re.compile(r">([^<>{}\n][^<>{}\n]{2,})<")
ATTR_RE = re.compile(r"\b(?:title|placeholder|aria-label|alt|label)=['\"]([^'\"]{2,})['\"]")
STRING_RE = re.compile(r"(?<![\w$])(?:const|let|var)\s+\w+\s*=\s*['\"]([^'\"]{3,})['\"]")
HAS_LETTER_RE = re.compile(r"[A-Za-z\u4e00-\u9fff\u0400-\u04ff]")
IGNORED_SNIPPETS = {
    "script",
    "template",
    "style",
    "true",
    "false",
    "null",
    "undefined",
}


def source_files(root: Path):
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in {".vue", ".ts", ".js", ".json"}:
            yield path


def clean_snippet(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def looks_user_facing(value: str) -> bool:
    value = clean_snippet(value)
    if not value or value.lower() in IGNORED_SNIPPETS:
        return False
    if " " not in value and re.fullmatch(r"[A-Za-z0-9_./:#-]+", value):
        return False
    if value.startswith(("http://", "https://", "/", "#", "@", "$", ".")):
        return False
    if "{{" in value or "$t(" in value or "t(" in value:
        return False
    if len(value) > 220:
        return False
    return bool(HAS_LETTER_RE.search(value))


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def scan_file(path: Path, base: Path):
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    findings = []
    rules = [("script_string", STRING_RE)]
    if path.suffix.lower() == ".vue":
        rules = [("text_node", TEXT_RE), ("attribute", ATTR_RE), ("script_string", STRING_RE)]
    for kind, regex in rules:
        for match in regex.finditer(text):
            snippet = clean_snippet(match.group(1))
            if not looks_user_facing(snippet):
                continue
            findings.append(
                {
                    "file": str(path.relative_to(base)),
                    "line": line_number(text, match.start(1)),
                    "kind": kind,
                    "text": snippet,
                }
            )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", action="append", dest="roots", help="Frontend root to scan. Can be repeated.")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--limit", type=int, default=5000)
    args = parser.parse_args()

    base = Path.cwd()
    roots = [base / root for root in (args.roots or DEFAULT_ROOTS)]
    findings = []
    for root in roots:
        if not root.exists():
            continue
        for path in source_files(root):
            findings.extend(scan_file(path, base))

    total = len(findings)
    findings = findings[: args.limit]
    if args.format == "json":
        print(json.dumps({"total": total, "returned": len(findings), "items": findings}, ensure_ascii=False, indent=2))
        return 0

    print(f"# Frontend i18n Audit\n\nTotal candidates: {total}\nDisplayed: {len(findings)}\n")
    current_file = ""
    for item in findings:
        if item["file"] != current_file:
            current_file = item["file"]
            print(f"\n## {current_file}")
        print(f"- L{item['line']} `{item['kind']}`: {item['text']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
