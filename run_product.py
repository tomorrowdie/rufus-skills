import argparse
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_SHARED = _HERE / "shared"
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))

from utils.helpers import log_step, save_json_output, load_json_input

from skill_01_taxonomy.skill_01 import Skill01
from skill_02_npo.skill_02 import Skill02
from skill_03_ugc.skill_03 import Skill03
from skill_04_visual_seo.skill_04 import Skill04
from skill_05_aplus.skill_05 import Skill05
from skill_06_mobile.skill_06 import Skill06
from skill_07_integrity.skill_07 import Skill07

def main():
    parser = argparse.ArgumentParser(description="Run the Rufus 7-skill pipeline on a single product JSON.")
    parser.add_argument("--input", required=True, help="Path to input product JSON file")
    parser.add_argument("--report", action="store_true", help="Generate HTML report via Skill 08")
    parser.add_argument("--infographics", action="store_true", help="Generate InfoGraphics via Skill 09")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file {input_path} not found.")
        sys.exit(1)

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    asin = data.get("asin", "UNKNOWN")
    title = data.get("title", "")
    bullets = data.get("bullets", [])
    clr = data.get("clr", {})
    spec = data.get("spec", {})
    btg = data.get("btg", {})
    keywords = data.get("keywords", [])
    topic_clusters = data.get("topic_clusters", {})
    reviews = data.get("reviews", [])
    competitor_qas = data.get("competitor_qas", [])
    product_context = data.get("product_context", {})
    images = data.get("images", [])
    comparison_table = data.get("comparison_table", {})
    modules = data.get("modules", [])
    product_claims = data.get("product_claims", [])
    videos = data.get("videos", [])
    category_path = data.get("category_path", "")
    market = data.get("market", "us")

    print(f"======================================================================")
    print(f"  RUNNING PIPELINE FOR ASIN: {asin}")
    print(f"======================================================================")

    # Skill 01
    log_step("SKILL01", "Taxonomy & Attribute Injection")
    s1 = Skill01(clr=clr, spec=spec, btg=btg, asin=asin).run()
    r1 = s1.to_json()

    # Skill 02
    log_step("SKILL02", "NPO & RAG-Ready Copy")
    s2 = Skill02(
        keywords=keywords,
        bullets=bullets,
        title=title,
        topic_clusters=topic_clusters,
        asin=asin
    ).run()
    r2 = s2.to_json()

    # Skill 03
    log_step("SKILL03", "UGC Mining & Q&A Seeding")
    s3 = Skill03(
        reviews=reviews,
        competitor_qas=competitor_qas,
        product_context=product_context,
        asin=asin
    ).run()
    r3 = s3.to_json()

    # Skill 04
    log_step("SKILL04", "Visual SEO Validation")
    s4 = Skill04(
        images=images,
        noun_phrases=r2.get("npo", {}).get("output_noun_phrases", []),
        product_name=title.split(',')[0] if title else "Product",
        asin=asin
    ).run()
    r4 = s4.to_json()

    # Skill 05
    log_step("SKILL05", "A+ Knowledge Base Engineering")
    s5 = Skill05(
        comparison_table=comparison_table,
        modules=modules,
        product_claims=product_claims,
        asin=asin
    ).run()
    r5 = s5.to_json()

    # Skill 06
    log_step("SKILL06", "Mobile Habitat Optimization")
    category = btg.get("category", "") if btg and "category" in btg else category_path.split("/")[-1].replace("_", " ")

    s6 = Skill06(
        title=title,
        bullets=bullets,
        images=images,
        modules=modules,
        videos=videos,
        category=category,
        asin=asin
    ).run()
    r6 = s6.to_json()

    # Skill 07
    log_step("SKILL07", "Integrity & Anti-Optimization")
    s7 = Skill07(
        title=title,
        bullets=r2.get("copy", {}).get("rag_ready_bullets", []),
        backend_attrs=r1.get("injection_payload", {}),
        negative_review_themes=list(
            r3.get("ugc_mining", {}).get("sentiment", {}).get("recurring_negative_keywords", {}).keys()
        ),
        asin=asin
    ).run()
    r7 = s7.to_json()

    # Compile result
    result = {
        "asin": asin,
        "product": title,
        "market": market,
        "category_path": category_path,
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

    out_json = _HERE / "results" / f"{asin}_pipeline.json"
    save_json_output(result, out_json)
    print(f"Pipeline JSON saved to: {out_json}")

    # Optionally run Skill 08
    if args.report:
        try:
            import subprocess
            out_html = _HERE / "results" / f"{asin}_report.html"
            cmd = [
                sys.executable,
                str(_SHARED / "skill_08_report" / "skill_08.py"),
                "--input", str(out_json),
                "--output", str(out_html)
            ]
            print(f"Running Skill 08 to generate HTML report...")
            subprocess.run(cmd, check=True)
            print(f"HTML Report generated at: {out_html}")
        except Exception as e:
            print(f"Failed to generate report: {e}")

    # Optionally run Skill 09
    if args.infographics:
        try:
            # Check import (Skill 09 pending migration)
            import subprocess
            cmd = [
                sys.executable,
                str(_SHARED / "skill_09_infographic" / "skill_09.py"),
                "--input", str(out_json)
            ]
            print(f"Running Skill 09 to generate infographics...")
            subprocess.run(cmd, check=True)
        except ImportError:
            print("Skill 09 (Infographic Generator) not found or pending migration.")
        except Exception as e:
            print(f"Failed to generate infographics: {e}")

if __name__ == "__main__":
    main()
