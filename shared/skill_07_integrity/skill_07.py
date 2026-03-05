"""
skill_07.py — Semantic Integrity & Anti-Optimization Check
===========================================================
Skill 07 of the Rufus Optimization Skills Library.

Goal:
    Protect the listing's "Trust Score" by detecting and removing legacy SEO habits,
    resolving conflicts between frontend claims and backend attributes, and addressing
    negative review patterns before they are baked into Rufus's product summary.

Logic:
    - Keyword Stuffing Detection: identify repetitive low-value phrases
    - Conflict Resolution: cross-check Title/Bullets against backend attributes
    - Negative Feedback Loop: flag recurring negative review themes in copy
    - Produces a "Rufus Compliance Report" and a sanitized listing diff

Callable 3 ways:
    1. Direct import:  from skill_07_integrity.skill_07 import Skill07
    2. CLI:            python skill_07.py --input data.json --output result.json
    3. JSON stdin:     echo '{"title": "", "bullets": [], "backend": {}}' | python skill_07.py

Author: John / Anergy Academy
Version: 1.0.0
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
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
    truncate_to_chars,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Repetition threshold: appearing more than N times across title + bullets = stuffing
STUFFING_THRESHOLD = 3

# Patterns that indicate keyword stuffing
STUFFING_INDICATORS = [
    r"\b(\w+)\b(?:.*?\b\1\b){2,}",  # same word 3+ times in a block
]

# Claims in title that must have a corresponding backend attribute match
VERIFIABLE_TITLE_CLAIMS = {
    r"\b(\d+)\s*pack\b": "quantity",
    r"\b(\d+)\s*(pcs|pieces|count)\b": "item_quantity",
    r"\b(\d+\.?\d*)\s*(in|inch|inches|cm)\b": "item_dimensions",
    r"\b(ipx\d+|ip\d+)\b": "waterproof_rating",
    r"\b(\d+)\s*mah\b": "battery_capacity",
}

# Legacy SEO phrases that harm Rufus trust score
LEGACY_SEO_PHRASES = [
    "best seller", "#1 best", "top rated", "amazon choice", "limited time",
    "buy now", "order today", "free shipping", "click here",
    "check our store", "visit our brand", "see more products",
]


class Skill07:
    """
    Skill07: Semantic Integrity & Anti-Optimization Check

    Audits the final listing for keyword stuffing, title/backend conflicts,
    and negative review alignment issues, producing a Rufus Compliance Report.

    Parameters:
        title           (str):        Product title.
        bullets         (list[str]):  Bullet points.
        backend_attrs   (dict):       Backend attribute key/values from Skill01.
        negative_review_themes (list[str]): Top negative review keywords from Skill03.
        asin            (str):        ASIN label.
    """

    SKILL_ID = "07"
    SKILL_NAME = "Semantic Integrity & Anti-Optimization Check"

    def __init__(
        self,
        title: str,
        bullets: list[str] | None = None,
        backend_attrs: dict[str, Any] | None = None,
        negative_review_themes: list[str] | None = None,
        asin: str = "UNKNOWN",
    ) -> None:
        self.title = sanitize_text(title)
        self.bullets = [sanitize_text(b) for b in (bullets or [])]
        self.backend_attrs = backend_attrs or {}
        self.negative_review_themes = [sanitize_text(t) for t in (negative_review_themes or [])]
        self.asin = sanitize_text(asin)
        self._result: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _detect_keyword_stuffing(self) -> dict[str, Any]:
        """
        Detect repetitive, low-value phrases across the full listing copy.

        Method:
        1. Tokenize all copy into bigrams and trigrams
        2. Count frequency of each phrase
        3. Flag any phrase appearing ≥ STUFFING_THRESHOLD times
        """
        full_copy = self.title + " " + " ".join(self.bullets)
        words = re.findall(r"\b\w+\b", full_copy.lower())

        # Build bigrams and trigrams
        phrases: list[str] = []
        for n in (2, 3):
            for i in range(len(words) - n + 1):
                phrase = " ".join(words[i: i + n])
                # Skip stop-word-only phrases
                stopwords = {"the", "a", "an", "and", "or", "for", "to", "of", "in", "with", "is", "it"}
                if all(w in stopwords for w in phrase.split()):
                    continue
                phrases.append(phrase)

        freq = Counter(phrases)
        stuffed = {p: c for p, c in freq.items() if c >= STUFFING_THRESHOLD}

        # Detect legacy SEO phrases
        legacy_found = [
            phrase for phrase in LEGACY_SEO_PHRASES
            if phrase in full_copy.lower()
        ]

        return {
            "stuffed_phrases": stuffed,
            "stuffed_count": len(stuffed),
            "legacy_seo_phrases": legacy_found,
            "legacy_count": len(legacy_found),
        }

    def _resolve_conflicts(self) -> list[dict[str, str]]:
        """
        Cross-check title claims against backend attributes for data consistency.

        Each conflict is: a title claim that either contradicts or is absent from backend.
        """
        conflicts: list[dict[str, str]] = []
        title_lower = self.title.lower()

        for claim_pattern, backend_key in VERIFIABLE_TITLE_CLAIMS.items():
            match = re.search(claim_pattern, title_lower, re.IGNORECASE)
            if not match:
                continue

            extracted_value = match.group(1) if match.lastindex else match.group(0)
            backend_value = str(self.backend_attrs.get(backend_key, ""))
            # Build a simple literal search pattern from the extracted value
            value_pattern = re.escape(extracted_value)

            if not backend_value:
                conflicts.append({
                    "claim": match.group(0),
                    "claim_type": backend_key,
                    "backend_value": "MISSING",
                    "severity": "HIGH",
                    "fix": f"Add '{backend_key}' to backend attributes with value '{extracted_value}'",
                })
            elif not re.search(value_pattern, backend_value, re.IGNORECASE):
                conflicts.append({
                    "claim": match.group(0),
                    "claim_type": backend_key,
                    "backend_value": backend_value,
                    "severity": "CRITICAL",
                    "fix": f"Update backend '{backend_key}' to match title claim '{extracted_value}'",
                })

        return conflicts

    def _check_negative_feedback_loop(self) -> list[dict[str, str]]:
        """
        Identify negative review themes that are NOT addressed in current copy.

        If customers complain about X but the listing doesn't address X,
        Rufus will embed X's sentiment in product summaries.
        """
        full_copy = (self.title + " " + " ".join(self.bullets)).lower()
        unaddressed: list[dict[str, str]] = []

        theme_responses = {
            "cheap": "Add a bullet about material certification or manufacturing standard",
            "flimsy": "Add a bullet about structural testing (e.g., 'drop-tested to MIL-STD-810G')",
            "stopped working": "Add warranty / reliability claim with proof (e.g., '50,000-cycle tested')",
            "defective": "Add quality control claim (e.g., '100% inspected before shipment')",
            "misleading": "Audit title claims vs backend for exact quantity/spec consistency",
            "not as described": "Ensure every title claim is verifiable in bullet points or A+",
            "poor quality": "Reference specific quality certifications (CE, FCC, RoHS) in copy",
            "fragile": "Add 'reinforced' or 'heavy-duty' with a measurable spec",
        }

        for theme in self.negative_review_themes:
            theme_lower = theme.lower()
            if theme_lower not in full_copy:
                response = theme_responses.get(
                    theme_lower,
                    f"Address '{theme}' concern explicitly in a bullet point or Q&A",
                )
                unaddressed.append({"theme": theme, "recommendation": response})

        return unaddressed

    def _sanitize_listing(self) -> dict[str, str]:
        """Return a cleaned version of the listing with stuffing removed."""
        stuffing_result = self._detect_keyword_stuffing()
        stuffed_phrases = list(stuffing_result.get("stuffed_phrases", {}).keys())
        legacy_phrases = stuffing_result.get("legacy_seo_phrases", [])

        def clean(text: str) -> str:
            for phrase in legacy_phrases:
                text = re.sub(re.escape(phrase), "", text, flags=re.IGNORECASE)
            # Remove extra spaces
            text = re.sub(r" {2,}", " ", text).strip()
            return text

        clean_title = clean(self.title)
        clean_bullets = [clean(b) for b in self.bullets]

        return {
            "sanitized_title": clean_title,
            "sanitized_bullets": clean_bullets,
            "phrases_removed": legacy_phrases + stuffed_phrases[:5],
        }

    def _compute_integrity_score(
        self,
        stuffing: dict,
        conflicts: list,
        unaddressed: list,
    ) -> float:
        """Compute overall integrity score (100 = perfect)."""
        score = 100.0
        score -= stuffing["stuffed_count"] * 5
        score -= stuffing["legacy_count"] * 8
        score -= sum(15 if c["severity"] == "CRITICAL" else 8 for c in conflicts)
        score -= len(unaddressed) * 6
        return max(0.0, round(score, 1))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> "Skill07":
        """
        Execute the Semantic Integrity & Anti-Optimization pipeline.

        Steps:
            1. Keyword stuffing & legacy SEO detection
            2. Title/backend conflict resolution
            3. Negative feedback loop check
            4. Sanitized listing generation
            5. Rufus Compliance Report scoring

        Returns:
            self (for method chaining)
        """
        log_step("SKILL07_START", f"ASIN={self.asin}")

        log_step("SKILL07_STUFFING_CHECK")
        stuffing = self._detect_keyword_stuffing()

        log_step("SKILL07_CONFLICT_CHECK")
        conflicts = self._resolve_conflicts()

        log_step("SKILL07_FEEDBACK_LOOP")
        unaddressed_themes = self._check_negative_feedback_loop()

        log_step("SKILL07_SANITIZE")
        sanitized = self._sanitize_listing()

        integrity_score = self._compute_integrity_score(stuffing, conflicts, unaddressed_themes)
        grade = score_to_grade(integrity_score)

        self._result = {
            "skill_id": self.SKILL_ID,
            "skill_name": self.SKILL_NAME,
            "asin": self.asin,
            "compliance_report": {
                "keyword_stuffing": stuffing,
                "backend_conflicts": conflicts,
                "conflict_count": len(conflicts),
                "unaddressed_negative_themes": unaddressed_themes,
            },
            "sanitized_listing": sanitized,
            "scores": {
                "integrity_score": integrity_score,
                "grade": grade,
                "issues_found": stuffing["stuffed_count"] + len(conflicts) + len(unaddressed_themes),
            },
        }

        log_step("SKILL07_DONE", f"integrity={integrity_score} grade={grade}")
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
        description="Skill07 — Semantic Integrity & Anti-Optimization Check"
    )
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

    skill = Skill07(
        title=data.get("title", ""),
        bullets=data.get("bullets", []),
        backend_attrs=data.get("backend_attrs", {}),
        negative_review_themes=data.get("negative_review_themes", []),
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
            "asin": "B0EXAMPLE7",
            "title": "Portable Power Bank 20000mAh Fast Charging USB-C — 3 Pack Power Bank Best Seller Power Bank",
            "bullets": [
                "Best seller portable power bank with amazing fast charging technology",
                "Top rated power bank — power bank for all your devices, power bank travel",
                "Buy now and enjoy long battery life with our world-class portable charger",
            ],
            "backend_attrs": {
                "quantity": "1",          # conflict: title says "3 Pack"
                "waterproof_rating": "",   # missing
                "battery_capacity": "20000mAh",
            },
            "negative_review_themes": [
                "cheap",
                "stopped working",
                "misleading",
            ],
        }

        skill = Skill07(
            title=sample["title"],
            bullets=sample["bullets"],
            backend_attrs=sample["backend_attrs"],
            negative_review_themes=sample["negative_review_themes"],
            asin=sample["asin"],
        )
        print(json.dumps(skill.to_json(), ensure_ascii=False, indent=2))
