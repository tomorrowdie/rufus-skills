"""
helpers.py — Shared utility functions for the Rufus Optimization Skills Library.

All skill modules import from this file to avoid code duplication.
Compatible with: Python 3.9+, n8n (subprocess/API), Claude Code, any Python agent.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Text Processing
# ---------------------------------------------------------------------------

def sanitize_text(text: str, max_length: int = 0, strip_html: bool = True) -> str:
    """
    Clean and normalize a string for use in Amazon listing copy.

    - Strips leading/trailing whitespace
    - Normalizes unicode (NFC)
    - Optionally removes HTML tags
    - Collapses multiple spaces/newlines into a single space
    - Optionally truncates to max_length characters

    Args:
        text:       Raw input string.
        max_length: If > 0, truncate the result to this many characters.
        strip_html: If True, remove all HTML/XML tags before sanitizing.

    Returns:
        Cleaned string.
    """
    if not isinstance(text, str):
        text = str(text)

    text = unicodedata.normalize("NFC", text)

    if strip_html:
        text = re.sub(r"<[^>]+>", " ", text)

    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r" {2,}", " ", text)
    text = text.strip()

    if max_length > 0:
        text = text[:max_length].rstrip()

    return text


def truncate_to_chars(text: str, limit: int, ellipsis: bool = False) -> str:
    """
    Truncate text to exactly `limit` characters, optionally adding '…'.

    Args:
        text:      Input string.
        limit:     Maximum character count.
        ellipsis:  Append '…' if truncation occurred (costs 1 char from limit).

    Returns:
        Possibly truncated string.
    """
    if len(text) <= limit:
        return text
    if ellipsis:
        return text[: limit - 1].rstrip() + "…"
    return text[:limit].rstrip()


def slugify(text: str) -> str:
    """
    Convert a string to a lowercase URL/filename-safe slug.

    Example:
        "High-Speed Blender (Pro)" -> "high-speed-blender-pro"

    Args:
        text: Input string.

    Returns:
        Slug string.
    """
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text


# ---------------------------------------------------------------------------
# Noun Phrase / Semantic Utilities
# ---------------------------------------------------------------------------

def count_noun_phrases(text: str, phrase_list: list[str]) -> dict[str, int]:
    """
    Count how many times each noun phrase from `phrase_list` appears in `text`.

    Matching is case-insensitive and whole-word where possible.

    Args:
        text:        The body of copy to search.
        phrase_list: List of noun phrases (e.g., ["portable charger", "fast charge"]).

    Returns:
        Dict mapping each phrase to its occurrence count.
    """
    text_lower = text.lower()
    result: dict[str, int] = {}
    for phrase in phrase_list:
        pattern = re.compile(re.escape(phrase.lower()))
        result[phrase] = len(pattern.findall(text_lower))
    return result


def rotate_connector(connector_list: list[str], current_index: int) -> tuple[str, int]:
    """
    Round-robin connector rotation for building varied bullet-point openers.

    Connectors include transitional phrases that prevent repetitive copy starts
    (e.g., "Designed for", "Built for", "Perfect for", "Ideal when").

    Args:
        connector_list:  List of connector strings.
        current_index:   The index of the last-used connector.

    Returns:
        Tuple of (next_connector, next_index).

    Example:
        connectors = ["Designed for", "Built for", "Ideal when"]
        phrase, idx = rotate_connector(connectors, 0)
        # phrase = "Built for", idx = 1
    """
    if not connector_list:
        return ("", 0)
    next_index = (current_index + 1) % len(connector_list)
    return connector_list[next_index], next_index


# ---------------------------------------------------------------------------
# JSON I/O
# ---------------------------------------------------------------------------

def load_json_input(source: str | dict | Path) -> dict[str, Any]:
    """
    Load a JSON payload from a file path, JSON string, or pass-through dict.

    Supports three calling conventions used by n8n, CLI, and direct Python calls:
      1. dict   → returned as-is (direct Python / agent call)
      2. str    → tried as JSON string first, then as a file path
      3. Path   → read from file

    Args:
        source: Input data as dict, JSON string, or file path.

    Returns:
        Parsed dict.

    Raises:
        ValueError: If parsing fails.
        FileNotFoundError: If a path is given but the file doesn't exist.
    """
    if isinstance(source, dict):
        return source

    if isinstance(source, Path):
        with open(source, "r", encoding="utf-8") as fh:
            return json.load(fh)

    if isinstance(source, str):
        stripped = source.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            try:
                return json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON string: {exc}") from exc
        path = Path(stripped)
        if path.exists():
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        raise FileNotFoundError(f"File not found: {stripped}")

    raise ValueError(f"Unsupported source type: {type(source)}")


def save_json_output(data: dict | list, output_path: str | Path | None) -> Path | None:
    """
    Write a JSON-serializable payload to disk, creating parent directories,
    or print to stdout if output_path is None.

    Args:
        data:        Dict or list to serialise.
        output_path: Destination file path, or None for stdout.

    Returns:
        Resolved Path of the written file, or None if printed to stdout.
    """
    if output_path is None:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return None
        
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    return out.resolve()


# ---------------------------------------------------------------------------
# Data Structure Utilities
# ---------------------------------------------------------------------------

def flatten_dict(nested: dict, parent_key: str = "", sep: str = ".") -> dict[str, Any]:
    """
    Recursively flatten a nested dict into a single-level dict with dotted keys.

    Example:
        {"a": {"b": 1, "c": 2}} -> {"a.b": 1, "a.c": 2}

    Args:
        nested:     The nested dictionary.
        parent_key: Prefix accumulated from parent levels (used in recursion).
        sep:        Separator between key segments.

    Returns:
        Flat dictionary.
    """
    items: list[tuple[str, Any]] = []
    for k, v in nested.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


# ---------------------------------------------------------------------------
# Scoring / Grading
# ---------------------------------------------------------------------------

def score_to_grade(score: float, thresholds: dict[str, float] | None = None) -> str:
    """
    Convert a numeric score (0–100) to a letter grade using configurable thresholds.

    Default thresholds: A≥90, B≥75, C≥60, D≥40, F<40

    Args:
        score:      Numeric score from 0 to 100.
        thresholds: Optional dict mapping grade letters to minimum scores.

    Returns:
        Grade letter string (e.g., "A", "B+", "F").
    """
    if thresholds is None:
        thresholds = {"A": 90, "B": 75, "C": 60, "D": 40, "F": 0}
    for grade, minimum in sorted(thresholds.items(), key=lambda x: -x[1]):
        if score >= minimum:
            return grade
    return "F"


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log_step(step: str, detail: str = "", level: str = "INFO") -> None:
    """
    Print a timestamped log line to stdout.

    Format: [2026-02-28T12:00:00Z INFO] Step: detail

    Args:
        step:   Short label for the operation (e.g., "NPO_SCAN").
        detail: Additional context.
        level:  Log level label (INFO, WARN, ERROR).
    """
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    suffix = f": {detail}" if detail else ""
    print(f"[{ts} {level}] {step}{suffix}", file=sys.stdout, flush=True)