"""
catalog_loader.py — Load parsed Amazon catalog data (fields + valid values) into Python dicts.

This module reads the CSV outputs of parse_catalog.py and returns structured
dictionaries that any skill or pipeline runner can consume.

Usage:
    from utils.catalog_loader import load_catalog

    catalog = load_catalog(
        market="us",
        category_path="cell_phones_accessories/accessories/chargers_power_adapters/portable_power_banks",
    )

    catalog["fields"]        → list of field dicts
    catalog["valid_values"]  → dict mapping field_name → list of allowed values
    catalog["fields_by_name"] → dict mapping field_name → field dict (quick lookup)
    catalog["sections"]      → dict mapping section_name → list of field dicts
    catalog["required_fields"] → list of field dicts where required == "Required"

Compatible with: Python 3.9+
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Path Resolution
# ---------------------------------------------------------------------------

# Project root: two levels up from this file (shared/utils/ → project root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _resolve_data_dir(
    market: str,
    category_path: str,
    project_root: Path | str | None = None,
) -> Path:
    """
    Resolve the data/ directory for a given market and category path.

    Args:
        market:        Market code (e.g., "us", "uk", "jp").
        category_path: Slash-separated category path under catalog/.
        project_root:  Override project root (defaults to auto-detected).

    Returns:
        Path to the data/ directory.

    Raises:
        FileNotFoundError: If the data directory doesn't exist.
    """
    root = Path(project_root) if project_root else _PROJECT_ROOT
    data_dir = root / "markets" / market / "catalog" / category_path / "data"

    if not data_dir.exists():
        raise FileNotFoundError(
            f"Data directory not found: {data_dir}\n"
            f"Have you run parse_catalog.py on the .xlsm file first?"
        )

    return data_dir


# ---------------------------------------------------------------------------
# CSV Readers
# ---------------------------------------------------------------------------

def _load_fields_csv(data_dir: Path) -> list[dict[str, Any]]:
    """
    Read fields.csv and return a list of field dictionaries.

    Each dict has keys:
        label, field_name, section, max_count, required,
        accepted_values, example, definition
    """
    fields_path = data_dir / "fields.csv"
    if not fields_path.exists():
        raise FileNotFoundError(f"fields.csv not found in {data_dir}")

    fields: list[dict[str, Any]] = []

    with open(fields_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Coerce max_count to int
            try:
                row["max_count"] = int(row.get("max_count", 1))
            except (ValueError, TypeError):
                row["max_count"] = 1

            fields.append(dict(row))

    return fields


def _load_valid_values_csv(data_dir: Path) -> dict[str, list[str]]:
    """
    Read valid_values.csv and return a dict mapping field_name → list of values.
    """
    vv_path = data_dir / "valid_values.csv"
    if not vv_path.exists():
        raise FileNotFoundError(f"valid_values.csv not found in {data_dir}")

    vv_map: dict[str, list[str]] = {}

    with open(vv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            field_name = row.get("field_name", "").strip()
            valid_value = row.get("valid_value", "").strip()
            if field_name and valid_value:
                vv_map.setdefault(field_name, []).append(valid_value)

    return vv_map


# ---------------------------------------------------------------------------
# Derived Indexes
# ---------------------------------------------------------------------------

def _build_fields_by_name(fields: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Build a quick-lookup dict: field_name → field dict."""
    return {f["field_name"]: f for f in fields}


def _build_sections(fields: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Group fields by their section."""
    sections: dict[str, list[dict[str, Any]]] = {}
    for f in fields:
        section = f.get("section", "Unknown")
        sections.setdefault(section, []).append(f)
    return sections


def _build_required_fields(fields: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter fields that are marked as Required."""
    return [f for f in fields if f.get("required", "").strip().lower() == "required"]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_catalog(
    market: str = "us",
    category_path: str = "",
    project_root: Path | str | None = None,
) -> dict[str, Any]:
    """
    Load the full parsed catalog for a market + category.

    Args:
        market:        Market code ("us", "uk", "jp", "mx", "cn").
        category_path: Slash-separated path under catalog/ (e.g.,
                       "cell_phones_accessories/accessories/chargers_power_adapters/portable_power_banks").
        project_root:  Override project root path (optional).

    Returns:
        Dict with keys:
            fields          — list[dict]: all fields from fields.csv
            valid_values    — dict[str, list[str]]: field_name → allowed values
            fields_by_name  — dict[str, dict]: field_name → field record
            sections        — dict[str, list[dict]]: section → fields in section
            required_fields — list[dict]: only fields where required == "Required"
            meta            — dict: market, category_path, data_dir
    """
    data_dir = _resolve_data_dir(market, category_path, project_root)

    fields = _load_fields_csv(data_dir)
    valid_values = _load_valid_values_csv(data_dir)

    return {
        "fields": fields,
        "valid_values": valid_values,
        "fields_by_name": _build_fields_by_name(fields),
        "sections": _build_sections(fields),
        "required_fields": _build_required_fields(fields),
        "meta": {
            "market": market,
            "category_path": category_path,
            "data_dir": str(data_dir),
            "total_fields": len(fields),
            "total_valid_value_fields": len(valid_values),
            "total_required_fields": len(_build_required_fields(fields)),
        },
    }


def get_field_values(catalog: dict, field_name: str) -> list[str]:
    """
    Convenience: get the valid values for a specific field.

    Returns empty list if field has no valid values.
    """
    return catalog["valid_values"].get(field_name, [])


def get_field_info(catalog: dict, field_name: str) -> dict[str, Any] | None:
    """
    Convenience: get the full field record for a specific field.

    Returns None if field not found.
    """
    return catalog["fields_by_name"].get(field_name)


def get_section_fields(catalog: dict, section: str) -> list[dict[str, Any]]:
    """
    Convenience: get all fields in a given section.

    Returns empty list if section not found.
    """
    return catalog["sections"].get(section, [])


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Quick smoke test with US power bank catalog
    cat = load_catalog(
        market="us",
        category_path="cell_phones_accessories/accessories/chargers_power_adapters/portable_power_banks",
    )

    print(f"=== Catalog Loaded ===")
    print(f"  Total fields:       {cat['meta']['total_fields']}")
    print(f"  Required fields:    {cat['meta']['total_required_fields']}")
    print(f"  Valid-value fields: {cat['meta']['total_valid_value_fields']}")
    print()

    # Show sections
    print("=== Sections ===")
    for section, flds in cat["sections"].items():
        print(f"  {section}: {len(flds)} fields")

    print()

    # Show some valid values
    for fname in ["battery_cell_composition", "color_map", "power_source_type"]:
        vals = get_field_values(cat, fname)
        print(f"  {fname}: {len(vals)} values → {vals[:5]}...")

    print()

    # Show a specific field
    info = get_field_info(cat, "battery_capacity")
    if info:
        print(f"  battery_capacity → required={info.get('required')}, "
              f"section={info.get('section')}, max_count={info.get('max_count')}")
