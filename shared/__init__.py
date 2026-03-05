"""
Rufus Optimization Skills Library
==================================
Universal, standalone library of 7 Amazon Rufus optimization skills.

Version: 1.0.0
Author:  John / Anergy Academy

Quick Start:
    from rufus_skills import Skill01, Skill02, Skill03, Skill04, Skill05, Skill06, Skill07

    # Example: Run all 7 skills in sequence
    s1 = Skill01(clr={...}, spec={...}, btg={...}, asin="B0XYZ").run()
    s2 = Skill02(keywords=[...], bullets=[...]).run()
    s3 = Skill03(reviews=[...]).run()
    s4 = Skill04(images=[...], noun_phrases=s2.to_json()["npo"]["output_noun_phrases"]).run()
    s5 = Skill05(comparison_table={...}, modules=[...]).run()
    s6 = Skill06(title="...").run()
    s7 = Skill07(title="...", bullets=[...], backend_attrs=s1.to_json()["injection_payload"]).run()

Compatibility:
    - Python 3.9+
    - n8n (subprocess or HTTP API call)
    - Claude Code, Open Claude, any Python AI agent
    - Direct CLI: python skill_0X.py --input data.json --output result.json
"""

from skill_01_taxonomy.skill_01 import Skill01
from skill_02_npo.skill_02 import Skill02
from skill_03_ugc.skill_03 import Skill03
from skill_04_visual_seo.skill_04 import Skill04
from skill_05_aplus.skill_05 import Skill05
from skill_06_mobile.skill_06 import Skill06
from skill_07_integrity.skill_07 import Skill07

__version__ = "1.0.0"
__author__ = "John / Anergy Academy"

__all__ = [
    "Skill01",
    "Skill02",
    "Skill03",
    "Skill04",
    "Skill05",
    "Skill06",
    "Skill07",
]
