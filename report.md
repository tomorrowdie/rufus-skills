# Project Status & Job Logs

## 1. Project Overview (Claude's Domain)

### Project Description

**Rufus Skills** is an AI-driven Amazon product listing optimization pipeline targeting
the **Rufus AI shopping assistant** ??Amazon's RAG-based (Retrieval-Augmented Generation)
conversational commerce engine. The system audits a product listing across 9 specialized
dimensions and outputs a structured JSON pipeline result + a visual HTML report.

The backend is a **pure Python rule-based engine** ??zero external LLM API required.
All 9 skills execute deterministically from product data, catalog data (CSV), and
review/Q&A text. BYOK (Bring Your Own Key) LLM integration points are reserved but
not yet wired.

---

### Core Architecture

#### Layer 1: Computation Engine (`shared/`)

Nine skill modules, each implementing a standard contract:

```
Skill.__init__(**params)   ??typed inputs
Skill.run()                ??self (method chaining, populates internal result)
Skill.to_json()            ??dict (JSON-serializable, always contains scores.grade)
```

Skills are **stateless** and **marketplace-agnostic**. They contain zero hardcoded
field names ??all catalog field names are read from CSV at runtime.

| Skill | Module | Responsibility |
|-------|--------|----------------|
| 01 | skill_01_taxonomy | Backend attribute completeness, Knowledge Graph alignment |
| 02 | skill_02_npo | Noun Phrase Optimization, RAG-ready bullet rewriting |
| 03 | skill_03_ugc | UGC mining, sentiment analysis, Q&A seeding |
| 04 | skill_04_visual_seo | Image alt-text scoring, OCR noun-phrase coverage |
| 05 | skill_05_aplus | A+ module audit, hallucination risk scoring |
| 06 | skill_06_mobile | 8-module mobile audit (2x Amazon algo weight) |
| 07 | skill_07_integrity | Keyword stuffing detection, backend conflict resolution |
| 08 | skill_08_report | HTML report generator from pipeline JSON |
| 09 | skill_09_infographic | OCR-optimized infographic generator (4 types) |

Skills 01-07 run in sequence. Skills 08-09 consume the combined pipeline JSON output.

#### Layer 2: Data Layer

```
markets/
  {market}/catalog/{category_path}/
    raw/     <- Amazon .xlsm flat file templates (gitignored)
    data/
      fields.csv        <- label, field_name, section, max_count
      valid_values.csv  <- field_name, valid_value
```

`tools/parse_catalog.py` converts raw .xlsm files to CSV. Skills read from `data/`
at runtime ??never from `raw/`. No SQL database. Catalog data is file-based CSV.
Job results are written as JSON files to `results/`.

#### Layer 3: Pipeline Data Flow

```
Input JSON (one per ASIN)
  -> Skill01  injection_payload        -> Skill07 backend_attrs
  -> Skill02  npo.output_noun_phrases  -> Skill04 noun_phrases
  -> Skill02  copy.rag_ready_bullets   -> Skill07 bullets
  -> Skill03  ugc.recurring_negatives  -> Skill07 negative_review_themes
  -> Skills 01-07 combined JSON        -> Skill08 (HTML report)
  -> Skills 01-07 combined JSON        -> Skill09 (infographics, optional)
```

#### Layer 4: Entry Points (Backend CLI)

| Script | Purpose | Usage |
|--------|---------|-------|
| `run_product.py` | Single-ASIN pipeline runner | `python run_product.py --input products/B0XYZ.json --report` |
| `run_batch.py` | Batch runner over a folder of ASINs | `python run_batch.py --input-dir products/ --report` |
| `run_pipeline.py` | Developer smoke test (hardcoded sample data) | Internal testing only |
| `run_anker_test.py` | Real Anker ASIN integration test | Internal testing only |

#### Layer 5: API Boundaries for Other Agents

**For Codex (Frontend):**
- `run_product.py` is the primary backend entry point. Input: product JSON (schema defined in `tools/MASTER_PROMPT.md`). Output: `results/{asin}_pipeline.json` + `results/{asin}_report.html`.
- The pipeline JSON structure is the data contract. The top-level keys are: `asin`, `product`, `market`, `category_path`, `grades_summary`, `skill_01` through `skill_07`.
- Every skill result exposes `skill_id`, `skill_name`, `asin`, `scores.score`, `scores.grade` at the root.
- The `grades_summary` dict is the fastest read for a dashboard view.

**For Antigravity (Automation/Integration):**
- All skills support JSON stdin piping: `echo '{...}' | python skill_01.py`
- `save_json_output(data, None)` prints to stdout ??fully pipeable.
- `load_json_input(source)` accepts dict, Path, or "-" (stdin).
- `run_batch.py` accepts a folder ??suitable for CRON or n8n Execute Command nodes.
- The `tools/MASTER_PROMPT.md` defines the LLM extraction prompt that produces the input JSON format.

---

### Folder Structure

```
rufus-skills/
??? agent_manifest.md          <- Multi-agent collaboration rules
??? report.md                  <- This file (project status + agent logs)
??? CLAUDE.md                  <- Repo rules (enforced by Claude Code)
??? MEMORY.md                  <- Agent handoff document
??? PLAN.md                    <- Architecture decisions and reasoning
??? SKILLS_INDEX.md            <- Full skill index and import patterns
??? rufus_skill_contract.md    <- JSON input/output contract for all 9 skills
??? requirements.txt
??? .gitignore
??
??? shared/                    <- All 9 skills (marketplace-agnostic engine)
??  ??? skill_01_taxonomy/     skill_01.py
??  ??? skill_02_npo/          skill_02.py
??  ??? skill_03_ugc/          skill_03.py
??  ??? skill_04_visual_seo/   skill_04.py
??  ??? skill_05_aplus/        skill_05.py
??  ??? skill_06_mobile/       skill_06.py (v2.0, 8 modules)
??  ??? skill_07_integrity/    skill_07.py
??  ??? skill_08_report/       skill_08.py
??  ??? skill_09_infographic/  skill_09.py
??  ??? utils/
??      ??? helpers.py         <- sanitize_text, score_to_grade, save_json_output, etc.
??      ??? catalog_loader.py  <- loads fields.csv + valid_values.csv
??
??? markets/                   <- Marketplace-specific catalog data
??  ??? us/catalog/.../portable_power_banks/raw/ + data/
??  ??? uk/ ca/ au/ jp/        (same structure per market)
??
??? tools/
??  ??? parse_catalog.py       <- XLSM -> CSV parser (612 lines, fully implemented)
??  ??? MASTER_PROMPT.md       <- LLM prompt template for product data extraction
??  ??? btg_lookup.json        <- Amazon Browse Tree Guide category lookup
??
??? run_product.py             <- Production single-ASIN runner (Task 2b - DONE)
??? run_batch.py               <- Production batch runner (Task 2c - DONE)
??? run_pipeline.py            <- Developer smoke test (VoltCharge sample data)
??? run_anker_test.py          <- Real Anker B0FKN7X7HM integration test
??
??? results/                   <- Pipeline JSON + HTML report outputs (gitignored)
    ??? anker_a1665_pipeline.json
    ??? anker_report_v2.html
    ??? infographics/
```

---

### Grading Scale (all skills)

| Score | Grade | Meaning |
|-------|-------|---------|
| >= 90 | A | Rufus-ready |
| >= 75 | B | Minor improvements needed |
| >= 60 | C | Notable gaps |
| >= 40 | D | Significant issues |
| < 40  | F | Major rework required |

---

### Known Issues / Open Items

1. ~~`run_product.py` line 167: imports `list_to_html` from skill_08~~ **FIXED (Session 5)**

2. `run_batch.py` uses `--input-dir` flag; MEMORY.md spec said `--folder`.
   Cosmetic inconsistency -- does not affect function.

---

### Files for Project Manager (Gemini) to Review

| File | What to Review |
|------|---------------|
| `shared/utils/helpers.py` | Core utilities: save_json_output stdout fallback (Gemini's change), load_json_input, score_to_grade |
| `run_product.py` | Single-ASIN production runner ??the primary backend entry point for Codex |
| `run_batch.py` | Batch runner ??primary entry point for Antigravity CRON/automation |
| `rufus_skill_contract.md` | Full JSON input/output contract for all 9 skills ??binding interface for all agents |
| `tools/MASTER_PROMPT.md` | LLM extraction prompt ??defines the input JSON Antigravity will produce |
| `tools/btg_lookup.json` | BTG category map ??used for category_path validation |
| `shared/skill_06_mobile/skill_06.py` | 8-module mobile audit ??highest-impact skill (2x Amazon algo weight) |
| `results/anker_a1665_pipeline.json` | Real Anker pipeline output ??use as reference for expected JSON shape |
| `results/anker_report_v2.html` | Visual HTML report ??reference for what Codex is building toward |

---

## 2. Agent Job Logs

### Claude (Backend/Architect) Log

* 2026-03-05 Session 4 ??Scaffolded new `rufus-skills/` project structure. Migrated Skills 01-07 + utils into `shared/`. Consolidated all 5 core MD files. Updated CLAUDE.md (removed mx/cn, added ca/au). Updated SKILLS_INDEX.md (Skills 08/09, Skill 06 v2.0 8-module table). Pushed initial commit + doc-drift fix commit to GitHub.
* 2026-03-05 Session 5 -- Reviewed Gemini's completed work (Tasks 0,1,2,4). All changes verified on disk. Identified 1 bug: `list_to_html` import in run_product.py --report path. Fixed bug. Wrote project overview and architecture definition in report.md (this file). Backend foundation ready for Gemini review.
* 2026-03-05 Session 6 -- Workspace cleanup and first local offline end-to-end test.
  - **Deleted:** `run_anker_test.py` (replaced by `input_jsons/anker_B0FKN7X7HM.json` + `run_product.py`)
  - **Deleted:** `run_pipeline.py` (replaced by `input_jsons/voltcharge_sample.json` + `run_product.py`)
  - **Preserved data:** Extracted all hardcoded Anker and VoltCharge product data to proper input JSON files before deletion. No data lost.
  - **New files:** `input_jsons/anker_B0FKN7X7HM.json`, `input_jsons/voltcharge_sample.json`
  - **E2E Test:** `python run_batch.py --input-dir input_jsons/ --report` -- **3/3 SUCCESS**
    - `B0FKN7X7HM` (Anker): Skills 01-07 complete, HTML report generated (46,214 chars)
    - `B0TEST1234` (Antigravity mock): Skills 01-07 complete, HTML report generated (37,224 chars)
    - `B0EXAMPLE_POWERBANK` (VoltCharge): Skills 01-07 complete, HTML report generated (45,177 chars)
  - **Results populated:** 3 pipeline JSONs + 3 HTML reports in `results/` -- Codex dashboard can now load any of them.
  - **Clean root:** Only `run_product.py` and `run_batch.py` remain as entry points (correct).

**Backend foundation status: COMPLETE. Workspace clean. E2E test passed. Results/ populated. Ready for Codex dashboard integration and Antigravity automation wiring.**

* 2026-03-06 Session 7 -- Built `api.py` — FastAPI REST API wrapping the full 7-skill pipeline.
  - **New file:** `api.py` (root level, 350+ lines)
  - **Framework:** FastAPI 0.135 + Pydantic v2 + uvicorn
  - **Pydantic models built from `rufus_skill_contract.md`:**
    - `BTGModel`, `ReviewItem`, `QAItem`, `ProductContextModel`, `ImageItem`, `ModuleItem`, `VideoItem`
    - `ProductPipelineRequest` — full input schema with field-level descriptions, constraints, and examples
    - `GradesSummary`, `PipelineResponse` — structured response models
    - `HealthResponse`
  - **Routes (4 application endpoints):**
    - `GET  /health` — confirms API up + lists 7 loaded skill modules
    - `POST /pipeline` — runs full 7-skill pipeline; auto-saves result to `results/{asin}_pipeline.json`
    - `GET  /results/{asin}` — retrieves cached pipeline result by ASIN
    - `GET  /results` — lists all cached results with size + timestamp
    - `GET  /` → redirects to `/docs`
  - **OpenAPI/Swagger UI** at `/docs` — serves as the handshake manual for external developers (Auto-Pilot, partners)
  - **Live test (TestClient):** `GET /health` → 200 ✓ | `POST /pipeline` (Anker B0FKN7X7HM) → 200 ✓
    - Grades confirmed: Skill01=A, Skill06=B, Skill07=C (matches CLI batch test output)
  - **Dependencies installed:** `fastapi>=0.111.0`, `uvicorn[standard]>=0.30.0`, `pydantic>=2.0.0` added to `requirements.txt`
  - **Core engine untouched** — `shared/` skills not modified. API is a pure wrapper layer.

  **To start the API server:**
  ```bash
  uvicorn api:app --host 0.0.0.0 --port 8000 --reload
  # Swagger UI: http://localhost:8000/docs
  ```

### Codex (Frontend/Builder) Log
* [2026-03-05] Built `lite/dashboard.html`, `lite/dashboard.css`, and `lite/dashboard.js` as a frontend prototype that consumes `results/{asin}_pipeline.json` from `run_product.py`. Added two input paths: (1) ASIN-based fetch (`../results/{asin}_pipeline.json`) and (2) local JSON file upload. Implemented a grades_summary dashboard with per-skill cards, grade badges, score bars, and computed overall grade. No backend or `shared/` files were modified.

### Antigravity (Integrator/Automation) Log
* [2026-03-05] ??Built and executed `automation_pipeline.py` which generates a mock product JSON matching the `tools/MASTER_PROMPT.md` schema, saves it to `input_jsons/test_product.json`, and feeds it into `run_batch.py`. The data piping is working successfully, generating pipeline JSONs and HTML reports through the system without modifying core `shared/` logic. Made a small syntactic fix to the `MASTER_PROMPT.md` schema as well.

