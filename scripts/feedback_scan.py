#!/usr/bin/env python3
"""Block personal, confidential, or data-like content in a draft Fiskwise report.

Usage: python3 scripts/feedback_scan.py DRAFT [DRAFT ...]

Exit 0 when no finding, 1 when anything must be removed, 2 on usage errors.
This is a deterministic floor for public issues and pull requests; the agent and
the user still read the draft before it is submitted.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

ALLOWED_EMAIL_DOMAINS = (
    "example.com", "example.org", "example.net", "example.invalid",
    "users.noreply.github.com", "noreply.github.com", "anthropic.com",
)

LINE_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("personal-path", re.compile(
        r"(?:/Users/|/home/|/private/var/folders/|[A-Za-z]:\\Users\\)[^\s/\\<>]+", re.I)),
    ("credential", re.compile(
        r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}"
        r"|\bgithub_pat_[A-Za-z0-9_]{20,}"
        r"|\bsk-(?:ant-)?[A-Za-z0-9_-]{20,}"
        r"|\bAKIA[0-9A-Z]{16}\b"
        r"|\bxox[abprs]-[A-Za-z0-9-]{10,}"
        r"|-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("credential-assignment", re.compile(
        r"\b(?:password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key)\b"
        r"\s*[:=]\s*['\"]?(?!<)[^\s'\"<>]{6,}", re.I)),
    ("ip-address", re.compile(
        r"\b(?!127\.0\.0\.1\b)(?:\d{1,3}\.){3}\d{1,3}\b")),
    ("internal-host", re.compile(
        r"\b[\w-]+(?:\.[\w-]+)*\.(?:imr\.no|hi\.no|local|internal|lan|corp|intra)\b", re.I)),
    ("coordinates", re.compile(
        r"-?\b\d{1,2}\.\d{3,}\s*[,;\s]\s*-?\d{1,3}\.\d{3,}\b"
        r"|\b\d{1,3}\s*°\s*\d{1,2}(?:[.,]\d+)?\s*['′]")),
    ("tibble-print", re.compile(r"^#\s*A tibble:\s*\d", re.I)),
]

EMAIL = re.compile(r"\b[\w.+-]+@([\w-]+(?:\.[\w-]+)+)\b")
TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
TABLE_RULE = re.compile(r"^\s*\|?\s*:?-{3,}")
NUMBER = re.compile(r"-?\d+(?:[.,]\d+)?")
MAX_TABLE_ROWS = 8
MAX_NUMERIC_LINES = 5


@dataclass
class Finding:
    path: str
    line: int
    rule: str
    excerpt: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.rule}: {self.excerpt}"


def mask(text: str) -> str:
    """Show enough to locate a hit without echoing a secret back."""
    text = text.strip()
    return text if len(text) <= 8 else f"{text[:4]}…{text[-2:]}"


def numeric_line(line: str) -> bool:
    """A delimited line that is mostly numbers looks like a data row."""
    cells = [c for c in re.split(r"[,;\t|]|\s{2,}", line.strip()) if c.strip()]
    if len(cells) < 3:
        return False
    numeric = sum(bool(NUMBER.fullmatch(c.strip())) for c in cells)
    return numeric / len(cells) >= 0.6


def scan_text(text: str, path: str = "<draft>") -> list[Finding]:
    findings: list[Finding] = []
    lines = text.splitlines()
    for number, line in enumerate(lines, start=1):
        for rule, pattern in LINE_RULES:
            for hit in pattern.finditer(line):
                findings.append(Finding(path, number, rule, mask(hit.group(0))))
        for hit in EMAIL.finditer(line):
            domain = hit.group(1).lower()
            if not any(domain == d or domain.endswith("." + d) for d in ALLOWED_EMAIL_DOMAINS):
                findings.append(Finding(path, number, "email", mask(hit.group(0))))

    findings += block_findings(lines, path, lambda l: bool(TABLE_ROW.match(l)),
                               MAX_TABLE_ROWS, "data-table", skip=TABLE_RULE)
    findings += block_findings(lines, path, numeric_line,
                               MAX_NUMERIC_LINES, "data-rows")
    return findings


def block_findings(lines, path, is_row, limit, rule, skip=None) -> list[Finding]:
    """Flag runs of consecutive data-like lines longer than ``limit``."""
    findings, start, count = [], None, 0
    for number, line in enumerate([*lines, ""], start=1):
        if skip is not None and skip.match(line) and start is not None:
            continue
        if is_row(line):
            start = number if start is None else start
            count += 1
            continue
        if start is not None and count > limit:
            findings.append(Finding(path, start, rule,
                                    f"{count} consecutive rows; summarise or use synthetic data"))
        start, count = None, 0
    return findings


def main(argv: list[str]) -> int:
    if not argv or any(a in ("-h", "--help") for a in argv):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    findings: list[Finding] = []
    for name in argv:
        path = Path(name)
        if not path.is_file():
            print(f"feedback_scan: not a file: {name}", file=sys.stderr)
            return 2
        findings += scan_text(path.read_text(encoding="utf-8", errors="replace"), name)
    for finding in findings:
        print(finding)
    if findings:
        print(f"feedback_scan: {len(findings)} finding(s); remove them and re-run.",
              file=sys.stderr)
        return 1
    print("feedback_scan: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
