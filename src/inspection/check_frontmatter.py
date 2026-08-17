#!/usr/bin/env python3
"""
Script Name  : check_frontmatter.py
Description  : Validate HTML-comment-wrapped YAML frontmatter and tag vocabulary across tracked Markdown files
Repository   : cosmos2025-anomalies
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-08-15
Link         : https://github.com/radioastronomyio/cosmos2025-anomalies

Description
-----------
Enforces the repository documentation contract from spec P2R-01 gate 1.3:
every tracked Markdown file outside the furniture exemption set carries
HTML-comment-wrapped YAML frontmatter, and every type/domain/tech/framework
tag value appears in the controlled vocabulary defined by
docs/documentation-standards/tagging-strategy.md. The vocabulary is parsed
from that document at runtime, so the guide remains the single source of
truth and this script never hardcodes allowed values.

Usage
-----
    python src/inspection/check_frontmatter.py
    python src/inspection/check_frontmatter.py --file <path>

Examples
--------
    python src/inspection/check_frontmatter.py
        Check every tracked Markdown file (git ls-files '*.md' minus
        exemptions). Exit 0 when clean, 1 with a violation listing
        otherwise.

    python src/inspection/check_frontmatter.py --file /tmp/kilo/scratch-copy.md
        Check one file regardless of git tracking; used for the gate 1.3
        mutation test on a scratch copy.
"""

# =============================================================================
# Imports
# =============================================================================

import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml

# =============================================================================
# Configuration
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parents[2]
TAGGING_STRATEGY = REPO_ROOT / "docs" / "documentation-standards" / "tagging-strategy.md"

# HUMAN NOTE: the exemption set is closed by convention (repo furniture);
# adding to it is a documentation-standards decision, not a checker tweak.
EXEMPT_BASENAMES = {"CONTRIBUTING.md", "SECURITY.md", "CODE_OF_CONDUCT.md"}

TAG_CATEGORIES = {"type", "domain", "tech", "framework"}
REQUIRED_TAG_CATEGORIES = {"type", "domain"}

FRONTMATTER_OPEN = re.compile(r"^<!--\s*\n---\s*\n")
FRONTMATTER_CLOSE = re.compile(r"\n---\s*\n-->\s*\n?", re.DOTALL)

# =============================================================================
# Functions
# =============================================================================


def load_vocabulary(strategy_path: Path) -> dict[str, set[str]]:
    """
    Parse the controlled tag vocabulary from tagging-strategy.md.

    Parameters
    ----------
    strategy_path : Path
        Location of tagging-strategy.md.

    Returns
    -------
    dict[str, set[str]]
        Allowed values per category: type, domain, tech, framework.

    Raises
    ------
    SystemExit
        If the strategy document cannot be parsed into a usable vocabulary.
    """
    text = strategy_path.read_text()
    vocab: dict[str, set[str]] = {c: set() for c in TAG_CATEGORIES}

    # Type and framework tags live in markdown tables as | `tag` | ... |
    for match in re.finditer(r"^\|\s*`([a-z0-9-]+)`\s*\|", text, re.MULTILINE):
        # AI NOTE: table rows under section 5 are type tags; the framework
        # table is empty by design and contributes nothing until filled.
        vocab["type"].add(match.group(1))

    # Domain and tech tags live in fenced yaml blocks; capture `- value`
    # entries inside each block and attribute them by preceding header.
    section = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("### ") or stripped.startswith("# This repository"):
            header = stripped.lstrip("# ").lower()
            if "domain vocabulary" in header:
                section = "domain"
            elif "technology stack" in header:
                section = "tech"
            else:
                section = None
        elif stripped.startswith("```"):
            if section and stripped == "```":
                section = None
        elif section and stripped.startswith("- ") and not stripped.startswith("- #"):
            value = stripped[2:].split("#")[0].strip()
            if value:
                vocab[section].add(value)

    if not vocab["type"] or not vocab["domain"]:
        sys.exit(f"unusable vocabulary parsed from {strategy_path}")

    return vocab


def tracked_markdown_files() -> list[Path]:
    """Enumerate tracked Markdown files minus the furniture exemption set."""
    output = subprocess.run(
        ["git", "ls-files", "*.md"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout
    files = []
    for rel in output.splitlines():
        path = REPO_ROOT / rel
        if path.name in EXEMPT_BASENAMES or path.name.startswith("LICENSE"):
            continue
        files.append(path)
    return files


def extract_frontmatter(path: Path) -> tuple[str | None, int]:
    """
    Extract the YAML payload from HTML-comment-wrapped frontmatter.

    Parameters
    ----------
    path : Path
        Markdown file to read.

    Returns
    -------
    tuple[str | None, int]
        YAML text (or None when absent/malformed) and the 1-based line
        number where the frontmatter block ends in the file.
    """
    text = path.read_text()
    opening = FRONTMATTER_OPEN.match(text)
    if not opening:
        return None, 0
    closing = FRONTMATTER_CLOSE.search(text, opening.end())
    if not closing:
        return None, text.count("\n", 0, len(text)) + 1
    payload = text[opening.end() : closing.start()]
    end_line = text.count("\n", 0, closing.start()) + 1
    return payload, end_line


def check_file(path: Path, vocab: dict[str, set[str]]) -> list[str]:
    """
    Validate one Markdown file against the frontmatter contract.

    Parameters
    ----------
    path : Path
        File to check.
    vocab : dict[str, set[str]]
        Allowed tag values per category.

    Returns
    -------
    list[str]
        Human-readable violations, empty when the file passes.
    """
    violations: list[str] = []
    payload, end_line = extract_frontmatter(path)
    rel = path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path

    if payload is None:
        return [f"{rel}: missing or malformed HTML-comment-wrapped frontmatter"]

    try:
        data = yaml.safe_load(payload)
    except yaml.YAMLError as exc:
        return [f"{rel}:{end_line}: frontmatter does not parse as YAML ({exc})"]

    if not isinstance(data, dict):
        return [f"{rel}:{end_line}: frontmatter is not a YAML mapping"]

    if not isinstance(data.get("title"), str) or not data["title"].strip():
        violations.append(f"{rel}:{end_line}: missing non-empty title")
    # HUMAN NOTE: `date` is standard; the project-brief template uses
    # `created` per its own schema. Either satisfies the date requirement.
    date_value = data.get("date") or data.get("created")
    if not isinstance(date_value, str) or not date_value.strip():
        violations.append(f"{rel}:{end_line}: missing date")

    tags = data.get("tags")
    if not isinstance(tags, list) or not tags:
        return violations + [f"{rel}:{end_line}: tags missing or empty"]

    seen_categories: set[str] = set()
    for tag_line in tags:
        # YAML loads `- type: guide` as a single-key dict and
        # `- domain: [a, b]` as {domain: [a, b]}; accept both shapes.
        if isinstance(tag_line, dict):
            if len(tag_line) != 1:
                violations.append(f"{rel}:{end_line}: tag entry has multiple keys ({tag_line!r})")
                continue
            key, raw = next(iter(tag_line.items()))
        elif isinstance(tag_line, str) and ":" in tag_line:
            key, _, raw = tag_line.partition(":")
            key, raw = key.strip(), raw.strip()
        else:
            violations.append(f"{rel}:{end_line}: tag entry is not 'key: value' ({tag_line!r})")
            continue
        if not isinstance(key, str):
            violations.append(f"{rel}:{end_line}: tag key is not a string ({key!r})")
            continue
        if key not in TAG_CATEGORIES:
            violations.append(f"{rel}:{end_line}: unknown tag category {key!r}")
            continue
        seen_categories.add(key)
        values = raw if isinstance(raw, list) else [raw]
        for value in values:
            value = str(value).strip()
            if value not in vocab[key]:
                violations.append(
                    f"{rel}:{end_line}: {key} tag {value!r} not in tagging-strategy.md vocabulary"
                )

    for category in sorted(REQUIRED_TAG_CATEGORIES - seen_categories):
        violations.append(f"{rel}:{end_line}: required tag category {category!r} not present")

    return violations


# =============================================================================
# Entry Point
# =============================================================================


def main() -> None:
    """Run the frontmatter contract check and report violations."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, help="check a single file instead of the tracked set")
    args = parser.parse_args()

    vocab = load_vocabulary(TAGGING_STRATEGY)
    files = [args.file.resolve()] if args.file else tracked_markdown_files()

    violations: list[str] = []
    for path in files:
        if not path.exists():
            violations.append(f"{path}: file does not exist")
            continue
        violations.extend(check_file(path, vocab))

    if violations:
        print(f"frontmatter check: {len(violations)} violation(s)")
        for violation in violations:
            print(f"  {violation}")
        sys.exit(1)
    print(f"frontmatter check: {len(files)} file(s) clean, zero violations")


if __name__ == "__main__":
    main()
