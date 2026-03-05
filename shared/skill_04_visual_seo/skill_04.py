"""
skill_04.py — Multimodal Visual SEO Validation
===============================================
Skill 04 of the Rufus Optimization Skills Library.

Goal:
    Provide clear visual data for Amazon's Computer Vision (CV) and OCR systems
    to "read" and verify, ensuring infographics and alt-text are AI-readable.

Logic:
    - OCR Optimization: verify key noun phrases appear in infographic text overlays
    - Alt-Text Scoring: assess descriptiveness of image alt-text (Intent + Context)
    - Compliance Check: flag images with missing, generic, or low-information alt-text
    - Output optimized alt-text and infographic layout recommendations

Callable 3 ways:
    1. Direct import:  from skill_04_visual_seo.skill_04 import Skill04
    2. CLI:            python skill_04.py --input data.json --output result.json
    3. JSON stdin:     echo '{"images": [], "noun_phrases": []}' | python skill_04.py

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
    count_noun_phrases,
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

ALT_TEXT_MAX_CHARS = 500
ALT_TEXT_MIN_CHARS = 40

# Patterns that signal generic / unhelpful alt-text
GENERIC_ALT_PATTERNS = [
    r"^product\s*(image|photo|picture|view)?\s*\d*$",
    r"^image\s*\d*$",
    r"^(main|front|back|side)\s*image$",
    r"^(photo|picture)$",
    r"^\d+$",
]

# OCR quality criteria for infographic text
OCR_CONTRAST_TIPS = [
    "Use dark text (#1A1A1A or similar) on light backgrounds (≥4.5:1 contrast ratio)",
    "Use font size ≥ 24px for overlay text to ensure OCR legibility",
    "Prefer sans-serif fonts (e.g., Helvetica, Inter) for machine readability",
    "Keep text blocks to ≤ 6 words per line to avoid OCR fragmentation",
]

# Intent + Context alt-text template
ALT_TEXT_TEMPLATE = (
    "{product_name} {feature} — {action_context} showing {scene_context}"
)


class Skill04:
    """
    Skill04: Multimodal Visual SEO Validation

    Audits product images for OCR optimization and AI-readable alt-text,
    then returns optimized metadata and infographic layout recommendations.

    Parameters:
        images        (list[dict]):  Image records with 'filename', 'alt_text',
                                     'ocr_text' (text extracted from infographic),
                                     'image_type' (main/lifestyle/infographic/video_thumb).
        noun_phrases  (list[str]):   Target noun phrases from Skill02 (NPO output).
        product_name  (str):         Product name for alt-text generation.
        asin          (str):         ASIN label.
    """

    SKILL_ID = "04"
    SKILL_NAME = "Multimodal Visual SEO Validation"

    def __init__(
        self,
        images: list[dict[str, Any]],
        noun_phrases: list[str] | None = None,
        product_name: str = "Product",
        asin: str = "UNKNOWN",
    ) -> None:
        self.images = images
        self.noun_phrases = noun_phrases or []
        self.product_name = sanitize_text(product_name)
        self.asin = sanitize_text(asin)
        self._result: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _is_generic_alt_text(self, alt_text: str) -> bool:
        """Return True if the alt-text matches a known generic/useless pattern."""
        cleaned = alt_text.strip().lower()
        if len(cleaned) < ALT_TEXT_MIN_CHARS:
            return True
        for pat in GENERIC_ALT_PATTERNS:
            if re.match(pat, cleaned, re.IGNORECASE):
                return True
        return False

    def _score_alt_text(self, alt_text: str) -> dict[str, Any]:
        """Score a single alt-text for descriptiveness and noun phrase density."""
        is_generic = self._is_generic_alt_text(alt_text)
        length_score = min(100, len(alt_text) / ALT_TEXT_MAX_CHARS * 100)
        np_counts = count_noun_phrases(alt_text, self.noun_phrases)
        np_hits = sum(np_counts.values())
        np_score = min(100, np_hits * 25)  # 4 hits = perfect score
        total = round((length_score * 0.3 + np_score * 0.7), 1) if not is_generic else 0.0

        return {
            "is_generic": is_generic,
            "length": len(alt_text),
            "noun_phrase_hits": np_hits,
            "score": total,
            "grade": score_to_grade(total),
        }

    def _generate_optimized_alt_text(self, image: dict[str, Any]) -> str:
        """
        Generate an Intent + Context alt-text string for an image.

        Format: "{product_name} {feature} — {action} showing {scene}"
        """
        img_type = image.get("image_type", "product").lower()
        ocr_text = sanitize_text(image.get("ocr_text", ""))
        filename = image.get("filename", "")

        # Determine feature and context from available data
        feature = ""
        if self.noun_phrases:
            feature = self.noun_phrases[0]
        elif ocr_text:
            feature = truncate_to_chars(ocr_text, 50)

        scene_map = {
            "lifestyle": "product in real-world use environment",
            "infographic": "technical specifications and key features",
            "main": "primary product view on white background",
            "video_thumb": "product demonstration in action",
        }
        scene = scene_map.get(img_type, "product detail view")

        action_map = {
            "lifestyle": "user interacting with product",
            "infographic": "callout annotations",
            "main": "clean studio shot",
            "video_thumb": "video thumbnail",
        }
        action = action_map.get(img_type, "product view")

        alt = ALT_TEXT_TEMPLATE.format(
            product_name=self.product_name,
            feature=feature,
            action_context=action,
            scene_context=scene,
        )
        return truncate_to_chars(sanitize_text(alt), ALT_TEXT_MAX_CHARS)

    def _audit_ocr_coverage(self, image: dict[str, Any]) -> dict[str, Any]:
        """Check whether an infographic's OCR text covers the target noun phrases."""
        ocr_text = sanitize_text(image.get("ocr_text", ""))
        if not ocr_text:
            return {"has_ocr_text": False, "np_coverage": 0, "missing_phrases": self.noun_phrases[:3]}

        np_counts = count_noun_phrases(ocr_text, self.noun_phrases)
        present = [p for p, c in np_counts.items() if c > 0]
        missing = [p for p, c in np_counts.items() if c == 0]
        coverage = round(len(present) / len(self.noun_phrases) * 100, 1) if self.noun_phrases else 100.0

        return {
            "has_ocr_text": True,
            "np_coverage_pct": coverage,
            "present_phrases": present,
            "missing_phrases": missing[:3],
        }

    def _build_image_report(self) -> list[dict[str, Any]]:
        """Build a per-image audit report."""
        reports = []
        for img in self.images:
            alt = sanitize_text(img.get("alt_text", ""))
            alt_score = self._score_alt_text(alt)
            optimized_alt = self._generate_optimized_alt_text(img)
            ocr_audit = self._audit_ocr_coverage(img)

            reports.append({
                "filename": img.get("filename", "unknown"),
                "image_type": img.get("image_type", "unknown"),
                "alt_text": {
                    "original": alt,
                    "optimized": optimized_alt,
                    "score": alt_score,
                },
                "ocr_audit": ocr_audit,
                "ocr_tips": OCR_CONTRAST_TIPS if img.get("image_type") == "infographic" else [],
            })
        return reports

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> "Skill04":
        """
        Execute the full Visual SEO Validation pipeline.

        Steps:
            1. Per-image alt-text scoring and optimization
            2. OCR noun phrase coverage audit (infographics)
            3. Overall visual SEO score
            4. Layout recommendations

        Returns:
            self (for method chaining)
        """
        log_step("SKILL04_START", f"ASIN={self.asin}")

        log_step("SKILL04_IMAGE_AUDIT", f"{len(self.images)} images")
        image_reports = self._build_image_report()

        # Aggregate scoring
        scores = [r["alt_text"]["score"]["score"] for r in image_reports]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
        grade = score_to_grade(avg_score)

        generic_count = sum(1 for r in image_reports if r["alt_text"]["score"]["is_generic"])
        infographic_reports = [r for r in image_reports if r["image_type"] == "infographic"]

        self._result = {
            "skill_id": self.SKILL_ID,
            "skill_name": self.SKILL_NAME,
            "asin": self.asin,
            "image_reports": image_reports,
            "summary": {
                "total_images": len(self.images),
                "generic_alt_text_count": generic_count,
                "infographics_audited": len(infographic_reports),
                "ocr_tips": OCR_CONTRAST_TIPS,
            },
            "scores": {
                "average_alt_text_score": avg_score,
                "grade": grade,
                "images_needing_update": generic_count,
            },
        }

        log_step("SKILL04_DONE", f"avg_score={avg_score} grade={grade}")
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
        description="Skill04 — Multimodal Visual SEO Validation",
    )
    parser.add_argument("--input", "-i", help="Input JSON file or string")
    parser.add_argument("--output", "-o", help="Output JSON file path")
    parser.add_argument("--asin", default="UNKNOWN", help="Product ASIN")
    return parser


def _run_cli(args: argparse.Namespace) -> None:
    if args.input:
        data = load_json_input(args.input)
    elif not sys.stdin.isatty():
        data = json.load(sys.stdin)
    else:
        print("Error: provide --input or pipe JSON.", file=sys.stderr)
        sys.exit(1)

    skill = Skill04(
        images=data.get("images", []),
        noun_phrases=data.get("noun_phrases", []),
        product_name=data.get("product_name", "Product"),
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
        sample_images = [
            {
                "filename": "main_image.jpg",
                "image_type": "main",
                "alt_text": "product image 1",
                "ocr_text": "",
            },
            {
                "filename": "infographic_specs.jpg",
                "image_type": "infographic",
                "alt_text": "Portable power bank fast charge infographic showing PD 65W output for laptop charging",
                "ocr_text": "PD 65W Output | 20000mAh | IPX5 Waterproof | Fast charge for laptops",
            },
            {
                "filename": "lifestyle_camping.jpg",
                "image_type": "lifestyle",
                "alt_text": "Portable power bank used for camping in a forest setting at night",
                "ocr_text": "",
            },
        ]
        skill = Skill04(
            images=sample_images,
            noun_phrases=["portable charger", "fast charge", "PD 65W output", "IPX5 waterproof"],
            product_name="Portable Power Bank 20000mAh",
            asin="B0EXAMPLE4",
        )
        print(json.dumps(skill.to_json(), ensure_ascii=False, indent=2))
