# Skill 05 — A+ Knowledge Base Engineering

## Skill Name
**A+ Knowledge Base Engineering**

## Goal
Transform A+ content from a design showcase into a technical manual for AI indexing, lowering Rufus's "Hallucination Risk" during product recommendations.

## Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `comparison_table` | `dict` | No | `{header: {asin: value}}` |
| `modules` | `list[dict]` | No | A+ modules: `{"type": str, "content": str}` |
| `product_claims` | `list[str]` | No | Key claims from title/bullets |
| `asin` | `str` | No | ASIN label |

## Output Format

```json
{
  "skill_id": "05",
  "comparison_table_audit": {
    "semantic_header_score": 80.0,
    "specific_data_ratio": 100.0,
    "recommendations": ["Add semantic headers: operating temperature, certifications"]
  },
  "hallucination_risk": { "vague_claims_found": ["long battery life"], "risk_level": "MEDIUM" },
  "scores": { "composite_aplus_score": 85.0, "grade": "B" }
}
```

## Logic Rules

- **Semantic Headers**: 12 recognized headers (battery life, waterproof rating, charging speed…)
- **Specific Data**: Values with units (mAh, W, h, IPX, g, cm) count as "anchored"
- **Hallucination Risk**: `(1 - vague_ratio * 0.6) * 100 * (0.4 + anchor_ratio * 0.6)`
- **Knowledge Base Modules**: FAQ, technical_specs, comparison_table = fallback source of truth

## Example Usage

```python
from skill_05_aplus.skill_05 import Skill05

skill = Skill05(
    comparison_table={"Battery Life": {"B001": "24 Hours", "B002": "12 Hours"}},
    modules=[{"type": "faq", "content": "Q: Waterproof? A: Yes, IPX7"}],
    product_claims=["Long battery life", "IPX7 waterproof"],
    asin="B0EXAMPLE5"
)
result = skill.to_json()
```

## How to Import from Other Projects

```python
import sys; sys.path.insert(0, "/path/to/016-rufus-skills")
from skill_05_aplus.skill_05 import Skill05
```
