# Rufus Skills — Amazon Listing Optimization Pipeline

An AI-driven pipeline that audits and optimizes Amazon product listings for the
**Rufus AI shopping assistant** (Amazon's RAG-based conversational commerce engine).

---

## What It Does

Runs 9 specialized skills against a product's data and outputs a structured JSON
pipeline result + a visual HTML report. Each skill targets a specific signal that
Rufus uses to answer customer questions and rank products in AI-generated responses.

---

## The 9 Skills

| # | Skill | Key Output |
|---|-------|-----------|
| 01 | **Structured Taxonomy & Attribute Injection** | Backend completeness score, Knowledge Graph mapping, injection payload |
| 02 | **Noun Phrase Optimization (NPO) & RAG-Ready Copy** | NPO phrases, rewritten bullets, semantic density score |
| 03 | **UGC Ground Truth Mining & Q&A Seeding** | Mined questions, sentiment analysis, seeded Q&A pairs |
| 04 | **Multimodal Visual SEO Validation** | Alt-text scores, OCR coverage, optimized alt-text |
| 05 | **A+ Knowledge Base Engineering** | Comparison table audit, hallucination risk score |
| 06 | **Mobile Habitat Optimization** | 8-module mobile audit (title, bullets, image order, swipe depth, A+ fold, touch targets, voice readiness, video arc) |
| 07 | **Semantic Integrity & Anti-Optimization Check** | Keyword stuffing detection, backend conflict resolution, sanitized listing |
| 08 | **Visual HTML Report Generator** | Full pipeline JSON → styled HTML report |
| 09 | **OCR-Optimized Infographic Generator** | 4 infographic types (specs, features, comparison, lifestyle overlay) |

---

## Directory Structure

```
rufus-skills/
├── CLAUDE.md                  ← Repo rules (read first — enforced by Claude Code)
├── MEMORY.md                  ← Agent handoff document (read before any session)
├── PLAN.md                    ← Architecture decisions and reasoning
├── SKILLS_INDEX.md            ← Full skill index, import patterns, pipeline chaining
├── rufus_skill_contract.md    ← Strict JSON input/output contract for all skills
├── requirements.txt
├── .gitignore
│
├── shared/                    ← All 9 skills (marketplace-agnostic)
│   ├── skill_01_taxonomy/
│   ├── skill_02_npo/
│   ├── skill_03_ugc/
│   ├── skill_04_visual_seo/
│   ├── skill_05_aplus/
│   ├── skill_06_mobile/       ← v2.0, 8-module mobile audit
│   ├── skill_07_integrity/
│   ├── skill_08_report/       ← pending migration
│   ├── skill_09_infographic/  ← pending migration
│   └── utils/                 ← Shared helpers (sanitize_text, score_to_grade, etc.)
│
├── markets/                   ← Marketplace-specific catalog data
│   ├── us/catalog/.../portable_power_banks/
│   │   ├── raw/               ← Drop .xlsm flat file templates here
│   │   └── data/              ← Auto-generated fields.csv + valid_values.csv (never edit)
│   ├── uk/
│   ├── jp/
│   ├── ca/
│   └── au/
│
├── tools/
│   └── parse_catalog.py       ← XLSM → CSV parser (run when new .xlsm is dropped in raw/)
│
└── results/                   ← Pipeline JSON + HTML report outputs (gitignored)
```

---

## Quick Start

### 1. Import a skill directly

```python
import sys
sys.path.insert(0, "/path/to/rufus-skills/shared")

from skill_01_taxonomy.skill_01 import Skill01
from skill_02_npo.skill_02      import Skill02
# ... etc.

result = Skill01(clr={...}, spec={...}, btg={...}, asin="B0XYZ").to_json()
print(result["scores"]["grade"])
```

### 2. Run the full pipeline on one product

```bash
python run_product.py --input products/B0FKN7X7HM.json --report
# Outputs: results/B0FKN7X7HM_pipeline.json
#          results/B0FKN7X7HM_report.html
```

### 3. Run a batch of products

```bash
python run_batch.py --folder products/ --report
```

### 4. Parse a new catalog flat file

```bash
python tools/parse_catalog.py --input markets/us/catalog/.../raw/POWER_BANK.xlsm
# Outputs: data/fields.csv + data/valid_values.csv
```

---

## Agent Onboarding

If you are an AI agent (Claude, Gemini, GPT) joining this project:

1. Read `MEMORY.md` first — it has the full task list and current state
2. Read `CLAUDE.md` — repo rules you must follow
3. Read `SKILLS_INDEX.md` — skill directory and import patterns
4. Do not write code until you have read all three

---

## Grading Scale

All 9 skills return a `scores.grade` using the same scale:

| Score | Grade | Meaning |
|-------|-------|---------|
| ≥ 90 | A | Rufus-ready |
| ≥ 75 | B | Minor improvements needed |
| ≥ 60 | C | Notable gaps |
| ≥ 40 | D | Significant issues |
| < 40 | F | Major rework required |

---

## Supported Markets (v1)

`us` · `uk` · `jp` · `ca` · `au`
