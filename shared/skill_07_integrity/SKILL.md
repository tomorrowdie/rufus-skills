# Skill 07 — Semantic Integrity & Anti-Optimization Check

## Skill Name
**Semantic Integrity & Anti-Optimization Check**

## Goal
Protect the listing's "Trust Score" by removing keyword stuffing, resolving title/backend conflicts, and addressing negative review themes before Rufus bakes them into product summaries.

## Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `title` | `str` | Yes | Product title |
| `bullets` | `list[str]` | No | Bullet points |
| `backend_attrs` | `dict` | No | Backend attribute key/values (from Skill01) |
| `negative_review_themes` | `list[str]` | No | Top negative keywords (from Skill03) |
| `asin` | `str` | No | ASIN label |

## Output Format

```json
{
  "skill_id": "07",
  "compliance_report": {
    "keyword_stuffing": { "stuffed_phrases": {"power bank": 4}, "legacy_seo_phrases": ["best seller"] },
    "backend_conflicts": [{ "claim": "3 pack", "backend_value": "1", "severity": "CRITICAL", "fix": "..." }],
    "unaddressed_negative_themes": [{ "theme": "cheap", "recommendation": "Add material certification bullet" }]
  },
  "sanitized_listing": { "sanitized_title": "...", "sanitized_bullets": [...] },
  "scores": { "integrity_score": 72.0, "grade": "C", "issues_found": 4 }
}
```

## Logic Rules

- **Stuffing Threshold**: Any bigram/trigram appearing ≥ 3× in full copy = stuffed
- **Legacy SEO**: "best seller", "#1 best", "buy now", "click here" = harmful phrases
- **Conflict Detection**: Title claims for quantity/size/waterproof must match backend values
- **Integrity Score**: `100 - (stuffed*5) - (legacy*8) - (conflicts*15) - (unaddressed*6)`

## Example Usage

```python
from skill_07_integrity.skill_07 import Skill07

skill = Skill07(
    title="Power Bank 3 Pack Best Seller Power Bank Power Bank",
    bullets=["Best seller power bank for all devices"],
    backend_attrs={"quantity": "1"},
    negative_review_themes=["cheap", "stopped working"],
    asin="B0EXAMPLE7"
)
result = skill.to_json()
print(result["compliance_report"]["backend_conflicts"])
```

## How to Import from Other Projects

```python
import sys; sys.path.insert(0, "/path/to/016-rufus-skills")
from skill_07_integrity.skill_07 import Skill07
```
