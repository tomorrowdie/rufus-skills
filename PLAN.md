# PLAN.md — Architecture Decisions & Reasoning

**Project:** Rufus Skills — Amazon Listing Optimization Pipeline
**Author:** John / Anergy Academy
**Version:** 1.0

> This file records WHY decisions were made, not just what was built.
> Do not duplicate content from README.md here. PLAN.md is for reasoning.

---

## Core Problem We Are Solving

Amazon's Rufus AI answers customer questions by performing RAG (Retrieval-Augmented
Generation) over product listings. If a listing is written for old-style keyword
stuffing, Rufus cannot extract clean facts — it either hallucinates, skips the
product, or gives low-confidence answers.

The pipeline converts a raw Amazon listing into a **Rufus-optimized listing**:
one where every field gives Rufus a clear, structured, factual signal.

---

## Architecture Decisions

---

### Decision 1 — Skills are marketplace-agnostic

**Why:** The optimization logic (NPO formula, semantic density scoring, hallucination
risk) does not change between US and UK. Only the catalog field names change
(different `.xlsm` schemas per marketplace). Separating skills from marketplace data
means skills never need to be duplicated or forked per market.

**How it works:**
- Skills live in `shared/` and never import market-specific data directly
- Catalog field definitions are read from `data/fields.csv` and `data/valid_values.csv`
- The `fields_path` and `valid_path` are passed at runtime:
  ```python
  fields_path = f"markets/{market}/catalog/{category_path}/data/fields.csv"
  ```

---

### Decision 2 — XLSM → CSV first, then skills read CSV

**Why:** Amazon's `.xlsm` flat file templates are proprietary Excel files that change
layout between categories and marketplaces. Parsing them inline inside skill code
would couple the skills to Amazon's file format. Instead, `tools/parse_catalog.py`
acts as a one-time converter: XLSM in, two clean CSVs out. Skills only ever read
the clean CSVs.

**Rule:** Never edit `data/` CSVs manually. They are generated artifacts.
**Rule:** Never overwrite existing CSVs — back up with a date suffix first.

---

### Decision 3 — 9 skills, sequential pipeline, structured JSON output

**Why 9 separate skills instead of one monolith:** Each skill addresses a distinct
signal layer (taxonomy, copy, UGC, visual, A+, mobile, integrity, report,
infographics). Keeping them separate lets us run any subset, test any skill in
isolation, and swap implementations without touching the others.

**Data flow between skills (outputs feed into next skill's inputs):**
```
Skill01.injection_payload                    → Skill07.backend_attrs
Skill02.npo.output_noun_phrases              → Skill04.noun_phrases
Skill02.copy.rag_ready_bullets               → Skill07.bullets
Skill03.ugc_mining.sentiment
  .recurring_negative_keywords               → Skill07.negative_review_themes
Skills 01–07 combined pipeline JSON          → Skill08 (HTML report)
Skills 01–07 combined pipeline JSON          → Skill09 (infographics)
```

**Every skill outputs the same envelope structure:**
```json
{
  "skill_id": "XX",
  "skill_name": "...",
  "asin": "...",
  ...skill-specific data...,
  "scores": { "grade": "A|B|C|D|F", ... }
}
```

---

### Decision 4 — One product JSON file per ASIN (not one Python file per ASIN)

**Why:** The early pattern of creating `run_anker_test.py`, `run_voltcharge_test.py`
etc. does not scale. For 100 ASINs we do not write 100 Python files.

**The correct pattern:**
- One product data file per ASIN: `products/B0FKN7X7HM.json`
- One general runner: `run_product.py --input products/B0FKN7X7HM.json --report`
- One batch runner: `run_batch.py --folder products/ --report`

The product JSON file contains all inputs the pipeline needs:
`title`, `bullets`, `clr`, `spec`, `btg`, `keywords`, `reviews`, `images`,
`modules`, `videos`, `product_claims`, `competitor_qas`, `asin`, `market`,
`category_path`.

---

### Decision 5 — Master Prompt over scraping for data intake (v1)

**Why not scraping:** Amazon actively blocks scrapers. It requires proxies, JS
rendering, and breaks whenever Amazon changes page layout. TOS risk is high.
High maintenance for v1.

**Why Master Prompt:** A structured prompt instructs any LLM (ChatGPT, Claude,
Gemini) to extract product data from an ASIN URL and output it in the exact JSON
format the pipeline expects. The user pastes the JSON into `products/{asin}.json`
and runs the pipeline. One extra human step — zero scraping infrastructure.

**Master Prompt design requirements (see Task 4 in MEMORY.md):**
- Output must validate against the `run_product.py` input JSON schema
- Must include BTG (Browse Tree Guide) category path — exact match, no guessing
- File location: `tools/MASTER_PROMPT.md`

---

### Decision 6 — run_pipeline.py is a developer smoke test, not production

**Why:** `run_pipeline.py` uses hardcoded "VoltCharge" fake sample data. It exists
so developers can verify the pipeline runs end-to-end after any code change — in
under 10 seconds, no external data needed.

**Production entry point is `run_product.py`** — it reads a real product JSON file
and runs the full pipeline. Do not add real product data to `run_pipeline.py`.

---

## Skill 06 v2.0 — Why 8 Modules

Skill 06 (Mobile Habitat Optimization) was rebuilt from v1 (title + video only) to
v2.0 covering all 8 signals Amazon's mobile algorithm weights:

| Module | Signal |
|--------|--------|
| Title truncation | First 70 chars visible in Rufus chat window |
| Bullet truncation | Mobile bullet display cutoff |
| Image order | First image shown in mobile carousel |
| Swipe depth | How many images a user swipes before deciding |
| A+ fold | Is A+ content visible above the mobile fold? |
| Touch targets | Are CTA buttons large enough for thumb navigation? |
| Voice readiness | Does the title answer a voice query naturally? |
| Video arc | 9:16 vertical, Problem→Solution narrative structure |

Amazon's algorithm gives **2× weight** to mobile signals. This is why Skill 06
receives double the scoring weight in the composite pipeline grade.

---

## Supported Markets (v1 Scope Decision)

| Market | Rationale |
|--------|-----------|
| us | Primary market, all development done here |
| uk | Same language, second largest English-speaking market |
| jp | Key market for electronics (power banks) |
| ca | Same language as us, low friction to add |
| au | Same language as us, low friction to add |
| ~~mx~~ | Excluded — requires Spanish localization, out of v1 scope |
| ~~cn~~ | Excluded — requires Chinese localization + different Rufus model |

---

## Open Architecture Questions (unresolved)

1. **Skill 09 integration** — run automatically in pipeline, or as `--infographics` flag?
   Recommendation: flag, since it's expensive (image generation) and not always needed.

2. **BTG lookup table** — how many categories at launch?
   Recommendation: portable power banks only (the one XLSM we have). Expand per request.

3. **Multi-agent collaboration model** — Claude Code writes code, Gemini/GPT review
   and advise. Coordination via GitHub Issues + `MEMORY.md` updates after every session.
