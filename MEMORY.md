# MEMORY.md — Agent Handoff Document
**Project:** Rufus Optimization Skills Library
**Owner:** John (johnchin@pandaocean.com)
**Last updated:** 2026-03-05
**Status:** Active development — context window closed, handing off to next agent(s)

---

## FIRST: Read These Files Before Anything Else

Before touching any code, every incoming agent MUST read these files in order:

1. `CLAUDE.md` — repo structure rules, catalog path conventions, parse_catalog SOP
2. `README.md` — project overview and how the skills connect
3. `SKILLS_INDEX.md` — full index of all 9 skills and their contracts
4. `rufus_skill_contract.md` — the strict JSON contract every skill must follow
5. `PLAN.md` — original architecture decisions and reasoning

These 5 files are the **source of truth**. Do not duplicate content from them into new files.

---

## What This Project Does

An AI-driven Amazon listing optimization pipeline for the **Rufus AI shopping assistant**. It runs 9 skills against a product's data and outputs a structured JSON + HTML report.

**Skills (all in `shared/`):**
| Skill | Folder | Purpose |
|-------|--------|---------|
| 01 | skill_01_taxonomy | Backend attribute completeness + Amazon Knowledge Graph alignment |
| 02 | skill_02_npo | Noun Phrase Optimization + RAG-ready bullets |
| 03 | skill_03_ugc | UGC mining, Q&A seeding from customer reviews |
| 04 | skill_04_visual_seo | Image audit + OCR text scoring |
| 05 | skill_05_aplus | A+ module scoring + hallucination risk |
| 06 | skill_06_mobile | Full Mobile Audit — 8 modules, 2× weight in Amazon algo |
| 07 | skill_07_integrity | Semantic integrity + keyword stuffing check |
| 08 | skill_08_report | Visual HTML Report Generator (reads pipeline JSON → HTML) |
| 09 | skill_09_infographic | OCR-optimized infographic generator (4 types) |

**Skill 06 v2.0 modules** (title, bullet truncation, image order, swipe depth, A+ fold, touch targets, voice readiness, video arc) — all 8 must be passed and rendered.

**Data flow:**
```
Skill01.injection_payload        → Skill07.backend_attrs
Skill02.npo.output_noun_phrases  → Skill04.noun_phrases
Skill02.copy.rag_ready_bullets   → Skill07.bullets
Skill03.ugc.recurring_negative_keywords → Skill07.negative_review_themes
```

---

## Current State of Key Files

### Entry Point Scripts (project root)
| File | Status | Issue |
|------|--------|-------|
| `run_pipeline.py` | ✅ Working | Uses fake "VoltCharge" sample data. See Task #2 below. |
| `run_anker_test.py` | ⚠️ Bug | Calls Skill 06 with only `title` + `videos` — missing `bullets`, `images`, `modules`. Needs fix. |

### The Bug in run_anker_test.py (Task #1 fix)
Line ~404, Skill 06 call is:
```python
s6 = Skill06(
    title=TITLE,
    videos=VIDEOS,
    category="Cell Phones & Accessories",
    asin=ASIN,
).run()
```
It should be:
```python
s6 = Skill06(
    title=TITLE,
    videos=VIDEOS,
    category="Cell Phones & Accessories",
    asin=ASIN,
    bullets=BULLETS,          # ← ADD THIS
    images=IMAGES,            # ← ADD THIS
    modules=MODULES,          # ← ADD THIS
).run()
```
After fixing, re-run `run_anker_test.py` to regenerate `results/anker_a1665_pipeline.json` with the full 8-module Skill 06 v2.0 data.

---

## TASK LIST FOR NEXT AGENTS

---

### TASK 0 — Consolidate & Clean MD Files (Assign to: any agent)

**Goal:** The 5 core MD files have some duplication and drift. Audit and clean them:
- Remove duplicate content between `README.md` and `PLAN.md`
- Make sure `SKILLS_INDEX.md` reflects all 9 skills (Skill 08 + Skill 09 may be missing)
- Make sure `rufus_skill_contract.md` is updated with Skill 06 v2.0 JSON schema (8 modules)
- Do NOT invent new content — only consolidate what exists
- Keep `CLAUDE.md` untouched (it is enforced by the Claude Code environment)

---

### TASK 1 — Fix run_anker_test.py Bug (Assign to: Claude Code or Gemini)

See bug detail above under "Current State." One-line fix, three parameters to add.
After fixing:
- Run `python run_anker_test.py` to regenerate `results/anker_a1665_pipeline.json`
- Then run Skill 08 on the new JSON to regenerate `results/anker_report_v2.html`

---

### TASK 2 — Redesign run_pipeline.py + XLSM Intake SOP (Assign to: Claude Code + Gemini for architecture advice)

**Problem:** The current `run_pipeline.py` uses hardcoded fake sample data. This is wrong for production. John's real question: when a new Amazon `.xlsm` flat file is dropped into a market folder, how does the pipeline pick it up and run — without creating a new Python file per product (like `run_anker_test.py`)?

**John's intent:**
> "If we had 100 ASINs, we don't create 100 anker.py files."

**What needs to be designed and built:**

**2a. XLSM Intake SOP (new file: `tools/xlsm_intake_sop.py` or extend `tools/parse_catalog.py`):**
- When a `.xlsm` is dropped into any `markets/{market}/catalog/{category_path}/raw/` folder
- Parser reads Template sheet (row 2 = labels, row 3 = API field names) + Valid Values sheet
- Outputs `fields.csv` + `valid_values.csv` to sibling `data/` folder
- Rule: never overwrite existing CSVs — backup with date suffix first
- This SOP already partially exists in `tools/parse_catalog.py` — extend it, don't rewrite

**2b. Product Input Container (new file: `run_product.py` or `cli/run_product.py`):**
- Replace `run_anker_test.py` as the general-purpose single-product runner
- Accepts a **product data file** (JSON or YAML) as input — one file per ASIN
- Product data file contains: title, bullets, clr, spec, btg, keywords, reviews, images, modules, videos, product_claims, competitor_qas, asin, market, category_path
- Runs the full pipeline on that data
- Saves JSON to `results/{asin}_pipeline.json`
- Saves HTML report to `results/{asin}_report.html`
- Usage: `python run_product.py --input products/B0FKN7X7HM.json --report`

**2c. Batch Runner (new file: `run_batch.py`):**
- Accepts a folder of product JSON files
- Runs `run_product.py` logic for each ASIN in sequence
- Aggregates a summary table (all grades) at the end
- Usage: `python run_batch.py --folder products/ --report`

**Architecture advice needed from agents:**
- Should `run_pipeline.py` be kept as-is (with fake sample data for quick testing) and `run_product.py` be the production runner? Or refactor `run_pipeline.py` to accept external input?
- Recommend: Keep `run_pipeline.py` as developer smoke test, build `run_product.py` as production entry point.

---

### TASK 3 — Clean Up Markets Folder (Assign to: Claude Code, simple task)

**Remove:** `markets/cn/` — we do not support Chinese marketplace.
**Keep:** `markets/us/`, `markets/uk/`, `markets/jp/`, and **ADD** `markets/ca/` and `markets/au/`

| Market | Marketplace ID | Language |
|--------|---------------|---------|
| us | ATVPDKIKX0DER | en_US |
| uk | A1F83G8C2ARO7P | en_GB |
| jp | A1VC38T7YXB528 | ja_JP |
| ca | A2EUQ1WTGCTBG2 | en_CA |
| au | A39IBJ37TRP1C6 | en_AU |

Each new market folder (`ca/`, `au/`) needs the same subfolder structure as `us/`:
```
markets/ca/
  catalog/
    cell_phones_accessories/accessories/chargers_power_adapters/portable_power_banks/
      raw/     ← placeholder .gitkeep
      data/    ← placeholder .gitkeep
```
Update `CLAUDE.md` marketplace table to reflect the 5 new markets.
Also update `run_pipeline.py` market_id lookup dict.

---

### TASK 4 — Input Procedure & SaaS/Webapp Architecture Decision (Assign to: all 3 agents — design discussion)

**John's two options for getting product data into the pipeline:**

**Option A — Scraping (harder):**
Build a scraper to pull ASIN data directly from Amazon product pages.
- Pro: Fully automated
- Con: Amazon actively blocks scrapers, TOS risk, brittle (breaks when Amazon changes layout), requires proxies, JS rendering
- Verdict: High-maintenance, not recommended for v1

**Option B — Master Prompt (recommended for v1):**
Provide users a structured prompt they paste into ChatGPT / Claude / Gemini.
The prompt instructs the LLM to extract product data from the ASIN URL in a **precise JSON format** that matches the pipeline's input contract.
User pastes the output JSON into the system.
- Pro: No scraping, LLM does the heavy lifting, controlled format
- Con: User has one extra step

**Master Prompt design requirements (build this):**
- Output must match the product JSON schema used by `run_product.py` (Task 2b)
- Fields required: title, bullets (5), clr (all catalog fields), spec, btg, keywords, reviews (min 10), images (with image_type tagged), modules, videos, product_claims, asin, market, category_path
- Include validation: the LLM should self-check that category_path matches the exact Amazon Browse Tree Guide node
- File: `tools/MASTER_PROMPT.md` — document the prompt template
- The category_path must be 100% match with Amazon BTG — no guessing. Suggest including a BTG lookup table in the prompt.

**For catalog selection (user selects region + category):**
- User selects market (us/uk/jp/ca/au) from a dropdown
- User selects category from a pre-built lookup table matching Amazon's BTG
- This maps to a `category_path` that must exist in `markets/{market}/catalog/`
- If the XLSM for that category hasn't been parsed yet, the system prompts user to upload it
- Build a `tools/btg_lookup.json` — a nested JSON of all supported categories per market

---

### TASK 5 — GitHub Setup + Multi-Agent Collaboration (Assign to: John + Claude Code)

**Goal:** Put the repo on GitHub so Gemini / Claude Code / ChatGPT can all read the same codebase.

**Steps:**
1. Initialize git repo in `C:\Users\john\PycharmProjects\PythonProject\016-rufus-skills\rufus-skills\`
2. Create `.gitignore`:
   - `*.xlsm` (never commit Amazon flat files — per CLAUDE.md rule)
   - `results/` (generated outputs, not source)
   - `__pycache__/`, `*.pyc`, `.env`
   - `markets/*/catalog/*/raw/*.xlsm`
3. Create GitHub repo (private recommended — this is proprietary optimization logic)
4. Initial commit with all source files
5. Push `MEMORY.md` as the permanent agent handoff document — update it after every session

**For multi-agent workflow:**
- Claude Code reads the repo via filesystem
- Gemini reads via GitHub URL or file upload
- ChatGPT reads via file upload or GitHub Copilot plugin
- All agents should update `MEMORY.md` with what they did and any new open tasks before ending a session
- Use GitHub Issues to track the tasks in this document

---

## Open Questions / Decisions Needed

1. **run_product.py vs refactoring run_pipeline.py** — next agent advises on architecture
2. **Master Prompt format** — needs to be designed with the exact JSON schema once `run_product.py` input contract is finalized
3. **BTG lookup table** — how many categories do we support at launch? Start with portable power banks only (the catalog we have), expand from there
4. **Skill 08 + 09 standalone CLI** — both skills have CLIs but they're not documented in SKILLS_INDEX.md yet
5. **Skill 09 integration into run_pipeline.py** — currently Skill 09 (infographics) is not wired into the main pipeline. Decide: run it automatically or as an optional `--infographics` flag?

---

## Results Folder — Current Files

| File | What it is |
|------|-----------|
| `results/anker_a1665_pipeline.json` | Real Anker B0FKN7X7HM pipeline output — **Skill 06 is v1.0 only** (bug not yet fixed) |
| `results/anker_report_v2.html` | Latest Anker HTML report (v2 educational sections, but Skill 06 data is still v1.0) |
| `results/upgraded_pipeline.json` | VoltCharge (sample) full pipeline with Skill 06 v2.0 — 8 modules complete |
| `results/upgraded_report.html` | VoltCharge full v2.0 report — use this as the reference for what the finished report looks like |
| `results/infographics/` | 4 Skill 09 infographics for Anker (specs, features, comparison, lifestyle overlay) |

---

## Session History Summary

- **Session 1:** Built catalog_loader, run_pipeline.py, all 7 skills (01–07), first test with VoltCharge sample data
- **Session 2:** Built Skill 08 report generator, tested on Anker real data, produced anker_report.html
- **Session 3:** Standardized report with educational sections (KG, NPO/RAG, infographic types), rebuilt Skill 06 as full 8-module Mobile Audit (v2.0), created Skill 09 Infographic Generator, full pipeline test passed, this MEMORY.md created
- **Session 4 (2026-03-05):** Scaffolded new `rufus-skills/` project structure inside `016-rufus-skills/`. Migrated Skills 01–07 + utils into `shared/`. Deleted old root-level files. Consolidated all MD files: wrote real README.md and PLAN.md (were empty stubs), updated CLAUDE.md (removed mx/cn, added ca/au, skill count 7→9), updated SKILLS_INDEX.md (added Skills 08/09 rows, added Skill 06 v2.0 8-module table, corrected import path, updated chaining example). **Skills 08, 09, run_pipeline.py, run_anker_test.py, and results/ NOT yet migrated** — they exist from prior sessions but were not in scope this session.
- **Next session:** (1) Locate and migrate Skills 08/09 + run scripts + results/. (2) Push to GitHub. (3) Fix run_anker_test.py bug (Task 1). (4) Design run_product.py (Task 2).

---

*This file should be updated at the end of every agent session. Add a new line to Session History. Do not delete old entries.*
