"""
skill_09.py — Infographic Generator (OCR-Optimized for Rufus)
==============================================================
Skill 09 of the Rufus Optimization Skills Library.

Goal:
    Generate downloadable infographic layouts (HTML/SVG) from pipeline data
    that are OCR-optimized for Amazon Rufus. Users can screenshot or convert
    these to PNG/JPG and upload to their Amazon listing (A+, image carousel).

Generates 4 infographic types:
    1. Specs Infographic — Key technical specifications in a grid
    2. Feature Callout — Top 5 features with benefit text
    3. Comparison Chart — Side-by-side vs competitors
    4. Lifestyle Overlay Template — Spec callouts for lifestyle photos

OCR Optimization Rules (baked in):
    - Font: Inter/system sans-serif at 24-36px
    - Color: #1A1A1A text on #FFFFFF or #F8FAFC background
    - Contrast ratio: ≥4.5:1
    - Max 6 words per text line
    - All text blocks use noun phrases from Skill 02

Callable 3 ways:
    1. Direct import:  from skill_09_infographic.skill_09 import Skill09
    2. CLI:            python skill_09.py --input pipeline.json --output-dir infographics/
    3. JSON stdin:     cat pipeline.json | python skill_09.py

Author: John / Anergy Academy
Version: 1.0.0
"""

from __future__ import annotations

import argparse
import html as html_lib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent.parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from utils.helpers import load_json_input, log_step, save_json_output, sanitize_text

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CANVAS_W = 1600   # Amazon recommended image width
CANVAS_H = 1600   # Amazon recommended image height
FONT_FAMILY = "-apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif"
TEXT_COLOR = "#1A1A1A"
BG_COLOR = "#FFFFFF"
ACCENT_BLUE = "#2563eb"
ACCENT_GREEN = "#16a34a"
LIGHT_BG = "#F8FAFC"
BORDER_COLOR = "#E5E7EB"

# Feature icons (SVG-safe unicode)
FEATURE_ICONS = ["&#x26A1;", "&#x1F50B;", "&#x2744;", "&#x1F6E1;", "&#x2705;",
                 "&#x1F4F1;", "&#x2B50;", "&#x1F3AF;"]


def _esc(text: Any) -> str:
    return html_lib.escape(str(text)) if text is not None else ""


# ---------------------------------------------------------------------------
# Shared CSS for all infographics
# ---------------------------------------------------------------------------
INFOGRAPHIC_BASE_CSS = f"""
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: {FONT_FAMILY}; background: {BG_COLOR}; color: {TEXT_COLOR}; }}
  .canvas {{ width: {CANVAS_W}px; height: {CANVAS_H}px; padding: 80px; position: relative; overflow: hidden; }}
  .brand-bar {{ position: absolute; top: 0; left: 0; right: 0; height: 6px; background: linear-gradient(90deg, {ACCENT_BLUE}, {ACCENT_GREEN}); }}
  .title {{ font-size: 48px; font-weight: 800; letter-spacing: -1px; margin-bottom: 8px; }}
  .subtitle {{ font-size: 24px; color: #6B7280; font-weight: 400; margin-bottom: 48px; }}
  .product-name {{ font-size: 28px; font-weight: 700; color: {ACCENT_BLUE}; margin-bottom: 40px; }}
  .ocr-text {{ font-size: 28px; font-weight: 600; line-height: 1.5; color: {TEXT_COLOR}; }}
  .ocr-text-sm {{ font-size: 24px; font-weight: 500; line-height: 1.5; color: {TEXT_COLOR}; }}
  .spec-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
  .spec-card {{ background: {LIGHT_BG}; border: 1px solid {BORDER_COLOR}; border-radius: 16px; padding: 32px; }}
  .spec-label {{ font-size: 18px; color: #6B7280; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }}
  .spec-value {{ font-size: 36px; font-weight: 800; }}
  .spec-unit {{ font-size: 20px; color: #6B7280; font-weight: 400; }}
  .feature-row {{ display: flex; align-items: flex-start; gap: 24px; padding: 28px 0; border-bottom: 1px solid {BORDER_COLOR}; }}
  .feature-row:last-child {{ border-bottom: none; }}
  .feature-icon {{ width: 64px; height: 64px; background: linear-gradient(135deg, #DBEAFE, #BFDBFE); border-radius: 16px; display: flex; align-items: center; justify-content: center; font-size: 32px; flex-shrink: 0; }}
  .feature-text h3 {{ font-size: 28px; font-weight: 700; margin-bottom: 6px; }}
  .feature-text p {{ font-size: 22px; color: #4B5563; line-height: 1.4; }}
  .comp-table {{ width: 100%; border-collapse: collapse; }}
  .comp-table th {{ font-size: 22px; font-weight: 700; padding: 20px 16px; text-align: center; background: {LIGHT_BG}; }}
  .comp-table th.highlight {{ background: linear-gradient(135deg, #DBEAFE, #EFF6FF); color: {ACCENT_BLUE}; }}
  .comp-table td {{ font-size: 24px; padding: 18px 16px; text-align: center; border-bottom: 1px solid {BORDER_COLOR}; }}
  .comp-table td.highlight {{ background: #EFF6FF; font-weight: 700; color: {ACCENT_BLUE}; }}
  .comp-table td.win {{ color: {ACCENT_GREEN}; font-weight: 700; }}
  .comp-header {{ font-size: 20px; font-weight: 600; padding: 16px; text-align: left; color: #6B7280; background: #F9FAFB; }}
  .footer-bar {{ position: absolute; bottom: 40px; left: 80px; right: 80px; font-size: 18px; color: #9CA3AF; display: flex; justify-content: space-between; }}
"""


# ---------------------------------------------------------------------------
# Infographic generators
# ---------------------------------------------------------------------------

def _generate_specs_infographic(data: dict, specs: dict, product_name: str) -> str:
    """Generate a specs grid infographic from injection payload data."""
    # Extract key specs for display
    spec_items = []
    spec_fields = [
        ("capacity_mah", "Battery Capacity", "mAh"),
        ("energy_wh", "Energy", "Wh"),
        ("output_ports", "Output Ports", ""),
        ("usb_c_output", "USB-C Output", ""),
        ("wireless_output", "Wireless Output", ""),
        ("total_output", "Total Output", ""),
        ("weight_grams", "Weight", "g"),
        ("dimensions_inches", "Dimensions", ""),
        ("waterproof_rating", "Water Rating", ""),
        ("charging_standard", "Charging", ""),
        ("battery_type", "Battery Type", ""),
        ("charge_cycles", "Charge Cycles", ""),
        ("certifications", "Certified", ""),
        ("material", "Material", ""),
        ("operating_temp_c", "Operating Temp", "°C"),
    ]

    for field, label, unit in spec_fields:
        val = specs.get(field)
        if val and str(val) != "MISSING":
            spec_items.append((label, str(val), unit))

    # Limit to 8 specs (4×2 grid)
    spec_items = spec_items[:8]

    cards = ""
    for label, value, unit in spec_items:
        unit_html = f'<span class="spec-unit"> {_esc(unit)}</span>' if unit else ""
        cards += (
            f'<div class="spec-card">'
            f'<div class="spec-label">{_esc(label)}</div>'
            f'<div class="spec-value">{_esc(value)}{unit_html}</div>'
            f'</div>'
        )

    return (
        f'<!DOCTYPE html><html><head><meta charset="UTF-8">'
        f'<style>{INFOGRAPHIC_BASE_CSS}</style></head><body>'
        f'<div class="canvas">'
        f'<div class="brand-bar"></div>'
        f'<div class="title">Technical Specifications</div>'
        f'<div class="product-name">{_esc(product_name)}</div>'
        f'<div class="spec-grid">{cards}</div>'
        f'<div class="footer-bar">'
        f'<span>All specifications verified &bull; OCR-optimized for Amazon Rufus</span>'
        f'<span>{_esc(data.get("asin", ""))}</span>'
        f'</div></div></body></html>'
    )


def _generate_feature_callout(data: dict, noun_phrases: list, specs: dict, product_name: str) -> str:
    """Generate feature callout infographic using noun phrases."""
    # Build feature items from noun phrases + specs
    features = []
    for i, np_text in enumerate(noun_phrases[:5]):
        # Truncate to 6 words per line for OCR
        words = np_text.split()
        headline = " ".join(words[:4])
        desc = " ".join(words[4:8]) if len(words) > 4 else ""
        icon = FEATURE_ICONS[i % len(FEATURE_ICONS)]
        features.append((icon, headline, desc))

    # If we have fewer than 5 NPs, add spec-based features
    if len(features) < 5:
        extra_specs = [
            ("&#x26A1;", f"{specs.get('total_output', 'Fast')} Output", "Maximum charging speed"),
            ("&#x1F50B;", f"{specs.get('capacity_mah', '?')}mAh Capacity", "Extended battery life"),
            ("&#x2744;", f"{specs.get('material', 'Premium')} Build", "Durable construction"),
            ("&#x1F6E1;", f"{specs.get('certifications', 'Certified')}", "Safety certified"),
        ]
        for spec in extra_specs:
            if len(features) >= 5:
                break
            features.append(spec)

    rows = ""
    for icon, headline, desc in features:
        desc_html = f'<p>{_esc(desc)}</p>' if desc else ""
        rows += (
            f'<div class="feature-row">'
            f'<div class="feature-icon">{icon}</div>'
            f'<div class="feature-text">'
            f'<h3>{_esc(headline)}</h3>'
            f'{desc_html}'
            f'</div></div>'
        )

    return (
        f'<!DOCTYPE html><html><head><meta charset="UTF-8">'
        f'<style>{INFOGRAPHIC_BASE_CSS}</style></head><body>'
        f'<div class="canvas">'
        f'<div class="brand-bar"></div>'
        f'<div class="title">Key Features</div>'
        f'<div class="product-name">{_esc(product_name)}</div>'
        f'{rows}'
        f'<div class="footer-bar">'
        f'<span>Feature highlights &bull; OCR-optimized for Amazon Rufus</span>'
        f'<span>{_esc(data.get("asin", ""))}</span>'
        f'</div></div></body></html>'
    )


def _generate_comparison_chart(data: dict, comparison_table: dict, product_name: str, asin: str) -> str:
    """Generate comparison infographic from A+ comparison table data."""
    if not comparison_table:
        return ""

    # Get header row (product ASINs/names)
    headers = set()
    for row_data in comparison_table.values():
        headers.update(row_data.keys())
    headers = sorted(headers)

    # Build table
    header_row = '<tr><th class="comp-header"></th>'
    for h in headers:
        css = ' class="highlight"' if h == asin else ""
        label = "This Product" if h == asin else h[:12]
        header_row += f'<th{css}>{_esc(label)}</th>'
    header_row += '</tr>'

    body_rows = ""
    for metric, values in comparison_table.items():
        body_rows += f'<tr><td class="comp-header">{_esc(metric)}</td>'
        for h in headers:
            val = values.get(h, "—")
            css = ' class="highlight"' if h == asin else ""
            body_rows += f'<td{css}>{_esc(val)}</td>'
        body_rows += '</tr>'

    return (
        f'<!DOCTYPE html><html><head><meta charset="UTF-8">'
        f'<style>{INFOGRAPHIC_BASE_CSS}</style></head><body>'
        f'<div class="canvas">'
        f'<div class="brand-bar"></div>'
        f'<div class="title">Compare Products</div>'
        f'<div class="product-name">{_esc(product_name)}</div>'
        f'<table class="comp-table">{header_row}{body_rows}</table>'
        f'<div class="footer-bar">'
        f'<span>Product comparison &bull; OCR-optimized for Amazon Rufus</span>'
        f'<span>{_esc(asin)}</span>'
        f'</div></div></body></html>'
    )


def _generate_lifestyle_overlay(data: dict, noun_phrases: list, specs: dict, product_name: str) -> str:
    """Generate a lifestyle overlay template with positioned callouts."""
    # Create callout positions (spread around a center product area)
    callouts = []
    positions = [
        (100, 200), (900, 200),     # top left, top right
        (100, 700), (900, 700),     # mid left, mid right
        (100, 1200), (900, 1200),   # bottom left, bottom right
    ]

    # Mix noun phrases and specs for callout text
    callout_texts = []
    for np_text in noun_phrases[:3]:
        words = np_text.split()[:6]
        callout_texts.append(" ".join(words))

    spec_callouts = [
        f"{specs.get('capacity_mah', '?')}mAh Capacity",
        f"{specs.get('total_output', '?')} Max Output",
        f"{specs.get('weight_grams', '?')}g Ultra-Light",
    ]
    for sc in spec_callouts:
        if len(callout_texts) < 6:
            callout_texts.append(sc)

    callout_html = ""
    for i, text in enumerate(callout_texts[:6]):
        x, y = positions[i]
        callout_html += (
            f'<div style="position:absolute; left:{x}px; top:{y}px; '
            f'background:rgba(255,255,255,0.95); padding:16px 24px; '
            f'border-radius:12px; border:2px solid {ACCENT_BLUE}; '
            f'max-width:500px;">'
            f'<div class="ocr-text-sm">{_esc(text)}</div>'
            f'</div>'
        )

    return (
        f'<!DOCTYPE html><html><head><meta charset="UTF-8">'
        f'<style>{INFOGRAPHIC_BASE_CSS}</style></head><body>'
        f'<div class="canvas" style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 50%, #dbeafe 100%);">'
        f'<div class="brand-bar"></div>'
        f'<div style="text-align:center; margin-bottom:40px;">'
        f'<div class="title" style="font-size:40px;">Lifestyle Overlay Template</div>'
        f'<div class="subtitle">Replace this background with your lifestyle photo. Keep the callout boxes.</div>'
        f'</div>'
        f'{callout_html}'
        f'<div class="footer-bar">'
        f'<span>Overlay template &bull; Position callouts over your product photo</span>'
        f'<span>{_esc(data.get("asin", ""))}</span>'
        f'</div></div></body></html>'
    )


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class Skill09:
    """
    Skill09: Infographic Generator (OCR-Optimized for Rufus)

    Generates 4 types of infographic HTML files from pipeline data.

    Parameters:
        pipeline_result: dict — Full pipeline output (contains skill_01..07).
        product_name:    str  — Product display name.
        asin:            str  — Product ASIN.
    """

    SKILL_ID = "09"
    SKILL_NAME = "Infographic Generator"

    def __init__(
        self,
        pipeline_result: dict[str, Any],
        product_name: str = "",
        asin: str = "UNKNOWN",
    ) -> None:
        self.data = pipeline_result
        self.asin = asin or pipeline_result.get("asin", "UNKNOWN")
        self.product_name = product_name or pipeline_result.get("product", f"Product {self.asin}")

        # Extract key data from pipeline
        s01 = pipeline_result.get("skill_01", {})
        s02 = pipeline_result.get("skill_02", {})
        s05 = pipeline_result.get("skill_05", {})

        self.specs = s01.get("injection_payload", {})
        self.noun_phrases = s02.get("npo", {}).get("output_noun_phrases", [])
        self.comparison_table = s05.get("comparison_table_audit", {})

        # Build comparison data from the original input if available
        # The comparison_table in s05 is an audit, not the raw table
        # We'll use what we have
        self._infographics: dict[str, str] = {}
        self._output: dict[str, Any] = {}
        log_step("Skill09", "initialized", f"ASIN={self.asin}")

    def run(self) -> "Skill09":
        """Generate all 4 infographic types."""
        log_step("Skill09", "generating", "4 infographic types")

        self._infographics["specs"] = _generate_specs_infographic(
            self.data, self.specs, self.product_name)

        self._infographics["features"] = _generate_feature_callout(
            self.data, self.noun_phrases, self.specs, self.product_name)

        # For comparison, try to build a simple table from specs
        comp_table = {}
        if self.comparison_table.get("semantic_headers_found"):
            # Build a minimal comparison structure
            for header in self.comparison_table.get("semantic_headers_found", []):
                comp_table[header.title()] = {self.asin: self.specs.get(header.replace(" ", "_"), "—")}
        if comp_table:
            self._infographics["comparison"] = _generate_comparison_chart(
                self.data, comp_table, self.product_name, self.asin)

        self._infographics["lifestyle_overlay"] = _generate_lifestyle_overlay(
            self.data, self.noun_phrases, self.specs, self.product_name)

        self._output = {
            "skill_id": self.SKILL_ID,
            "skill_name": self.SKILL_NAME,
            "asin": self.asin,
            "infographics_generated": list(self._infographics.keys()),
            "count": len(self._infographics),
            "ocr_rules": {
                "font": "Sans-serif (Inter/system)",
                "min_font_size": "24px",
                "text_color": TEXT_COLOR,
                "bg_color": BG_COLOR,
                "contrast_ratio": "≥4.5:1",
                "max_words_per_line": 6,
                "canvas_size": f"{CANVAS_W}×{CANVAS_H}px",
            },
        }

        log_step("Skill09", "complete", f"{len(self._infographics)} infographics generated")
        return self

    def to_json(self) -> dict[str, Any]:
        return self._output

    def get_infographics(self) -> dict[str, str]:
        """Return dict of infographic_type → HTML string."""
        return self._infographics

    def save_infographics(self, output_dir: str | Path) -> list[Path]:
        """Write all infographics to files and return paths."""
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        paths = []
        for itype, html_content in self._infographics.items():
            if not html_content:
                continue
            path = out_dir / f"{self.asin}_{itype}_infographic.html"
            path.write_text(html_content, encoding="utf-8")
            paths.append(path)
            log_step("Skill09", "saved", str(path))
        return paths


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Skill 09 — Infographic Generator: Creates OCR-optimized infographics from pipeline data"
    )
    parser.add_argument("--input", "-i", help="Path to pipeline JSON file")
    parser.add_argument("--output-dir", "-o", default="results/infographics",
                        help="Directory for infographic output files")
    args = parser.parse_args()

    pipeline_data = load_json_input(args.input)

    skill = Skill09(pipeline_data)
    skill.run()
    paths = skill.save_infographics(args.output_dir)

    print(f"Generated {len(paths)} infographics:")
    for p in paths:
        print(f"  {p}")

    save_json_output(skill.to_json(), None)


if __name__ == "__main__":
    main()
