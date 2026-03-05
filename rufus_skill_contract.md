# rufus_skill_contract.md

> **Version:** 1.0.0 | **Author:** John / Anergy Academy
>
> This is the official JSON Contract for the 016-rufus-skills library.
> Any upstream system (Auto-Pilot, n8n agent, or any AI agent) MUST
> match these exact field names and data types before calling any skill.
> If the data frame does not match, the skill will fail silently or
> return incorrect grades.
>
> **HOW TO USE THIS CONTRACT:**
> Step 1 — Read the MASTER COMPATIBILITY TABLE
> Step 2 — For each skill you plan to call, check your data against
>           the INPUT JSON format exactly
> Step 3 — Run the VALIDATION CHECKLIST before executing
> Step 4 — Compare your output against the OUTPUT JSON format

---

## MASTER COMPATIBILITY TABLE

| # | Class | Required Inputs | Optional Inputs | Key Output Path | Grade Path |
|---|-------|----------------|-----------------|-----------------|------------|
| 01 | `Skill01` | `clr` dict, `spec` dict, `btg` dict | `asin` str | `injection_payload` | `scores.grade` |
| 02 | `Skill02` | `keywords` list[str], `bullets` list[str] | `topic_clusters` dict, `title` str, `asin` str | `copy.rag_ready_bullets` | `scores.grade` |
| 03 | `Skill03` | `reviews` list[dict] | `competitor_qas` list[dict], `product_context` dict, `asin` str | `qa_seeding.qa_pairs` | `scores.grade` |
| 04 | `Skill04` | `images` list[dict] | `noun_phrases` list[str], `product_name` str, `asin` str | `image_reports` | `scores.grade` |
| 05 | `Skill05` | *(none required)* | `comparison_table` dict, `modules` list[dict], `product_claims` list[str], `asin` str | `hallucination_risk` | `scores.grade` |
| 06 | `Skill06` | `title` str | `videos` list[dict], `category` str, `asin` str | `title_analysis` | `scores.grade` |
| 07 | `Skill07` | `title` str | `bullets` list[str], `backend_attrs` dict, `negative_review_themes` list[str], `asin` str | `compliance_report` | `scores.grade` |

> **Universal output fields present in every skill:** `skill_id` (str), `skill_name` (str), `asin` (str), `scores.grade` (str: A/B/C/D/F)

---

## SKILL 01 — Structured Taxonomy & Attribute Injection

### 1. Skill ID and Name
- **ID:** `"01"`
- **Class:** `Skill01`
- **Import:** `from skill_01_taxonomy.skill_01 import Skill01`

---

### 2. INPUT JSON

```json
{
  "clr": {
    "item_name":           "Portable Power Bank 20000mAh",
    "color_name":          "Midnight Ocean",
    "material_type":       "Space-Grade Alloy",
    "specific_use":        "Camping, Travel",
    "batteries_included":  "",
    "warranty_description": ""
  },
  "spec": {
    "capacity_mah":        20000,
    "output_ports":        3,
    "weight_grams":        450,
    "waterproof_rating":   "IPX5",
    "charging_standard":   "PD 65W"
  },
  "btg": {
    "category":  "Electronics > Portable Power",
    "node_id":   "2407749011",
    "node_path": "Electronics > Accessories > Batteries > Portable Power Banks"
  },
  "asin": "B0EXAMPLE1"
}
```

---

### 3. OUTPUT JSON

```json
{
  "skill_id": "01",
  "skill_name": "Structured Taxonomy & Attribute Injection",
  "asin": "B0EXAMPLE1",
  "audit": {
    "null_fields":        { "batteries_included": "MISSING", "warranty_description": "MISSING" },
    "null_count":         2,
    "standardized_values":   { "color_name": "Navy Blue", "material_type": "Aluminum Alloy" },
    "standardized_count": 2,
    "knowledge_graph_mapping": {
      "Camping, Travel": ["Outdoor", "Forest", "Portable Power"]
    }
  },
  "injection_payload": {
    "item_name":          "Portable Power Bank 20000mAh",
    "color_name":         "Navy Blue",
    "material_type":      "Aluminum Alloy",
    "specific_use":       "Camping, Travel",
    "capacity_mah":       20000,
    "output_ports":       3,
    "weight_grams":       450,
    "waterproof_rating":  "IPX5",
    "charging_standard":  "PD 65W",
    "knowledge_graph_nodes": {
      "Camping, Travel": ["Outdoor", "Forest", "Portable Power"]
    },
    "browse_tree": {
      "category":  "Electronics > Portable Power",
      "node_id":   "2407749011",
      "node_path": "Electronics > Accessories > Batteries > Portable Power Banks"
    }
  },
  "scores": {
    "completeness_pct":      72.7,
    "grade":                 "C",
    "high_confidence_tokens": 11
  }
}
```

---

### 4. FIELD RULES

| Field | Type | ✅/⚙️ | Default if omitted | Notes |
|-------|------|-------|-------------------|-------|
| `clr` | `dict` | ✅ Required | — | Flat key/value pairs. Empty dict `{}` is accepted but all fields score as null. Keys must include `color` or `colour` in name for color standardization; `material` for material standardization; `use` or `purpose` for Knowledge Graph mapping. |
| `spec` | `dict` | ✅ Required | — | Technical attributes. Merged with `clr`; `spec` values are overridden by `clr` values on key collision. |
| `btg` | `dict` | ✅ Required | — | Must contain `category`, `node_id`, `node_path` as string keys. Empty dict `{}` produces no `browse_tree` in payload. |
| `asin` | `str` | ⚙️ Optional | `"UNKNOWN"` | Label only — does not affect scoring. Passed through `sanitize_text()`. |

**Color standardization keys recognized in `clr`/`spec`:**
`"midnight ocean"` → `"Navy Blue"` | `"forest whisper"` → `"Dark Green"` | `"arctic mist"` → `"Light Gray"` | `"rose gold blush"` → `"Rose Gold"` | `"obsidian night"` → `"Black"` | `"champagne shimmer"` → `"Gold"` | `"desert sand"` → `"Beige"` | `"cobalt storm"` → `"Blue"`

**Material standardization keys recognized:**
`"space-grade alloy"` → `"Aluminum Alloy"` | `"nano-fiber fabric"` → `"Polyester"` | `"eco-wood composite"` → `"Bamboo"` | `"military polymer"` → `"ABS Plastic"`

**Use-case Knowledge Graph keys recognized:**
`"camping"` → `["Outdoor","Forest","Portable Power"]` | `"travel"` → `["Airport","Hotel","International"]` | `"home office"` → `["Workspace","Desk Setup","Productivity"]` | `"gym"` → `["Fitness","Sports","Active Lifestyle"]` | `"kitchen"` → `["Cooking","Food Prep","Culinary"]`

---

### 5. VALIDATION CHECKLIST

```
[ ] clr is a dict (not a list, not None)
[ ] spec is a dict (not a list, not None)
[ ] btg is a dict containing at least "category", "node_id", "node_path" as strings
[ ] asin is a string (or omitted)
[ ] Color attribute key contains "color" or "colour" in its name for standardization
[ ] Use-case attribute key contains "use" or "purpose" in its name for graph mapping
[ ] Empty string values in clr/spec will appear in audit.null_fields — intentional
[ ] Result accessed via: skill.to_json()["injection_payload"]
[ ] Grade accessed via: skill.to_json()["scores"]["grade"]
```

---
---

## SKILL 02 — Noun Phrase Optimization (NPO) & RAG-Ready Copy

### 1. Skill ID and Name
- **ID:** `"02"`
- **Class:** `Skill02`
- **Import:** `from skill_02_npo.skill_02 import Skill02`

---

### 2. INPUT JSON

```json
{
  "keywords": [
    "fast charge",
    "portable charger for camping",
    "high-capacity power bank"
  ],
  "bullets": [
    "Amazing fast charging technology",
    "Best-in-class portable design for travel",
    "World-class battery life for all devices"
  ],
  "topic_clusters": {
    "charging_speed": ["How fast does it charge?", "What is the wattage output?"],
    "portability":    ["Is it allowed on airplanes?", "How heavy is it?"],
    "compatibility":  ["Does it work with MacBook?", "Is it iPhone compatible?"]
  },
  "title": "Power Bank 20000mAh Fast Charging USB-C PD 65W for Camping Travel",
  "asin": "B0EXAMPLE2"
}
```

---

### 3. OUTPUT JSON

```json
{
  "skill_id": "02",
  "skill_name": "Noun Phrase Optimization (NPO) & RAG-Ready Copy",
  "asin": "B0EXAMPLE2",
  "npo": {
    "input_keywords": [
      "fast charge",
      "portable charger for camping",
      "high-capacity power bank"
    ],
    "output_noun_phrases": [
      "Fast with charge capability for enhanced user experience",
      "Portable charger that delivers superior performance for camping",
      "High-capacity power with bank capability for enhanced user experience"
    ],
    "phrase_count": 3
  },
  "copy": {
    "rag_ready_bullets": [
      "Designed for  fast charging technology — answers the question: How fast does it charge?",
      "Built for  portable design for travel — answers the question: Is it allowed on airplanes?",
      "Ideal when  battery life for all devices — answers the question: Does it work with MacBook?"
    ],
    "title": {
      "original":            "Power Bank 20000mAh Fast Charging USB-C PD 65W for Camping Travel",
      "optimized":           "Power Bank 20000mAh Fast Charging USB-C PD 65W for Camping Travel",
      "char_count":          64,
      "truncated_preview_70": "Power Bank 20000mAh Fast Charging USB-C PD 65W for Camping Tra",
      "leads_with_category": true
    }
  },
  "scores": {
    "semantic_density": {
      "per_bullet": [
        { "bullet": "Designed for fast charging technology — answers the…", "np_hits": 0 },
        { "bullet": "Built for  portable design for travel — answers the …", "np_hits": 0 },
        { "bullet": "Ideal when  battery life for all devices — answers t…", "np_hits": 0 }
      ],
      "average_np_hits": 0.0,
      "density_label":  "LOW",
      "density_score":  0.0
    },
    "grade": "F"
  }
}
```

> **Note — title subfield edge case:** When `title=""` (empty string), the `copy.title` object returns
> keys `original`, `optimized`, `char_count`, `truncated_preview` (no `_70` suffix, no `leads_with_category`).
> When title is provided, the keys are `truncated_preview_70` and `leads_with_category` are also present.

---

### 4. FIELD RULES

| Field | Type | ✅/⚙️ | Default if omitted | Notes |
|-------|------|-------|-------------------|-------|
| `keywords` | `list[str]` | ✅ Required | — | Each keyword passed through `sanitize_text()`. Each becomes one noun phrase via NPO Formula. Empty list `[]` produces 0 phrases. |
| `bullets` | `list[str]` | ✅ Required | — | Each bullet passed through `sanitize_text()`. Each becomes one RAG-ready bullet. Empty list `[]` produces empty output and `density_score=0`. |
| `topic_clusters` | `dict[str, list[str]]` | ⚙️ Optional | `{}` | Format: `{intent_label: [query_string, ...]}`. Queries are consumed in order, 2 per bullet. |
| `title` | `str` | ⚙️ Optional | `""` | Amazon product title. When empty, `copy.title` returns minimal dict without `truncated_preview_70`. |
| `asin` | `str` | ⚙️ Optional | `"UNKNOWN"` | Label only. |

**Filler words stripped from bullets during optimization:**
`"amazing"`, `"incredible"`, `"best-in-class"`, `"world-class"`, `"premium quality"`, `"top-notch"`

**NPO Formula applied per keyword:**
- Keyword contains `" for "` → `"{noun} that delivers superior performance for {context}"`
- Single word → `"{Word} technology that maximizes efficiency in everyday use"`
- Multi-word, no `"for"` → `"{Noun} with {qualifier} capability for enhanced user experience"`

---

### 5. VALIDATION CHECKLIST

```
[ ] keywords is a non-empty list of strings
[ ] bullets is a non-empty list of strings (ideally 3–5 bullets)
[ ] topic_clusters format: {"intent": ["question1", "question2"]} — values are lists of strings
[ ] title is a string (empty string is acceptable, omit for no title optimization)
[ ] For best density scores: provide noun_phrases from this skill's output back into Skill04
[ ] Result accessed via: skill.to_json()["copy"]["rag_ready_bullets"]
[ ] Noun phrases for downstream use: skill.to_json()["npo"]["output_noun_phrases"]
[ ] Grade accessed via: skill.to_json()["scores"]["grade"]
```

---
---

## SKILL 03 — UGC Ground Truth Mining & Q&A Seeding

### 1. Skill ID and Name
- **ID:** `"03"`
- **Class:** `Skill03`
- **Import:** `from skill_03_ugc.skill_03 import Skill03`

---

### 2. INPUT JSON

```json
{
  "reviews": [
    { "text": "Does it work on airplanes? I need it for international travel.", "rating": 4 },
    { "text": "Charges my MacBook in 1.5 hours. Love it! Long battery life.", "rating": 5 },
    { "text": "Stopped working after 2 weeks. Cheap quality, very disappointing.", "rating": 1 },
    { "text": "Is this waterproof? How fast does it charge my iPhone?", "rating": 3 },
    { "text": "Works perfectly. Exactly as described. Highly recommend.", "rating": 5 }
  ],
  "competitor_qas": [
    {
      "question": "Can I charge two devices at the same time?",
      "answer":   "Yes, it supports simultaneous dual charging via USB-C and USB-A."
    }
  ],
  "product_context": {
    "waterproof_rating": "IPX5",
    "warranty_months":   18,
    "charge_hours":      1.5
  },
  "asin": "B0EXAMPLE3"
}
```

---

### 3. OUTPUT JSON

```json
{
  "skill_id": "03",
  "skill_name": "UGC Ground Truth Mining & Q&A Seeding",
  "asin": "B0EXAMPLE3",
  "ugc_mining": {
    "technical_questions_found": [
      "does it work on airplanes",
      "is this waterproof",
      "how fast does it charge my iphone"
    ],
    "question_count": 3,
    "sentiment": {
      "positive_count":  3,
      "negative_count":  1,
      "top_positive_snippets": [
        "Charges my MacBook in 1.5 hours. Love it! Long battery life.",
        "Works perfectly. Exactly as described. Highly recommend."
      ],
      "top_negative_snippets": [
        "Stopped working after 2 weeks. Cheap quality, very disappointing."
      ],
      "recurring_negative_keywords": {
        "stopped working": 1,
        "cheap":           1
      }
    }
  },
  "qa_seeding": {
    "qa_pairs": [
      { "question": "Is this product allowed on airplanes?",
        "answer":   "Yes, this product meets FAA regulations for carry-on. Battery capacity is within the 100Wh limit.",
        "template_key": "airplane" },
      { "question": "Is it waterproof or water-resistant?",
        "answer":   "This product carries an IPX5 waterproof rating, suitable for splashing and rain exposure.",
        "template_key": "waterproof" },
      { "question": "What is the warranty policy?",
        "answer":   "Covered by a 18-month manufacturer warranty. Contact our support team for replacements.",
        "template_key": "warranty" },
      { "question": "How long does it take to fully charge?",
        "answer":   "With PD fast charging, a full charge takes approximately 1.5 hours.",
        "template_key": "charging_time" },
      { "question": "Is it compatible with iPhone and Android?",
        "answer":   "Yes, works with all USB-C and USB-A devices including iPhone (via adapter), Android, and laptops.",
        "template_key": "compatibility" },
      { "question": "Can I charge two devices at the same time?",
        "answer":   "Yes, it supports simultaneous dual charging via USB-C and USB-A.",
        "template_key": "competitor_derived" }
    ],
    "pair_count": 6
  },
  "recommendations": [
    "Add a bullet explicitly stating build material and certification (e.g., 'Aircraft-grade aluminum chassis, drop-tested to MIL-STD-810G')",
    "Seed Q&A with warranty/return policy answer to intercept Rufus reliability queries"
  ],
  "scores": {
    "qa_coverage_pct":    100.0,
    "grade":              "A",
    "proof_nodes_seeded": 6
  }
}
```

---

### 4. FIELD RULES

| Field | Type | ✅/⚙️ | Default if omitted | Notes |
|-------|------|-------|-------------------|-------|
| `reviews` | `list[dict]` | ✅ Required | — | Each dict must have `"text"` (str) and `"rating"` (int 1–5). Missing keys use `.get()` defaults: text=`""`, rating=`3`. Empty list `[]` produces 0 questions, neutral sentiment. |
| `reviews[].text` | `str` | ✅ in each review | `""` | Free-text review. Mined for question patterns via regex. |
| `reviews[].rating` | `int` | ✅ in each review | `3` | 1–5. Rating ≤2 flags as negative; ≥4 flags as positive. |
| `competitor_qas` | `list[dict]` | ⚙️ Optional | `[]` | Each dict: `{"question": str, "answer": str}`. Added to qa_pairs with `template_key: "competitor_derived"`. |
| `product_context` | `dict` | ⚙️ Optional | `{}` | Keys used to fill Q&A templates (see below). |
| `product_context.waterproof_rating` | `str` | ⚙️ Optional | `"IPX4"` | Fills `{rating}` placeholder in waterproof Q&A answer. |
| `product_context.warranty_months` | `int` | ⚙️ Optional | `12` | Fills `{months}` placeholder in warranty Q&A answer. |
| `product_context.charge_hours` | `float` | ⚙️ Optional | `2` | Fills `{hours}` placeholder in charging_time Q&A answer. |
| `asin` | `str` | ⚙️ Optional | `"UNKNOWN"` | Label only. |

**Negative keywords flagged in reviews:**
`"broke"`, `"broken"`, `"stopped working"`, `"doesn't work"`, `"does not work"`, `"defective"`, `"poor quality"`, `"cheap"`, `"flimsy"`, `"misleading"`, `"wrong size"`, `"not as described"`, `"disappointing"`, `"returned"`, `"waste of money"`, `"fragile"`, `"peeling"`, `"cracked"`

**5 Q&A templates always generated** (keys: `airplane`, `waterproof`, `warranty`, `charging_time`, `compatibility`) — plus any `competitor_qas` appended after.

---

### 5. VALIDATION CHECKLIST

```
[ ] reviews is a non-empty list of dicts
[ ] Each review dict has "text" (str) and "rating" (int 1–5)
[ ] competitor_qas: each dict has both "question" (str) and "answer" (str)
[ ] product_context keys: "waterproof_rating" (str), "warranty_months" (int), "charge_hours" (float)
[ ] Negative themes for Skill07: skill.to_json()["ugc_mining"]["sentiment"]["recurring_negative_keywords"].keys()
[ ] Q&A pairs for seeding: skill.to_json()["qa_seeding"]["qa_pairs"]
[ ] Grade accessed via: skill.to_json()["scores"]["grade"]
```

---
---

## SKILL 04 — Multimodal Visual SEO Validation

### 1. Skill ID and Name
- **ID:** `"04"`
- **Class:** `Skill04`
- **Import:** `from skill_04_visual_seo.skill_04 import Skill04`

---

### 2. INPUT JSON

```json
{
  "images": [
    {
      "filename":   "main_product.jpg",
      "image_type": "main",
      "alt_text":   "product image 1",
      "ocr_text":   ""
    },
    {
      "filename":   "specs_infographic.jpg",
      "image_type": "infographic",
      "alt_text":   "Power bank specs showing PD 65W output and 20000mAh capacity for laptop charging",
      "ocr_text":   "PD 65W Output | 20000mAh | IPX5 Waterproof | Fast charge for laptops"
    },
    {
      "filename":   "camping_lifestyle.jpg",
      "image_type": "lifestyle",
      "alt_text":   "Portable power bank used for camping in a forest setting at night",
      "ocr_text":   ""
    }
  ],
  "noun_phrases": [
    "portable charger",
    "fast charge",
    "PD 65W output",
    "IPX5 waterproof"
  ],
  "product_name": "Portable Power Bank 20000mAh",
  "asin": "B0EXAMPLE4"
}
```

---

### 3. OUTPUT JSON

```json
{
  "skill_id": "04",
  "skill_name": "Multimodal Visual SEO Validation",
  "asin": "B0EXAMPLE4",
  "image_reports": [
    {
      "filename":   "main_product.jpg",
      "image_type": "main",
      "alt_text": {
        "original":  "product image 1",
        "optimized": "Portable Power Bank 20000mAh portable charger — clean studio shot showing primary product view on white background",
        "score": {
          "is_generic":       true,
          "length":           15,
          "noun_phrase_hits": 0,
          "score":            0.0,
          "grade":            "F"
        }
      },
      "ocr_audit": {
        "has_ocr_text":   false,
        "np_coverage":    0,
        "missing_phrases": ["portable charger", "fast charge", "PD 65W output"]
      },
      "ocr_tips": []
    },
    {
      "filename":   "specs_infographic.jpg",
      "image_type": "infographic",
      "alt_text": {
        "original":  "Power bank specs showing PD 65W output and 20000mAh capacity for laptop charging",
        "optimized": "Portable Power Bank 20000mAh portable charger — callout annotations showing technical specifications and key features",
        "score": {
          "is_generic":       false,
          "length":           82,
          "noun_phrase_hits": 2,
          "score":            55.0,
          "grade":            "F"
        }
      },
      "ocr_audit": {
        "has_ocr_text":    true,
        "np_coverage_pct": 75.0,
        "present_phrases": ["fast charge", "PD 65W output"],
        "missing_phrases": ["portable charger"]
      },
      "ocr_tips": [
        "Use dark text (#1A1A1A or similar) on light backgrounds (≥4.5:1 contrast ratio)",
        "Use font size ≥ 24px for overlay text to ensure OCR legibility",
        "Prefer sans-serif fonts (e.g., Helvetica, Inter) for machine readability",
        "Keep text blocks to ≤ 6 words per line to avoid OCR fragmentation"
      ]
    },
    {
      "filename":   "camping_lifestyle.jpg",
      "image_type": "lifestyle",
      "alt_text": {
        "original":  "Portable power bank used for camping in a forest setting at night",
        "optimized": "Portable Power Bank 20000mAh portable charger — user interacting with product showing product in real-world use environment",
        "score": {
          "is_generic":       false,
          "length":           64,
          "noun_phrase_hits": 0,
          "score":            38.4,
          "grade":            "F"
        }
      },
      "ocr_audit": {
        "has_ocr_text":   false,
        "np_coverage":    0,
        "missing_phrases": ["portable charger", "fast charge", "PD 65W output"]
      },
      "ocr_tips": []
    }
  ],
  "summary": {
    "total_images":          3,
    "generic_alt_text_count": 1,
    "infographics_audited":  1,
    "ocr_tips": [
      "Use dark text (#1A1A1A or similar) on light backgrounds (≥4.5:1 contrast ratio)",
      "Use font size ≥ 24px for overlay text to ensure OCR legibility",
      "Prefer sans-serif fonts (e.g., Helvetica, Inter) for machine readability",
      "Keep text blocks to ≤ 6 words per line to avoid OCR fragmentation"
    ]
  },
  "scores": {
    "average_alt_text_score": 31.1,
    "grade":                  "F",
    "images_needing_update":  1
  }
}
```

> **⚠️ OCR audit key inconsistency in source code:**
> When `ocr_text` is empty → `ocr_audit` has key `"np_coverage"` (int, no `_pct` suffix).
> When `ocr_text` is provided → `ocr_audit` has key `"np_coverage_pct"` (float, with `_pct` suffix).
> Always check `ocr_audit["has_ocr_text"]` first before reading the coverage value.

---

### 4. FIELD RULES

| Field | Type | ✅/⚙️ | Default if omitted | Notes |
|-------|------|-------|-------------------|-------|
| `images` | `list[dict]` | ✅ Required | — | At least 1 image dict. Empty list `[]` produces empty reports and `average_alt_text_score=0`. |
| `images[].filename` | `str` | ✅ in each image | `"unknown"` | Used as identifier in report. |
| `images[].image_type` | `str` | ✅ in each image | `"unknown"` | Must be one of: `"main"`, `"lifestyle"`, `"infographic"`, `"video_thumb"`. Controls alt-text generation template and OCR tip inclusion. |
| `images[].alt_text` | `str` | ✅ in each image | `""` | The current alt-text string to audit. |
| `images[].ocr_text` | `str` | ✅ in each image | `""` | Text visible inside the image (infographic overlays). Leave `""` if not an infographic. |
| `noun_phrases` | `list[str]` | ⚙️ Optional | `[]` | Feed output of `Skill02.to_json()["npo"]["output_noun_phrases"]` here for best scores. |
| `product_name` | `str` | ⚙️ Optional | `"Product"` | Used as prefix in auto-generated alt-text. |
| `asin` | `str` | ⚙️ Optional | `"UNKNOWN"` | Label only. |

**Alt-text scored as generic (score forced to 0.0) if:**
Length < 40 chars OR matches patterns: `"product image N"`, `"image N"`, `"main image"`, `"front image"`, `"photo"`, `"picture"`, or a bare integer.

**Alt-text scoring formula:**
`score = (length_score × 0.3) + (np_score × 0.7)` where `length_score = min(100, len(alt_text) / 500 × 100)` and `np_score = min(100, noun_phrase_hits × 25)`.

---

### 5. VALIDATION CHECKLIST

```
[ ] images is a non-empty list of dicts
[ ] Each image dict has: "filename" (str), "image_type" (str), "alt_text" (str), "ocr_text" (str)
[ ] image_type is one of: "main", "lifestyle", "infographic", "video_thumb"
[ ] ocr_text is populated ONLY for infographic images (empty string for others)
[ ] noun_phrases ideally sourced from Skill02.to_json()["npo"]["output_noun_phrases"]
[ ] When reading ocr_audit: check has_ocr_text before reading np_coverage vs np_coverage_pct
[ ] Grade accessed via: skill.to_json()["scores"]["grade"]
[ ] Images needing fix: skill.to_json()["scores"]["images_needing_update"]
```

---
---

## SKILL 05 — A+ Knowledge Base Engineering

### 1. Skill ID and Name
- **ID:** `"05"`
- **Class:** `Skill05`
- **Import:** `from skill_05_aplus.skill_05 import Skill05`

---

### 2. INPUT JSON

```json
{
  "comparison_table": {
    "Battery Life":      { "B0EXAMPLE5": "24 Hours",  "B0COMP001": "12 Hours" },
    "Waterproof Rating": { "B0EXAMPLE5": "IPX7",       "B0COMP001": "IPX4"     },
    "Charging Speed":    { "B0EXAMPLE5": "PD 65W",     "B0COMP001": "18W"      },
    "Weight":            { "B0EXAMPLE5": "450g",        "B0COMP001": "600g"     },
    "Capacity":          { "B0EXAMPLE5": "20000mAh",   "B0COMP001": "10000mAh" }
  },
  "modules": [
    { "type": "comparison_table", "content": "See comparison table above" },
    { "type": "faq",              "content": "Q: Is it waterproof? A: Yes, IPX7. Q: Airplane safe? A: Yes, under 100Wh." },
    { "type": "lifestyle_image",  "content": "" }
  ],
  "product_claims": [
    "Long battery life",
    "Fast charging technology",
    "IPX7 waterproof",
    "PD 65W output for laptops",
    "20000mAh capacity"
  ],
  "asin": "B0EXAMPLE5"
}
```

---

### 3. OUTPUT JSON

```json
{
  "skill_id": "05",
  "skill_name": "A+ Knowledge Base Engineering",
  "asin": "B0EXAMPLE5",
  "comparison_table_audit": {
    "has_table": true,
    "semantic_headers_found":   ["battery life", "waterproof rating", "charging speed", "weight", "capacity"],
    "semantic_headers_missing": ["dimensions", "compatibility", "warranty", "material", "output power"],
    "semantic_header_score":    41.7,
    "specific_data_ratio":      100.0,
    "recommendations": [
      "Add these semantic headers: dimensions, compatibility, warranty"
    ]
  },
  "module_audit": {
    "module_count":            3,
    "module_types":            ["comparison_table", "faq", "lifestyle_image"],
    "has_knowledge_base_module": true,
    "missing_kb_modules":      ["technical_specs"]
  },
  "hallucination_risk": {
    "vague_claims_found":     ["long battery life", "fast charging"],
    "specific_data_anchors":  3,
    "hallucination_risk_score": 65.0,
    "risk_level":             "MEDIUM"
  },
  "scores": {
    "composite_aplus_score": 66.7,
    "grade":                 "C"
  }
}
```

---

### 4. FIELD RULES

| Field | Type | ✅/⚙️ | Default if omitted | Notes |
|-------|------|-------|-------------------|-------|
| `comparison_table` | `dict` | ⚙️ Optional | `{}` | Format: `{header_string: {asin_string: value_string}}`. Empty dict gives `has_table: false` and `semantic_header_score: 0`. |
| `modules` | `list[dict]` | ⚙️ Optional | `[]` | Each dict: `{"type": str, "content": str}`. `type` is matched (case-insensitive, substring) against recognized KB types. |
| `modules[].type` | `str` | ✅ in each module | — | Knowledge-base types recognized: `"faq"`, `"technical_specs"`, `"comparison_table"`, `"specification_chart"`, `"q&a"`, `"detailed_description"`, `"product_description_text"`. Other types count as modules but not KB. |
| `modules[].content` | `str` | ✅ in each module | `""` | Content scanned for specific data anchors in hallucination risk scoring. |
| `product_claims` | `list[str]` | ⚙️ Optional | `[]` | Key claims from title/bullets. Scanned for vague terms and numeric anchors. |
| `asin` | `str` | ⚙️ Optional | `"UNKNOWN"` | Label only. |

**12 recognized semantic comparison table headers:**
`"waterproof rating"`, `"battery life"`, `"charging speed"`, `"weight"`, `"dimensions"`, `"compatibility"`, `"warranty"`, `"material"`, `"capacity"`, `"output power"`, `"certifications"`, `"operating temperature"`

**Vague terms that raise hallucination risk:**
`"long battery life"`, `"fast charging"`, `"lightweight"`, `"durable"`, `"high quality"`, `"premium"`, `"advanced"`, `"powerful"`, `"efficient"`, `"smart"`, `"easy to use"`, `"compact"`

**Specific data pattern (anchors that lower hallucination risk):**
Numbers followed by units: `mAh`, `Wh`, `W`, `V`, `A`, `kg`, `lbs`, `oz`, `g`, `h`, `min`, `hrs`, `hours`, `inches`, `cm`, `mm`, `IPX*`, `MIL-STD`, `°C`, `°F`

---

### 5. VALIDATION CHECKLIST

```
[ ] comparison_table format: {"Header Name": {"ASIN1": "value", "ASIN2": "value"}}
[ ] Header names should contain recognized semantic keywords (battery life, waterproof rating, etc.)
[ ] Table values should contain numbers + units (e.g., "24 Hours", "IPX7", "450g") not vague text
[ ] modules: each dict has "type" (str) and "content" (str)
[ ] At least one module type matches KB keywords (faq, technical_specs, comparison_table)
[ ] product_claims: replace vague phrases with specific data (e.g., "24 Hours" not "Long battery life")
[ ] Hallucination risk: skill.to_json()["hallucination_risk"]["risk_level"] — aim for "LOW"
[ ] Grade accessed via: skill.to_json()["scores"]["grade"]
```

---
---

## SKILL 06 — Mobile Habitat Optimization

### 1. Skill ID and Name
- **ID:** `"06"`
- **Class:** `Skill06`
- **Import:** `from skill_06_mobile.skill_06 import Skill06`

---

### 2. INPUT JSON

```json
{
  "title": "Power Bank 20000mAh Fast Charging USB-C PD 65W — Portable Charger for Camping Travel iPhone Android",
  "videos": [
    {
      "title":        "Stop struggling with dead batteries while camping",
      "description":  "Solve your power problem with our 20000mAh power bank. Finally enjoy all-day power anywhere you go.",
      "aspect_ratio": "9:16"
    },
    {
      "title":        "Product overview and features",
      "description":  "Check out the great features of our portable power bank.",
      "aspect_ratio": "16:9"
    }
  ],
  "category": "Electronics",
  "asin":     "B0EXAMPLE6"
}
```

---

### 3. OUTPUT JSON

```json
{
  "skill_id": "06",
  "skill_name": "Mobile Habitat Optimization",
  "asin": "B0EXAMPLE6",
  "title_analysis": {
    "original_title":              "Power Bank 20000mAh Fast Charging USB-C PD 65W — Portable Charger for Camping Travel iPhone Android",
    "char_count":                  97,
    "rufus_chat_preview":          "Power Bank 20000mAh Fast Charging USB-C PD 65W — Portable Char…",
    "opens_with_category":         true,
    "category_keywords_in_first_70": ["power bank"],
    "filler_openers_detected":     [],
    "optimized_title_suggestion":  "",
    "title_score":                 90.0
  },
  "video_analysis": [
    {
      "video_title":      "Stop struggling with dead batteries while camping",
      "aspect_ratio":     "9:16",
      "is_vertical_9x16": true,
      "has_problem_arc":  true,
      "has_solution_arc": true,
      "has_ps_arc":       true,
      "video_score":      90.0,
      "recommendations":  []
    },
    {
      "video_title":      "Product overview and features",
      "aspect_ratio":     "16:9",
      "is_vertical_9x16": false,
      "has_problem_arc":  false,
      "has_solution_arc": false,
      "has_ps_arc":       false,
      "video_score":      0.0,
      "recommendations":  [
        "Convert to 9:16 vertical format (mobile-first for Rufus carousel)",
        "Open video with a customer pain point / problem scenario",
        "Close video with clear solution narrative and product CTA"
      ]
    }
  ],
  "scores": {
    "title_score":           90.0,
    "video_avg_score":       45.0,
    "composite_mobile_score": 72.0,
    "grade":                 "C"
  }
}
```

---

### 4. FIELD RULES

| Field | Type | ✅/⚙️ | Default if omitted | Notes |
|-------|------|-------|-------------------|-------|
| `title` | `str` | ✅ Required | — | Passed through `sanitize_text()`. Must not be empty for meaningful analysis. |
| `videos` | `list[dict]` | ⚙️ Optional | `[]` | When omitted, `video_avg_score` defaults to `50.0` in composite calculation. |
| `videos[].title` | `str` | ✅ in each video | `""` | Video title. Scanned for problem/solution keywords. |
| `videos[].description` | `str` | ✅ in each video | `""` | Video description. Combined with title for arc detection. |
| `videos[].aspect_ratio` | `str` | ✅ in each video | `"16:9"` | `"9:16"` or `"vertical"` → +50 pts. Any other value → 0 pts for vertical. |
| `category` | `str` | ⚙️ Optional | `""` | Used in `optimized_title_suggestion` when title doesn't open with a category keyword. |
| `asin` | `str` | ⚙️ Optional | `"UNKNOWN"` | Label only. |

**Category keywords recognized in first 70 chars of title (for `opens_with_category`):**
`"power bank"`, `"phone charger"`, `"laptop stand"`, `"bluetooth speaker"`, `"wireless earbuds"`, `"portable battery"`, `"usb hub"`, `"desk lamp"`, `"keyboard"`, `"mouse"`, `"webcam"`, `"monitor"`, `"case"`, `"cover"`, `"bag"`

**Filler openers that penalize title score (-30 pts):**
`"introducing"`, `"new!"`, `"hot!"`, `"sale!"`, `"best seller"`, `"our amazing"`, `"you will love"`

**Title score formula:**
Start at 100 → -30 if filler opener → -25 if no category keyword in first 70 chars → -20 if title > 200 chars → -10 if title > 120 chars (but ≤ 200).

**Video score formula:**
0 base → +50 if `aspect_ratio` is `"9:16"` or `"vertical"` → +40 if both problem AND solution keywords present → +20 if only solution keywords present (no problem). Max 100.

**Problem keywords scanned:** `"struggle"`, `"problem"`, `"issue"`, `"can't"`, `"don't"`, `"limited"`, `"stuck"`, `"always"`

**Solution keywords scanned:** `"solve"`, `"solution"`, `"now you can"`, `"finally"`, `"easy"`, `"perfect"`, `"works"`, `"enjoy"`

---

### 5. VALIDATION CHECKLIST

```
[ ] title is a non-empty string
[ ] Title starts with a category keyword (power bank, portable battery, etc.) for best score
[ ] Title does NOT start with filler words (introducing, new!, best seller, etc.)
[ ] Title length is ideally 70–120 chars; max 200 chars
[ ] Each video dict has: "title" (str), "description" (str), "aspect_ratio" (str)
[ ] aspect_ratio must be exactly "9:16" or "vertical" for vertical scoring
[ ] Video description must contain problem keywords AND solution keywords for full +40 arc bonus
[ ] Rufus preview (first 70 chars): skill.to_json()["title_analysis"]["rufus_chat_preview"]
[ ] Grade accessed via: skill.to_json()["scores"]["grade"]
```

---
---

## SKILL 07 — Semantic Integrity & Anti-Optimization Check

### 1. Skill ID and Name
- **ID:** `"07"`
- **Class:** `Skill07`
- **Import:** `from skill_07_integrity.skill_07 import Skill07`

---

### 2. INPUT JSON

```json
{
  "title": "Power Bank 20000mAh USB-C Fast Charging — 3 Pack Power Bank IPX5",
  "bullets": [
    "Best seller portable power bank with fast charging technology for all your devices",
    "Top rated power bank — power bank for travel, camping, and power bank for iPhone",
    "Buy now and enjoy long battery life with our world-class portable charger power bank"
  ],
  "backend_attrs": {
    "quantity":          "3",
    "waterproof_rating": "IPX5",
    "battery_capacity":  "20000mAh",
    "item_dimensions":   "6.3 inches"
  },
  "negative_review_themes": [
    "cheap",
    "stopped working",
    "misleading"
  ],
  "asin": "B0EXAMPLE7"
}
```

---

### 3. OUTPUT JSON

```json
{
  "skill_id": "07",
  "skill_name": "Semantic Integrity & Anti-Optimization Check",
  "asin": "B0EXAMPLE7",
  "compliance_report": {
    "keyword_stuffing": {
      "stuffed_phrases": {
        "power bank": 5,
        "power bank for": 3
      },
      "stuffed_count":    2,
      "legacy_seo_phrases": ["best seller", "buy now", "top rated"],
      "legacy_count":     3
    },
    "backend_conflicts": [
      {
        "claim":         "3 pack",
        "claim_type":    "quantity",
        "backend_value": "3",
        "severity":      "CRITICAL",
        "fix":           "Update backend 'quantity' to match title claim '3'"
      },
      {
        "claim":         "ipx5",
        "claim_type":    "waterproof_rating",
        "backend_value": "IPX5",
        "severity":      "CRITICAL",
        "fix":           "Update backend 'waterproof_rating' to match title claim 'ipx5'"
      }
    ],
    "conflict_count": 2,
    "unaddressed_negative_themes": [
      {
        "theme":          "cheap",
        "recommendation": "Add a bullet about material certification or manufacturing standard"
      },
      {
        "theme":          "stopped working",
        "recommendation": "Add warranty / reliability claim with proof (e.g., '50,000-cycle tested')"
      },
      {
        "theme":          "misleading",
        "recommendation": "Audit title claims vs backend for exact quantity/spec consistency"
      }
    ]
  },
  "sanitized_listing": {
    "sanitized_title":   "Power Bank 20000mAh USB-C Fast Charging — 3 Pack Power Bank IPX5",
    "sanitized_bullets": [
      "portable power bank with fast charging technology for all your devices",
      " rated power bank — power bank for travel, camping, and power bank for iPhone",
      " and enjoy long battery life with our world-class portable charger power bank"
    ],
    "phrases_removed": ["best seller", "buy now", "top rated", "power bank", "power bank for"]
  },
  "scores": {
    "integrity_score": 21.0,
    "grade":           "F",
    "issues_found":    7
  }
}
```

---

### 4. FIELD RULES

| Field | Type | ✅/⚙️ | Default if omitted | Notes |
|-------|------|-------|-------------------|-------|
| `title` | `str` | ✅ Required | — | Passed through `sanitize_text()`. Combined with bullets for stuffing detection. |
| `bullets` | `list[str]` | ⚙️ Optional | `[]` | Each bullet passed through `sanitize_text()`. Combined with title for stuffing check. |
| `backend_attrs` | `dict` | ⚙️ Optional | `{}` | Key names MUST match exactly for conflict detection (see table below). |
| `negative_review_themes` | `list[str]` | ⚙️ Optional | `[]` | Strings from `Skill03.to_json()["ugc_mining"]["sentiment"]["recurring_negative_keywords"].keys()`. |
| `asin` | `str` | ⚙️ Optional | `"UNKNOWN"` | Label only. |

**`backend_attrs` keys recognized for conflict detection:**

| Key in `backend_attrs` | Title pattern matched | Example |
|------------------------|----------------------|---------|
| `"quantity"` | `N pack` | `"3 pack"` → checks `backend_attrs["quantity"]` contains `"3"` |
| `"item_quantity"` | `N pcs` / `N pieces` / `N count` | `"6 pcs"` |
| `"item_dimensions"` | `N in` / `N inch` / `N cm` | `"6.3 inches"` |
| `"waterproof_rating"` | `IPX5` / `IP68` (any IP pattern) | `"IPX5"` |
| `"battery_capacity"` | `N mAh` | `"20000mAh"` |

**Conflict severity rules:**
- Backend key exists but value doesn't match title claim → `"CRITICAL"` (-15 pts)
- Backend key is missing entirely → `"HIGH"` (-8 pts)

**Integrity score formula:**
`100 - (stuffed_count × 5) - (legacy_count × 8) - (CRITICAL_conflicts × 15) - (HIGH_conflicts × 8) - (unaddressed_themes × 6)`

**Legacy SEO phrases that trigger penalty:**
`"best seller"`, `"#1 best"`, `"top rated"`, `"amazon choice"`, `"limited time"`, `"buy now"`, `"order today"`, `"free shipping"`, `"click here"`, `"check our store"`, `"visit our brand"`, `"see more products"`

---

### 5. VALIDATION CHECKLIST

```
[ ] title is a non-empty string
[ ] bullets is a list of strings (empty list is acceptable)
[ ] backend_attrs uses exact key names: "quantity", "item_quantity", "item_dimensions",
    "waterproof_rating", "battery_capacity" — for conflict detection to work
[ ] backend_attrs values are strings (even numeric values like "3" or "20000mAh")
[ ] negative_review_themes: list of strings sourced from Skill03 output
[ ] No filler/legacy phrases in title or bullets before calling (or note they will be flagged)
[ ] Title claims for quantity/size/waterproof MUST match backend_attrs values exactly
[ ] Sanitized listing: skill.to_json()["sanitized_listing"]["sanitized_title"]
[ ] Compliance report: skill.to_json()["compliance_report"]
[ ] Grade accessed via: skill.to_json()["scores"]["grade"]
```

---

## GRADING REFERENCE

All 7 skills use the same `score_to_grade()` function from `utils/helpers.py`:

| Score Range | Grade | Meaning |
|-------------|-------|---------|
| ≥ 90 | **A** | Excellent — Rufus-ready |
| ≥ 75 | **B** | Good — minor improvements needed |
| ≥ 60 | **C** | Acceptable — notable gaps |
| ≥ 40 | **D** | Poor — significant issues |
| < 40 | **F** | Failing — major rework required |

---

## PIPELINE CHAINING REFERENCE

The recommended data flow between skills:

```
Skill01.injection_payload
    └──→ Skill07.backend_attrs

Skill02.npo.output_noun_phrases
    └──→ Skill04.noun_phrases

Skill03.ugc_mining.sentiment.recurring_negative_keywords.keys()
    └──→ Skill07.negative_review_themes

Skill02.copy.rag_ready_bullets
    └──→ Skill07.bullets
```

```python
import sys
sys.path.insert(0, "/path/to/016-rufus-skills")

from skill_01_taxonomy.skill_01   import Skill01
from skill_02_npo.skill_02        import Skill02
from skill_03_ugc.skill_03        import Skill03
from skill_04_visual_seo.skill_04 import Skill04
from skill_05_aplus.skill_05      import Skill05
from skill_06_mobile.skill_06     import Skill06
from skill_07_integrity.skill_07  import Skill07

asin = "B0EXAMPLE"

s1 = Skill01(clr=my_clr, spec=my_spec, btg=my_btg, asin=asin).run()
s2 = Skill02(keywords=my_keywords, bullets=my_bullets, title=my_title, asin=asin).run()
s3 = Skill03(reviews=my_reviews, product_context=my_context, asin=asin).run()
s4 = Skill04(
    images=my_images,
    noun_phrases=s2.to_json()["npo"]["output_noun_phrases"],   # ← from Skill02
    asin=asin
).run()
s5 = Skill05(comparison_table=my_table, modules=my_modules, asin=asin).run()
s6 = Skill06(title=my_title, videos=my_videos, asin=asin).run()
s7 = Skill07(
    title=my_title,
    bullets=s2.to_json()["copy"]["rag_ready_bullets"],         # ← from Skill02
    backend_attrs=s1.to_json()["injection_payload"],           # ← from Skill01
    negative_review_themes=list(                               # ← from Skill03
        s3.to_json()["ugc_mining"]["sentiment"]["recurring_negative_keywords"].keys()
    ),
    asin=asin,
).run()
```
