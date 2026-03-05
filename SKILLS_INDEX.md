# SKILLS_INDEX.md — Rufus Optimization Skills Library

## Overview

The **Rufus Optimization Skills Library** contains 9 standalone Python skills for
optimizing Amazon product listings for the Rufus AI shopping assistant.

Each skill implements a class with:
- `__init__(**params)` — typed input parameters
- `run()` → self — executes the skill pipeline
- `to_json()` → dict — returns JSON-serializable structured output

---

## Skill Directory

| ID | Skill Name | Key Input | Key Output | Status |
|----|-----------|-----------|------------|--------|
| 01 | Structured Taxonomy & Attribute Injection | CLR + Spec Sheet + BTG | Injection payload, completeness grade | ✅ Ready |
| 02 | Noun Phrase Optimization (NPO) & RAG-Ready Copy | Keywords + Bullets | NPO phrases, RAG bullets, density score | ✅ Ready |
| 03 | UGC Ground Truth Mining & Q&A Seeding | Reviews + Competitor Q&As | Mined questions, seeded Q&A pairs | ✅ Ready |
| 04 | Multimodal Visual SEO Validation | Images (alt-text + OCR) | Alt-text scores, optimized alt-text, OCR audit | ✅ Ready |
| 05 | A+ Knowledge Base Engineering | Comparison table + Modules | Hallucination risk score, A+ recommendations | ✅ Ready |
| 06 | Mobile Habitat Optimization **v2.0** | Title + Bullets + Images + Modules + Videos | 8-module mobile audit — 2× weight in Amazon algo | ✅ Ready |
| 07 | Semantic Integrity & Anti-Optimization Check | Title + Bullets + Backend | Compliance report, sanitized listing, integrity score | ✅ Ready |
| 08 | Visual HTML Report Generator | Full pipeline JSON | Styled HTML report with educational sections | ⚠️ Pending migration |
| 09 | OCR-Optimized Infographic Generator | Pipeline JSON + ASIN | 4 infographic types (specs, features, comparison, lifestyle) | ⚠️ Pending migration |

> **Skill 06 v2.0** covers 8 mobile modules: title truncation, bullet truncation,
> image order, swipe depth, A+ fold, touch targets, voice readiness, video arc.

---

## Import Note

The repo root `rufus-skills/shared/` must be on `sys.path`. Skill package names
(`skill_01_taxonomy`, etc.) are valid Python identifiers and import normally.

```python
# These FAIL
from rufus_skills import Skill01      # ❌ no package named rufus_skills
from shared import Skill01            # ❌ shared is not a package root

# This WORKS
import sys
sys.path.insert(0, "/path/to/rufus-skills/shared")
from skill_01_taxonomy.skill_01 import Skill01   # ✅
```

---

## How to Use from External Projects

### Method 1: sys.path + Direct Module Import (Recommended)
```python
import sys
sys.path.insert(0, "/absolute/path/to/rufus-skills/shared")

from skill_01_taxonomy.skill_01   import Skill01   # ✅
from skill_02_npo.skill_02        import Skill02   # ✅
from skill_03_ugc.skill_03        import Skill03   # ✅
from skill_04_visual_seo.skill_04 import Skill04   # ✅
from skill_05_aplus.skill_05      import Skill05   # ✅
from skill_06_mobile.skill_06     import Skill06   # ✅
from skill_07_integrity.skill_07  import Skill07   # ✅
# Skills 08 and 09 — pending migration, import pattern same as above
```

### Method 2: CLI (subprocess / n8n Execute Command Node)
```bash
python /path/to/rufus-skills/shared/skill_01_taxonomy/skill_01.py \
  --input data.json --output result.json --asin B0XYZ123
```

### Method 3: JSON Stdin (n8n / pipe)
```bash
echo '{"clr": {}, "spec": {}, "btg": {}}' | python skill_01.py
```

### Method 4: Production Runner (one product)
```bash
python run_product.py --input products/B0FKN7X7HM.json --report
```

### Method 5: Batch Runner
```bash
python run_batch.py --folder products/ --report
```

---

## Skill 06 v2.0 — 8 Module Reference

| Module | What It Checks | Signal |
|--------|---------------|--------|
| Title truncation | First 70 chars = Rufus chat window zone | Must lead with Category + Core Benefit |
| Bullet truncation | Mobile bullet display cutoff | Key info must appear before truncation |
| Image order | First image in mobile carousel | Most informative image must be first |
| Swipe depth | Images before user decides | Fewer high-quality images > many poor ones |
| A+ fold | A+ visible above mobile fold | Above-fold A+ directly influences Rufus indexing |
| Touch targets | CTA button size for thumbs | ≥ 44×44px touch target minimum |
| Voice readiness | Title answers a voice query | Natural language, starts with category noun |
| Video arc | 9:16 format + Problem→Solution narrative | +50 pts vertical, +40 pts P→S arc |

> Amazon gives **2× algorithmic weight** to mobile signals. Skill 06 is the highest-impact skill in the pipeline.

---

## Pipeline Data Flow

```
Skill01.injection_payload                         → Skill07.backend_attrs
Skill02.npo.output_noun_phrases                   → Skill04.noun_phrases
Skill02.copy.rag_ready_bullets                    → Skill07.bullets
Skill03.ugc_mining.sentiment
  .recurring_negative_keywords.keys()             → Skill07.negative_review_themes
Skills 01–07 combined JSON                        → Skill08 (HTML report)
Skills 01–07 combined JSON                        → Skill09 (infographics, optional)
```

---

## Full Pipeline Chaining Example (Skills 01–07)

```python
import sys
sys.path.insert(0, "/path/to/rufus-skills/shared")

from skill_01_taxonomy.skill_01   import Skill01
from skill_02_npo.skill_02        import Skill02
from skill_03_ugc.skill_03        import Skill03
from skill_04_visual_seo.skill_04 import Skill04
from skill_05_aplus.skill_05      import Skill05
from skill_06_mobile.skill_06     import Skill06
from skill_07_integrity.skill_07  import Skill07

asin = "B0EXAMPLE"

s1 = Skill01(clr=my_clr, spec=my_spec, btg=my_btg, asin=asin).run()
backend_payload  = s1.to_json()["injection_payload"]

s2 = Skill02(keywords=my_keywords, bullets=my_bullets, title=my_title, asin=asin).run()
noun_phrases     = s2.to_json()["npo"]["output_noun_phrases"]
rag_bullets      = s2.to_json()["copy"]["rag_ready_bullets"]

s3 = Skill03(reviews=my_reviews, product_context=my_context, asin=asin).run()
negative_themes  = list(
    s3.to_json()["ugc_mining"]["sentiment"]["recurring_negative_keywords"].keys()
)

s4 = Skill04(images=my_images, noun_phrases=noun_phrases, asin=asin).run()

s5 = Skill05(comparison_table=my_table, modules=my_modules, asin=asin).run()

s6 = Skill06(
    title=my_title,
    bullets=my_bullets,
    images=my_images,
    modules=my_modules,
    videos=my_videos,
    category="Cell Phones & Accessories",
    asin=asin,
).run()

s7 = Skill07(
    title=my_title,
    bullets=rag_bullets,
    backend_attrs=backend_payload,
    negative_review_themes=negative_themes,
    asin=asin,
).run()

pipeline_result = {
    "skill_01": s1.to_json(),
    "skill_02": s2.to_json(),
    "skill_03": s3.to_json(),
    "skill_04": s4.to_json(),
    "skill_05": s5.to_json(),
    "skill_06": s6.to_json(),
    "skill_07": s7.to_json(),
}
# → pass pipeline_result to Skill08 for HTML report
# → pass pipeline_result to Skill09 for infographics (optional)
```
