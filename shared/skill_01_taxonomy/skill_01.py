"""
skill_01.py — Structured Taxonomy & Attribute Injection
========================================================
Skill 01 of the Rufus Optimization Skills Library.

Goal:
    Eliminate "Information Uncertainty" by bridging the gap between raw
    product data and the Amazon Knowledge Graph via backend attribute injection.

Callable 3 ways:
    1. Direct import:  from skill_01_taxonomy.skill_01 import Skill01
    2. CLI:            python skill_01.py --input data.json --output result.json
    3. JSON stdin:     echo '{"clr": {}, "spec": {}, "btg": {}}' | python skill_01.py

Author: John / Anergy Academy
Version: 1.0.0
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Allow running as standalone script
_HERE = Path(__file__).resolve().parent.parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from utils.helpers import (
    flatten_dict,
    load_json_input,
    log_step,
    sanitize_text,
    save_json_output,
    score_to_grade,
)

# ---------------------------------------------------------------------------
# Amazon Standard Value mappings (representative subset)
# ---------------------------------------------------------------------------
COLOR_STANDARD_MAP: dict[str, str] = {
    "midnight ocean": "Navy Blue",
    "forest whisper": "Dark Green",
    "arctic mist": "Light Gray",
    "rose gold blush": "Rose Gold",
    "obsidian night": "Black",
    "champagne shimmer": "Gold",
    "desert sand": "Beige",
    "cobalt storm": "Blue",
}

MATERIAL_STANDARD_MAP: dict[str, str] = {
    "space-grade alloy": "Aluminum Alloy",
    "nano-fiber fabric": "Polyester",
    "eco-wood composite": "Bamboo",
    "military polymer": "ABS Plastic",
}

# Use-case to Knowledge Graph node mapping
USE_CASE_GRAPH_MAP: dict[str, list[str]] = {
    "camping": ["Outdoor", "Forest", "Portable Power"],
    "travel": ["Airport", "Hotel", "International"],
    "home office": ["Workspace", "Desk Setup", "Productivity"],
    "gym": ["Fitness", "Sports", "Active Lifestyle"],
    "kitchen": ["Cooking", "Food Prep", "Culinary"],
}


class Skill01:
    """
    Skill01: Structured Taxonomy & Attribute Injection

    Audits a product's backend attributes (from a Category Listing Report),
    standardizes creative values to Amazon Standard Values, maps use-cases to
    the Knowledge Graph, and returns a flat-file-ready injection payload.

    Parameters:
        clr  (dict): Category Listing Report data — dict of attribute:value pairs.
        spec (dict): Product specification sheet — dict of attribute:value pairs.
        btg  (dict): Amazon Browse Tree Guide entry — category and node metadata.
        asin (str):  Amazon ASIN for the product (optional, for labelling output).
    """

    SKILL_ID = "01"
    SKILL_NAME = "Structured Taxonomy & Attribute Injection"

    def __init__(
        self,
        clr: dict[str, Any],
        spec: dict[str, Any],
        btg: dict[str, Any],
        asin: str = "UNKNOWN",
    ) -> None:
        self.clr = clr
        self.spec = spec
        self.btg = btg
        self.asin = sanitize_text(asin)
        self._result: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _audit_null_fields(self) -> dict[str, str]:
        """Identify all empty/missing attributes across CLR and Spec. ('Death of Null' audit)"""
        nulls: dict[str, str] = {}
        all_attrs = {**self.clr, **self.spec}
        for attr, value in all_attrs.items():
            if value is None or (isinstance(value, str) and value.strip() == ""):
                nulls[attr] = "MISSING"
        return nulls

    def _standardize_values(self) -> dict[str, str]:
        """Replace creative/marketing values with Amazon Standard Values."""
        standardized: dict[str, str] = {}
        all_attrs = {**self.clr, **self.spec}

        for attr, value in all_attrs.items():
            if not isinstance(value, str):
                continue
            lower_val = value.strip().lower()

            # Color standardization
            if any(kw in attr.lower() for kw in ["color", "colour"]):
                mapped = COLOR_STANDARD_MAP.get(lower_val)
                if mapped:
                    standardized[attr] = mapped
                    continue

            # Material standardization
            if "material" in attr.lower():
                mapped = MATERIAL_STANDARD_MAP.get(lower_val)
                if mapped:
                    standardized[attr] = mapped

        return standardized

    def _map_use_cases(self) -> dict[str, list[str]]:
        """Map Specific Use attributes to Amazon Knowledge Graph nodes."""
        graph_mapping: dict[str, list[str]] = {}
        all_attrs = {**self.clr, **self.spec}

        for attr, value in all_attrs.items():
            if "use" not in attr.lower() and "purpose" not in attr.lower():
                continue
            if not isinstance(value, str):
                continue
            lower_val = value.strip().lower()
            for use_case, nodes in USE_CASE_GRAPH_MAP.items():
                if use_case in lower_val:
                    graph_mapping[value] = nodes

        return graph_mapping

    def _build_injection_payload(
        self,
        standardized: dict[str, str],
        graph_mapping: dict[str, list[str]],
        null_fields: dict[str, str],
    ) -> dict[str, Any]:
        """Assemble the final flat-file injection payload."""
        payload: dict[str, Any] = {}

        # Start with full merged attributes
        merged = {**self.spec, **self.clr}
        for attr, value in merged.items():
            if attr not in null_fields:
                payload[attr] = sanitize_text(str(value)) if isinstance(value, str) else value

        # Override with standardized values
        payload.update(standardized)

        # Attach Knowledge Graph nodes
        if graph_mapping:
            payload["knowledge_graph_nodes"] = graph_mapping

        # Attach BTG metadata
        if self.btg:
            payload["browse_tree"] = {
                "category": self.btg.get("category", ""),
                "node_id": self.btg.get("node_id", ""),
                "node_path": self.btg.get("node_path", ""),
            }

        return payload

    def _score_completeness(self, null_fields: dict, total_attrs: int) -> float:
        """Score data completeness from 0–100."""
        if total_attrs == 0:
            return 0.0
        filled = total_attrs - len(null_fields)
        return round((filled / total_attrs) * 100, 1)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> "Skill01":
        """
        Execute the full Taxonomy & Attribute Injection pipeline.

        Steps:
            1. Death-of-Null audit
            2. Value standardization
            3. Use-case Knowledge Graph mapping
            4. Injection payload assembly
            5. Completeness scoring

        Returns:
            self (for method chaining)
        """
        log_step("SKILL01_START", f"ASIN={self.asin}")

        log_step("SKILL01_NULL_AUDIT")
        null_fields = self._audit_null_fields()

        log_step("SKILL01_STANDARDIZE")
        standardized = self._standardize_values()

        log_step("SKILL01_GRAPH_MAP")
        graph_mapping = self._map_use_cases()

        log_step("SKILL01_BUILD_PAYLOAD")
        payload = self._build_injection_payload(standardized, graph_mapping, null_fields)

        total_attrs = len({**self.clr, **self.spec})
        completeness = self._score_completeness(null_fields, total_attrs)
        grade = score_to_grade(completeness)

        self._result = {
            "skill_id": self.SKILL_ID,
            "skill_name": self.SKILL_NAME,
            "asin": self.asin,
            "audit": {
                "null_fields": null_fields,
                "null_count": len(null_fields),
                "standardized_values": standardized,
                "standardized_count": len(standardized),
                "knowledge_graph_mapping": graph_mapping,
            },
            "injection_payload": payload,
            "scores": {
                "completeness_pct": completeness,
                "grade": grade,
                "high_confidence_tokens": len(payload),
            },
        }

        log_step("SKILL01_DONE", f"completeness={completeness}% grade={grade}")
        return self

    def to_json(self) -> dict[str, Any]:
        """Return the structured result as a JSON-serializable dict."""
        if not self._result:
            self.run()
        return self._result


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def _build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Skill01 — Structured Taxonomy & Attribute Injection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python skill_01.py --input product_data.json --output result.json
  echo '{"clr":{},"spec":{},"btg":{}}' | python skill_01.py
        """,
    )
    parser.add_argument("--input", "-i", help="Path to input JSON file or inline JSON string")
    parser.add_argument("--output", "-o", help="Path to write output JSON (optional)")
    parser.add_argument("--asin", default="UNKNOWN", help="Product ASIN (optional label)")
    return parser


def _run_cli(args: argparse.Namespace) -> None:
    if args.input:
        data = load_json_input(args.input)
    elif not sys.stdin.isatty():
        data = json.load(sys.stdin)
    else:
        print("Error: provide --input or pipe JSON via stdin.", file=sys.stderr)
        sys.exit(1)

    skill = Skill01(
        clr=data.get("clr", {}),
        spec=data.get("spec", {}),
        btg=data.get("btg", {}),
        asin=args.asin or data.get("asin", "UNKNOWN"),
    )
    result = skill.to_json()

    if args.output:
        out_path = save_json_output(result, args.output)
        print(f"Output written to: {out_path}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) > 1:
        _run_cli(_build_cli_parser().parse_args())
    else:
        # ── Quick smoke test ────────────────────────────────────────────
        sample_clr = {
            "item_name": "Portable Power Bank 20000mAh",
            "color_name": "Midnight Ocean",
            "material_type": "Space-Grade Alloy",
            "specific_use": "Camping, Travel",
            "batteries_included": "",
            "warranty_description": "",
        }
        sample_spec = {
            "capacity_mah": 20000,
            "output_ports": 3,
            "weight_grams": 450,
            "waterproof_rating": "IPX5",
            "charging_standard": "PD 65W",
        }
        sample_btg = {
            "category": "Electronics > Portable Power",
            "node_id": "2407749011",
            "node_path": "Electronics > Accessories > Batteries > Portable Power Banks",
        }

        skill = Skill01(clr=sample_clr, spec=sample_spec, btg=sample_btg, asin="B0EXAMPLE1")
        result = skill.to_json()
        print(json.dumps(result, ensure_ascii=False, indent=2))