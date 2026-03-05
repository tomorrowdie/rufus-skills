# CLAUDE.md — Rufus Skills Project

## Project Overview
This repo powers AI-driven Amazon listing optimization across multiple marketplaces.
Skills are marketplace-agnostic. Data is marketplace-specific.

---

## Repo Structure Rules

### Marketplace Folders
| Folder        | Marketplace ID   | Language Tag |
|---------------|-----------------|--------------|
| `markets/us/` | ATVPDKIKX0DER   | en_US        |
| `markets/uk/` | A1F83G8C2ARO7P  | en_GB        |
| `markets/jp/` | A1VC38T7YXB528  | ja_JP        |
| `markets/ca/` | A2EUQ1WTGCTBG2  | en_CA        |
| `markets/au/` | A39IBJ37TRP1C6  | en_AU        |

> **Not supported:** `mx` (Mexico) and `cn` (China) are excluded from v1 scope.

### Catalog Path Convention
Amazon category path → snake_case nested folders under `markets/{market}/catalog/`

Example:
```
Cell Phones & Accessories > Accessories > Chargers & Power Adapters > Portable Power Banks
→ markets/us/catalog/cell_phones_accessories/accessories/chargers_power_adapters/portable_power_banks/
```

### Every category leaf folder has exactly two subfolders:
```
portable_power_banks/
  raw/     ← drop Amazon .xlsm flat file templates here
  data/    ← auto-generated CSVs go here (never edit manually)
```

---

## Parse Catalog Task
When a `.xlsm` file is placed in any `raw/` folder, run the parser:

```bash
python tools/parse_catalog.py --input <path_to_xlsm>
```

The parser will:
1. Read **Template sheet** — Row 2 (human labels) + Row 3 (API field names)
2. Read **Valid Values sheet** — map each field to its allowed values
3. Collapse numbered repeated fields: `special_features1..5` → one row with `max_count=5`
4. Output two files to the sibling `data/` folder:
   - `fields.csv` — label, field_name, section, max_count
   - `valid_values.csv` — field_name, valid_value
5. **Never overwrite** existing CSVs — backup with date suffix first

> `tools/parse_catalog.py` is currently a stub. Full implementation is Task 2a in MEMORY.md.

---

## Skills Read From
```python
# Pattern each skill uses to load its data
fields_path = f"markets/{market}/catalog/{category_path}/data/fields.csv"
valid_path  = f"markets/{market}/catalog/{category_path}/data/valid_values.csv"
```

---

## Skills Location
All 9 skills live in `shared/` — they do NOT contain marketplace-specific data.

```
shared/
  skill_01_taxonomy/       ✅ migrated
  skill_02_npo/            ✅ migrated
  skill_03_ugc/            ✅ migrated
  skill_04_visual_seo/     ✅ migrated
  skill_05_aplus/          ✅ migrated
  skill_06_mobile/         ✅ migrated (v2.0 — 8 modules)
  skill_07_integrity/      ✅ migrated
  skill_08_report/         ✅ present
  skill_09_infographic/    ✅ present
  utils/
```

---

## Do Not
- Do not hardcode field names inside skill code — always read from CSV
- Do not edit files inside `data/` folders manually
- Do not commit `.xlsm` files — they are in `.gitignore`
- Do not mix marketplace data across market folders
- Do not add new markets not listed in the Marketplace Folders table above
