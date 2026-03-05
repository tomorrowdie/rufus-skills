"""
skill_08.py — Visual Report Generator
======================================
Skill 08 of the Rufus Optimization Skills Library.

Goal:
    Convert the raw JSON output of the 7-skill pipeline into a polished,
    human-readable HTML report with infographics, grade cards, score bars,
    sentiment breakdowns, image audit grids, and a prioritized action plan.

Callable 3 ways:
    1. Direct import:  from skill_08_report.skill_08 import Skill08
    2. CLI:            python skill_08.py --input pipeline.json --output report.html
    3. JSON stdin:     cat pipeline.json | python skill_08.py

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

# Allow running as standalone script
_HERE = Path(__file__).resolve().parent.parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from utils.helpers import load_json_input, log_step, save_json_output, score_to_grade


# ---------------------------------------------------------------------------
# Grade → CSS class / color mapping
# ---------------------------------------------------------------------------
GRADE_COLORS: dict[str, dict[str, str]] = {
    "A": {"css": "grade-A", "gradient": "#22c55e, #16a34a", "fill": "fill-green"},
    "B": {"css": "grade-B", "gradient": "#16a34a, #15803d", "fill": "fill-green"},
    "C": {"css": "grade-C", "gradient": "#eab308, #f59e0b", "fill": "fill-yellow"},
    "D": {"css": "grade-D", "gradient": "#f97316, #ea580c", "fill": "fill-yellow"},
    "F": {"css": "grade-F", "gradient": "#ef4444, #dc2626", "fill": "fill-red"},
}

SKILL_LABELS: dict[str, str] = {
    "skill_01": "Taxonomy",
    "skill_02": "NPO Copy",
    "skill_03": "UGC / Q&A",
    "skill_04": "Visual SEO",
    "skill_05": "A+ Content",
    "skill_06": "Mobile",
    "skill_07": "Integrity",
}

SKILL_FULL_NAMES: dict[str, str] = {
    "skill_01": "Structured Taxonomy & Attribute Injection",
    "skill_02": "Noun Phrase Optimization & RAG Copy",
    "skill_03": "UGC Ground Truth Mining & Q&A Seeding",
    "skill_04": "Multimodal Visual SEO Validation",
    "skill_05": "A+ Knowledge Base Engineering",
    "skill_06": "Mobile Habitat Optimization",
    "skill_07": "Semantic Integrity & Anti-Optimization",
}


# ---------------------------------------------------------------------------
# HTML building blocks
# ---------------------------------------------------------------------------
def _esc(text: Any) -> str:
    """HTML-escape a value, converting non-strings to str first."""
    return html_lib.escape(str(text)) if text is not None else ""


def _grade_css(grade: str) -> str:
    return GRADE_COLORS.get(grade, GRADE_COLORS["F"])["css"]


def _grade_gradient(grade: str) -> str:
    return GRADE_COLORS.get(grade, GRADE_COLORS["F"])["gradient"]


def _fill_class(grade: str) -> str:
    return GRADE_COLORS.get(grade, GRADE_COLORS["F"])["fill"]


def _fill_class_for_score(score: float) -> str:
    if score >= 75:
        return "fill-green"
    elif score >= 40:
        return "fill-yellow"
    return "fill-red"


def _grade_color_var(grade: str) -> str:
    mapping = {"A": "var(--green)", "B": "var(--green)", "C": "var(--yellow)", "D": "var(--yellow)", "F": "var(--red)"}
    return mapping.get(grade, "var(--red)")


def _priority_class(priority: str) -> str:
    return f"priority-{priority.lower()}"


def _tag(text: str, color: str = "gray") -> str:
    return f'<span class="tag tag-{color}">{_esc(text)}</span>'


def _stat_box(value: Any, label: str, color: str = "") -> str:
    style = f' style="color:{color}"' if color else ""
    return (
        f'<div class="stat-box">'
        f'<div class="stat-value"{style}>{_esc(value)}</div>'
        f'<div class="stat-label">{_esc(label)}</div>'
        f'</div>'
    )


def _score_bar(label: str, score: float, fill_class: str = "") -> str:
    if not fill_class:
        fill_class = _fill_class_for_score(score)
    return (
        f'<div class="score-bar-wrap">'
        f'<div class="score-bar-label"><span>{_esc(label)}</span><span>{score:.1f}%</span></div>'
        f'<div class="score-bar"><div class="score-bar-fill {fill_class}" style="width:{min(score, 100):.1f}%"></div></div>'
        f'</div>'
    )


def _callout(text: str, color: str = "blue") -> str:
    return f'<div class="callout callout-{color}">{text}</div>'


def _section_header(skill_num: str, title: str, subtitle: str, grade: str) -> str:
    gradient = _grade_gradient(grade)
    return (
        f'<div class="section-header">'
        f'<div class="section-icon" style="background: linear-gradient(135deg, {gradient});">{_esc(skill_num)}</div>'
        f'<div>'
        f'<h2>{_esc(title)} <span>&mdash; Grade {_esc(grade)}</span></h2>'
        f'<div style="font-size:14px; color:#6b7280;">{_esc(subtitle)}</div>'
        f'</div>'
        f'</div>'
    )


# ---------------------------------------------------------------------------
# CSS (embedded — same design language as the original hand-crafted report)
# ---------------------------------------------------------------------------
CSS = """
  :root {
    --green: #22c55e; --green-bg: #dcfce7;
    --yellow: #eab308; --yellow-bg: #fef9c3;
    --red: #ef4444; --red-bg: #fee2e2;
    --blue: #3b82f6; --blue-bg: #dbeafe;
    --gray: #6b7280; --gray-bg: #f3f4f6;
    --dark: #111827; --body-bg: #f8fafc;
    --card: #ffffff; --border: #e5e7eb;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: var(--body-bg); color: var(--dark); line-height: 1.6; }
  .container { max-width: 1100px; margin: 0 auto; padding: 32px 24px; }
  .header { background: linear-gradient(135deg, #1e293b 0%, #334155 100%); color: #fff; padding: 48px 40px; border-radius: 16px; margin-bottom: 32px; }
  .header h1 { font-size: 28px; font-weight: 700; margin-bottom: 4px; }
  .header .subtitle { font-size: 15px; color: #94a3b8; margin-bottom: 20px; }
  .header-meta { display: flex; gap: 32px; flex-wrap: wrap; font-size: 14px; color: #cbd5e1; }
  .header-meta span { display: flex; align-items: center; gap: 6px; }
  .header-meta .label { color: #94a3b8; }
  .grade-strip { display: grid; grid-template-columns: repeat(7, 1fr); gap: 12px; margin-bottom: 32px; }
  .grade-card { background: var(--card); border-radius: 12px; padding: 20px 12px; text-align: center; border: 1px solid var(--border); transition: transform 0.15s; }
  .grade-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
  .grade-card .skill-num { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: var(--gray); margin-bottom: 8px; }
  .grade-card .grade { font-size: 36px; font-weight: 800; margin-bottom: 4px; }
  .grade-card .skill-label { font-size: 12px; color: var(--gray); }
  .grade-A { color: var(--green); } .grade-B { color: #16a34a; } .grade-C { color: var(--yellow); } .grade-D { color: #f97316; } .grade-F { color: var(--red); }
  .score-bar-wrap { margin: 12px 0; }
  .score-bar-label { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px; }
  .score-bar { height: 10px; background: #e5e7eb; border-radius: 5px; overflow: hidden; }
  .score-bar-fill { height: 100%; border-radius: 5px; transition: width 0.5s ease; }
  .fill-green { background: linear-gradient(90deg, #22c55e, #16a34a); }
  .fill-yellow { background: linear-gradient(90deg, #eab308, #f59e0b); }
  .fill-red { background: linear-gradient(90deg, #ef4444, #dc2626); }
  .fill-blue { background: linear-gradient(90deg, #3b82f6, #2563eb); }
  .section { background: var(--card); border-radius: 16px; border: 1px solid var(--border); padding: 32px; margin-bottom: 24px; }
  .section-header { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }
  .section-icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 22px; font-weight: 800; color: #fff; flex-shrink: 0; }
  .section h2 { font-size: 20px; font-weight: 700; }
  .section h2 span { font-size: 14px; font-weight: 400; color: var(--gray); }
  .tag { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; margin: 2px 4px 2px 0; }
  .tag-green { background: var(--green-bg); color: #166534; } .tag-yellow { background: var(--yellow-bg); color: #854d0e; } .tag-red { background: var(--red-bg); color: #991b1b; } .tag-blue { background: var(--blue-bg); color: #1e40af; } .tag-gray { background: var(--gray-bg); color: #374151; }
  .data-table { width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 14px; }
  .data-table th { text-align: left; padding: 10px 12px; background: #f8fafc; border-bottom: 2px solid var(--border); font-weight: 600; color: var(--gray); font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
  .data-table td { padding: 10px 12px; border-bottom: 1px solid var(--border); }
  .data-table tr:last-child td { border-bottom: none; }
  .callout { padding: 16px 20px; border-radius: 10px; margin: 16px 0; font-size: 14px; }
  .callout-green { background: var(--green-bg); border-left: 4px solid var(--green); } .callout-yellow { background: var(--yellow-bg); border-left: 4px solid var(--yellow); } .callout-red { background: var(--red-bg); border-left: 4px solid var(--red); } .callout-blue { background: var(--blue-bg); border-left: 4px solid var(--blue); }
  .callout strong { font-weight: 700; }
  .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
  @media (max-width: 768px) { .grade-strip { grid-template-columns: repeat(4, 1fr); } .two-col { grid-template-columns: 1fr; } }
  .stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 16px; margin: 16px 0; }
  .stat-box { background: #f8fafc; border-radius: 10px; padding: 16px; text-align: center; }
  .stat-box .stat-value { font-size: 28px; font-weight: 800; }
  .stat-box .stat-label { font-size: 12px; color: var(--gray); margin-top: 4px; }
  .img-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; margin: 16px 0; }
  .img-card { background: #f8fafc; border-radius: 10px; padding: 14px; text-align: center; border: 1px solid var(--border); }
  .img-card .img-icon { font-size: 32px; margin-bottom: 6px; }
  .img-card .img-name { font-size: 11px; color: var(--gray); word-break: break-all; }
  .img-card .img-grade { font-size: 24px; font-weight: 800; margin: 6px 0 2px; }
  .img-card .img-type { font-size: 11px; }
  .rufus-preview { background: #1e293b; color: #e2e8f0; padding: 16px 20px; border-radius: 12px; font-size: 15px; margin: 12px 0; font-family: 'SF Pro', -apple-system, sans-serif; }
  .rufus-preview .rufus-label { font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
  .footer { text-align: center; padding: 32px; color: var(--gray); font-size: 13px; }
  .list-disc { padding-left: 20px; margin: 8px 0; }
  .list-disc li { margin-bottom: 6px; font-size: 14px; }
  .divider { border: none; border-top: 1px solid var(--border); margin: 20px 0; }
  .priority { display: inline-flex; align-items: center; gap: 4px; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
  .priority-critical { background: #fecaca; color: #991b1b; } .priority-high { background: #fed7aa; color: #9a3412; } .priority-medium { background: #fef08a; color: #854d0e; } .priority-low { background: #d1fae5; color: #166534; }
  .edu-box { background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border: 1px solid #bae6fd; border-radius: 12px; padding: 24px; margin: 20px 0; }
  .edu-box h4 { font-size: 15px; font-weight: 700; color: #0369a1; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }
  .edu-box p { font-size: 14px; color: #334155; line-height: 1.7; margin-bottom: 12px; }
  .edu-box p:last-child { margin-bottom: 0; }
  .kg-flow { display: flex; flex-direction: column; gap: 8px; margin: 16px 0; font-size: 13px; font-family: 'SF Mono', 'Fira Code', monospace; }
  .kg-row { display: flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 8px; }
  .kg-row.kg-match { background: var(--green-bg); }
  .kg-row.kg-miss { background: var(--red-bg); }
  .kg-arrow { color: var(--gray); font-weight: 600; }
  .kg-node { background: #dbeafe; color: #1e40af; padding: 2px 8px; border-radius: 4px; font-weight: 600; }
  .kg-field { background: var(--gray-bg); color: #374151; padding: 2px 8px; border-radius: 4px; }
  .kg-result { font-weight: 700; }
  .npo-transform { display: grid; grid-template-columns: 1fr 40px 1fr; gap: 8px; align-items: center; margin: 12px 0; }
  .npo-before { background: var(--gray-bg); padding: 12px; border-radius: 8px; font-size: 13px; text-align: center; }
  .npo-after { background: var(--blue-bg); padding: 12px; border-radius: 8px; font-size: 13px; text-align: center; font-weight: 600; }
  .npo-arrow-col { text-align: center; font-size: 20px; color: var(--blue); font-weight: 800; }
  .rag-flow { background: #1e293b; color: #e2e8f0; padding: 20px; border-radius: 12px; margin: 16px 0; font-size: 13px; line-height: 1.8; }
  .rag-flow .rag-step { display: flex; gap: 12px; margin-bottom: 8px; }
  .rag-flow .rag-label { color: #94a3b8; min-width: 80px; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; flex-shrink: 0; }
  .rag-flow .rag-text { color: #e2e8f0; }
  .rag-flow .rag-highlight { color: #38bdf8; font-weight: 600; }
  .infographic-types { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin: 16px 0; }
  .infographic-type-card { background: #f8fafc; border: 1px solid var(--border); border-radius: 10px; padding: 16px; }
  .infographic-type-card h5 { font-size: 14px; font-weight: 700; margin-bottom: 6px; display: flex; align-items: center; gap: 6px; }
  .infographic-type-card p { font-size: 12px; color: var(--gray); line-height: 1.5; }
  .mobile-weight { background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border: 2px solid #f59e0b; border-radius: 12px; padding: 20px; margin: 20px 0; text-align: center; }
  .mobile-weight .mw-title { font-size: 16px; font-weight: 800; color: #92400e; margin-bottom: 8px; }
  .mobile-weight .mw-bar { display: flex; gap: 4px; align-items: flex-end; justify-content: center; height: 60px; margin: 16px 0; }
  .mobile-weight .mw-bar-item { display: flex; flex-direction: column; align-items: center; gap: 4px; }
  .mobile-weight .mw-bar-block { border-radius: 4px 4px 0 0; width: 80px; }
  .mobile-weight .mw-bar-label { font-size: 11px; color: #92400e; font-weight: 600; }
  .bullet-trunc { margin: 12px 0; }
  .bullet-trunc-row { display: flex; gap: 0; margin-bottom: 6px; font-size: 13px; line-height: 1.5; }
  .bullet-trunc-visible { background: var(--green-bg); padding: 6px 0 6px 10px; border-radius: 6px 0 0 6px; }
  .bullet-trunc-hidden { background: var(--red-bg); padding: 6px 10px 6px 0; border-radius: 0 6px 6px 0; color: var(--gray); opacity: 0.6; }
  .bullet-trunc-cut { background: #fecaca; color: #991b1b; padding: 6px 4px; font-weight: 800; font-size: 11px; display: flex; align-items: center; }
  .img-order { display: flex; gap: 8px; margin: 12px 0; flex-wrap: wrap; }
  .img-order-slot { width: 72px; text-align: center; }
  .img-order-num { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 16px; margin: 0 auto 4px; }
  .img-order-num.order-good { background: var(--green-bg); color: #166534; }
  .img-order-num.order-warn { background: var(--yellow-bg); color: #854d0e; }
  .img-order-num.order-bad { background: var(--red-bg); color: #991b1b; }
  .img-order-label { font-size: 10px; color: var(--gray); }
"""


# ---------------------------------------------------------------------------
# Section renderers — each builds one <div class="section"> block
# ---------------------------------------------------------------------------

def _render_header(data: dict) -> str:
    """Render the dark gradient header with product info."""
    asin = data.get("asin", "N/A")
    product = data.get("product", "Unknown Product")
    market = data.get("market", "US")
    market_id = data.get("market_id", "ATVPDKIKX0DER")
    category = data.get("category", "N/A")
    date_str = data.get("report_date", datetime.now(timezone.utc).strftime("%B %-d, %Y"))

    # Try to extract model from skill_01 injection payload
    model = ""
    s01 = data.get("skill_01", {})
    payload = s01.get("injection_payload", {})
    model = payload.get("model", payload.get("part_number", ""))

    return (
        f'<div class="header">\n'
        f'  <h1>Rufus AI Optimization Report</h1>\n'
        f'  <div class="subtitle">Full 7-Skill Listing Audit &amp; Recommendations</div>\n'
        f'  <div class="header-meta">\n'
        f'    <span><strong>{_esc(product)}</strong></span>\n'
        f'  </div>\n'
        f'  <div class="header-meta" style="margin-top: 12px;">\n'
        f'    <span><span class="label">ASIN:</span> {_esc(asin)}</span>\n'
        + (f'    <span><span class="label">Model:</span> {_esc(model)}</span>\n' if model else "")
        + f'    <span><span class="label">Market:</span> {_esc(market)} ({_esc(market_id)})</span>\n'
        f'    <span><span class="label">Category:</span> {_esc(category)}</span>\n'
        f'    <span><span class="label">Date:</span> {_esc(date_str)}</span>\n'
        f'  </div>\n'
        f'</div>\n'
    )


def _render_grade_strip(grades: dict) -> str:
    """Render the 7-card grade overview strip."""
    cards = []
    for i in range(1, 8):
        key = f"skill_{i:02d}"
        grade_key = f"skill_{i:02d}_taxonomy" if i == 1 else key
        # Try various key patterns from grades_summary
        grade = "N/A"
        for k in [grade_key, key, f"skill_{i:02d}_{SKILL_LABELS.get(key, '').lower().replace(' / ', '_').replace(' ', '_')}"]:
            if k in grades:
                grade = grades[k]
                break
        # fallback: look in the skill data itself
        label = SKILL_LABELS.get(key, f"Skill {i:02d}")
        css = _grade_css(grade) if grade != "N/A" else ""
        cards.append(
            f'  <div class="grade-card">\n'
            f'    <div class="skill-num">Skill {i:02d}</div>\n'
            f'    <div class="grade {css}">{_esc(grade)}</div>\n'
            f'    <div class="skill-label">{_esc(label)}</div>\n'
            f'  </div>'
        )
    return '<div class="grade-strip">\n' + "\n".join(cards) + "\n</div>\n"


def _render_skill_01(data: dict) -> str:
    """Skill 01 — Taxonomy section."""
    s = data.get("skill_01", {})
    scores = s.get("scores", {})
    audit = s.get("audit", {})
    grade = scores.get("grade", "N/A")
    completeness = scores.get("completeness_pct", 0)
    tokens = scores.get("high_confidence_tokens", 0)
    null_count = audit.get("null_count", 0)
    standardized = audit.get("standardized_count", 0)
    null_fields = audit.get("null_fields", {})
    kg = audit.get("knowledge_graph_mapping", {})

    parts = [
        '<div class="section">',
        _section_header("01", "Structured Taxonomy & Attribute Injection",
                        "Backend attribute completeness & Amazon Knowledge Graph alignment", grade),
        # ── Educational: Knowledge Graph explanation ──
        '<div class="edu-box">',
        '<h4>&#x1F9E0; Why Backend Attributes Power the Knowledge Graph</h4>',
        '<p>Amazon\'s <strong>Knowledge Graph</strong> is a web of connected entities: '
        'products, features, use-cases, and customer intents. When Rufus answers a shopping '
        'question, it traverses this graph to find matching products. <strong>Your backend '
        'attributes are the entry points</strong> &mdash; every populated field creates a '
        'node connection that Rufus can follow.</p>',
        '<p>Empty fields = missing connections = invisible to Rufus for that query type:</p>',
        '<div class="kg-flow">',
        '<div class="kg-row kg-match">'
        '<span>Customer asks: <em>"power bank for camping"</em></span>'
        '<span class="kg-arrow">&rarr;</span>'
        '<span class="kg-node">Outdoor</span>'
        '<span class="kg-arrow">&rarr;</span>'
        '<span class="kg-field">recommended_uses = Indoor/Outdoor</span>'
        '<span class="kg-arrow">&rarr;</span>'
        '<span class="kg-result" style="color:#166534;">&#x2705; Matched</span>'
        '</div>',
        '<div class="kg-row kg-miss">'
        '<span>Customer asks: <em>"waterproof charger"</em></span>'
        '<span class="kg-arrow">&rarr;</span>'
        '<span class="kg-node">Water Resistant</span>'
        '<span class="kg-arrow">&rarr;</span>'
        '<span class="kg-field">waterproof_rating = MISSING</span>'
        '<span class="kg-arrow">&rarr;</span>'
        '<span class="kg-result" style="color:#991b1b;">&#x274C; Invisible</span>'
        '</div>',
        '</div>',
        '<p style="font-size:13px; color:#64748b; margin-top:8px;">'
        'Each high-confidence token below is a node that Rufus can index. '
        'More tokens = more ways customers can discover your product.</p>',
        '</div>',
        # ── Score data ──
        f'<div class="stat-grid">',
        _stat_box(f"{completeness:.1f}%", "Completeness", _grade_color_var(grade)),
        _stat_box(tokens, "High-Confidence Tokens"),
        _stat_box(null_count, "Null Fields"),
        _stat_box(standardized, "Values Standardized"),
        '</div>',
        _score_bar("Backend Completeness", completeness),
    ]

    # Null fields callout
    if null_count == 0:
        parts.append(_callout("<strong>Perfect.</strong> All backend attributes are populated with valid values.", "green"))
    elif null_count <= 3:
        null_list = ", ".join(f"<code>{_esc(f)}</code>" for f in null_fields.keys())
        parts.append(_callout(
            f"<strong>Excellent.</strong> Only {null_count} field(s) empty: {null_list}. "
            "All other backend attributes are populated with valid values.", "green"
        ))
    else:
        null_list = ", ".join(f"<code>{_esc(f)}</code>" for f in list(null_fields.keys())[:5])
        parts.append(_callout(
            f"<strong>Needs attention.</strong> {null_count} empty fields including: {null_list}.", "yellow"
        ))

    # Knowledge Graph
    if not kg:
        parts.append(_callout(
            "<strong>Knowledge Graph:</strong> No use-case mappings were triggered. "
            "Consider adding use-case keywords to <code>recommended_uses_for_product</code> "
            "to activate Rufus Knowledge Graph node chains.", "blue"
        ))
    else:
        kg_items = ", ".join(f"{_esc(k)} &rarr; {_esc(', '.join(v))}" for k, v in kg.items())
        parts.append(_callout(f"<strong>Knowledge Graph Mappings:</strong> {kg_items}", "green"))

    parts.append('</div>')
    return "\n".join(parts)


def _render_skill_02(data: dict) -> str:
    """Skill 02 — NPO section."""
    s = data.get("skill_02", {})
    scores = s.get("scores", {})
    npo = s.get("npo", {})
    copy = s.get("copy", {})
    grade = scores.get("grade", "N/A")
    density = scores.get("semantic_density", {})

    title_info = copy.get("title", {})
    char_count = title_info.get("char_count", 0)
    leads_cat = title_info.get("leads_with_category", False)
    preview_70 = title_info.get("truncated_preview_70", "")
    phrases = npo.get("input_keywords", npo.get("output_noun_phrases", []))
    filler_count = len(density.get("filler_words", []))

    # Determine explanation color based on grade
    expl_color = "yellow" if grade == "F" else ("green" if grade in ("A", "B") else "blue")

    # Get keywords and noun phrases for the educational visual
    input_kws = npo.get("input_keywords", [])
    output_nps = npo.get("output_noun_phrases", [])

    parts = [
        '<div class="section">',
        _section_header("02", "Noun Phrase Optimization & RAG Copy",
                        "Keyword density & Rufus-ready bullet copy assessment", grade),
        # ── Educational: NPO + RAG explanation ──
        '<div class="edu-box">',
        '<h4>&#x1F50D; What Are Noun Phrases &amp; How RAG Uses Them</h4>',
        '<p><strong>Noun Phrases</strong> are structured semantic units that combine '
        '[Feature] + [Benefit] + [Context]. Unlike raw keywords (<code>"fast charger"</code>), '
        'noun phrases carry complete meaning that AI can retrieve and cite as standalone facts.</p>',
        '<p><strong>RAG (Retrieval-Augmented Generation)</strong> is how Rufus answers questions. '
        'It retrieves product data chunks, then generates a natural answer. Noun phrases make your '
        'content "chunk-friendly" &mdash; each phrase is a self-contained fact Rufus can pull '
        'and cite directly.</p>',
    ]

    # Show actual keyword → noun phrase transforms for THIS product
    if input_kws and output_nps:
        parts.append('<h4 style="font-size: 13px; color: #0369a1; margin: 16px 0 8px;">Keyword &rarr; Noun Phrase Transformation (this product)</h4>')
        max_show = min(3, len(input_kws), len(output_nps))
        for i in range(max_show):
            kw = input_kws[i] if i < len(input_kws) else ""
            np_text = output_nps[i] if i < len(output_nps) else ""
            # Truncate long NPs for display
            np_display = np_text[:80] + "..." if len(np_text) > 80 else np_text
            parts.append(
                f'<div class="npo-transform">'
                f'<div class="npo-before"><code>{_esc(kw)}</code></div>'
                f'<div class="npo-arrow-col">&rarr;</div>'
                f'<div class="npo-after">{_esc(np_display)}</div>'
                f'</div>'
            )

    # RAG flow visualization
    sample_np = output_nps[0][:60] if output_nps else "Fast-charging USB-C technology"
    parts.append(
        '<div class="rag-flow">'
        '<div style="font-size:11px; color:#64748b; text-transform:uppercase; letter-spacing:1px; margin-bottom:10px;">How Rufus Uses Your Noun Phrases</div>'
        '<div class="rag-step">'
        '<span class="rag-label">Customer:</span>'
        '<span class="rag-text">"What\'s a good slim power bank for my iPhone?"</span>'
        '</div>'
        '<div class="rag-step">'
        '<span class="rag-label">Retrieves:</span>'
        f'<span class="rag-text"><span class="rag-highlight">{_esc(sample_np)}</span></span>'
        '</div>'
        '<div class="rag-step">'
        '<span class="rag-label">Answers:</span>'
        f'<span class="rag-text">"This product offers <span class="rag-highlight">{_esc(sample_np[:40])}...</span>"</span>'
        '</div>'
        '</div>'
    )

    parts.append('</div>')  # close edu-box

    if grade == "F":
        parts.append(_callout(
            "<strong>Why F?</strong> The density scorer checks whether the generated noun phrases "
            "appear verbatim inside the bullet text. If the listing uses natural marketing copy "
            "(not formula-generated text), the density match will be low. "
            "<strong>This is a scoring calibration issue, not necessarily a content quality issue.</strong>",
            "yellow"
        ))

    # Title preview
    parts.append(f'<div style="margin-top:16px;"><strong>Title Analysis</strong>')
    parts.append(
        f'<div class="rufus-preview">'
        f'<div class="rufus-label">Rufus Chat Preview (first 70 chars)</div>'
        f'{_esc(preview_70)}&hellip;</div></div>'
    )

    parts.append('<div class="stat-grid">')
    parts.append(_stat_box(char_count, "Title Characters"))
    parts.append(_stat_box("Yes" if leads_cat else "No", "Opens with Category",
                           "var(--green)" if leads_cat else "var(--red)"))
    parts.append(_stat_box(len(phrases), "NPO Phrases Generated"))
    parts.append(_stat_box(filler_count, "Filler Words Found"))
    parts.append('</div>')

    # Noun phrases
    if phrases:
        parts.append('<h4 style="margin-top: 16px; font-size: 14px; color: var(--gray);">Generated Noun Phrases (for downstream skills)</h4>')
        parts.append('<div style="margin-top: 8px;">')
        for p in phrases:
            parts.append(_tag(p, "blue"))
        parts.append('</div>')

    parts.append('</div>')
    return "\n".join(parts)


def _render_skill_03(data: dict) -> str:
    """Skill 03 — UGC section."""
    s = data.get("skill_03", {})
    scores = s.get("scores", {})
    ugc = s.get("ugc_mining", {})
    qa = s.get("qa_seeding", {})
    grade = scores.get("grade", "N/A")
    sentiment = ugc.get("sentiment", {})
    pos = sentiment.get("positive_count", 0)
    neg = sentiment.get("negative_count", 0)
    neutral = max(0, len(ugc.get("technical_questions_found", [])) - pos - neg) if pos + neg < 12 else 0
    # Better: count total reviews minus pos/neg
    total_reviews = pos + neg
    neutral_count = max(0, total_reviews - pos - neg) if total_reviews > pos + neg else 0
    # Use a simple heuristic: if we have snippets count
    pos_snips = sentiment.get("top_positive_snippets", [])
    neg_snips = sentiment.get("top_negative_snippets", [])
    neg_themes = sentiment.get("recurring_negative_keywords", {})
    questions = ugc.get("technical_questions_found", [])
    qa_pairs = qa.get("qa_pairs", [])

    parts = [
        '<div class="section">',
        _section_header("03", "UGC Ground Truth Mining & Q&A Seeding",
                        "Customer review sentiment, question extraction & Q&A pair generation", grade),
    ]

    if grade == "F":
        parts.append(_callout(
            "<strong>Why F?</strong> The coverage scorer measures how well the existing listing "
            "copy addresses the mined questions. The F grade means the listing's bullets and "
            "backend don't yet explicitly answer the customer questions extracted from reviews. "
            f"The Q&A pairs were successfully generated ({len(qa_pairs)} pairs) &mdash; "
            "they just haven't been seeded into the listing yet.",
            "yellow"
        ))

    # Sentiment breakdown
    parts.append('<div class="two-col" style="margin-top: 20px;"><div>')
    parts.append('<h4 style="font-size: 14px; color: var(--gray); margin-bottom: 12px;">Customer Sentiment Breakdown</h4>')
    parts.append('<div class="stat-grid" style="grid-template-columns: repeat(3, 1fr);">')
    parts.append(_stat_box(pos, "Positive", "var(--green)"))

    # Estimate neutral from total if available
    est_neutral = max(0, len(pos_snips) + len(neg_snips) - pos - neg)
    parts.append(_stat_box(est_neutral if est_neutral > 0 else "—", "Neutral", "var(--gray)"))
    parts.append(_stat_box(neg, "Negative", "var(--red)"))
    parts.append('</div>')

    # Negative themes
    if neg_themes:
        parts.append('<h4 style="font-size: 14px; color: var(--gray); margin-top: 20px; margin-bottom: 8px;">Recurring Negative Themes</h4>')
        for theme in neg_themes:
            parts.append(_tag(theme, "red"))

    parts.append('</div><div>')

    # Questions
    if questions:
        parts.append('<h4 style="font-size: 14px; color: var(--gray); margin-bottom: 12px;">Questions Found in Reviews</h4>')
        parts.append('<ul class="list-disc">')
        for q in questions[:5]:
            parts.append(f'<li>{_esc(q)}</li>')
        parts.append('</ul>')

    # QA count
    parts.append('<h4 style="font-size: 14px; color: var(--gray); margin-top: 20px; margin-bottom: 8px;">Q&A Pairs Seeded</h4>')
    parts.append(f'<div class="stat-box" style="display: inline-block;">')
    parts.append(f'<div class="stat-value" style="color:var(--blue)">{len(qa_pairs)}</div>')
    parts.append(f'<div class="stat-label">Ready-to-Seed Pairs</div></div>')

    parts.append('</div></div>')  # close two-col

    # Negative snippets
    if neg_snips:
        parts.append('<hr class="divider">')
        parts.append('<h4 style="font-size: 14px; color: var(--gray); margin-bottom: 8px;">Top Negative Review Snippets</h4>')
        for snip in neg_snips[:3]:
            truncated = snip[:200] + "…" if len(snip) > 200 else snip
            parts.append(
                f'<div class="callout callout-red" style="margin-bottom:8px;">'
                f'<strong>{_esc(truncated)}</strong> '
                f'{_tag("1-2 stars", "red")}</div>'
            )

    # Recommendation
    recs = data.get("skill_03", {}).get("recommendations", [])
    if recs:
        rec_text = " ".join(f"({i+1}) {_esc(r)}" for i, r in enumerate(recs[:3]))
        parts.append(_callout(f"<strong>Recommendation:</strong> {rec_text}", "blue"))

    parts.append('</div>')
    return "\n".join(parts)


def _render_skill_04(data: dict) -> str:
    """Skill 04 — Visual SEO section."""
    s = data.get("skill_04", {})
    scores = s.get("scores", {})
    summary = s.get("summary", {})
    images = s.get("image_reports", [])
    grade = scores.get("grade", "N/A")

    total = summary.get("total_images", len(images))
    generic = summary.get("generic_alt_text_count", 0)
    infographics = summary.get("infographics_audited", 0)
    avg_score = scores.get("average_alt_text_score", 0)

    type_icons = {"main": "🖼️", "infographic": "📊", "lifestyle": "🏕️", "comparison": "📱", "detail": "🔍"}

    parts = [
        '<div class="section">',
        _section_header("04", "Multimodal Visual SEO Validation",
                        "Image alt-text quality, OCR audit & infographic noun-phrase coverage", grade),
        # ── Educational: What are infographics + why Rufus reads them ──
        '<div class="edu-box">',
        '<h4>&#x1F4F7; What Are Infographics &amp; Why Rufus Reads Them</h4>',
        '<p><strong>Infographics</strong> are product images that contain <strong>text overlays</strong> '
        '&mdash; specs, feature callouts, comparison charts, dimension labels. Unlike lifestyle photos, '
        'infographics carry structured data that Rufus can read via <strong>OCR (Optical Character Recognition)</strong>.</p>',
        '<p>When Rufus scans your listing, it reads text from ALL image types. Infographics with clear, '
        'OCR-optimized text give Rufus extra data points beyond your title and bullets.</p>',
        '<div class="infographic-types">',
        '<div class="infographic-type-card">'
        '<h5>&#x1F4CA; Specs Infographic</h5>'
        '<p>Technical specifications in a clean grid: capacity, wattage, dimensions, weight. '
        'Use dark text on white background, &#x2265;24px font.</p></div>',
        '<div class="infographic-type-card">'
        '<h5>&#x2B50; Feature Callout</h5>'
        '<p>Top 3-5 features with icons and benefit text. Each callout should be a '
        'self-contained noun phrase Rufus can index.</p></div>',
        '<div class="infographic-type-card">'
        '<h5>&#x1F4CB; Comparison Chart</h5>'
        '<p>Side-by-side comparison vs competitors. Headers should match A+ comparison '
        'table for consistency across the listing.</p></div>',
        '<div class="infographic-type-card">'
        '<h5>&#x1F3AF; Lifestyle + Overlay</h5>'
        '<p>Product in use with spec callouts overlaid. Combines emotional appeal with '
        'data Rufus can read. Keep text areas high-contrast.</p></div>',
        '</div>',
        '</div>',
    ]

    if grade == "F":
        parts.append(_callout(
            "<strong>Why F?</strong> This skill audits alt-text quality and OCR text on infographic images. "
            "Without direct access to the actual listing images, estimated metadata is used. "
            "<strong>In production, this skill works best with actual image alt-text and OCR text. "
            "Use Skill 09 (Infographic Generator) to create OCR-optimized infographics from your product data.</strong>",
            "yellow"
        ))

    parts.append('<div class="stat-grid">')
    parts.append(_stat_box(total, "Total Images"))
    parts.append(_stat_box(generic, "Generic Alt-Text", "var(--red)" if generic > 0 else ""))
    parts.append(_stat_box(infographics, "Infographics Audited"))
    parts.append(_stat_box(avg_score, "Avg Alt-Text Score", "var(--red)" if avg_score < 5 else "var(--green)"))
    parts.append('</div>')

    # Image grid
    if images:
        parts.append('<h4 style="font-size: 14px; color: var(--gray); margin: 16px 0 8px;">Image-by-Image Audit</h4>')
        parts.append('<div class="img-grid">')
        for img in images:
            itype = img.get("image_type", "unknown")
            icon = type_icons.get(itype, "📷")
            fname = img.get("filename", "unknown")
            alt_score = img.get("alt_text", {}).get("score", {})
            img_grade = alt_score.get("grade", "F")
            is_generic = alt_score.get("is_generic", False)
            ocr = img.get("ocr_audit", {})
            has_ocr = ocr.get("has_ocr_text", False)

            type_color = "blue" if itype == "infographic" else ("green" if itype == "lifestyle" else "gray")
            ocr_note = ""
            if itype == "infographic" and has_ocr:
                phrases = len(ocr.get("present_phrases", []))
                ocr_note = f'<div style="font-size:11px; color:var(--yellow); margin-top:4px;">OCR: {phrases} phrases detected</div>'
            elif is_generic:
                ocr_note = '<div style="font-size:11px; color:var(--red); margin-top:4px;">Generic alt-text</div>'
            elif not has_ocr and itype != "main":
                ocr_note = '<div style="font-size:11px; color:var(--gray); margin-top:4px;">No OCR text</div>'

            parts.append(
                f'<div class="img-card">'
                f'<div class="img-icon">{icon}</div>'
                f'<div class="img-grade {_grade_css(img_grade)}">{_esc(img_grade)}</div>'
                f'<div class="img-type">{_tag(itype, type_color)}</div>'
                f'<div class="img-name">{_esc(fname)}</div>'
                f'{ocr_note}'
                f'</div>'
            )
        parts.append('</div>')

    # OCR tips
    ocr_tips = summary.get("ocr_tips", [])
    if ocr_tips:
        parts.append('<h4 style="font-size: 14px; color: var(--gray); margin: 16px 0 8px;">OCR Best Practices for Infographics</h4>')
        parts.append('<ul class="list-disc">')
        for tip in ocr_tips:
            parts.append(f'<li>{_esc(tip)}</li>')
        parts.append('</ul>')

    parts.append('</div>')
    return "\n".join(parts)


def _render_skill_05(data: dict) -> str:
    """Skill 05 — A+ Content section."""
    s = data.get("skill_05", {})
    scores = s.get("scores", {})
    ct = s.get("comparison_table_audit", {})
    mod = s.get("module_audit", {})
    hall = s.get("hallucination_risk", {})
    grade = scores.get("grade", "N/A")

    composite = scores.get("composite_aplus_score", 0)
    risk_level = hall.get("risk_level", "N/A")
    specific_ratio = ct.get("specific_data_ratio", 0)
    mod_count = mod.get("module_count", 0)
    header_score = ct.get("semantic_header_score", 0)

    parts = [
        '<div class="section">',
        _section_header("05", "A+ Knowledge Base Engineering",
                        "Comparison table semantics, module audit & hallucination risk", grade),
        '<div class="stat-grid">',
        _stat_box(f"{composite:.1f}", "Composite A+ Score", _grade_color_var(grade)),
        _stat_box(risk_level, "Hallucination Risk",
                  "var(--green)" if risk_level == "LOW" else "var(--red)"),
        _stat_box(f"{specific_ratio:.1f}%", "Specific Data Ratio"),
        _stat_box(mod_count, "A+ Modules"),
        '</div>',
        '<div class="two-col" style="margin-top: 20px;"><div>',
        '<h4 style="font-size: 14px; color: var(--gray); margin-bottom: 12px;">Comparison Table Headers</h4>',
        _score_bar("Semantic Header Coverage", header_score),
    ]

    # Found headers
    found = ct.get("semantic_headers_found", [])
    if found:
        parts.append('<div style="margin-top: 12px;"><strong style="font-size:13px;">Found:</strong><br>')
        for h in found:
            parts.append(_tag(h, "green"))
        parts.append('</div>')

    missing = ct.get("semantic_headers_missing", [])
    if missing:
        parts.append('<div style="margin-top: 8px;"><strong style="font-size:13px;">Missing:</strong><br>')
        for h in missing:
            parts.append(_tag(h, "red"))
        parts.append('</div>')

    parts.append('</div><div>')

    # Module audit
    parts.append('<h4 style="font-size: 14px; color: var(--gray); margin-bottom: 12px;">Module Audit</h4>')
    parts.append('<table class="data-table"><tr><th>Module Type</th><th>Status</th></tr>')
    present_types = [t.lower().replace(" ", "_") for t in mod.get("module_types", [])]
    all_types = list(set(present_types + [m.lower().replace(" ", "_") for m in mod.get("missing_kb_modules", [])]))
    for mt in all_types:
        label = mt.replace("_", " ").title()
        present = mt in present_types
        status = _tag("Present", "green") if present else _tag("Missing", "red")
        parts.append(f'<tr><td>{_esc(label)}</td><td>{status}</td></tr>')
    parts.append('</table>')

    # Vague claims
    vague = hall.get("vague_claims_found", [])
    if vague:
        parts.append('<h4 style="font-size: 14px; color: var(--gray); margin: 16px 0 8px;">Vague Claims Flagged</h4>')
        for v in vague:
            parts.append(_tag(v, "yellow"))

    parts.append('</div></div>')  # close two-col

    # Recommendations
    recs = ct.get("recommendations", [])
    if recs:
        rec_text = " ".join(f"({i+1}) {_esc(r)}" for i, r in enumerate(recs[:3]))
        parts.append(_callout(f"<strong>Recommendations:</strong> {rec_text}", "blue"))

    parts.append('</div>')
    return "\n".join(parts)


def _render_skill_06(data: dict) -> str:
    """Skill 06 — Mobile section (Full Mobile Audit)."""
    s = data.get("skill_06", {})
    scores = s.get("scores", {})
    title_a = s.get("title_analysis", {})
    bullet_t = s.get("bullet_truncation", {})
    img_order = s.get("image_order", {})
    swipe = s.get("swipe_depth", {})
    fold = s.get("aplus_fold", {})
    touch = s.get("touch_targets", {})
    voice = s.get("voice_readiness", {})
    videos = s.get("video_analysis", [])
    grade = scores.get("grade", "N/A")

    title_score = scores.get("title_score", title_a.get("title_score", 0))
    bullet_score = scores.get("bullet_truncation_score", bullet_t.get("avg_bullet_score", 50))
    image_score = scores.get("image_order_score", img_order.get("order_score", 50))
    swipe_score = scores.get("swipe_depth_score", swipe.get("swipe_depth_score", 50))
    fold_score = scores.get("aplus_fold_score", fold.get("fold_score", 50))
    touch_score_val = scores.get("touch_target_score", touch.get("touch_target_score", 50))
    voice_score = scores.get("voice_readiness_score", voice.get("voice_readiness_score", 50))
    video_score = scores.get("video_avg_score", 50)
    composite = scores.get("composite_mobile_score", 0)
    char_count = title_a.get("char_count", 0)
    preview = title_a.get("rufus_chat_preview", "")
    opens_cat = title_a.get("opens_with_category", False)

    parts = [
        '<div class="section">',
        _section_header("06", "Mobile Habitat Optimization — Full Audit",
                        "8-module mobile-first analysis: title, bullets, images, swipe, A+ fold, CTA, voice, video", grade),
        # ── Mobile weight education ──
        '<div class="mobile-weight">',
        '<div class="mw-title">Amazon Mobile Algorithm Weighs 2&times; Heavier Than Desktop</div>',
        '<div class="mw-bar">',
        '<div class="mw-bar-item">'
        '<div class="mw-bar-block" style="height:25px; background:#94a3b8;"></div>'
        '<div class="mw-bar-label">Desktop</div></div>',
        '<div class="mw-bar-item">'
        '<div class="mw-bar-block" style="height:20px; background:#94a3b8;"></div>'
        '<div class="mw-bar-label">iPad</div></div>',
        '<div class="mw-bar-item">'
        '<div class="mw-bar-block" style="height:55px; background: linear-gradient(180deg, #f59e0b, #d97706);"></div>'
        '<div class="mw-bar-label">Mobile</div></div>',
        '</div>',
        '<div style="font-size:13px; color:#92400e;">Mobile signals carry significantly more weight in Amazon\'s ranking algorithm. '
        'This audit covers 8 mobile-specific optimization dimensions.</div>',
        '</div>',
    ]

    # ── Composite Score Grid (8 modules) ──
    parts.append('<div class="stat-grid" style="grid-template-columns: repeat(4, 1fr);">')
    for label, sc in [
        ("Title (20%)", title_score), ("Bullets (20%)", bullet_score),
        ("Image Order (15%)", image_score), ("Swipe Depth (10%)", swipe_score),
        ("A+ Fold (10%)", fold_score), ("Touch CTA (5%)", touch_score_val),
        ("Voice Ready (10%)", voice_score), ("Video (10%)", video_score),
    ]:
        parts.append(_stat_box(f"{sc:.0f}", label, _grade_color_var(score_to_grade(sc))))
    parts.append('</div>')
    parts.append(_score_bar("Composite Mobile Score", composite, _fill_class(grade)))

    # ── Module 1: Title ──
    parts.append('<hr class="divider">')
    parts.append('<h3 style="font-size: 16px; margin-bottom: 12px;">&#x2460; Title First-70 Rule</h3>')
    parts.append(
        f'<div class="rufus-preview">'
        f'<div class="rufus-label">How Rufus Shows This Title in Chat</div>'
        f'{_esc(preview)}</div>'
    )
    if opens_cat:
        parts.append(_callout(
            f'<strong>Score: {title_score:.0f}</strong> &mdash; Opens with category keyword. '
            f'At {char_count} chars, first 70 characters capture key differentiators.', "green"))
    else:
        parts.append(_callout(
            f'<strong>Score: {title_score:.0f}</strong> &mdash; Does not open with category keyword. '
            f'Reorder so category appears in first 70 chars for Rufus matching.', "yellow"))

    # ── Module 2: Bullet Truncation ──
    per_bullet = bullet_t.get("per_bullet", [])
    if per_bullet:
        trunc_count = bullet_t.get("truncated_count", 0)
        parts.append('<hr class="divider">')
        parts.append(f'<h3 style="font-size: 16px; margin-bottom: 12px;">&#x2461; Bullet Truncation (mobile cuts at ~80 chars)</h3>')
        if trunc_count == 0:
            parts.append(_callout(f"<strong>Score: {bullet_score:.0f}</strong> &mdash; All bullets fit within mobile truncation.", "green"))
        else:
            parts.append(_callout(f"<strong>Score: {bullet_score:.0f}</strong> &mdash; {trunc_count} of {len(per_bullet)} bullets are truncated on mobile.", "yellow"))
        parts.append('<div class="bullet-trunc">')
        for b in per_bullet:
            visible = b.get("visible_text", "")
            hidden = b.get("hidden_text", "")
            if hidden:
                parts.append(
                    f'<div class="bullet-trunc-row">'
                    f'<div class="bullet-trunc-visible">{_esc(visible)}</div>'
                    f'<div class="bullet-trunc-cut">CUT</div>'
                    f'<div class="bullet-trunc-hidden">{_esc(hidden[:40])}{"..." if len(hidden) > 40 else ""}</div>'
                    f'</div>'
                )
            else:
                parts.append(
                    f'<div class="bullet-trunc-row">'
                    f'<div class="bullet-trunc-visible" style="border-radius:6px;">{_esc(visible)}</div>'
                    f'</div>'
                )
        parts.append('</div>')

    # ── Module 3: Image Order ──
    slots = img_order.get("per_slot", [])
    if slots:
        parts.append('<hr class="divider">')
        parts.append(f'<h3 style="font-size: 16px; margin-bottom: 12px;">&#x2462; Image Stack Order</h3>')
        parts.append(f'<div class="img-order">')
        for slot in slots:
            num = slot.get("slot", 0)
            actual = slot.get("actual_type", "?")
            recommended = slot.get("recommended_type", "?")
            is_match = slot.get("is_match", False)
            is_crit = slot.get("is_critical_mismatch", False)
            css_class = "order-good" if is_match else ("order-bad" if is_crit else "order-warn")
            parts.append(
                f'<div class="img-order-slot">'
                f'<div class="img-order-num {css_class}">{num}</div>'
                f'<div class="img-order-label">{_esc(actual)}</div>'
                f'</div>'
            )
        parts.append('</div>')
        rec = img_order.get("recommendation", "")
        if rec:
            parts.append(_callout(f"<strong>Score: {image_score:.0f}</strong> &mdash; {_esc(rec)}", "yellow"))
        else:
            parts.append(_callout(f"<strong>Score: {image_score:.0f}</strong> &mdash; Image order matches the recommended mobile sequence.", "green"))

    # ── Module 4+5+6: Swipe, Fold, Touch (compact grid) ──
    parts.append('<hr class="divider">')
    parts.append('<div class="two-col"><div>')

    # Swipe Depth
    parts.append(f'<h3 style="font-size: 16px; margin-bottom: 12px;">&#x2463; Swipe Depth</h3>')
    first_info = swipe.get("first_infographic_at_swipe")
    comp_pos = swipe.get("comparison_table_at_position")
    parts.append(f'<div class="stat-grid" style="grid-template-columns: 1fr 1fr;">')
    parts.append(_stat_box(f"Swipe {first_info}" if first_info else "N/A", "First Specs",
                           "var(--green)" if first_info and first_info <= 2 else "var(--yellow)"))
    parts.append(_stat_box(f"Pos {comp_pos}" if comp_pos else "N/A", "Comparison Table",
                           "var(--green)" if comp_pos and comp_pos <= 6 else "var(--yellow)"))
    parts.append('</div>')

    # A+ Fold
    parts.append(f'<h3 style="font-size: 16px; margin: 16px 0 12px;">&#x2464; A+ Fold</h3>')
    first_mod_type = fold.get("first_module_type", "N/A")
    fact_density = fold.get("fact_density", 0)
    if first_mod_type:
        mod_color = "green" if fold_score >= 70 else "yellow"
        parts.append(_callout(
            f'<strong>First A+ module:</strong> {_tag(first_mod_type.replace("_", " ").title(), mod_color)} '
            f'&mdash; {fact_density} fact patterns detected. Score: {fold_score:.0f}', mod_color))

    parts.append('</div><div>')

    # Touch Targets
    parts.append(f'<h3 style="font-size: 16px; margin-bottom: 12px;">&#x2465; Touch Targets</h3>')
    touch_issues = touch.get("issues", [])
    if touch_issues:
        for ti in touch_issues:
            parts.append(f'<div style="font-size:13px; color:var(--red); margin-bottom:6px;">&#x26A0; {_esc(ti)}</div>')
    else:
        parts.append(_callout("<strong>All touch-target checks passed.</strong>", "green"))

    # Voice Readiness
    parts.append(f'<h3 style="font-size: 16px; margin: 16px 0 12px;">&#x2466; Voice-Search Readiness</h3>')
    flagged = voice.get("flagged_phrases", [])
    conv_ratio = voice.get("conversational_ratio", 0)
    parts.append(f'<div class="stat-grid" style="grid-template-columns: 1fr 1fr;">')
    parts.append(_stat_box(f"{voice_score:.0f}", "Voice Score", _grade_color_var(score_to_grade(voice_score))))
    parts.append(_stat_box(f"{conv_ratio:.0%}", "Conversational Ratio",
                           "var(--green)" if conv_ratio >= 0.6 else "var(--yellow)"))
    parts.append('</div>')
    if flagged:
        parts.append('<div style="margin-top: 8px;">')
        for f in flagged[:5]:
            parts.append(_tag(f.get("text", ""), "yellow"))
        parts.append('</div>')

    parts.append('</div></div>')  # close two-col

    # ── Module 8: Video Table ──
    if videos:
        parts.append('<hr class="divider">')
        parts.append(f'<h3 style="font-size: 16px; margin-bottom: 12px;">&#x2467; Video Arc Strategy</h3>')
        parts.append('<table class="data-table">')
        parts.append('<tr><th>Video</th><th>Format</th><th>Problem Arc</th><th>Solution Arc</th><th>Score</th></tr>')
        for v in videos:
            vtitle = v.get("video_title", "Untitled")
            ratio = v.get("aspect_ratio", "?")
            is_vert = v.get("is_vertical_9x16", False)
            has_p = v.get("has_problem_arc", False)
            has_s = v.get("has_solution_arc", False)
            vscore = v.get("video_score", 0)
            fmt_tag = _tag(f"{ratio} Vertical", "green") if is_vert else _tag(f"{ratio}", "yellow")
            p_tag = _tag("Yes", "green") if has_p else _tag("No", "red")
            s_tag = _tag("Yes", "green") if has_s else _tag("No", "red")
            parts.append(
                f'<tr><td style="font-size:13px;">"{_esc(vtitle)}"</td>'
                f'<td>{fmt_tag}</td><td>{p_tag}</td><td>{s_tag}</td>'
                f'<td><strong style="color:{_grade_color_var(score_to_grade(vscore))}">{vscore:.0f}</strong></td></tr>'
            )
        parts.append('</table>')

    parts.append('</div>')
    return "\n".join(parts)


def _render_skill_07(data: dict) -> str:
    """Skill 07 — Integrity section."""
    s = data.get("skill_07", {})
    scores = s.get("scores", {})
    report = s.get("compliance_report", {})
    grade = scores.get("grade", "N/A")

    integrity_score = scores.get("integrity_score", 0)
    issues = scores.get("issues_found", 0)
    stuffing = report.get("keyword_stuffing", {})
    stuffed = stuffing.get("stuffed_phrases", {})
    legacy = stuffing.get("legacy_seo_phrases", [])
    conflicts = report.get("backend_conflicts", [])
    neg_themes = report.get("unaddressed_negative_themes", [])

    parts = [
        '<div class="section">',
        _section_header("07", "Semantic Integrity & Anti-Optimization",
                        "Keyword stuffing, backend conflicts & negative theme coverage", grade),
        _score_bar("Integrity Score", integrity_score),
        '<div class="stat-grid">',
        _stat_box(f"{integrity_score:.0f}", "Integrity Score", _grade_color_var(grade)),
        _stat_box(issues, "Total Issues", "var(--red)" if issues > 0 else "var(--green)"),
        _stat_box(len(conflicts), "Backend Conflicts", "var(--green)" if not conflicts else "var(--red)"),
        _stat_box(len(legacy), "Legacy SEO Spam", "var(--green)" if not legacy else "var(--red)"),
        '</div>',
        '<div class="two-col" style="margin-top: 20px;"><div>',
    ]

    # Keyword stuffing table
    if stuffed:
        parts.append('<h4 style="font-size: 14px; color: var(--gray); margin-bottom: 12px;">Keyword Stuffing Detected</h4>')
        parts.append('<table class="data-table"><tr><th>Phrase</th><th>Occurrences</th><th>Severity</th></tr>')
        for phrase, count in stuffed.items():
            severity = "high" if count >= 5 else ("medium" if count >= 3 else "low")
            parts.append(
                f'<tr><td><code>{_esc(phrase)}</code></td>'
                f'<td>{count}x across title + bullets</td>'
                f'<td><span class="priority {_priority_class(severity)}">{severity.title()}</span></td></tr>'
            )
        parts.append('</table>')
    else:
        parts.append(_callout("<strong>No keyword stuffing detected.</strong>", "green"))

    parts.append('</div><div>')

    # Negative themes
    if neg_themes:
        parts.append('<h4 style="font-size: 14px; color: var(--gray); margin-bottom: 12px;">Unaddressed Negative Themes</h4>')
        parts.append('<table class="data-table"><tr><th>Theme</th><th>Action Required</th></tr>')
        for nt in neg_themes:
            theme = nt.get("theme", "unknown") if isinstance(nt, dict) else str(nt)
            rec = nt.get("recommendation", "") if isinstance(nt, dict) else ""
            parts.append(
                f'<tr><td>{_tag(theme, "red")}</td>'
                f'<td style="font-size:13px;">{_esc(rec)}</td></tr>'
            )
        parts.append('</table>')

    parts.append('</div></div>')  # close two-col

    # Good news callout
    if not conflicts and not legacy:
        parts.append(_callout(
            "<strong>Good news:</strong> Zero backend conflicts &mdash; all title claims match "
            "the backend attributes. No legacy SEO phrases detected.", "green"
        ))

    parts.append('</div>')
    return "\n".join(parts)


def _render_action_plan(data: dict) -> str:
    """Build the prioritized action plan from all skills' recommendations."""
    actions: list[dict] = []

    # Skill 07 — unaddressed negative themes → Critical
    s07 = data.get("skill_07", {}).get("compliance_report", {})
    for nt in s07.get("unaddressed_negative_themes", []):
        if isinstance(nt, dict):
            actions.append({
                "action": f"Address \"{nt['theme']}\" concern",
                "detail": nt.get("recommendation", ""),
                "priority": "critical",
                "skills": ["S07"],
            })

    # Skill 03 — QA seeding
    s03 = data.get("skill_03", {})
    qa_count = s03.get("qa_seeding", {}).get("pair_count", len(s03.get("qa_seeding", {}).get("qa_pairs", [])))
    if qa_count > 0:
        actions.append({
            "action": f"Seed Q&A with {qa_count} generated pairs",
            "detail": "Prioritize answers for the most common customer questions extracted from reviews.",
            "priority": "high",
            "skills": ["S03"],
        })

    # Skill 05 — missing modules
    s05 = data.get("skill_05", {})
    missing_mods = s05.get("module_audit", {}).get("missing_kb_modules", [])
    for m in missing_mods:
        actions.append({
            "action": f"Add {m.replace('_', ' ').title()} module to A+ Content",
            "detail": "Include structured specifications for Rufus Knowledge Graph indexing.",
            "priority": "high",
            "skills": ["S05"],
        })

    # Skill 05 — comparison table headers
    ct = s05.get("comparison_table_audit", {})
    missing_headers = ct.get("semantic_headers_missing", [])
    if missing_headers:
        header_list = ", ".join(missing_headers[:4])
        actions.append({
            "action": "Expand A+ comparison table headers",
            "detail": f"Add: {header_list} to increase semantic header coverage.",
            "priority": "high",
            "skills": ["S05"],
        })

    # Skill 01 — knowledge graph
    s01 = data.get("skill_01", {})
    kg = s01.get("audit", {}).get("knowledge_graph_mapping", {})
    if not kg:
        actions.append({
            "action": "Add use-case keywords to backend attributes",
            "detail": "Update recommended_uses_for_product to trigger Knowledge Graph node chains.",
            "priority": "medium",
            "skills": ["S01"],
        })

    # Skill 04 — generic alt text
    s04 = data.get("skill_04", {})
    generic_count = s04.get("summary", {}).get("generic_alt_text_count", 0)
    if generic_count > 0:
        actions.append({
            "action": "Optimize image alt-text",
            "detail": f"Replace {generic_count} generic alt-text entries with descriptive text containing target noun phrases.",
            "priority": "medium",
            "skills": ["S04"],
        })

    # Skill 07 — keyword stuffing
    stuffed = s07.get("keyword_stuffing", {}).get("stuffed_phrases", {})
    for phrase, count in stuffed.items():
        if count >= 3:
            actions.append({
                "action": f"Reduce \"{phrase}\" keyword repetition",
                "detail": f"Currently {count}x across title + bullets. Vary phrasing to avoid stuffing.",
                "priority": "low",
                "skills": ["S07"],
            })

    # Sort by priority
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    actions.sort(key=lambda a: priority_order.get(a["priority"], 99))

    if not actions:
        return ""

    parts = [
        '<div class="section" style="border: 2px solid var(--blue);">',
        '<div class="section-header">',
        '<div class="section-icon" style="background: linear-gradient(135deg, #3b82f6, #2563eb);">🎯</div>',
        '<div><h2>Priority Action Plan</h2>',
        '<div style="font-size:14px; color:#6b7280;">Top recommendations ranked by impact on Rufus optimization</div>',
        '</div></div>',
        '<table class="data-table">',
        '<tr><th style="width:40px;">#</th><th>Action</th><th>Impact</th><th>Skills Affected</th></tr>',
    ]

    for i, a in enumerate(actions[:10], 1):
        skill_tags = " ".join(_tag(s, "gray") for s in a["skills"])
        parts.append(
            f'<tr><td><strong>{i}</strong></td>'
            f'<td><strong>{_esc(a["action"])}</strong><br>'
            f'<span style="font-size:13px; color:var(--gray);">{_esc(a["detail"])}</span></td>'
            f'<td><span class="priority {_priority_class(a["priority"])}">{a["priority"].title()}</span></td>'
            f'<td>{skill_tags}</td></tr>'
        )

    parts.append('</table></div>')
    return "\n".join(parts)


def _render_footer(data: dict) -> str:
    """Render footer with metadata."""
    asin = data.get("asin", "N/A")
    market = data.get("market", "US")
    market_id = data.get("market_id", "ATVPDKIKX0DER")
    date_str = data.get("report_date", datetime.now(timezone.utc).strftime("%B %-d, %Y"))
    runtime = data.get("runtime", "—")
    total_fields = data.get("total_fields", "—")

    return (
        f'<div class="footer">\n'
        f'  <div style="margin-bottom: 8px; font-weight: 600;">Rufus Optimization Skills Library v1.0</div>\n'
        f'  <div>Generated {_esc(date_str)} &bull; Market: {_esc(market)} ({_esc(market_id)}) '
        f'&bull; ASIN: {_esc(asin)} &bull; 7 Skills &bull; {_esc(str(total_fields))} Catalog Fields</div>\n'
        f'  <div style="margin-top: 4px;">Pipeline runtime: {_esc(str(runtime))} &bull; Powered by Anergy Academy</div>\n'
        f'</div>\n'
    )


# ---------------------------------------------------------------------------
# Main class — follows the standard skill contract
# ---------------------------------------------------------------------------

class Skill08:
    """
    Skill08: Visual Report Generator

    Converts the full 7-skill pipeline JSON output into a polished HTML report
    with infographics, grade cards, score bars, and a prioritized action plan.

    Parameters:
        pipeline_result: dict — The full output dict from run_pipeline.py
                         (contains skill_01..skill_07 + grades_summary + meta).
        market:          str  — Market code for header display (default "US").
        market_id:       str  — Amazon marketplace ID (default "ATVPDKIKX0DER").
        category:        str  — Human-readable category name for header.
        total_fields:    int  — Number of catalog fields (for footer).
        runtime:         str  — Pipeline runtime string (for footer).
    """

    def __init__(
        self,
        pipeline_result: dict[str, Any],
        *,
        market: str = "US",
        market_id: str = "ATVPDKIKX0DER",
        category: str = "N/A",
        total_fields: int = 0,
        runtime: str = "—",
    ) -> None:
        self.data = dict(pipeline_result)
        # Inject display metadata
        self.data.setdefault("market", market)
        self.data.setdefault("market_id", market_id)
        self.data.setdefault("category", category)
        self.data.setdefault("total_fields", total_fields)
        self.data.setdefault("runtime", runtime)
        self.data.setdefault("report_date", datetime.now(timezone.utc).strftime("%B %-d, %Y"))

        self._html: str = ""
        self._output: dict[str, Any] = {}
        log_step("Skill08", "initialized", f"ASIN={self.data.get('asin', '?')}")

    def run(self) -> "Skill08":
        """Generate the HTML report."""
        log_step("Skill08", "building", "HTML report")

        grades = self.data.get("grades_summary", {})

        sections = [
            f'<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            f'<title>Rufus Optimization Report &mdash; {_esc(self.data.get("product", "Product"))}</title>\n'
            f'<style>{CSS}</style>\n</head>\n<body>\n<div class="container">\n',
            _render_header(self.data),
            _render_grade_strip(grades),
            _render_skill_01(self.data),
            _render_skill_02(self.data),
            _render_skill_03(self.data),
            _render_skill_04(self.data),
            _render_skill_05(self.data),
            _render_skill_06(self.data),
            _render_skill_07(self.data),
            _render_action_plan(self.data),
            _render_footer(self.data),
            '</div>\n</body>\n</html>',
        ]

        self._html = "\n".join(sections)

        self._output = {
            "skill_id": "08",
            "skill_name": "Visual Report Generator",
            "asin": self.data.get("asin", "N/A"),
            "report_html_length": len(self._html),
            "report_date": self.data.get("report_date"),
            "grades": grades,
        }

        log_step("Skill08", "complete", f"{len(self._html)} chars of HTML generated")
        return self

    def to_json(self) -> dict[str, Any]:
        """Return the skill output as a JSON-serializable dict."""
        return self._output

    def get_html(self) -> str:
        """Return the generated HTML string."""
        return self._html

    def save_html(self, output_path: str | Path) -> Path:
        """Write the HTML report to a file and return the path."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self._html, encoding="utf-8")
        log_step("Skill08", "saved", str(path))
        return path


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Skill 08 — Visual Report Generator: Converts pipeline JSON to HTML report"
    )
    parser.add_argument("--input", "-i", help="Path to pipeline JSON file")
    parser.add_argument("--output", "-o", help="Path for HTML report output")
    parser.add_argument("--market", default="US", help="Market code (default: US)")
    parser.add_argument("--market-id", default="ATVPDKIKX0DER", help="Marketplace ID")
    parser.add_argument("--category", default="N/A", help="Category name for display")
    parser.add_argument("--total-fields", type=int, default=0, help="Number of catalog fields")
    args = parser.parse_args()

    # Load pipeline JSON
    pipeline_data = load_json_input(args.input)

    # Run the report generator
    skill = Skill08(
        pipeline_data,
        market=args.market,
        market_id=args.market_id,
        category=args.category,
        total_fields=args.total_fields,
    )
    skill.run()

    # Determine output path
    if args.output:
        out_path = Path(args.output)
    else:
        asin = pipeline_data.get("asin", "unknown")
        out_path = Path(f"results/{asin}_report.html")

    skill.save_html(out_path)

    # Also output the JSON metadata
    save_json_output(skill.to_json(), None)  # prints to stdout


if __name__ == "__main__":
    main()
