# Skill 06 — Mobile Habitat Optimization

## Skill Name
**Mobile Habitat Optimization**

## Goal
Dominate the "Rufus Habitat" on mobile, where the AI chat interface occupies 50% of the screen, by optimizing title truncation and vertical video strategy.

## Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `title` | `str` | Yes | Current product title |
| `videos` | `list[dict]` | No | Video records: `{"title", "description", "aspect_ratio"}` |
| `category` | `str` | No | Product category (e.g., "Electronics") |
| `asin` | `str` | No | ASIN label |

## Output Format

```json
{
  "skill_id": "06",
  "title_analysis": {
    "rufus_chat_preview": "Portable Power Bank 20000mAh — Fast Charge PD 65W f…",
    "opens_with_category": true,
    "filler_openers_detected": ["introducing"],
    "optimized_title_suggestion": "Power Bank — Portable 20000mAh PD 65W Fast Charge",
    "title_score": 75.0
  },
  "video_analysis": [{ "is_vertical_9x16": true, "has_ps_arc": true, "video_score": 90.0 }],
  "scores": { "composite_mobile_score": 80.0, "grade": "B" }
}
```

## Logic Rules

- **First-70-Characters Rule**: Title must lead with `[Category] + [Core Benefit]` visible before truncation
- **Filler Penalty**: Titles opening with "Introducing", "New!", "Best seller" lose 30 points
- **Video Vertical**: 9:16 aspect ratio = +50 points (mobile-first for Rufus carousel)
- **Problem→Solution Arc**: Problem keywords + Solution keywords both present = +40 points

## Example Usage

```python
from skill_06_mobile.skill_06 import Skill06

skill = Skill06(
    title="Introducing Our Amazing Portable Power Bank 20000mAh...",
    videos=[{"title": "Stop struggling with dead batteries", "description": "Solve your power problem...", "aspect_ratio": "9:16"}],
    category="Electronics",
    asin="B0EXAMPLE6"
)
result = skill.to_json()
```

## How to Import from Other Projects

```python
import sys; sys.path.insert(0, "/path/to/016-rufus-skills")
from skill_06_mobile.skill_06 import Skill06
```
