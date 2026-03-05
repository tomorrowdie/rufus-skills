# Skill 04 — Multimodal Visual SEO Validation

## Skill Name
**Multimodal Visual SEO Validation**

## Goal
Provide clear visual data for Amazon's Computer Vision (CV) and OCR systems to read and verify product details.

## Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `images` | `list[dict]` | Yes | Image records: `{"filename", "alt_text", "ocr_text", "image_type"}` |
| `noun_phrases` | `list[str]` | No | Target noun phrases (from Skill02) |
| `product_name` | `str` | No | Product name for alt-text generation |
| `asin` | `str` | No | ASIN label |

## Output Format

```json
{
  "skill_id": "04",
  "image_reports": [{
    "filename": "main_image.jpg",
    "image_type": "main",
    "alt_text": { "original": "product image 1", "optimized": "...", "score": {"is_generic": true, "score": 0} },
    "ocr_audit": { "np_coverage_pct": 75.0, "missing_phrases": ["portable charger"] }
  }],
  "scores": { "average_alt_text_score": 62.0, "grade": "C" }
}
```

## Logic Rules

- **Generic Detection**: Alt-text matching patterns like "product image 1", "photo", "image 2" = generic (score 0)
- **Alt-Text Formula**: `{product_name} {feature} — {action_context} showing {scene_context}`
- **OCR Coverage**: % of target noun phrases found in infographic OCR text
- **Score**: `length_score * 0.3 + noun_phrase_score * 0.7`

## Example Usage

```python
from skill_04_visual_seo.skill_04 import Skill04

skill = Skill04(
    images=[{"filename": "main.jpg", "image_type": "main", "alt_text": "product image", "ocr_text": ""}],
    noun_phrases=["portable charger", "fast charge"],
    product_name="Portable Power Bank",
    asin="B0EXAMPLE4"
)
result = skill.to_json()
```

## How to Import from Other Projects

```python
import sys; sys.path.insert(0, "/path/to/016-rufus-skills")
from skill_04_visual_seo.skill_04 import Skill04
```
