"""
skill_05.py — A+ Knowledge Base Engineering
============================================
Skill 05 of the Rufus Optimization Skills Library.

Goal:
    Transform A+ content from a design showcase into a technical manual for
    AI indexing, lowering Rufus's "Hallucination Risk" during product recommendations.

Logic:
    - Comparison Power Play: validate comparison table has semantic headers + specific data
    - Technical Appendices: detect presence of FAQ/specs module (fallback source of truth)
    - Data specificity check: flag vague values (e.g., "Long battery life" → "24 Hours")
    - Hallucination risk scoring: measure how many claims lack a numeric/factual anchor

Callable 3 ways:
    1. Direct import:  from skill_05_aplus.skill_05 import Skill05
    2. CLI:            python skill_05.py --input data.json --output result.json
    3. JSON stdin:     echo '{"comparison_table": {}, "modules": []}' | python skill_05.py

Author: John / Anergy Academy
Version: 1.0.0
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent.parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from utils.helpers import (
    load_json_input,
    log_step,
    sanitize_text,
    save_json_output,
    score_to_grade,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Semantic headers that signal a knowledge-base-ready comparison table
SEMANTIC_HEADERS = [
    "waterproof rating", "battery life", "charging speed", "weight",
    "dimensions", "compatibility", "warranty", "material", "capacity",
    "output power", "certifications", "operating temperature",
]

# A+ module types that serve as fallback source of truth for RAG
KNOWLEDGE_BASE_MODULES = [
    "faq", "technical_specs", "comparison_table", "specification_chart",
    "q&a", "detailed_description", "product_description_text",
]

# Vague terms that lack a quantified anchor (hallucination risk)
VAGUE_TERMS = [
    "long battery life", "fast charging", "lightweight", "durable",
    "high quality", "premium", "advanced", "powerful", "efficient",
    "smart", "easy to use", "compact",
]

# Pattern to detect numeric/specific data anchors
SPECIFIC_DATA_PATTERN = re.compile(
    r"\b(\d+(\.\d+)?\s*(mah|wh|w|v|a|kg|lbs|oz|g|h|min|hrs|hours|inches|cm|mm|ip[x\d]+|mil-std|°[cf]))\b",
    re.IGNORECASE,
)


class Skill05:
    """
    Skill05: A+ Knowledge Base Engineering

    Audits an A+ content structure for AI indexability, validates comparison
    table semantic quality, and produces a hallucination risk score.

    Parameters:
        comparison_table  (dict):       A+ comparison table: {header: {asin: value}}
        modules           (list[dict]): A+ modules list. Each: {"type": str, "content": str}
        product_claims    (list[str]):  Key claims from title/bullets to verify in A+.
        asin              (str):        ASIN label.
    """

    SKILL_ID = "05"
    SKILL_NAME = "A+ Knowledge Base Engineering"

    def __init__(
        self,
        comparison_table: dict[str, Any] | None = None,
        modules: list[dict[str, Any]] | None = None,
        product_claims: list[str] | None = None,
        asin: str = "UNKNOWN",
    ) -> None:
        self.comparison_table = comparison_table or {}
        self.modules = modules or []
        self.product_claims = [sanitize_text(c) for c in (product_claims or [])]
        self.asin = sanitize_text(asin)
        self._result: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _audit_comparison_table(self) -> dict[str, Any]:
        """Evaluate comparison table headers for semantic quality."""
        if not self.comparison_table:
            return {
                "has_table": False,
                "semantic_headers_found": [],
                "semantic_headers_missing": SEMANTIC_HEADERS[:5],
                "semantic_header_score": 0.0,
                "specific_data_ratio": 0.0,
                "recommendations": ["Add a Comparison Table module with semantic headers"],
            }

        headers_lower = [h.lower() for h in self.comparison_table.keys()]
        found = [h for h in SEMANTIC_HEADERS if any(h in hl for hl in headers_lower)]
        missing = [h for h in SEMANTIC_HEADERS if h not in found]
        header_score = round(len(found) / len(SEMANTIC_HEADERS) * 100, 1)

        # Check values for specific data (numbers + units)
        all_values = []
        for header_data in self.comparison_table.values():
            if isinstance(header_data, dict):
                all_values.extend(str(v) for v in header_data.values())
            else:
                all_values.append(str(header_data))

        specific_count = sum(1 for v in all_values if SPECIFIC_DATA_PATTERN.search(v))
        specific_ratio = round(specific_count / len(all_values) * 100, 1) if all_values else 0.0

        recommendations = []
        if missing:
            recommendations.append(f"Add these semantic headers: {', '.join(missing[:3])}")
        if specific_ratio < 50:
            recommendations.append(
                "Replace vague values (e.g., 'Long battery') with specific data (e.g., '24 Hours / 87.7Wh')"
            )

        return {
            "has_table": True,
            "semantic_headers_found": found,
            "semantic_headers_missing": missing[:5],
            "semantic_header_score": header_score,
            "specific_data_ratio": specific_ratio,
            "recommendations": recommendations,
        }

    def _audit_modules(self) -> dict[str, Any]:
        """Check whether knowledge-base modules are present."""
        present_types = [m.get("type", "").lower() for m in self.modules]
        has_knowledge_base = any(
            kb in t for kb in KNOWLEDGE_BASE_MODULES for t in present_types
        )
        missing_kb = [
            m for m in ["faq", "technical_specs", "comparison_table"]
            if not any(m in t for t in present_types)
        ]

        return {
            "module_count": len(self.modules),
            "module_types": present_types,
            "has_knowledge_base_module": has_knowledge_base,
            "missing_kb_modules": missing_kb,
        }

    def _score_hallucination_risk(self) -> dict[str, Any]:
        """
        Score hallucination risk by counting claims without numeric anchors.

        High risk = many vague claims without specific data to back them up.
        Low risk  = every claim is paired with a measurable data point.

        Risk score is inverted: 100 = low risk (good), 0 = high risk (bad).
        """
        all_content = " ".join(self.product_claims)
        for module in self.modules:
            all_content += " " + sanitize_text(module.get("content", ""))

        vague_found = [v for v in VAGUE_TERMS if v in all_content.lower()]
        specific_anchors = len(SPECIFIC_DATA_PATTERN.findall(all_content))

        total_claims = len(self.product_claims) or 1
        vague_ratio = len(vague_found) / total_claims
        anchor_ratio = min(1.0, specific_anchors / total_claims)

        risk_score = round((1 - vague_ratio * 0.6) * 100 * (0.4 + anchor_ratio * 0.6), 1)
        risk_score = max(0.0, min(100.0, risk_score))

        return {
            "vague_claims_found": vague_found,
            "specific_data_anchors": specific_anchors,
            "hallucination_risk_score": risk_score,
            "risk_level": (
                "LOW" if risk_score >= 75
                else "MEDIUM" if risk_score >= 50
                else "HIGH"
            ),
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> "Skill05":
        """
        Execute the A+ Knowledge Base Engineering pipeline.

        Steps:
            1. Comparison table semantic audit
            2. Module presence check
            3. Hallucination risk scoring
            4. Overall A+ knowledge score

        Returns:
            self (for method chaining)
        """
        log_step("SKILL05_START", f"ASIN={self.asin}")

        log_step("SKILL05_TABLE_AUDIT")
        table_audit = self._audit_comparison_table()

        log_step("SKILL05_MODULE_AUDIT", f"{len(self.modules)} modules")
        module_audit = self._audit_modules()

        log_step("SKILL05_HALLUCINATION_RISK")
        hallucination = self._score_hallucination_risk()

        # Composite score
        table_score = table_audit.get("semantic_header_score", 0) * 0.4
        module_score = 100.0 if module_audit["has_knowledge_base_module"] else 0.0
        hal_score = hallucination["hallucination_risk_score"] * 0.3
        composite = round(table_score + module_score * 0.3 + hal_score, 1)
        grade = score_to_grade(composite)

        self._result = {
            "skill_id": self.SKILL_ID,
            "skill_name": self.SKILL_NAME,
            "asin": self.asin,
            "comparison_table_audit": table_audit,
            "module_audit": module_audit,
            "hallucination_risk": hallucination,
            "scores": {
                "composite_aplus_score": composite,
                "grade": grade,
            },
        }

        log_step("SKILL05_DONE", f"score={composite} grade={grade}")
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
    parser = argparse.ArgumentParser(description="Skill05 — A+ Knowledge Base Engineering")
    parser.add_argument("--input", "-i", help="Input JSON file or string")
    parser.add_argument("--output", "-o", help="Output JSON file path")
    parser.add_argument("--asin", default="UNKNOWN")
    return parser


def _run_cli(args: argparse.Namespace) -> None:
    if args.input:
        data = load_json_input(args.input)
    elif not sys.stdin.isatty():
        data = json.load(sys.stdin)
    else:
        print("Error: provide --input or pipe JSON.", file=sys.stderr)
        sys.exit(1)

    skill = Skill05(
        comparison_table=data.get("comparison_table", {}),
        modules=data.get("modules", []),
        product_claims=data.get("product_claims", []),
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
        sample = {
            "asin": "B0EXAMPLE5",
            "comparison_table": {
                "Battery Life": {"B0EXAMPLE5": "24 Hours", "B0COMP001": "12 Hours"},
                "Waterproof Rating": {"B0EXAMPLE5": "IPX7", "B0COMP001": "IPX4"},
                "Charging Speed": {"B0EXAMPLE5": "PD 65W", "B0COMP001": "18W"},
                "Weight": {"B0EXAMPLE5": "450g", "B0COMP001": "600g"},
            },
            "modules": [
                {"type": "comparison_table", "content": "See table above"},
                {"type": "faq", "content": "Q: Is it waterproof? A: Yes, IPX7 rated."},
                {"type": "lifestyle_image", "content": ""},
            ],
            "product_claims": [
                "Long battery life",
                "Fast charging technology",
                "IPX7 waterproof",
                "PD 65W output for laptops",
            ],
        }

        skill = Skill05(
            comparison_table=sample["comparison_table"],
            modules=sample["modules"],
            product_claims=sample["product_claims"],
            asin=sample["asin"],
        )
        print(json.dumps(skill.to_json(), ensure_ascii=False, indent=2))
