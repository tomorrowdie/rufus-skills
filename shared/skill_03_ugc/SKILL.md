# Skill 03 — UGC Ground Truth Mining & Q&A Seeding

## Skill Name
**UGC Ground Truth Mining & Q&A Seeding**

## Goal
Use User-Generated Content (UGC) as "Ground Truth" to validate product claims and seed the Q&A section with definitive proof nodes for Rufus indexing.

## Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `reviews` | `list[dict]` | Yes | Customer reviews: `{"text": str, "rating": int}` |
| `competitor_qas` | `list[dict]` | No | Competitor Q&A pairs: `{"question": str, "answer": str}` |
| `product_context` | `dict` | No | Metadata: `{"waterproof_rating", "warranty_months", "charge_hours"}` |
| `asin` | `str` | No | ASIN label |

## Output Format

```json
{
  "skill_id": "03",
  "ugc_mining": {
    "technical_questions_found": ["Is it allowed on airplanes?"],
    "sentiment": { "positive_count": 3, "negative_count": 1, "recurring_negative_keywords": {"cheap": 1} }
  },
  "qa_seeding": { "qa_pairs": [{"question": "...", "answer": "..."}], "pair_count": 6 },
  "recommendations": ["Add bullet about material certification"],
  "scores": { "qa_coverage_pct": 80.0, "grade": "B" }
}
```

## Logic Rules

- **Question Extraction**: Regex-mine reviews for "Is it…?", "How long…?", "What is…?" patterns
- **Sentiment Classification**: Rating ≤ 2 = negative; keywords like "stopped working" also flag negative
- **Q&A Seeding**: 5 standard templates (airplane, waterproof, warranty, charging time, compatibility)
- **Coverage Score**: `answered_questions / total_questions_found * 100`

## Example Usage

```python
from skill_03_ugc.skill_03 import Skill03

skill = Skill03(
    reviews=[{"text": "Does it work on airplanes?", "rating": 4}],
    product_context={"waterproof_rating": "IPX5", "warranty_months": 18},
    asin="B0EXAMPLE3"
)
result = skill.to_json()
```

## How to Import from Other Projects

```python
import sys; sys.path.insert(0, "/path/to/016-rufus-skills")
from skill_03_ugc.skill_03 import Skill03
```
