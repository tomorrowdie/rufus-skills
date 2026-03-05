"""
run_pipeline.py — Full 7-Skill Rufus Optimization Pipeline Runner
==================================================================

Loads the parsed Amazon catalog data (fields.csv + valid_values.csv) via
catalog_loader, then runs all 7 skills in sequence with proper data chaining:

    Skill01 → Skill02 → Skill03 → Skill04 → Skill05 → Skill06 → Skill07

Data flow between skills:
    Skill01.injection_payload        → Skill07.backend_attrs
    Skill02.npo.output_noun_phrases  → Skill04.noun_phrases
    Skill02.copy.rag_ready_bullets   → Skill07.bullets
    Skill03.ugc_mining...recurring_negative_keywords.keys() → Skill07.negative_review_themes

Usage:
    python run_pipeline.py
    python run_pipeline.py --market us --category cell_phones_accessories/accessories/chargers_power_adapters/portable_power_banks
    python run_pipeline.py --asin B0EXAMPLE123 --output results/pipeline_output.json

Author: John / Anergy Academy
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Path setup — allow imports from shared/
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_SHARED = _HERE / "shared"
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))

from utils.catalog_loader import load_catalog, get_field_values, get_section_fields
from utils.helpers import log_step, save_json_output

from skill_01_taxonomy.skill_01 import Skill01
from skill_02_npo.skill_02 import Skill02
from skill_03_ugc.skill_03 import Skill03
from skill_04_visual_seo.skill_04 import Skill04
from skill_05_aplus.skill_05 import Skill05
from skill_06_mobile.skill_06 import Skill06
from skill_07_integrity.skill_07 import Skill07
from skill_08_report.skill_08 import Skill08


# ---------------------------------------------------------------------------
# Default configuration
# ---------------------------------------------------------------------------
DEFAULT_MARKET = "us"
DEFAULT_CATEGORY = "cell_phones_accessories/accessories/chargers_power_adapters/portable_power_banks"
DEFAULT_ASIN = "B0EXAMPLE_POWERBANK"


# ---------------------------------------------------------------------------
# Sample data builder — creates realistic input from the catalog
# ---------------------------------------------------------------------------

def build_sample_inputs(catalog: dict[str, Any], asin: str) -> dict[str, Any]:
    """
    Build sample input data for all 7 skills using the real catalog schema.

    This uses the fields.csv and valid_values.csv to construct realistic
    test data that matches the actual Amazon flat-file template structure.

    In production, this data would come from:
    - SP-API Category Listing Report (CLR)
    - Product spec sheets / manufacturer data
    - Amazon Browse Tree Guide (BTG)
    - Customer reviews scraped from the listing
    - Product images metadata

    Returns:
        Dict with keys: clr, spec, btg, keywords, bullets, title, reviews,
        competitor_qas, product_context, images, comparison_table, modules,
        product_claims, videos, category
    """
    vv = catalog["valid_values"]
    fields_by_name = catalog["fields_by_name"]

    # ------------------------------------------------------------------
    # CLR (Category Listing Report) — backend attributes
    # Uses actual field_names from fields.csv with realistic values
    # ------------------------------------------------------------------
    clr = {
        "feed_product_type": "ConsumerElectronics",
        "item_sku": "PB-20K-BLK-001",
        "brand_name": "VoltCharge",
        "item_name": "VoltCharge PowerCore 20000mAh Portable Power Bank — USB-C PD 65W Fast Charging for iPhone, Android, MacBook, Camping Travel",
        "manufacturer": "VoltCharge International Ltd.",
        "product_description": "The VoltCharge PowerCore delivers 20000mAh of portable power with 65W USB-C PD fast charging. Charge your MacBook Pro to 50% in just 30 minutes. IPX5 water-resistant with aircraft-grade aluminum chassis. TSA-approved for carry-on. Includes USB-C to USB-C cable and travel pouch.",
        "item_type": "portable-power-bank",
        "external_product_id": "0850045678901",
        "external_product_id_type": "UPC",
        "color_name": "Midnight Black",
        "color_map": vv.get("color_map", ["Black"])[0] if "Black" not in vv.get("color_map", []) else "Black",
        "recommended_uses_for_product": vv.get("recommended_uses_for_product", ["Indoor/Outdoor"])[0],
        "power_source_type": "DC",
        "voltage": "5",
        "voltage_unit_of_measure": "Volts",
        "connector_type": "USB-C",
        "battery_capacity": "20000",
        "battery_capacity_unit_of_measure": vv.get("battery_capacity_unit_of_measure", ["milliamp_hours"])[0],
        "battery_cell_composition": "Lithium-Ion",
        "number_of_ports": "3",
        "reusability": "Rechargeable",
        "battery_charge_time": "1.5",
        "battery_charge_time_unit_of_measure": "Hours",
        # Compliance fields
        "are_batteries_included": "Yes",
        "batteries_required": "Yes",
        "lithium_battery_packaging": vv.get("lithium_battery_packaging", ["Batteries contained in equipment"])[0],
        "number_of_batteries": "1",
        "number_of_lithium_ion_cells": "4",
        "number_of_lithium_metal_cells": "0",
        "lithium_battery_energy_content": "74",
        "lithium_battery_energy_content_unit_of_measure": "Watt Hours",
        "lithium_battery_weight": "320",
        "lithium_battery_weight_unit_of_measure": "Grams",
        "battery_weight": "320",
        "battery_weight_unit_of_measure": "GR",
        "item_weight": "450",
        "item_weight_unit_of_measure": "Grams",
        "item_volume": "240",
        "item_volume_unit_of_measure": "milliliters",
        "country_of_origin": "China",
        "has_less_than_30_percent_state_of_charge": "Yes",
        # Dimensions
        "thickness_head_to_toe": "6.3",
        "thickness_head_to_toe_unit_of_measure": "Inches",
        "thickness_width_side_to_side": "3.1",
        "thickness_width_side_to_side_unit_of_measure": "Inches",
        "thickness_floor_to_top": "0.9",
        "thickness_floor_to_top_unit_of_measure": "Inches",
        # Offer
        "standard_price": "49.99",
        "currency": "USD",
        "condition_type": "New",
        "fulfillment_center_id": "AMAZON_NA",
    }

    # ------------------------------------------------------------------
    # Spec sheet — technical data (often from manufacturer)
    # ------------------------------------------------------------------
    spec = {
        "capacity_mah": 20000,
        "output_ports": 3,
        "usb_c_output": "65W PD 3.0",
        "usb_a_output_1": "18W QC 3.0",
        "usb_a_output_2": "12W",
        "input": "65W USB-C PD",
        "total_output": "65W max",
        "weight_grams": 450,
        "dimensions_inches": "6.3 x 3.1 x 0.9",
        "waterproof_rating": "IPX5",
        "charging_standard": "PD 65W + QC 3.0",
        "battery_type": "Li-ion 21700 cells",
        "cell_count": 4,
        "energy_wh": 74,
        "charge_cycles": 500,
        "operating_temp_c": "-10 to 45",
        "certifications": "FCC, CE, RoHS, UN38.3, MSDS",
        "material": "Aircraft-grade Aluminum Alloy + ABS",
        "led_display": "Yes, percentage readout",
        "pass_through_charging": "Yes",
        "tsa_approved": True,
    }

    # ------------------------------------------------------------------
    # BTG (Browse Tree Guide)
    # ------------------------------------------------------------------
    btg = {
        "category": "Cell Phones & Accessories",
        "node_id": "2407749011",
        "node_path": "Cell Phones & Accessories > Accessories > Chargers & Power Adapters > Portable Power Banks",
    }

    # ------------------------------------------------------------------
    # Keywords — from keyword research tools
    # ------------------------------------------------------------------
    keywords = [
        "portable power bank 20000mah",
        "fast charging power bank usb c",
        "portable charger for camping",
        "65w pd power bank for macbook",
        "power bank for iphone android",
        "travel power bank tsa approved",
        "high capacity portable charger",
    ]

    # ------------------------------------------------------------------
    # Bullets — current listing copy
    # ------------------------------------------------------------------
    bullets = [
        "20000mAh high-capacity portable power bank charges iPhone 15 Pro Max 4.5 times, Samsung Galaxy S24 3.8 times, or MacBook Air once on a single charge",
        "65W USB-C PD 3.0 fast charging output — charge your MacBook Pro to 50% in just 30 minutes, with simultaneous 3-device charging via USB-C + dual USB-A ports",
        "IPX5 water-resistant with aircraft-grade aluminum chassis and drop-tested to MIL-STD-810G — built for camping, hiking, and travel adventures",
        "TSA-approved 74Wh battery meets FAA carry-on regulations — LED percentage display shows exact remaining power at a glance",
        "What's in the box: VoltCharge PowerCore 20000, USB-C to USB-C cable, travel pouch, quick start guide, and 18-month manufacturer warranty",
    ]

    # ------------------------------------------------------------------
    # Title — current listing title
    # ------------------------------------------------------------------
    title = clr["item_name"]

    # ------------------------------------------------------------------
    # Reviews — sample customer reviews
    # ------------------------------------------------------------------
    reviews = [
        {"text": "Charges my MacBook Pro amazingly fast — 50% in 30 minutes with the PD output. Love the aluminum build.", "rating": 5},
        {"text": "Does it work on airplanes? I need it for international travel and layovers.", "rating": 4},
        {"text": "Is this waterproof? I want to use it camping near lakes and rivers.", "rating": 4},
        {"text": "How fast does it charge my iPhone 15? Looking for something quick.", "rating": 3},
        {"text": "Stopped working after 3 weeks. The USB-C port feels loose and cheap. Disappointing.", "rating": 1},
        {"text": "Can I charge my MacBook and iPhone at the same time? Works perfectly for that!", "rating": 5},
        {"text": "The LED display is nice but the power bank is heavier than expected. 450g is a lot.", "rating": 3},
        {"text": "Best portable charger I've owned. TSA friendly, fast charging, great build quality.", "rating": 5},
        {"text": "Misleading capacity — doesn't actually deliver 20000mAh to the device due to conversion loss.", "rating": 2},
        {"text": "Survived a 4-foot drop onto concrete. The aluminum really protects it.", "rating": 5},
    ]

    # ------------------------------------------------------------------
    # Competitor Q&As
    # ------------------------------------------------------------------
    competitor_qas = [
        {
            "question": "Can I charge two devices at the same time?",
            "answer": "Yes, it supports simultaneous dual charging via USB-C and USB-A.",
        },
        {
            "question": "Is this safe for airplane carry-on?",
            "answer": "Yes, at 74Wh it's under the FAA 100Wh limit for carry-on lithium batteries.",
        },
    ]

    # ------------------------------------------------------------------
    # Product context — for Q&A template filling
    # ------------------------------------------------------------------
    product_context = {
        "waterproof_rating": "IPX5",
        "warranty_months": 18,
        "charge_hours": 1.5,
    }

    # ------------------------------------------------------------------
    # Images — current listing images metadata
    # ------------------------------------------------------------------
    images = [
        {
            "filename": "main_product.jpg",
            "image_type": "main",
            "alt_text": "product image 1",
            "ocr_text": "",
        },
        {
            "filename": "specs_infographic.jpg",
            "image_type": "infographic",
            "alt_text": "Power bank specs showing PD 65W output and 20000mAh capacity",
            "ocr_text": "PD 65W Output | 20000mAh | IPX5 Water-Resistant | 3 Ports | USB-C + Dual USB-A",
        },
        {
            "filename": "camping_lifestyle.jpg",
            "image_type": "lifestyle",
            "alt_text": "Portable power bank used for camping in a forest setting at night",
            "ocr_text": "",
        },
        {
            "filename": "size_comparison.jpg",
            "image_type": "infographic",
            "alt_text": "Size comparison of VoltCharge power bank next to iPhone and MacBook",
            "ocr_text": "6.3 x 3.1 x 0.9 inches | 450g | Fits in your pocket",
        },
        {
            "filename": "video_thumb_camping.jpg",
            "image_type": "video_thumb",
            "alt_text": "camping power bank video thumbnail",
            "ocr_text": "",
        },
    ]

    # ------------------------------------------------------------------
    # A+ Comparison table
    # ------------------------------------------------------------------
    comparison_table = {
        "Battery Capacity": {asin: "20000mAh", "B0COMP001": "10000mAh", "B0COMP002": "26800mAh"},
        "USB-C Output": {asin: "65W PD 3.0", "B0COMP001": "18W", "B0COMP002": "30W PD"},
        "Waterproof Rating": {asin: "IPX5", "B0COMP001": "None", "B0COMP002": "IPX4"},
        "Weight": {asin: "450g", "B0COMP001": "280g", "B0COMP002": "600g"},
        "Charging Speed": {asin: "30 min to 50% (MacBook)", "B0COMP001": "2 hours", "B0COMP002": "1.5 hours"},
        "Number of Ports": {asin: "3 (USB-C + 2×USB-A)", "B0COMP001": "2", "B0COMP002": "4"},
    }

    # ------------------------------------------------------------------
    # A+ Modules
    # ------------------------------------------------------------------
    modules = [
        {"type": "comparison_table", "content": "See comparison table above"},
        {"type": "faq", "content": "Q: Is it waterproof? A: Yes, IPX5 rated. Q: Airplane safe? A: Yes, 74Wh is under 100Wh FAA limit. Q: How fast? A: 65W PD charges MacBook to 50% in 30 min."},
        {"type": "technical_specs", "content": "Capacity: 20000mAh / 74Wh | Output: 65W USB-C PD + 18W QC + 12W USB-A | Input: 65W USB-C | Weight: 450g | Dimensions: 6.3 x 3.1 x 0.9 in | Material: Aluminum Alloy | Cells: 4× 21700 Li-ion"},
        {"type": "lifestyle_image", "content": ""},
    ]

    # ------------------------------------------------------------------
    # Product claims for hallucination check
    # ------------------------------------------------------------------
    product_claims = [
        "20000mAh capacity",
        "65W PD 3.0 fast charging",
        "IPX5 water-resistant",
        "Aircraft-grade aluminum",
        "TSA-approved 74Wh",
        "MIL-STD-810G drop tested",
        "18-month warranty",
        "Charges MacBook to 50% in 30 minutes",
    ]

    # ------------------------------------------------------------------
    # Videos
    # ------------------------------------------------------------------
    videos = [
        {
            "title": "Stop struggling with dead batteries while camping — VoltCharge PowerCore 20000",
            "description": "Tired of your phone dying mid-hike? Solve your power problem with 20000mAh of portable power. 65W PD charges your MacBook in minutes. Finally enjoy all-day power anywhere you go.",
            "aspect_ratio": "9:16",
        },
        {
            "title": "VoltCharge PowerCore — product overview and features",
            "description": "Check out the features of our 20000mAh portable power bank with 65W USB-C PD fast charging.",
            "aspect_ratio": "16:9",
        },
    ]

    return {
        "clr": clr,
        "spec": spec,
        "btg": btg,
        "keywords": keywords,
        "bullets": bullets,
        "title": title,
        "reviews": reviews,
        "competitor_qas": competitor_qas,
        "product_context": product_context,
        "images": images,
        "comparison_table": comparison_table,
        "modules": modules,
        "product_claims": product_claims,
        "videos": videos,
        "category": "Cell Phones & Accessories",
    }


# ---------------------------------------------------------------------------
# Pipeline Runner
# ---------------------------------------------------------------------------

def run_pipeline(
    market: str = DEFAULT_MARKET,
    category_path: str = DEFAULT_CATEGORY,
    asin: str = DEFAULT_ASIN,
    project_root: Path | str | None = None,
    output_path: str | None = None,
    report_path: str | None = None,
) -> dict[str, Any]:
    """
    Execute the full 7-skill Rufus optimization pipeline.

    Steps:
        1. Load catalog (fields.csv + valid_values.csv)
        2. Build input data from catalog schema
        3. Run Skills 01–07 with proper data chaining
        4. Aggregate and return all results

    Args:
        market:        Market code (default: "us").
        category_path: Category path under catalog/ (default: portable power banks).
        asin:          Product ASIN (default: sample).
        project_root:  Override project root path.
        output_path:   If provided, write JSON output to this path.

    Returns:
        Aggregated results dict with all 7 skill outputs + pipeline metadata.
    """
    start_ts = datetime.now(timezone.utc)
    log_step("PIPELINE_START", f"market={market} asin={asin}")

    # ── Step 1: Load catalog ──────────────────────────────────────────
    log_step("CATALOG_LOAD", f"market={market} path={category_path}")
    catalog = load_catalog(
        market=market,
        category_path=category_path,
        project_root=project_root or _HERE,
    )
    log_step("CATALOG_LOADED", (
        f"fields={catalog['meta']['total_fields']} "
        f"required={catalog['meta']['total_required_fields']} "
        f"valid_value_fields={catalog['meta']['total_valid_value_fields']}"
    ))

    # ── Step 2: Build inputs ──────────────────────────────────────────
    log_step("BUILD_INPUTS")
    inputs = build_sample_inputs(catalog, asin)

    # ── Step 3: Run Skill 01 — Taxonomy & Attribute Injection ─────────
    log_step("SKILL01_RUN", "Structured Taxonomy & Attribute Injection")
    s1 = Skill01(
        clr=inputs["clr"],
        spec=inputs["spec"],
        btg=inputs["btg"],
        asin=asin,
    ).run()
    r1 = s1.to_json()
    log_step("SKILL01_DONE", f"grade={r1['scores']['grade']} completeness={r1['scores']['completeness_pct']}%")

    # ── Step 4: Run Skill 02 — NPO & RAG-Ready Copy ──────────────────
    log_step("SKILL02_RUN", "Noun Phrase Optimization & RAG-Ready Copy")
    s2 = Skill02(
        keywords=inputs["keywords"],
        bullets=inputs["bullets"],
        topic_clusters={
            "charging_speed": ["How fast does it charge?", "What is the wattage output?"],
            "portability": ["Is it allowed on airplanes?", "How heavy is it?"],
            "compatibility": ["Does it work with MacBook?", "Is it iPhone compatible?"],
            "durability": ["Is it waterproof?", "How durable is the build?"],
            "capacity": ["How many times can it charge my phone?", "What's the actual battery capacity?"],
        },
        title=inputs["title"],
        asin=asin,
    ).run()
    r2 = s2.to_json()
    log_step("SKILL02_DONE", f"grade={r2['scores']['grade']} phrases={r2['npo']['phrase_count']}")

    # ── Step 5: Run Skill 03 — UGC Mining & Q&A Seeding ──────────────
    log_step("SKILL03_RUN", "UGC Ground Truth Mining & Q&A Seeding")
    s3 = Skill03(
        reviews=inputs["reviews"],
        competitor_qas=inputs["competitor_qas"],
        product_context=inputs["product_context"],
        asin=asin,
    ).run()
    r3 = s3.to_json()
    log_step("SKILL03_DONE", f"grade={r3['scores']['grade']} qa_pairs={r3['qa_seeding']['pair_count']}")

    # ── Step 6: Run Skill 04 — Visual SEO Validation ─────────────────
    # ← Receives noun_phrases FROM Skill02
    log_step("SKILL04_RUN", "Multimodal Visual SEO Validation")
    noun_phrases_from_s2 = r2["npo"]["output_noun_phrases"]
    s4 = Skill04(
        images=inputs["images"],
        noun_phrases=noun_phrases_from_s2,
        product_name=inputs["clr"]["item_name"],
        asin=asin,
    ).run()
    r4 = s4.to_json()
    log_step("SKILL04_DONE", f"grade={r4['scores']['grade']} images_needing_update={r4['scores']['images_needing_update']}")

    # ── Step 7: Run Skill 05 — A+ Knowledge Base Engineering ─────────
    log_step("SKILL05_RUN", "A+ Knowledge Base Engineering")
    s5 = Skill05(
        comparison_table=inputs["comparison_table"],
        modules=inputs["modules"],
        product_claims=inputs["product_claims"],
        asin=asin,
    ).run()
    r5 = s5.to_json()
    log_step("SKILL05_DONE", f"grade={r5['scores']['grade']} risk={r5['hallucination_risk']['risk_level']}")

    # ── Step 8: Run Skill 06 — Mobile Habitat Optimization ───────────
    log_step("SKILL06_RUN", "Mobile Habitat Optimization (Full Audit)")
    s6 = Skill06(
        title=inputs["title"],
        videos=inputs["videos"],
        category=inputs["category"],
        asin=asin,
        bullets=inputs["bullets"],
        images=inputs["images"],
        modules=inputs["modules"],
    ).run()
    r6 = s6.to_json()
    log_step("SKILL06_DONE", f"grade={r6['scores']['grade']} composite={r6['scores']['composite_mobile_score']}")

    # ── Step 9: Run Skill 07 — Integrity & Anti-Optimization ─────────
    # ← Receives backend_attrs FROM Skill01, bullets FROM Skill02,
    #    negative_themes FROM Skill03
    log_step("SKILL07_RUN", "Semantic Integrity & Anti-Optimization Check")
    negative_themes_from_s3 = list(
        r3["ugc_mining"]["sentiment"]["recurring_negative_keywords"].keys()
    )
    rag_bullets_from_s2 = r2["copy"]["rag_ready_bullets"]
    backend_from_s1 = r1["injection_payload"]

    s7 = Skill07(
        title=inputs["title"],
        bullets=rag_bullets_from_s2,
        backend_attrs=backend_from_s1,
        negative_review_themes=negative_themes_from_s3,
        asin=asin,
    ).run()
    r7 = s7.to_json()
    log_step("SKILL07_DONE", f"grade={r7['scores']['grade']} issues={r7['scores']['issues_found']}")

    # ── Step 10: Aggregate results ────────────────────────────────────
    end_ts = datetime.now(timezone.utc)
    elapsed = (end_ts - start_ts).total_seconds()

    pipeline_result = {
        "pipeline_meta": {
            "asin": asin,
            "market": market,
            "category_path": category_path,
            "catalog_fields": catalog["meta"]["total_fields"],
            "catalog_required_fields": catalog["meta"]["total_required_fields"],
            "catalog_valid_value_fields": catalog["meta"]["total_valid_value_fields"],
            "started_at": start_ts.isoformat(),
            "finished_at": end_ts.isoformat(),
            "elapsed_seconds": round(elapsed, 2),
        },
        "grades_summary": {
            "skill_01_taxonomy": r1["scores"]["grade"],
            "skill_02_npo": r2["scores"]["grade"],
            "skill_03_ugc": r3["scores"]["grade"],
            "skill_04_visual_seo": r4["scores"]["grade"],
            "skill_05_aplus": r5["scores"]["grade"],
            "skill_06_mobile": r6["scores"]["grade"],
            "skill_07_integrity": r7["scores"]["grade"],
        },
        "skill_01": r1,
        "skill_02": r2,
        "skill_03": r3,
        "skill_04": r4,
        "skill_05": r5,
        "skill_06": r6,
        "skill_07": r7,
    }

    # ── Step 11: Run Skill 08 — Visual Report Generator ─────────────
    if report_path:
        log_step("SKILL08_RUN", "Visual Report Generator")
        pipeline_result.setdefault("asin", asin)
        pipeline_result.setdefault("product", r1.get("injection_payload", {}).get("item_name", f"Product {asin}"))
        s8 = Skill08(
            pipeline_result,
            market=market.upper(),
            market_id={"us": "ATVPDKIKX0DER", "uk": "A1F83G8C2ARO7P", "jp": "A1VC38T7YXB528", "mx": "A1AM78C64UM0Y8", "cn": "AAHKV2X7AFYLW"}.get(market, market),
            category=category_path.split("/")[-1].replace("_", " ").title(),
            total_fields=catalog["meta"]["total_fields"],
            runtime=f"{elapsed:.2f}s",
        )
        s8.run()
        report_out = s8.save_html(report_path)
        pipeline_result["skill_08"] = s8.to_json()
        pipeline_result["skill_08"]["report_path"] = str(report_out)
        log_step("SKILL08_DONE", f"saved to {report_out}")

    # ── Print summary ─────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  RUFUS OPTIMIZATION PIPELINE — COMPLETE")
    print("=" * 70)
    print(f"  ASIN:     {asin}")
    print(f"  Market:   {market}")
    print(f"  Elapsed:  {elapsed:.2f}s")
    print()
    print("  GRADES:")
    for skill_key, grade in pipeline_result["grades_summary"].items():
        label = skill_key.replace("skill_", "Skill ").replace("_", " — ", 1).replace("_", " ")
        print(f"    {label:40s} {grade}")
    if report_path:
        print(f"\n  HTML REPORT: {report_path}")
    print("=" * 70)

    # ── Save if output path provided ──────────────────────────────────
    if output_path:
        out = save_json_output(pipeline_result, output_path)
        log_step("OUTPUT_SAVED", str(out))

    log_step("PIPELINE_DONE", f"elapsed={elapsed:.2f}s")
    return pipeline_result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Run the full 7-skill Rufus optimization pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_pipeline.py
  python run_pipeline.py --asin B0MYASIN123
  python run_pipeline.py --market us --output results/output.json
  python run_pipeline.py --category cell_phones_accessories/accessories/chargers_power_adapters/portable_power_banks
        """,
    )
    parser.add_argument("--market", default=DEFAULT_MARKET, help="Market code (default: us)")
    parser.add_argument("--category", default=DEFAULT_CATEGORY, help="Category path under catalog/")
    parser.add_argument("--asin", default=DEFAULT_ASIN, help="Product ASIN")
    parser.add_argument("--output", "-o", help="Output JSON file path")
    parser.add_argument("--report", "-r", help="Output HTML report file path (runs Skill 08)")

    args = parser.parse_args()

    result = run_pipeline(
        market=args.market,
        category_path=args.category,
        asin=args.asin,
        output_path=args.output,
        report_path=args.report,
    )

    if not args.output:
        # Print full JSON to stdout if no output file specified
        print("\n" + json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
