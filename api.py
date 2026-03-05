"""
api.py — Rufus Optimization Skills Library: FastAPI Web API
==============================================================

Exposes the full 7-skill pipeline as a REST API for external systems
(Auto-Pilot, n8n, partners) to call via HTTP.

The auto-generated OpenAPI/Swagger UI (served at /docs) acts as the
complete handshake manual for external developers. Every field, type,
and constraint is documented inline from rufus_skill_contract.md.

Usage:
    uvicorn api:app --host 0.0.0.0 --port 8000 --reload

Swagger UI:
    http://localhost:8000/docs

ReDoc UI:
    http://localhost:8000/redoc

Health check:
    GET  http://localhost:8000/health

Run pipeline:
    POST http://localhost:8000/pipeline
    Content-Type: application/json
    Body: <ProductRequest JSON — see schema at /docs>

Fetch cached result:
    GET  http://localhost:8000/results/{asin}
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Path setup — allow imports from shared/
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_SHARED = _HERE / "shared"
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))

from utils.helpers import save_json_output

from skill_01_taxonomy.skill_01 import Skill01
from skill_02_npo.skill_02 import Skill02
from skill_03_ugc.skill_03 import Skill03
from skill_04_visual_seo.skill_04 import Skill04
from skill_05_aplus.skill_05 import Skill05
from skill_06_mobile.skill_06 import Skill06
from skill_07_integrity.skill_07 import Skill07

# ---------------------------------------------------------------------------
# App definition
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Rufus Optimization Skills API",
    description=(
        "AI-driven Amazon listing optimization pipeline for the **Rufus AI shopping assistant** "
        "(Amazon's RAG-based conversational commerce engine).\n\n"
        "This API wraps the full 7-skill pipeline. Submit a product JSON and receive a structured "
        "audit across 9 dimensions: taxonomy, NPO copy, UGC mining, visual SEO, A+ content, "
        "mobile optimization, and semantic integrity.\n\n"
        "**Source of truth:** `rufus_skill_contract.md` in the project repository.\n\n"
        "**Grading scale:** A (≥90) · B (≥75) · C (≥60) · D (≥40) · F (<40)"
    ),
    version="1.0.0",
    contact={
        "name": "John / Anergy Academy",
        "email": "johnchin@pandaocean.com",
    },
    license_info={
        "name": "Proprietary",
    },
)


# ===========================================================================
# INPUT MODELS
# Modelled directly from rufus_skill_contract.md — field names and types
# must match exactly. Do not rename fields without updating the contract.
# ===========================================================================

class BTGModel(BaseModel):
    """
    Amazon Browse Tree Guide node.
    Provides category classification and Knowledge Graph alignment for Skill01.
    """
    category: str = Field(
        ...,
        description="Top-level Amazon category string (e.g. 'Cell Phones & Accessories').",
        example="Cell Phones & Accessories",
    )
    node_id: str = Field(
        "",
        description="Amazon Browse Node ID. Leave empty if unknown.",
        example="2407749011",
    )
    node_path: str = Field(
        "",
        description=(
            "Full breadcrumb path from root to the leaf node. "
            "Example: 'Cell Phones & Accessories > Accessories > Chargers & Power Adapters > Portable Power Banks'"
        ),
        example="Cell Phones & Accessories > Accessories > Chargers & Power Adapters > Portable Power Banks",
    )


class ReviewItem(BaseModel):
    """
    A single customer review. Used by Skill03 (UGC Mining).
    Ratings ≤2 are classified as negative; ratings ≥4 are classified as positive.
    """
    text: str = Field(
        "",
        description="Free-text review body. Mined for customer questions and negative sentiment keywords.",
        example="Incredibly thin — barely adds any bulk to my iPhone 16 Pro.",
    )
    rating: int = Field(
        3,
        ge=1,
        le=5,
        description="Star rating 1–5. Rating ≤2 → negative; ≥4 → positive.",
        example=5,
    )


class QAItem(BaseModel):
    """
    A competitor or platform Q&A pair. Used by Skill03 to seed additional Q&A answers.
    """
    question: str = Field(
        ...,
        description="Customer question text.",
        example="Can I use this while wirelessly charging my phone?",
    )
    answer: str = Field(
        ...,
        description="Answer text to the question.",
        example="Yes, you can use your phone normally while the power bank charges wirelessly.",
    )


class ProductContextModel(BaseModel):
    """
    Factual product attributes used by Skill03 to fill Q&A answer templates.
    Omitting these fields uses safe defaults (IPX4, 12-month warranty, 2 hours).
    """
    waterproof_rating: str = Field(
        "IPX4",
        description="Waterproof/water-resistance rating (e.g. 'IPX5', 'IPX7', 'None').",
        example="None",
    )
    warranty_months: int = Field(
        12,
        description="Warranty duration in months. Fills the warranty Q&A template.",
        example=24,
    )
    charge_hours: float = Field(
        2.0,
        description="Hours to fully charge the device. Fills the charging_time Q&A template.",
        example=2.0,
    )


class ImageItem(BaseModel):
    """
    Metadata for a single listing image.
    Used by Skill04 (Visual SEO) and Skill06 (Mobile Audit — image order + swipe depth).
    """
    filename: str = Field(
        ...,
        description="Descriptive filename used as the image identifier in audit reports.",
        example="anker_a1665_main.jpg",
    )
    image_type: str = Field(
        ...,
        description=(
            "Image category. Must be one of: 'main', 'lifestyle', 'infographic', 'video_thumb'. "
            "Controls alt-text generation template and OCR tip inclusion."
        ),
        example="main",
    )
    alt_text: str = Field(
        "",
        description=(
            "Current alt-text string. Scored against generic patterns and noun-phrase coverage. "
            "Generic alt-text (e.g. 'product image 1', length <40 chars) scores 0."
        ),
        example="Anker Nano Power Bank black",
    )
    ocr_text: str = Field(
        "",
        description=(
            "Visible overlay text found inside the image (for infographic images only). "
            "Leave empty for non-infographic images."
        ),
        example="15W Qi2 MagSafe | 20W USB-C | 5000mAh | 0.34 inch Ultra-Slim",
    )


class ModuleItem(BaseModel):
    """
    An A+ content module. Used by Skill05 (A+ Knowledge Base) and Skill06 (Mobile — A+ fold).
    """
    type: str = Field(
        ...,
        description=(
            "Module type. Knowledge-base types recognized: 'faq', 'technical_specs', "
            "'comparison_table', 'specification_chart', 'q&a', 'detailed_description', "
            "'product_description_text'. Other types count as modules but not KB modules."
        ),
        example="faq",
    )
    content: str = Field(
        "",
        description=(
            "Text content of the module. Scanned for specific data anchors "
            "(numbers with units: mAh, W, IPX*, etc.) in hallucination risk scoring."
        ),
        example="Q: Is it airplane safe? A: Yes, 18.5Wh is under the 100Wh FAA limit.",
    )


class VideoItem(BaseModel):
    """
    Listing video metadata. Used by Skill06 (Mobile Audit — video arc scoring).
    Score = +50 if 9:16 vertical, +40 if problem→solution narrative arc detected.
    """
    title: str = Field(
        "",
        description="Video title. Scanned for problem and solution arc keywords.",
        example="Stop settling for bulky MagSafe batteries — meet the Anker Nano Power Bank",
    )
    description: str = Field(
        "",
        description=(
            "Video description or transcript. Combined with title for P→S arc detection. "
            "Problem keywords: 'struggle', 'problem', 'issue', 'can\\'t', 'stuck'. "
            "Solution keywords: 'solve', 'solution', 'finally', 'easy', 'enjoy'."
        ),
        example="Tired of thick battery packs? The ultra-slim Anker Nano finally solves the bulk problem.",
    )
    aspect_ratio: str = Field(
        "16:9",
        description=(
            "Video aspect ratio. Use '9:16' or 'vertical' for mobile-first vertical format (+50 pts). "
            "Any other value scores 0 for the vertical bonus. "
            "Amazon gives 2x algorithmic weight to mobile signals."
        ),
        example="9:16",
    )


class ProductPipelineRequest(BaseModel):
    """
    Full product data payload required to run the 7-skill Rufus optimization pipeline.

    All fields match the schema defined in `tools/MASTER_PROMPT.md` and `rufus_skill_contract.md`.
    Use the Master Prompt (tools/MASTER_PROMPT.md) with an LLM to extract this JSON from
    an Amazon product page URL.

    **Data flow between skills (automatic, handled by the API):**
    - Skill02 → noun_phrases → Skill04
    - Skill01 → injection_payload → Skill07 (backend_attrs)
    - Skill02 → rag_ready_bullets → Skill07 (bullets)
    - Skill03 → recurring_negative_keywords → Skill07 (negative_review_themes)
    """

    asin: str = Field(
        ...,
        min_length=1,
        description="Amazon Standard Identification Number (10 characters).",
        example="B0FKN7X7HM",
    )
    market: str = Field(
        "us",
        description="Marketplace code. Supported: 'us', 'uk', 'jp', 'ca', 'au'.",
        example="us",
    )
    category_path: str = Field(
        "",
        description=(
            "Amazon category path in snake_case slash-separated format. "
            "Example: 'cell_phones_accessories/accessories/chargers_power_adapters/portable_power_banks'"
        ),
        example="cell_phones_accessories/accessories/chargers_power_adapters/portable_power_banks",
    )
    title: str = Field(
        ...,
        min_length=1,
        description=(
            "Exact product title as it appears on the Amazon listing. "
            "Skill06 evaluates the first 70 characters as the Rufus chat window preview. "
            "Best titles open with a category keyword (e.g. 'Power Bank', 'Portable Charger')."
        ),
        example=(
            "Anker Nano Power Bank, Ultra-Slim 5,000mAh Magnetic Wireless Charging Battery, "
            "Qi2 Certified 15W Max MagSafe-Compatible Portable Charger"
        ),
    )
    bullets: list[str] = Field(
        ...,
        min_length=1,
        description=(
            "Bullet points from the 'About this item' section. Provide 3–5 bullets. "
            "Skill02 rewrites these as RAG-ready copy. Skill06 audits mobile truncation cutoff."
        ),
        example=[
            "Ultra-Slim 0.3-Inch Design: 5,000mAh of dependable charging in a 0.3-inch magnetic power bank.",
            "Qi2 Certified Fast Charging: 15W Max MagSafe-compatible fast charging, iPhone 16 Pro to 25% in 42 minutes.",
        ],
    )
    clr: dict[str, Any] = Field(
        ...,
        description=(
            "Category Listing Report (CLR) flat-file attributes. Key/value pairs from the Amazon "
            "backend flat-file template. Empty values ('') will appear in Skill01's null_fields audit. "
            "Keys containing 'color'/'colour' are standardized; keys containing 'use'/'purpose' trigger "
            "Knowledge Graph mapping."
        ),
        example={
            "brand_name": "Anker",
            "battery_capacity": "5000",
            "battery_capacity_unit_of_measure": "milliamp_hours",
            "color_name": "Black",
            "connector_type": "USB-C",
        },
    )
    spec: dict[str, Any] = Field(
        ...,
        description=(
            "Technical specification sheet. Snake_case keys, numeric values where appropriate. "
            "Merged with clr; spec values are overridden by clr values on key collision."
        ),
        example={
            "capacity_mah": 5000,
            "wireless_output": "15W Qi2 MagSafe",
            "usb_c_output": "20W Max",
            "weight_grams": 122,
        },
    )
    btg: BTGModel = Field(
        ...,
        description="Amazon Browse Tree Guide node. Drives Knowledge Graph alignment in Skill01.",
    )
    keywords: list[str] = Field(
        default_factory=list,
        description=(
            "5–10 relevant search terms from keyword research. "
            "Skill02 transforms each keyword into a Noun Phrase Optimization (NPO) phrase "
            "using the formula: [Noun/Feature] + [Benefit] + [Context]."
        ),
        example=["magsafe power bank", "qi2 wireless power bank iphone", "slim magnetic portable charger"],
    )
    topic_clusters: dict[str, list[str]] = Field(
        default_factory=dict,
        description=(
            "Customer intent clusters. Format: {intent_label: [question1, question2]}. "
            "Used by Skill02 to anchor RAG-ready bullets to specific customer queries. "
            "Example: {'charging_speed': ['How fast does it charge?', 'What wattage is wireless?']}"
        ),
        example={
            "charging_speed": ["How fast does it charge?", "What wattage is the wireless charging?"],
            "compatibility": ["Does it work with iPhone 16?", "Does it work through a case?"],
        },
    )
    reviews: list[ReviewItem] = Field(
        default_factory=list,
        description=(
            "Customer reviews. Provide 10+ reviews for best Skill03 scoring. "
            "Skill03 mines questions, classifies sentiment, and seeds Q&A pairs. "
            "Negative themes (rating ≤2) flow into Skill07's integrity check."
        ),
    )
    competitor_qas: list[QAItem] = Field(
        default_factory=list,
        description=(
            "Q&A pairs from the product page or competitor listings. "
            "Added to Skill03's qa_pairs output with template_key='competitor_derived'."
        ),
    )
    product_context: ProductContextModel = Field(
        default_factory=ProductContextModel,
        description=(
            "Factual context used to fill Skill03 Q&A answer templates. "
            "Affects the waterproof, warranty, and charging_time Q&A answers."
        ),
    )
    images: list[ImageItem] = Field(
        default_factory=list,
        description=(
            "Listing image metadata. Used by Skill04 (alt-text scoring + OCR audit) and "
            "Skill06 (image order + swipe depth). Provide images in display order. "
            "Main image should be first."
        ),
    )
    comparison_table: dict[str, dict[str, str]] = Field(
        default_factory=dict,
        description=(
            "A+ comparison table. Format: {header: {asin_or_competitor_label: value_string}}. "
            "Skill05 audits header semantic coverage and data specificity. "
            "Values should contain numbers+units (e.g. '5,000mAh', 'IPX5') not vague text."
        ),
        example={
            "Battery Capacity": {"B0FKN7X7HM": "5,000mAh", "Competitor": "3,000mAh"},
            "Wireless Charging": {"B0FKN7X7HM": "15W Qi2", "Competitor": "7.5W"},
        },
    )
    modules: list[ModuleItem] = Field(
        default_factory=list,
        description=(
            "A+ content modules. Skill05 checks for KB module coverage. "
            "Skill06 audits A+ fold position (above-fold = +points for Rufus indexing). "
            "Include at minimum: comparison_table + faq + technical_specs."
        ),
    )
    product_claims: list[str] = Field(
        default_factory=list,
        description=(
            "Key marketing claims from the listing. Used by Skill05 to detect hallucination risk. "
            "Vague claims ('long battery life', 'fast charging') raise risk score. "
            "Specific claims ('18.5Wh', '42 minutes to 25%') lower it."
        ),
        example=["5,000mAh capacity", "Qi2 certified 15W fast charging", "25% charge in 42 minutes"],
    )
    videos: list[VideoItem] = Field(
        default_factory=list,
        description=(
            "Listing videos. Skill06 scores each video on two signals: "
            "(1) 9:16 vertical format (+50 pts — mobile-first), "
            "(2) Problem→Solution narrative arc (+40 pts). "
            "Amazon gives 2x algorithmic weight to mobile signals."
        ),
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "asin": "B0FKN7X7HM",
                "market": "us",
                "category_path": "cell_phones_accessories/accessories/chargers_power_adapters/portable_power_banks",
                "title": "Anker Nano Power Bank, Ultra-Slim 5,000mAh Magnetic Wireless Charging Battery, Qi2 Certified 15W Max MagSafe-Compatible Portable Charger",
                "bullets": [
                    "Ultra-Slim 0.3-Inch Design: 5,000mAh of dependable charging in a 0.3-inch magnetic power bank.",
                    "Qi2 Certified Fast Charging: 15W Max, iPhone 16 Pro to 25% in just 42 minutes.",
                    "20W Max USB-C Charging: up to 20W of power out through its USB-C port.",
                    "Advanced Cooling System: stays below 104F — 14 degrees cooler than industry standard.",
                    "What You Get: Anker Nano Power Bank, USB-C cable, welcome guide, 24-month warranty.",
                ],
                "clr": {"brand_name": "Anker", "battery_capacity": "5000", "color_name": "Black", "connector_type": "USB-C"},
                "spec": {"capacity_mah": 5000, "wireless_output": "15W Qi2 MagSafe", "weight_grams": 122},
                "btg": {
                    "category": "Cell Phones & Accessories",
                    "node_id": "2407749011",
                    "node_path": "Cell Phones & Accessories > Accessories > Chargers & Power Adapters > Portable Power Banks",
                },
                "keywords": ["magsafe power bank", "qi2 wireless power bank iphone", "slim magnetic portable charger"],
                "topic_clusters": {
                    "charging_speed": ["How fast does it charge?", "What wattage is the wireless charging?"],
                    "compatibility": ["Does it work with iPhone 16?", "Does it work through a case?"],
                },
                "reviews": [
                    {"text": "Incredibly thin — love how it snaps on with strong magnets.", "rating": 5},
                    {"text": "USB-C port stopped working after 2 months.", "rating": 2},
                ],
                "competitor_qas": [
                    {"question": "Does it work with MagSafe cases?", "answer": "Yes, compatible with MagSafe cases."}
                ],
                "product_context": {"waterproof_rating": "None", "warranty_months": 24, "charge_hours": 2},
                "images": [
                    {"filename": "main.jpg", "image_type": "main", "alt_text": "Anker Nano Power Bank black", "ocr_text": ""},
                    {"filename": "specs.jpg", "image_type": "infographic", "alt_text": "Anker specs infographic", "ocr_text": "15W Qi2 | 20W USB-C | 5000mAh"},
                ],
                "comparison_table": {
                    "Battery Capacity": {"B0FKN7X7HM": "5,000mAh", "B09NRG4GK3": "5,000mAh"},
                    "Wireless Charging": {"B0FKN7X7HM": "15W Qi2", "B09NRG4GK3": "7.5W MagSafe"},
                },
                "modules": [
                    {"type": "comparison_table", "content": "See comparison table above"},
                    {"type": "faq", "content": "Q: Is it airplane safe? A: Yes, 18.5Wh is under the 100Wh FAA limit."},
                ],
                "product_claims": ["5,000mAh capacity", "Qi2 certified 15W fast charging", "25% charge in 42 minutes"],
                "videos": [
                    {
                        "title": "Stop settling for bulky MagSafe batteries",
                        "description": "Tired of thick battery packs? The ultra-slim Anker Nano finally solves the bulk problem. Enjoy effortless portable power.",
                        "aspect_ratio": "9:16",
                    }
                ],
            }
        }
    }


# ===========================================================================
# OUTPUT MODELS
# ===========================================================================

class GradesSummary(BaseModel):
    """
    Top-level grade for each of the 7 pipeline skills.
    Use this for dashboard views and quick pass/fail checks.
    Grades: A (≥90) · B (≥75) · C (≥60) · D (≥40) · F (<40)
    """
    skill_01_taxonomy: str = Field(..., description="Taxonomy & Attribute Injection grade.", example="A")
    skill_02_npo: str = Field(..., description="Noun Phrase Optimization & RAG Copy grade.", example="B")
    skill_03_ugc: str = Field(..., description="UGC Mining & Q&A Seeding grade.", example="A")
    skill_04_visual_seo: str = Field(..., description="Visual SEO Validation grade.", example="C")
    skill_05_aplus: str = Field(..., description="A+ Knowledge Base Engineering grade.", example="C")
    skill_06_mobile: str = Field(..., description="Mobile Habitat Optimization grade (2x weight in Amazon algo).", example="B")
    skill_07_integrity: str = Field(..., description="Semantic Integrity & Anti-Optimization grade.", example="C")


class PipelineResponse(BaseModel):
    """
    Full pipeline output for a single ASIN.

    The `grades_summary` field gives a fast overview. Each `skill_NN` field
    contains the complete structured output from that skill, matching the
    output schema defined in `rufus_skill_contract.md`.

    **Key output paths (per contract):**
    - `skill_01.injection_payload` → optimized backend attribute payload
    - `skill_02.copy.rag_ready_bullets` → RAG-optimized listing bullets
    - `skill_02.npo.output_noun_phrases` → noun phrases for alt-text optimization
    - `skill_03.qa_seeding.qa_pairs` → seeded Q&A pairs ready for Amazon Q&A upload
    - `skill_04.image_reports` → per-image alt-text scores and OCR audit
    - `skill_05.hallucination_risk` → hallucination risk level and vague claims found
    - `skill_06.title_analysis.rufus_chat_preview` → first 70-char Rufus chat window preview
    - `skill_07.compliance_report` → keyword stuffing and backend conflict report
    """
    asin: str = Field(..., description="Product ASIN.")
    product: str = Field(..., description="Product title (truncated to 120 chars for display).")
    market: str = Field(..., description="Marketplace code.")
    category_path: str = Field(..., description="Amazon category path.")
    pipeline_run_at: str = Field(..., description="ISO 8601 UTC timestamp of this pipeline run.")
    grades_summary: GradesSummary
    skill_01: dict[str, Any] = Field(..., description="Full Skill01 (Taxonomy) output. See rufus_skill_contract.md §SKILL 01.")
    skill_02: dict[str, Any] = Field(..., description="Full Skill02 (NPO & Copy) output. See rufus_skill_contract.md §SKILL 02.")
    skill_03: dict[str, Any] = Field(..., description="Full Skill03 (UGC Mining) output. See rufus_skill_contract.md §SKILL 03.")
    skill_04: dict[str, Any] = Field(..., description="Full Skill04 (Visual SEO) output. See rufus_skill_contract.md §SKILL 04.")
    skill_05: dict[str, Any] = Field(..., description="Full Skill05 (A+ KB) output. See rufus_skill_contract.md §SKILL 05.")
    skill_06: dict[str, Any] = Field(..., description="Full Skill06 (Mobile Audit) output. See rufus_skill_contract.md §SKILL 06.")
    skill_07: dict[str, Any] = Field(..., description="Full Skill07 (Integrity) output. See rufus_skill_contract.md §SKILL 07.")


class HealthResponse(BaseModel):
    """API health check response."""
    status: str = Field(..., example="ok")
    version: str = Field(..., example="1.0.0")
    timestamp: str = Field(..., description="UTC timestamp of health check.")
    skills_loaded: list[str] = Field(..., description="Names of skill modules loaded successfully.")


# ===========================================================================
# PIPELINE EXECUTION HELPER
# ===========================================================================

def _run_pipeline(req: ProductPipelineRequest) -> dict[str, Any]:
    """
    Execute the 7-skill pipeline against the validated request.
    Implements the cross-skill data flow from rufus_skill_contract.md:
      Skill01.injection_payload       → Skill07.backend_attrs
      Skill02.npo.output_noun_phrases → Skill04.noun_phrases
      Skill02.copy.rag_ready_bullets  → Skill07.bullets
      Skill03.ugc.recurring_negatives → Skill07.negative_review_themes
    """
    asin = req.asin

    # Skill 01 — Taxonomy & Attribute Injection
    s1 = Skill01(
        clr=req.clr,
        spec=req.spec,
        btg=req.btg.model_dump(),
        asin=asin,
    ).run()
    r1 = s1.to_json()

    # Skill 02 — NPO & RAG-Ready Copy
    s2 = Skill02(
        keywords=req.keywords,
        bullets=req.bullets,
        title=req.title,
        topic_clusters=req.topic_clusters,
        asin=asin,
    ).run()
    r2 = s2.to_json()

    # Skill 03 — UGC Mining & Q&A Seeding
    s3 = Skill03(
        reviews=[r.model_dump() for r in req.reviews],
        competitor_qas=[q.model_dump() for q in req.competitor_qas],
        product_context=req.product_context.model_dump(),
        asin=asin,
    ).run()
    r3 = s3.to_json()

    # Skill 04 — Visual SEO (receives noun_phrases FROM Skill02)
    s4 = Skill04(
        images=[img.model_dump() for img in req.images],
        noun_phrases=r2.get("npo", {}).get("output_noun_phrases", []),
        product_name=req.title.split(",")[0] if req.title else "Product",
        asin=asin,
    ).run()
    r4 = s4.to_json()

    # Skill 05 — A+ Knowledge Base
    s5 = Skill05(
        comparison_table=req.comparison_table,
        modules=[m.model_dump() for m in req.modules],
        product_claims=req.product_claims,
        asin=asin,
    ).run()
    r5 = s5.to_json()

    # Skill 06 — Mobile Habitat Optimization
    category = req.btg.category if req.btg.category else req.category_path.split("/")[-1].replace("_", " ")
    s6 = Skill06(
        title=req.title,
        bullets=req.bullets,
        images=[img.model_dump() for img in req.images],
        modules=[m.model_dump() for m in req.modules],
        videos=[v.model_dump() for v in req.videos],
        category=category,
        asin=asin,
    ).run()
    r6 = s6.to_json()

    # Skill 07 — Semantic Integrity (receives data FROM Skills 01, 02, 03)
    s7 = Skill07(
        title=req.title,
        bullets=r2.get("copy", {}).get("rag_ready_bullets", req.bullets),
        backend_attrs=r1.get("injection_payload", {}),
        negative_review_themes=list(
            r3.get("ugc_mining", {}).get("sentiment", {}).get("recurring_negative_keywords", {}).keys()
        ),
        asin=asin,
    ).run()
    r7 = s7.to_json()

    return {
        "asin": asin,
        "product": req.title[:120],
        "market": req.market,
        "category_path": req.category_path,
        "pipeline_run_at": datetime.now(timezone.utc).isoformat(),
        "grades_summary": {
            "skill_01_taxonomy":   r1["scores"]["grade"],
            "skill_02_npo":        r2["scores"]["grade"],
            "skill_03_ugc":        r3["scores"]["grade"],
            "skill_04_visual_seo": r4["scores"]["grade"],
            "skill_05_aplus":      r5["scores"]["grade"],
            "skill_06_mobile":     r6["scores"]["grade"],
            "skill_07_integrity":  r7["scores"]["grade"],
        },
        "skill_01": r1,
        "skill_02": r2,
        "skill_03": r3,
        "skill_04": r4,
        "skill_05": r5,
        "skill_06": r6,
        "skill_07": r7,
    }


# ===========================================================================
# ROUTES
# ===========================================================================

@app.get(
    "/",
    include_in_schema=False,
    summary="Redirect to Swagger UI",
)
async def root() -> RedirectResponse:
    """Redirect bare root URL to the interactive API documentation."""
    return RedirectResponse(url="/docs")


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Health check",
    description=(
        "Confirms the API is running and all 7 skill modules are loaded. "
        "Use this endpoint in Auto-Pilot and monitoring systems to verify service availability "
        "before submitting pipeline jobs."
    ),
)
async def health() -> HealthResponse:
    """Return service health and loaded skill inventory."""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
        skills_loaded=[
            "Skill01 — Taxonomy & Attribute Injection",
            "Skill02 — NPO & RAG-Ready Copy",
            "Skill03 — UGC Mining & Q&A Seeding",
            "Skill04 — Visual SEO Validation",
            "Skill05 — A+ Knowledge Base Engineering",
            "Skill06 — Mobile Habitat Optimization (v2.0, 8 modules)",
            "Skill07 — Semantic Integrity & Anti-Optimization",
        ],
    )


@app.post(
    "/pipeline",
    response_model=PipelineResponse,
    tags=["Pipeline"],
    summary="Run the full 7-skill optimization pipeline",
    description=(
        "Submits a product JSON and synchronously runs all 7 Rufus optimization skills "
        "in sequence with correct cross-skill data chaining.\n\n"
        "**Processing time:** Typically <1 second (all skills are pure-Python, no external API calls).\n\n"
        "**Data flow (automatic):**\n"
        "- `Skill01.injection_payload` → `Skill07.backend_attrs`\n"
        "- `Skill02.npo.output_noun_phrases` → `Skill04.noun_phrases`\n"
        "- `Skill02.copy.rag_ready_bullets` → `Skill07.bullets`\n"
        "- `Skill03.ugc_mining.recurring_negative_keywords` → `Skill07.negative_review_themes`\n\n"
        "**Result is also saved to disk** at `results/{asin}_pipeline.json` for caching and "
        "retrieval via `GET /results/{asin}`.\n\n"
        "**Grading scale:** A (≥90) · B (≥75) · C (≥60) · D (≥40) · F (<40)\n\n"
        "**How to prepare the input:** Use the Master Prompt in `tools/MASTER_PROMPT.md` "
        "with any LLM (Claude, GPT-4, Gemini) to extract a product JSON from an Amazon "
        "product page URL, then POST it here."
    ),
    responses={
        200: {"description": "Pipeline completed successfully. All 7 skill results returned."},
        422: {"description": "Validation error — input JSON does not match schema. Check field names and types against rufus_skill_contract.md."},
        500: {"description": "Internal pipeline error. Check that all required fields are populated."},
    },
)
async def run_pipeline(request: ProductPipelineRequest) -> PipelineResponse:
    """
    Execute the full 7-skill Rufus optimization pipeline for a single ASIN.

    Submit a product JSON matching the schema defined in `rufus_skill_contract.md`.
    The API handles all cross-skill data wiring automatically.

    Returns a structured audit report with grades A–F for each of the 7 skills,
    plus the full detailed output from every skill.
    """
    try:
        result = _run_pipeline(request)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline execution error for ASIN '{request.asin}': {str(exc)}",
        ) from exc

    # Persist result to disk (non-blocking — failure here does not fail the request)
    try:
        out_path = _HERE / "results" / f"{request.asin}_pipeline.json"
        save_json_output(result, out_path)
    except Exception:
        pass  # Disk write failure is non-fatal

    return PipelineResponse(**result)


@app.get(
    "/results/{asin}",
    tags=["Pipeline"],
    summary="Retrieve a cached pipeline result",
    description=(
        "Returns the most recent pipeline JSON saved to disk for the given ASIN. "
        "Results are written after every successful `POST /pipeline` call.\n\n"
        "Use this to retrieve results without re-running the pipeline — useful for "
        "the Codex dashboard, Auto-Pilot reporting, and partner integrations.\n\n"
        "Returns 404 if no result exists for the ASIN yet."
    ),
    responses={
        200: {"description": "Cached pipeline result returned."},
        404: {"description": "No cached result found for this ASIN. Run POST /pipeline first."},
    },
)
async def get_result(asin: str) -> JSONResponse:
    """
    Retrieve the most recently cached pipeline result for a given ASIN.

    Results are stored as JSON files at `results/{asin}_pipeline.json`.
    The file is written automatically after every successful `POST /pipeline` call.
    """
    result_path = _HERE / "results" / f"{asin}_pipeline.json"
    if not result_path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"No cached result found for ASIN '{asin}'. "
                f"Run POST /pipeline with this ASIN first."
            ),
        )
    with open(result_path, encoding="utf-8") as fh:
        data = json.load(fh)
    return JSONResponse(content=data)


@app.get(
    "/results",
    tags=["Pipeline"],
    summary="List all cached pipeline results",
    description=(
        "Returns a list of all ASINs that have cached pipeline results on disk, "
        "along with their file size and last-modified timestamp.\n\n"
        "Use this to discover which products have already been processed."
    ),
)
async def list_results() -> JSONResponse:
    """List all ASINs with cached pipeline results."""
    results_dir = _HERE / "results"
    if not results_dir.exists():
        return JSONResponse(content={"cached_results": [], "count": 0})

    entries = []
    for f in sorted(results_dir.glob("*_pipeline.json")):
        asin_name = f.stem.replace("_pipeline", "")
        stat = f.stat()
        entries.append({
            "asin": asin_name,
            "file": f.name,
            "size_kb": round(stat.st_size / 1024, 1),
            "last_modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        })

    return JSONResponse(content={"cached_results": entries, "count": len(entries)})


# ===========================================================================
# ENTRYPOINT (for direct execution)
# ===========================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
