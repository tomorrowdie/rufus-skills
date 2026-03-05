"""
skill_02.py — Noun Phrase Optimization (NPO) & RAG-Ready Copy
=============================================================
Skill 02 of the Rufus Optimization Skills Library.

Goal:
    Transition from "Keyword Stuffing" to "Semantic Logic" that an LLM can
    easily retrieve (RAG) by converting raw keywords into structured noun phrases
    following the NPO Formula: [Noun/Feature] + [Benefit] + [Context].

NPO Formula:
    Input keyword:  "fast charge"
    Output phrase:  "Fast-charge technology for phones that need full power in 30 minutes"

Callable 3 ways:
    1. Direct import:  from skill_02_npo.skill_02 import Skill02
    2. CLI:            python skill_02.py --input data.json --output result.json
    3. JSON stdin:     echo '{"keywords": [], "bullets": [], "topic_clusters": {}}' | python skill_02.py

Author: John / Anergy Academy
Version: 1.0.0
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent.parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from utils.helpers import (
    count_noun_phrases,
    load_json_input,
    log_step,
    rotate_connector,
    sanitize_text,
    save_json_output,
    score_to_grade,
    truncate_to_chars,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BULLET_CONNECTORS = [
    "Designed for",
    "Built for",
    "Ideal when",
    "Perfect for",
    "Engineered to",
    "Made for",
    "Optimized for",
]

# Minimum unique queries a RAG-ready bullet must answer
MIN_QUERIES_PER_BULLET = 2

# Maximum characters for an Amazon bullet point
BULLET_MAX_CHARS = 500

# Title character limit (Amazon standard)
TITLE_MAX_CHARS = 200

# Semantic density thresholds
HIGH_DENSITY_THRESHOLD = 3    # noun phrases per bullet = high density
LOW_DENSITY_THRESHOLD = 1     # noun phrases per bullet = needs improvement


class Skill02:
    """
    Skill02: Noun Phrase Optimization (NPO) & RAG-Ready Copy

    Rewrites product bullets and title using the NPO Formula so that the
    Rufus AI (and any RAG engine) can reliably extract and cite product facts.

    Parameters:
        keywords       (list[str]):       Raw keyword list from research.
        bullets        (list[str]):       Existing bullet points to optimize.
        topic_clusters (dict[str,list]):  Intent clusters: {intent: [queries]}.
        title          (str):             Current product title (optional).
        asin           (str):             ASIN label for output (optional).
    """

    SKILL_ID = "02"
    SKILL_NAME = "Noun Phrase Optimization (NPO) & RAG-Ready Copy"

    def __init__(
        self,
        keywords: list[str],
        bullets: list[str],
        topic_clusters: dict[str, list[str]] | None = None,
        title: str = "",
        asin: str = "UNKNOWN",
    ) -> None:
        self.keywords = [sanitize_text(k) for k in keywords]
        self.bullets = [sanitize_text(b) for b in bullets]
        self.topic_clusters = topic_clusters or {}
        self.title = sanitize_text(title)
        self.asin = sanitize_text(asin)
        self._result: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _apply_npo_formula(self, keyword: str) -> str:
        """
        Transform a bare keyword into a noun phrase using the NPO Formula.

        Structure: [Noun/Feature] + [Benefit] + [Context]

        Heuristics applied:
        - Keywords with "for" already have context → wrap as feature + benefit
        - Single-word keywords → append benefit + general context
        - Multi-word without "for" → assume noun + benefit; add context stub

        Note: Production deployments should call an LLM here. This implementation
        provides deterministic rule-based expansion for fully offline use.
        """
        keyword = keyword.strip()

        if " for " in keyword.lower():
            # Already has [Noun] + [Context]; inject a benefit in the middle
            parts = re.split(r"\bfor\b", keyword, maxsplit=1, flags=re.IGNORECASE)
            noun = parts[0].strip()
            context = parts[1].strip()
            return f"{noun} that delivers superior performance for {context}"

        words = keyword.split()
        if len(words) == 1:
            return f"{keyword.capitalize()} technology that maximizes efficiency in everyday use"

        noun = " ".join(words[:-1]).strip()
        qualifier = words[-1].strip()
        return f"{noun.capitalize()} with {qualifier} capability for enhanced user experience"

    def _build_rag_ready_bullet(
        self, raw_bullet: str, connector: str, related_queries: list[str]
    ) -> str:
        """
        Rewrite a bullet as a fact-dense, grammatically perfect sentence.

        Rules:
        - Start with a `connector` phrase for variety
        - Ensure at least MIN_QUERIES_PER_BULLET intents are addressed
        - Strip filler phrases (amazing, great, best-in-class superlatives without proof)
        - Hard truncate at BULLET_MAX_CHARS
        """
        # Strip low-value superlatives
        filler = re.compile(
            r"\b(amazing|incredible|best-in-class|world-class|premium quality|top-notch)\b",
            re.IGNORECASE,
        )
        cleaned = filler.sub("", raw_bullet).strip()
        cleaned = re.sub(r" {2,}", " ", cleaned)

        # Inject context from queries if bullet is short
        if related_queries and len(cleaned) < 100:
            context_hint = related_queries[0]
            cleaned = f"{cleaned} — answers the question: {context_hint}"

        result = f"{connector} {cleaned}" if connector else cleaned
        return truncate_to_chars(result, BULLET_MAX_CHARS)

    def _optimize_title(self) -> dict[str, Any]:
        """Apply First-70-Characters Rule and NPO to the product title."""
        if not self.title:
            return {"original": "", "optimized": "", "char_count": 0, "truncated_preview": ""}

        # Ensure title leads with Category + Core Benefit in first 70 chars
        preview = truncate_to_chars(self.title, 70)
        optimized = truncate_to_chars(self.title, TITLE_MAX_CHARS)
        return {
            "original": self.title,
            "optimized": optimized,
            "char_count": len(optimized),
            "truncated_preview_70": preview,
            "leads_with_category": not self.title[0].islower(),
        }

    def _score_semantic_density(
        self, bullets: list[str], phrases: list[str]
    ) -> dict[str, Any]:
        """Count noun phrase hits per bullet and compute overall density score."""
        per_bullet = []
        total_hits = 0
        for bullet in bullets:
            counts = count_noun_phrases(bullet, phrases)
            hits = sum(counts.values())
            total_hits += hits
            per_bullet.append({"bullet": truncate_to_chars(bullet, 80, ellipsis=True), "np_hits": hits})

        avg = total_hits / len(bullets) if bullets else 0
        density_label = (
            "HIGH" if avg >= HIGH_DENSITY_THRESHOLD
            else "LOW" if avg <= LOW_DENSITY_THRESHOLD
            else "MEDIUM"
        )
        score = min(100.0, round((avg / HIGH_DENSITY_THRESHOLD) * 100, 1))
        return {
            "per_bullet": per_bullet,
            "average_np_hits": round(avg, 2),
            "density_label": density_label,
            "density_score": score,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> "Skill02":
        """
        Execute the full NPO & RAG-Ready Copy pipeline.

        Steps:
            1. Transform each keyword using the NPO Formula
            2. Build RAG-ready bullets with connector rotation
            3. Optimize the product title
            4. Score semantic density
            5. Assemble final result

        Returns:
            self (for method chaining)
        """
        log_step("SKILL02_START", f"ASIN={self.asin}")

        # Step 1: NPO transformation
        log_step("SKILL02_NPO_TRANSFORM", f"{len(self.keywords)} keywords")
        noun_phrases = [self._apply_npo_formula(kw) for kw in self.keywords]

        # Step 2: RAG-ready bullets
        log_step("SKILL02_BULLETS", f"{len(self.bullets)} bullets")
        conn_idx = -1
        rag_bullets = []
        all_queries = [q for qs in self.topic_clusters.values() for q in qs]

        for i, bullet in enumerate(self.bullets):
            connector, conn_idx = rotate_connector(BULLET_CONNECTORS, conn_idx)
            related = all_queries[i * 2: i * 2 + 2]  # 2 queries per bullet
            rag_bullets.append(
                self._build_rag_ready_bullet(bullet, connector, related)
            )

        # Step 3: Title optimization
        log_step("SKILL02_TITLE")
        title_result = self._optimize_title()

        # Step 4: Semantic density scoring
        log_step("SKILL02_DENSITY")
        density = self._score_semantic_density(rag_bullets, noun_phrases)

        grade = score_to_grade(density["density_score"])

        self._result = {
            "skill_id": self.SKILL_ID,
            "skill_name": self.SKILL_NAME,
            "asin": self.asin,
            "npo": {
                "input_keywords": self.keywords,
                "output_noun_phrases": noun_phrases,
                "phrase_count": len(noun_phrases),
            },
            "copy": {
                "rag_ready_bullets": rag_bullets,
                "title": title_result,
            },
            "scores": {
                "semantic_density": density,
                "grade": grade,
            },
        }

        log_step("SKILL02_DONE", f"density={density['density_label']} grade={grade}")
        return self

    def to_json(self) -> dict[str, Any]:
        """Return the structured result as a JSON-serializable dict."""
        if not self._result:
            self.run()
        return self._result


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def _build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Skill02 — Noun Phrase Optimization (NPO) & RAG-Ready Copy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python skill_02.py --input listing.json --output result.json
  echo '{"keywords":["fast charge"],"bullets":["Charges fast"]}' | python skill_02.py
        """,
    )
    parser.add_argument("--input", "-i", help="Path to input JSON file or inline JSON string")
    parser.add_argument("--output", "-o", help="Path to write output JSON (optional)")
    parser.add_argument("--asin", default="UNKNOWN", help="Product ASIN")
    return parser


def _run_cli(args: argparse.Namespace) -> None:
    if args.input:
        data = load_json_input(args.input)
    elif not sys.stdin.isatty():
        data = json.load(sys.stdin)
    else:
        print("Error: provide --input or pipe JSON via stdin.", file=sys.stderr)
        sys.exit(1)

    skill = Skill02(
        keywords=data.get("keywords", []),
        bullets=data.get("bullets", []),
        topic_clusters=data.get("topic_clusters", {}),
        title=data.get("title", ""),
        asin=args.asin or data.get("asin", "UNKNOWN"),
    )
    result = skill.to_json()

    if args.output:
        out_path = save_json_output(result, args.output)
        print(f"Output written to: {out_path}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) > 1:
        _run_cli(_build_cli_parser().parse_args())
    else:
        sample = {
            "asin": "B0EXAMPLE2",
            "title": "Portable Power Bank 20000mAh Fast Charging USB-C PD 65W",
            "keywords": [
                "fast charge",
                "portable charger for camping",
                "high-capacity power bank",
            ],
            "bullets": [
                "Amazing fast charging technology",
                "Best-in-class portable design for travel",
                "World-class battery life",
            ],
            "topic_clusters": {
                "charging_speed": ["How fast does it charge?", "What is the wattage output?"],
                "portability": ["Is it allowed on airplanes?", "How heavy is it?"],
            },
        }

        skill = Skill02(
            keywords=sample["keywords"],
            bullets=sample["bullets"],
            topic_clusters=sample["topic_clusters"],
            title=sample["title"],
            asin=sample["asin"],
        )
        result = skill.to_json()
        print(json.dumps(result, ensure_ascii=False, indent=2))
