# Skill 02 — Noun Phrase Optimization (NPO) & RAG-Ready Copy

## Skill Name
**Noun Phrase Optimization (NPO) & RAG-Ready Copy**

## Goal
Transition from "Keyword Stuffing" to "Semantic Logic" that an LLM can easily retrieve (RAG) by rewriting copy using the NPO Formula.

## Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `keywords` | `list[str]` | Yes | Raw keywords from research |
| `bullets` | `list[str]` | Yes | Existing bullet points to optimize |
| `topic_clusters` | `dict[str, list[str]]` | No | Intent clusters: {intent: [queries]} |
| `title` | `str` | No | Current product title |
| `asin` | `str` | No | ASIN label |

## Output Format

```json
{
  "skill_id": "02",
  "npo": {
    "input_keywords": ["fast charge"],
    "output_noun_phrases": ["Fast-charge technology that maximizes efficiency in everyday use"],
    "phrase_count": 1
  },
  "copy": {
    "rag_ready_bullets": ["Designed for fast-charge technology..."],
    "title": { "original": "...", "optimized": "...", "char_count": 120, "truncated_preview_70": "..." }
  },
  "scores": { "semantic_density": { "density_label": "HIGH" }, "grade": "A" }
}
```

## NPO Formula

```
[Noun/Feature] + [Benefit] + [Context]
Input:  "portable charger for camping"
Output: "Portable charger that delivers superior performance for camping"
```

## Logic Rules

- **Connector Rotation**: Each bullet starts with a different opener (Designed for / Built for / Ideal when...)
- **Filler Stripping**: Remove "amazing", "incredible", "best-in-class" without proof
- **First-70 Rule**: Title leading 70 chars must contain Category + Core Benefit
- **Density Scoring**: High ≥ 3 noun phrases/bullet | Medium = 2 | Low ≤ 1

## Example Usage

```python
from skill_02_npo.skill_02 import Skill02

skill = Skill02(
    keywords=["fast charge", "portable charger for camping"],
    bullets=["Amazing fast charging", "Best-in-class battery"],
    topic_clusters={"charging": ["How fast does it charge?", "What wattage?"]},
    title="Portable Power Bank 20000mAh Fast Charging USB-C",
    asin="B0EXAMPLE2"
)
result = skill.to_json()
print(result["copy"]["rag_ready_bullets"])
```

## How to Import from Other Projects

```python
import sys; sys.path.insert(0, "/path/to/016-rufus-skills")
from skill_02_npo.skill_02 import Skill02   # ✅
```
