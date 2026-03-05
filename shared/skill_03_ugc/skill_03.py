"""
skill_03.py — UGC Ground Truth Mining & Q&A Seeding
====================================================
Skill 03 of the Rufus Optimization Skills Library.

Goal:
    Use User-Generated Content (UGC) as "Ground Truth" to validate product
    claims, mine technical questions, and seed the Q&A section with exact
    question-answer pairs that Rufus can index as definitive proof nodes.

Callable 3 ways:
    1. Direct import:  from skill_03_ugc.skill_03 import Skill03
    2. CLI:            python skill_03.py --input data.json --output result.json
    3. JSON stdin:     echo '{"reviews": [], "competitor_qas": []}' | python skill_03.py

Author: John / Anergy Academy
Version: 1.0.0
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent.parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from utils.helpers import (
    load_json_input,
    log_step,
    sanitize_text,
    save_json_output,
    score_to_grade,
    truncate_to_chars,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Question patterns: regex to detect technical/factual questions in reviews
QUESTION_PATTERNS = [
    r"\b(is it|does it|can it|will it|does this|is this|can this|will this)\b[^?.!]{5,80}[?]",
    r"\b(how (long|many|much|fast|far|often))[^?.!]{3,80}[?]",
    r"\b(what (is|are|does|kind|type|size|color|weight|voltage|watt))[^?.!]{3,80}[?]",
]

# Negative sentiment keywords that flag a listing flaw
NEGATIVE_KEYWORDS = [
    "broke", "broken", "stopped working", "doesn't work", "does not work",
    "defective", "poor quality", "cheap", "flimsy", "misleading",
    "wrong size", "not as described", "disappointing", "returned",
    "waste of money", "fragile", "peeling", "cracked",
]

# Positive sentiment keywords that indicate a proof node
POSITIVE_KEYWORDS = [
    "love", "excellent", "perfect", "amazing", "great", "fantastic",
    "works perfectly", "highly recommend", "worth every penny",
    "exactly as described", "fast charging", "long battery life",
]

# Templates for Q&A seeding
QA_TEMPLATES = {
    "airplane":      ("Is this product allowed on airplanes?",
                      "Yes, this product meets FAA regulations for carry-on. Battery capacity is within the 100Wh limit."),
    "waterproof":    ("Is it waterproof or water-resistant?",
                      "This product carries an {rating} waterproof rating, suitable for splashing and rain exposure."),
    "warranty":      ("What is the warranty policy?",
                      "Covered by a {months}-month manufacturer warranty. Contact our support team for replacements."),
    "charging_time": ("How long does it take to fully charge?",
                      "With PD fast charging, a full charge takes approximately {hours} hours."),
    "compatibility": ("Is it compatible with iPhone and Android?",
                      "Yes, works with all USB-C and USB-A devices including iPhone (via adapter), Android, and laptops."),
}


class Skill03:
    """
    Skill03: UGC Ground Truth Mining & Q&A Seeding

    Processes customer reviews and competitor Q&As to extract technical
    questions, classify sentiment, and generate Q&A seed pairs for Rufus indexing.

    Parameters:
        reviews          (list[dict]): Customer reviews. Each: {"text": str, "rating": int}
        competitor_qas   (list[dict]): Competitor Q&A pairs: {"question": str, "answer": str}
        product_context  (dict):       Product metadata for Q&A template filling.
        asin             (str):        ASIN label.
    """

    SKILL_ID = "03"
    SKILL_NAME = "UGC Ground Truth Mining & Q&A Seeding"

    def __init__(
        self,
        reviews: list[dict[str, Any]],
        competitor_qas: list[dict[str, str]] | None = None,
        product_context: dict[str, Any] | None = None,
        asin: str = "UNKNOWN",
    ) -> None:
        self.reviews = reviews
        self.competitor_qas = competitor_qas or []
        self.product_context = product_context or {}
        self.asin = sanitize_text(asin)
        self._result: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_technical_questions(self) -> list[str]:
        """Mine reviews for customer-phrased technical questions."""
        found: list[str] = []
        combined_pattern = re.compile(
            "|".join(QUESTION_PATTERNS), re.IGNORECASE
        )
        for review in self.reviews:
            text = review.get("text", "")
            matches = combined_pattern.findall(text)
            found.extend([sanitize_text(m) for m in matches if m])
        # Deduplicate while preserving order
        seen: set[str] = set()
        unique = []
        for q in found:
            lower = q.lower()
            if lower not in seen:
                seen.add(lower)
                unique.append(q)
        return unique

    def _classify_sentiment(self) -> dict[str, Any]:
        """Classify reviews as positive/negative and extract keyword evidence."""
        positive: list[str] = []
        negative: list[str] = []
        neg_keyword_freq: Counter = Counter()

        for review in self.reviews:
            text = review.get("text", "").lower()
            rating = review.get("rating", 3)

            is_positive = rating >= 4 or any(k in text for k in POSITIVE_KEYWORDS)
            is_negative = rating <= 2 or any(k in text for k in NEGATIVE_KEYWORDS)

            snippet = truncate_to_chars(sanitize_text(review.get("text", "")), 120, ellipsis=True)

            if is_negative:
                negative.append(snippet)
                for kw in NEGATIVE_KEYWORDS:
                    if kw in text:
                        neg_keyword_freq[kw] += 1
            elif is_positive:
                positive.append(snippet)

        return {
            "positive_count": len(positive),
            "negative_count": len(negative),
            "top_positive_snippets": positive[:3],
            "top_negative_snippets": negative[:3],
            "recurring_negative_keywords": dict(neg_keyword_freq.most_common(5)),
        }

    def _seed_qa_pairs(self) -> list[dict[str, str]]:
        """Generate Q&A seed pairs from templates using product context."""
        ctx = self.product_context
        seeded: list[dict[str, str]] = []

        for key, (question, answer_template) in QA_TEMPLATES.items():
            # Fill template placeholders from product_context
            try:
                answer = answer_template.format(
                    rating=ctx.get("waterproof_rating", "IPX4"),
                    months=ctx.get("warranty_months", 12),
                    hours=ctx.get("charge_hours", 2),
                )
            except KeyError:
                answer = answer_template

            seeded.append({"question": question, "answer": answer, "template_key": key})

        # Also de-duplicate and include competitor Q&As
        for qa in self.competitor_qas:
            q = sanitize_text(qa.get("question", ""))
            a = sanitize_text(qa.get("answer", ""))
            if q and a:
                seeded.append({"question": q, "answer": a, "template_key": "competitor_derived"})

        return seeded

    def _correlate_sentiment_to_attributes(
        self, sentiment: dict, qa_pairs: list[dict]
    ) -> list[str]:
        """
        Produce bullet-point update recommendations based on negative review patterns.

        Each recommendation addresses a specific flaw flagged by customers to prevent
        it being 'baked into' Rufus's product summary.
        """
        recommendations: list[str] = []
        neg_keywords = sentiment.get("recurring_negative_keywords", {})

        if "flimsy" in neg_keywords or "cheap" in neg_keywords:
            recommendations.append(
                "Add a bullet explicitly stating build material and certification (e.g., 'Aircraft-grade aluminum chassis, drop-tested to MIL-STD-810G')"
            )
        if "misleading" in neg_keywords or "not as described" in neg_keywords:
            recommendations.append(
                "Verify all Title claims match backend attributes exactly (quantity, dimensions, included accessories)"
            )
        if "stopped working" in neg_keywords or "defective" in neg_keywords:
            recommendations.append(
                "Seed Q&A with warranty/return policy answer to intercept Rufus reliability queries"
            )
        if not neg_keywords:
            recommendations.append("No critical negative patterns detected — maintain current copy quality")

        return recommendations

    def _score_ugc_coverage(self, questions: list, qa_pairs: list) -> float:
        """Score what fraction of mined questions are addressed by Q&A pairs."""
        if not questions:
            return 100.0
        answered = sum(
            1 for q in questions
            if any(
                re.search(re.escape(q[:20].lower()), pair["question"].lower())
                for pair in qa_pairs
            )
        )
        return round((answered / len(questions)) * 100, 1)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> "Skill03":
        """
        Execute the full UGC Mining & Q&A Seeding pipeline.

        Steps:
            1. Extract technical questions from reviews
            2. Sentiment classification + keyword analysis
            3. Q&A seed pair generation
            4. Sentiment-to-attribute correlation & recommendations
            5. Scoring

        Returns:
            self (for method chaining)
        """
        log_step("SKILL03_START", f"ASIN={self.asin}")

        log_step("SKILL03_EXTRACT_QUESTIONS", f"{len(self.reviews)} reviews")
        questions = self._extract_technical_questions()

        log_step("SKILL03_SENTIMENT")
        sentiment = self._classify_sentiment()

        log_step("SKILL03_QA_SEED")
        qa_pairs = self._seed_qa_pairs()

        log_step("SKILL03_CORRELATE")
        recommendations = self._correlate_sentiment_to_attributes(sentiment, qa_pairs)

        coverage_score = self._score_ugc_coverage(questions, qa_pairs)
        grade = score_to_grade(coverage_score)

        self._result = {
            "skill_id": self.SKILL_ID,
            "skill_name": self.SKILL_NAME,
            "asin": self.asin,
            "ugc_mining": {
                "technical_questions_found": questions,
                "question_count": len(questions),
                "sentiment": sentiment,
            },
            "qa_seeding": {
                "qa_pairs": qa_pairs,
                "pair_count": len(qa_pairs),
            },
            "recommendations": recommendations,
            "scores": {
                "qa_coverage_pct": coverage_score,
                "grade": grade,
                "proof_nodes_seeded": len(qa_pairs),
            },
        }

        log_step("SKILL03_DONE", f"coverage={coverage_score}% grade={grade}")
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
        description="Skill03 — UGC Ground Truth Mining & Q&A Seeding",
    )
    parser.add_argument("--input", "-i", help="Path to input JSON or inline JSON string")
    parser.add_argument("--output", "-o", help="Path to write output JSON")
    parser.add_argument("--asin", default="UNKNOWN", help="Product ASIN")
    return parser


def _run_cli(args: argparse.Namespace) -> None:
    if args.input:
        data = load_json_input(args.input)
    elif not sys.stdin.isatty():
        data = json.load(sys.stdin)
    else:
        print("Error: provide --input or pipe JSON.", file=sys.stderr)
        sys.exit(1)

    skill = Skill03(
        reviews=data.get("reviews", []),
        competitor_qas=data.get("competitor_qas", []),
        product_context=data.get("product_context", {}),
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
        sample_reviews = [
            {"text": "Does it work on airplanes? I need it for travel.", "rating": 4},
            {"text": "The charger is amazing! Works perfectly with my MacBook.", "rating": 5},
            {"text": "Stopped working after 2 weeks. Very disappointing. Cheap quality.", "rating": 1},
            {"text": "Is this waterproof? How fast does it charge?", "rating": 3},
            {"text": "Love it! Long battery life and exactly as described.", "rating": 5},
        ]
        sample_context = {
            "waterproof_rating": "IPX5",
            "warranty_months": 18,
            "charge_hours": 1.5,
        }
        skill = Skill03(
            reviews=sample_reviews,
            product_context=sample_context,
            asin="B0EXAMPLE3",
        )
        print(json.dumps(skill.to_json(), ensure_ascii=False, indent=2))
