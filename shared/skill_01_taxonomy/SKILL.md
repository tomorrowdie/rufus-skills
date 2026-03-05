# Skill 01 — Structured Taxonomy & Attribute Injection

## Skill Name
**Structured Taxonomy & Attribute Injection**

## Goal
Eliminate "Information Uncertainty" by bridging the gap between raw product data and the Amazon Knowledge Graph through rigorous backend attribute standardization and injection.

## Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `clr`     | `dict` | Yes | Category Listing Report — key/value pairs of backend attributes |
| `spec`    | `dict` | Yes | Product Specification Sheet — technical attributes |
| `btg`     | `dict` | Yes | Amazon Browse Tree Guide entry (category, node_id, node_path) |
| `asin`    | `str`  | No  | Amazon ASIN for labelling output (default: "UNKNOWN") |

## Output Format

```json
{
  "skill_id": "01",
  "skill_name": "Structured Taxonomy & Attribute Injection",
  "asin": "B0EXAMPLE1",
  "audit": {
    "null_fields": { "batteries_included": "MISSING" },
    "null_count": 1,
    "standardized_values": { "color_name": "Navy Blue" },
    "knowledge_graph_mapping": { "Camping": ["Outdoor", "Forest", "Portable Power"] }
  },
  "injection_payload": { "color_name": "Navy Blue", "capacity_mah": 20000 },
  "scores": { "completeness_pct": 83.3, "grade": "B", "high_confidence_tokens": 9 }
}
```

## NPO Formula / Logic Rules

- **Death of Null**: Flag every empty attribute. `completeness_pct = filled/total * 100`
- **Standardization**: Map creative names → Amazon Standard Values (color, material)
- **Graph Map**: `specific_use` keywords → Knowledge Graph node chains
- **Grading**: A≥90 | B≥75 | C≥60 | D≥40 | F<40

## Example Usage

```python
from skill_01_taxonomy.skill_01 import Skill01

skill = Skill01(
    clr={"color_name": "Midnight Ocean", "specific_use": "Camping"},
    spec={"capacity_mah": 20000},
    btg={"category": "Electronics > Portable Power", "node_id": "2407749011", "node_path": "..."},
    asin="B0EXAMPLE1"
)
result = skill.to_json()
print(result["scores"]["grade"])  # "A" or "B"
```

## How to Import from Other Projects

```python
import sys
sys.path.insert(0, "/path/to/016-rufus-skills")
from skill_01_taxonomy.skill_01 import Skill01   # ✅
```
