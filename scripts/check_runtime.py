#!/usr/bin/env python3
"""Read-only Fiskwise toolchain discovery; network release checks fail to unknown.

Run ``python3 scripts/check_runtime.py``. Git, R, Quarto CLI, compiler tools,
and an existing writable user R library are inspected without installing or
changing anything. Stable release metadata comes from official CRAN and Quarto
GitHub endpoints; pass ``--offline`` to skip network checks.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Iterable

CRAN_R_INDEX = "https://cran.r-project.org/src/base/"
QUARTO_RELEASES = "https://api.github.com/repos/quarto-dev/quarto-cli/releases?per_page=100"


def run_version(command: list[str], pattern: str | None = None) -> str | None:
    """Run a version command without shell evaluation; return None if absent."""
    if not shutil.which(command[0]):
        return None
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=8, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    output = (result.stdout + "\n" + result.stderr).strip()
    if result.returncode:
        return None
    if pattern:
        match = re.search(pattern, output, re.IGNORECASE)
        return match.group(1) if match else output.splitlines()[0] if output else None
    return output.splitlines()[0] if output else None


def fetch_text(url: str, timeout: float = 5.0) -> str | None:
    """Fetch official release metadata; offline, HTTP, and parse failures are unknown."""
    request = urllib.request.Request(url, headers={"User-Agent": "Fiskwise-runtime-check/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")
    except (OSError, urllib.error.URLError, TimeoutError, ValueError):
        return None


def stable_lines(versions: Iterable[str], count: int = 2) -> list[str]:
    """Return newest distinct stable major.minor lines from version strings."""
    parsed: dict[tuple[int, int], tuple[int, int, int]] = {}
    for version in versions:
        match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)(?:\+.*)?", str(version).strip())
        if not match:
            continue
        major, minor, patch = map(int, match.groups())
        line = (major, minor)
        parsed[line] = max(parsed.get(line, (0, 0, 0)), (major, minor, patch))
    ordered = sorted(parsed, reverse=True)[: max(0, count)]
    return [f"{major}.{minor}" for major, minor in ordered]


def r_major_directories(html: str | None) -> list[str] | None:
    """Find R major-version directories linked from CRAN's official index."""
    if html is None:
        return None
    majors = sorted({int(value) for value in re.findall(r"href=[\"']R-(\d+)/[\"']", html)}, reverse=True)
    return [f"R-{major}/" for major in majors] or None


def r_versions_from_pages(pages: Iterable[str | None]) -> list[str] | None:
    """Extract full stable R versions from CRAN major-version directory pages."""
    versions = {version for page in pages if page is not None
                for version in re.findall(r"R-(\d+\.\d+\.\d+)\.tar\.gz", page)}
    return sorted(versions, key=lambda value: tuple(map(int, value.split("."))), reverse=True) or None


def official_r_versions(fetch=fetch_text) -> list[str] | None:
    """Discover CRAN major directories, then read their official release listings."""
    directories = r_major_directories(fetch(CRAN_R_INDEX))
    if not directories:
        return None
    pages = [fetch(CRAN_R_INDEX + directory) for directory in directories]
    return r_versions_from_pages(pages)


def quarto_stable_versions(payload: str | None) -> list[str] | None:
    """Extract stable Quarto release versions from official release JSON."""
    if payload is None:
        return None
    try:
        releases = json.loads(payload)
    except (json.JSONDecodeError, TypeError):
        return None
    versions = [item.get("tag_name", "") for item in releases
                if isinstance(item, dict) and not item.get("draft") and not item.get("prerelease")]
    stable = [v for v in versions if re.fullmatch(r"v?\d+\.\d+\.\d+(?:\+.*)?", v)]
    return sorted(stable, key=lambda value: tuple(map(int, re.match(r"v?(\d+)\.(\d+)\.(\d+)", value).groups())), reverse=True) or None


def release_action(current: str | None, versions: Iterable[str] | None) -> str:
    """Suggest an update action using discovered stable versions and their two newest lines."""
    if not current or not versions:
        return "unknown"
    versions = list(versions)
    latest = versions[0]
    lines = stable_lines(versions)
    match = re.match(r"v?(\d+)\.(\d+)\.(\d+)", current)
    if not match:
        return "unknown"
    current_line = ".".join(match.groups()[:2])
    if current_line not in lines:
        return f"upgrade to {latest} (outside newest two stable lines)"
    latest_match = re.match(r"v?(\d+)\.(\d+)\.(\d+)", latest)
    latest_line = ".".join(latest_match.groups()[:2])
    if current_line != latest_line:
        return f"supported older stable line; consider upgrade to {latest}"
    if tuple(map(int, match.groups())) < tuple(map(int, latest_match.groups())):
        return f"update to {latest}"
    return "current"


def user_library() -> dict[str, object]:
    """Inspect the configured or first R user library without creating it."""
    rscript = shutil.which("Rscript")
    configured = os.environ.get("R_LIBS_USER", "")
    if rscript:
        value = run_version([rscript, "-e", "cat(Sys.getenv('R_LIBS_USER'))"])
        if value:
            configured = value
    candidates = [Path(os.path.expanduser(p)) for p in configured.split(os.pathsep) if p]
    existing = next((p for p in candidates if p.is_dir()), None)
    return {
        "configured": configured or None,
        "existing": str(existing) if existing else None,
        "writable": bool(existing and os.access(existing, os.W_OK)),
    }


def inspect(offline: bool = False) -> dict[str, object]:
    """Collect local tool versions and official stable release metadata."""
    git_version = run_version(["git", "--version"], r"git version\s+([^\s]+)")
    r_version = run_version(["R", "--version"], r"R version\s+([^\s]+)")
    quarto_version = run_version(["quarto", "--version"], r"(\d+\.\d+\.\d+(?:[-+][^\s]+)?)")
    compiler = next((f"{name}: {version}" for name in ("clang", "gcc", "cc", "make")
                     if (version := run_version([name, "--version"]))), None)
    r_versions = None if offline else official_r_versions()
    quarto_versions = None if offline else quarto_stable_versions(fetch_text(QUARTO_RELEASES))
    r_lines = stable_lines(r_versions) if r_versions else None
    quarto_lines = stable_lines(quarto_versions) if quarto_versions else None
    return {
        "git": git_version or "unknown",
        "R": {"version": r_version or "unknown", "latest_stable_version": r_versions[0] if r_versions else "unknown",
              "latest_stable_lines": r_lines or "unknown", "action": release_action(r_version, r_versions)},
        "quarto_cli": {"version": quarto_version or "unknown", "latest_stable_version": quarto_versions[0] if quarto_versions else "unknown",
                       "latest_stable_lines": quarto_lines or "unknown", "action": release_action(quarto_version, quarto_versions)},
        "compiler": compiler or "unknown",
        "user_r_library": user_library(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="skip online release metadata checks")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()
    report = inspect(offline=args.offline)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Git: {report['git']}")
        print(f"R: {report['R']['version']} (latest stable: {report['R']['latest_stable_version']}; {report['R']['action']})")
        print(f"Quarto CLI: {report['quarto_cli']['version']} (latest stable: {report['quarto_cli']['latest_stable_version']}; {report['quarto_cli']['action']})")
        print(f"Compiler: {report['compiler']}")
        lib = report["user_r_library"]
        print(f"User R library: {lib['existing'] or 'unknown'} (writable: {lib['writable']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
