"""
skill_06.py — Mobile Habitat Optimization (Full Mobile Audit)
==============================================================
Skill 06 of the Rufus Optimization Skills Library.

Goal:
    Dominate the "Rufus Habitat" on mobile, where the AI chat interface occupies
    50% of the screen. Amazon's mobile ranking algorithm weighs mobile signals 2×
    heavier than desktop/iPad, making this the highest-leverage optimization.

Analysis Modules:
    1. Title First-70 Rule — Rufus chat truncation zone
    2. Bullet Truncation — Mobile cuts at ~80 chars per bullet
    3. Image Stack Order — Sequential swipe scoring
    4. Swipe-Depth Analysis — How many swipes to reach key info
    5. Mobile A+ Fold — Above-the-fold content density
    6. Touch-Target CTA — CTA accessibility sizing
    7. Voice-Search Readiness — Conversational query matching
    8. Video Arc Strategy — 9:16 vertical + Problem→Solution

Composite Score Weights:
    title_score      × 0.20
    bullet_trunc     × 0.20
    image_order      × 0.15
    swipe_depth      × 0.10
    a_fold           × 0.10
    touch_target     × 0.05
    voice_ready      × 0.10
    video_avg        × 0.10

Callable 3 ways:
    1. Direct import:  from skill_06_mobile.skill_06 import Skill06
    2. CLI:            python skill_06.py --input data.json --output result.json
    3. JSON stdin:     echo '{"title": "", "videos": []}' | python skill_06.py

Author: John / Anergy Academy
Version: 2.0.0
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

RUFUS_CHAT_TRUNCATION_CHARS = 70   # Characters visible in Rufus mobile chat window
MOBILE_BULLET_TRUNCATION = 80      # Characters visible per bullet on mobile
AMAZON_TITLE_MAX_CHARS = 200       # Amazon title hard limit
MOBILE_TITLE_IDEAL_CHARS = 120     # Ideal length for mobile: visible before scroll
MOBILE_FOLD_PX = 400               # Approximate first screen fold on mobile (px)
TOUCH_TARGET_MIN_PX = 44           # Minimum touch target per Apple/Google HIG
IDEAL_SWIPE_KEY_INFO = 2           # Key info should appear within N swipes
IDEAL_SWIPE_COMPARISON = 4         # Comparison table should appear within N swipes

# Category keywords that signal a strong title opening
CATEGORY_OPENER_KEYWORDS = [
    "power bank", "phone charger", "laptop stand", "bluetooth speaker",
    "wireless earbuds", "portable battery", "usb hub", "desk lamp",
    "keyboard", "mouse", "webcam", "monitor", "case", "cover", "bag",
    "charger", "cable", "adapter", "headphones", "speaker", "camera",
    "tablet", "stylus",
]

# Brand/marketing filler words that waste the 70-char budget
FILLER_OPENERS = [
    "introducing", "new!", "hot!", "sale!", "best seller",
    "our amazing", "you will love",
]

# Problem→Solution video arc keywords
VIDEO_PROBLEM_KEYWORDS = [
    "struggle", "problem", "issue", "can't", "don't", "limited",
    "stuck", "always", "frustrated", "tired of", "hate", "annoying",
    "dead battery", "dying", "running out",
]
VIDEO_SOLUTION_KEYWORDS = [
    "solve", "solution", "now you can", "finally", "easy", "perfect",
    "works", "enjoy", "never again", "the answer", "meet the",
]

# Non-conversational patterns (hard for voice search)
NON_CONVERSATIONAL_PATTERNS = [
    r'\b\d+[xX]\b',              # "3x" — abbreviation
    r'[A-Z]{3,}',                # "USB" "PD" — acronyms (allow 2-char)
    r'[/|&+]{2,}',              # "USB-C/USB-A" — slash chains
    r'\b\w+\d+\w*\b',           # "20000mAh" — number embedded in word
    r'[-—]{2,}',                 # double dashes
]

# Recommended image order for mobile carousel
RECOMMENDED_IMAGE_ORDER = [
    "main",          # Slot 1: Clean product shot
    "infographic",   # Slot 2: Key specs / features
    "infographic",   # Slot 3: Tech details or comparison
    "lifestyle",     # Slot 4: Product in use
    "infographic",   # Slot 5: Additional features or dimensions
    "lifestyle",     # Slot 6: Secondary lifestyle
    "video_thumb",   # Slot 7: Video thumbnail
]


class Skill06:
    """
    Skill06: Mobile Habitat Optimization (Full Mobile Audit)

    Comprehensive mobile-first optimization covering title truncation, bullet
    visibility, image stack ordering, swipe depth, A+ fold, touch targets,
    voice-search readiness, and video arc strategy.

    Parameters:
        title      (str):         Current product title.
        bullets    (list[str]):   Product bullet points (5 typically).
        videos     (list[dict]):  Video records: {"title": str, "description": str, "aspect_ratio": str}
        images     (list[dict]):  Image records: {"filename": str, "image_type": str, ...}
        modules    (list[dict]):  A+ modules: {"type": str, "content": str}
        category   (str):         Product top-level category.
        asin       (str):         ASIN label.
    """

    SKILL_ID = "06"
    SKILL_NAME = "Mobile Habitat Optimization"

    def __init__(
        self,
        title: str,
        videos: list[dict[str, Any]] | None = None,
        category: str = "",
        asin: str = "UNKNOWN",
        bullets: list[str] | None = None,
        images: list[dict[str, Any]] | None = None,
        modules: list[dict[str, Any]] | None = None,
    ) -> None:
        self.title = sanitize_text(title)
        self.videos = videos or []
        self.category = sanitize_text(category)
        self.asin = sanitize_text(asin)
        self.bullets = [sanitize_text(b) for b in (bullets or [])]
        self.images = images or []
        self.modules = modules or []
        self._result: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Module 1: Title First-70 Rule
    # ------------------------------------------------------------------

    def _analyze_title_mobile(self) -> dict[str, Any]:
        """Apply the First-70-Characters Rule and produce mobile optimization data."""
        title = self.title
        char_count = len(title)

        preview_70 = truncate_to_chars(title, RUFUS_CHAT_TRUNCATION_CHARS, ellipsis=True)

        title_lower = title.lower()
        filler_detected = [f for f in FILLER_OPENERS if title_lower.startswith(f)]

        first_70 = title[:RUFUS_CHAT_TRUNCATION_CHARS].lower()
        category_keywords_found = [k for k in CATEGORY_OPENER_KEYWORDS if k in first_70]

        opens_with_category = bool(category_keywords_found) and not filler_detected

        suggestion = ""
        if not opens_with_category:
            category_hint = self.category or (category_keywords_found[0] if category_keywords_found else "Product")
            core_benefit = re.sub(
                r"\b(" + "|".join(FILLER_OPENERS) + r")\b", "", title, flags=re.IGNORECASE
            ).strip()
            core_benefit = truncate_to_chars(core_benefit, 100)
            suggestion = f"{category_hint} — {core_benefit}"

        score = 100.0
        if filler_detected:
            score -= 30
        if not opens_with_category:
            score -= 25
        if char_count > AMAZON_TITLE_MAX_CHARS:
            score -= 20
        elif char_count > MOBILE_TITLE_IDEAL_CHARS:
            score -= 10
        score = max(0.0, round(score, 1))

        return {
            "original_title": title,
            "char_count": char_count,
            "rufus_chat_preview": preview_70,
            "opens_with_category": opens_with_category,
            "category_keywords_in_first_70": category_keywords_found,
            "filler_openers_detected": filler_detected,
            "optimized_title_suggestion": suggestion,
            "title_score": score,
        }

    # ------------------------------------------------------------------
    # Module 2: Bullet Truncation Analysis
    # ------------------------------------------------------------------

    def _analyze_bullet_truncation(self) -> dict[str, Any]:
        """
        Mobile cuts bullets at ~80 characters. Score whether the key
        value proposition is visible before the cut.
        """
        reports = []
        total_score = 0.0

        for i, bullet in enumerate(self.bullets):
            char_count = len(bullet)
            visible_part = bullet[:MOBILE_BULLET_TRUNCATION]
            hidden_part = bullet[MOBILE_BULLET_TRUNCATION:]
            is_truncated = char_count > MOBILE_BULLET_TRUNCATION

            # Check if visible part contains a number/spec (concrete claim)
            has_spec_in_visible = bool(re.search(r'\d+\s*(?:mAh|W|V|Wh|mm|g|oz|hr|min|hours?|inch)', visible_part, re.IGNORECASE))

            # Check for colon pattern "Feature: benefit" — is the benefit visible?
            colon_pos = bullet.find(":")
            benefit_visible = colon_pos < 0 or colon_pos < MOBILE_BULLET_TRUNCATION - 20

            # Score this bullet
            bullet_score = 100.0
            if is_truncated and not has_spec_in_visible:
                bullet_score -= 40  # Key spec hidden after truncation
            if is_truncated and not benefit_visible:
                bullet_score -= 30  # Benefit text cut off
            if is_truncated:
                bullet_score -= 10  # Any truncation is a minor penalty
            bullet_score = max(0.0, round(bullet_score, 1))
            total_score += bullet_score

            reports.append({
                "bullet_index": i + 1,
                "char_count": char_count,
                "visible_text": visible_part,
                "hidden_text": hidden_part if is_truncated else "",
                "is_truncated": is_truncated,
                "has_spec_in_visible": has_spec_in_visible,
                "benefit_visible": benefit_visible,
                "bullet_score": bullet_score,
            })

        avg_score = round(total_score / len(reports), 1) if reports else 50.0

        return {
            "bullets_analyzed": len(reports),
            "truncated_count": sum(1 for r in reports if r["is_truncated"]),
            "per_bullet": reports,
            "avg_bullet_score": avg_score,
        }

    # ------------------------------------------------------------------
    # Module 3: Image Stack Order Scoring
    # ------------------------------------------------------------------

    def _analyze_image_order(self) -> dict[str, Any]:
        """
        Mobile users swipe through images sequentially. Score whether the
        image order follows the optimal sequence: main → specs → features → lifestyle.
        """
        if not self.images:
            return {"images_analyzed": 0, "order_score": 50.0, "per_slot": [], "recommendation": "No image data available."}

        slot_reports = []
        matches = 0

        for i, img in enumerate(self.images[:7]):
            actual_type = img.get("image_type", "unknown").lower()
            recommended = RECOMMENDED_IMAGE_ORDER[i] if i < len(RECOMMENDED_IMAGE_ORDER) else "any"
            is_match = actual_type == recommended
            if is_match:
                matches += 1

            # Special scoring: main must be slot 1
            is_critical_mismatch = (i == 0 and actual_type != "main")
            # Infographic before slot 3 is ideal
            is_early_infographic = (i <= 2 and actual_type == "infographic")
            if is_early_infographic and not is_match:
                matches += 0.5  # partial credit

            slot_reports.append({
                "slot": i + 1,
                "actual_type": actual_type,
                "recommended_type": recommended,
                "is_match": is_match,
                "is_critical_mismatch": is_critical_mismatch,
                "filename": img.get("filename", ""),
            })

        order_score = round((matches / min(len(self.images), 7)) * 100, 1) if self.images else 50.0
        order_score = min(100.0, order_score)

        recommendation = ""
        if any(s["is_critical_mismatch"] for s in slot_reports):
            recommendation = "Slot 1 must be the main product shot (white background). Move lifestyle/infographic images to later slots."
        elif order_score < 70:
            recommendation = "Reorder images: Slot 1=Main, Slot 2-3=Specs Infographics, Slot 4=Lifestyle."

        return {
            "images_analyzed": len(slot_reports),
            "per_slot": slot_reports,
            "order_score": order_score,
            "recommendation": recommendation,
        }

    # ------------------------------------------------------------------
    # Module 4: Swipe-Depth Analysis
    # ------------------------------------------------------------------

    def _analyze_swipe_depth(self) -> dict[str, Any]:
        """
        How many swipes to reach key product information on mobile?
        Score based on: key spec ≤ 2 swipes, comparison ≤ 4 swipes.
        """
        # Image swipes (each image = 1 swipe)
        infographic_positions = [i + 1 for i, img in enumerate(self.images) if img.get("image_type", "").lower() == "infographic"]
        first_infographic_swipe = infographic_positions[0] if infographic_positions else 99

        # A+ module positions (each module ≈ 1-2 scroll actions)
        comparison_pos = 99
        for i, mod in enumerate(self.modules):
            if mod.get("type", "").lower() in ("comparison_table", "comparison"):
                comparison_pos = len(self.images) + i + 1  # after images
                break

        # Score
        spec_score = 100.0 if first_infographic_swipe <= IDEAL_SWIPE_KEY_INFO else max(0, 100 - (first_infographic_swipe - IDEAL_SWIPE_KEY_INFO) * 20)
        comparison_score = 100.0 if comparison_pos <= len(self.images) + IDEAL_SWIPE_COMPARISON else max(0, 100 - (comparison_pos - len(self.images) - IDEAL_SWIPE_COMPARISON) * 15)
        depth_score = round((spec_score + comparison_score) / 2, 1)

        return {
            "first_infographic_at_swipe": first_infographic_swipe if first_infographic_swipe < 99 else None,
            "comparison_table_at_position": comparison_pos if comparison_pos < 99 else None,
            "spec_reachability_score": round(spec_score, 1),
            "comparison_reachability_score": round(comparison_score, 1),
            "swipe_depth_score": depth_score,
            "total_images": len(self.images),
            "total_modules": len(self.modules),
        }

    # ------------------------------------------------------------------
    # Module 5: Mobile A+ Fold Analysis
    # ------------------------------------------------------------------

    def _analyze_aplus_fold(self) -> dict[str, Any]:
        """
        First ~400px of A+ content = above the fold on mobile.
        Does the first A+ module contain high-density facts?
        """
        if not self.modules:
            return {"has_modules": False, "fold_score": 50.0, "first_module_type": None, "fact_density": 0}

        first_mod = self.modules[0]
        first_type = first_mod.get("type", "unknown").lower()
        first_content = first_mod.get("content", "")

        # Count fact-like patterns in content (numbers, measurements, specs)
        fact_patterns = [
            r'\d+\s*(?:mAh|W|V|Wh|mm|g|oz|hr|min|hours?|inch)',  # measurements
            r'\d+%',                                                # percentages
            r'\d+\.\d+',                                           # decimals
            r'\d+x\d+',                                            # dimensions
            r'\b(?:USB-C|USB-A|PD|QC|Qi|MagSafe|Bluetooth|Wi-Fi)\b',  # tech standards
        ]
        fact_count = sum(len(re.findall(p, first_content, re.IGNORECASE)) for p in fact_patterns)

        # Score: high-density first module is ideal
        if first_type in ("comparison_table", "technical_specs"):
            fold_score = 90.0
        elif first_type == "faq":
            fold_score = 75.0
        elif fact_count >= 5:
            fold_score = 70.0
        elif first_type in ("hero_image", "lifestyle_image") and fact_count == 0:
            fold_score = 30.0  # Hero-only is wasteful on mobile
        else:
            fold_score = 50.0

        return {
            "has_modules": True,
            "first_module_type": first_type,
            "fact_density": fact_count,
            "fold_score": round(fold_score, 1),
            "recommendation": "" if fold_score >= 70 else
                "Move a fact-dense module (comparison table or tech specs) to the first A+ position for mobile above-the-fold visibility.",
        }

    # ------------------------------------------------------------------
    # Module 6: Touch-Target CTA Sizing
    # ------------------------------------------------------------------

    def _analyze_touch_targets(self) -> dict[str, Any]:
        """
        Amazon mobile CTAs need ≥44×44px touch targets. Audit the listing
        structure for CTA accessibility.
        """
        # We can't measure actual pixel sizes from data alone, but we can audit
        # structural elements that affect touch accessibility
        issues = []

        # Check: Does comparison table exist? (comparison tables have Add-to-Cart proximity)
        has_comparison = any(
            m.get("type", "").lower() in ("comparison_table", "comparison")
            for m in self.modules
        )
        if not has_comparison:
            issues.append("No comparison table found — missing high-conversion CTA proximity point on mobile.")

        # Check: Video thumbnail exists (video CTAs are large touch targets)
        has_video = bool(self.videos)
        if not has_video:
            issues.append("No video content — video play buttons are high-engagement 44×44px touch targets on mobile.")

        # Check: Too many images without CTAs (swipe fatigue)
        if len(self.images) > 7:
            issues.append("More than 7 images may cause swipe fatigue before reaching CTA on mobile.")

        score = 100.0 - (len(issues) * 20)
        score = max(0.0, round(score, 1))

        return {
            "has_comparison_table": has_comparison,
            "has_video_content": has_video,
            "image_count": len(self.images),
            "issues": issues,
            "touch_target_score": score,
        }

    # ------------------------------------------------------------------
    # Module 7: Voice-Search Readiness
    # ------------------------------------------------------------------

    def _analyze_voice_readiness(self) -> dict[str, Any]:
        """
        Voice queries are longer and more conversational than typed.
        Score how well the listing content reads as natural speech.
        """
        # Combine title + bullets for analysis
        all_text = self.title + " " + " ".join(self.bullets)

        # Count non-conversational patterns
        flagged_phrases: list[dict[str, str]] = []
        for pattern in NON_CONVERSATIONAL_PATTERNS:
            matches = re.findall(pattern, all_text)
            for m in matches:
                if len(m) > 2:  # skip tiny matches
                    flagged_phrases.append({"text": m, "issue": "Non-conversational pattern"})

        # Check if title reads naturally as a sentence fragment
        title_words = self.title.split()
        has_natural_flow = len(title_words) >= 5 and not self.title.startswith(("[[", "{{", "##"))

        # Check bullets for natural sentence structure
        conversational_bullets = 0
        for bullet in self.bullets:
            # A conversational bullet starts with a verb or has subject-verb structure
            first_word = bullet.split()[0] if bullet else ""
            if first_word and first_word[0].isupper() and len(bullet) > 30:
                conversational_bullets += 1

        bullet_ratio = conversational_bullets / len(self.bullets) if self.bullets else 0

        # Score
        score = 100.0
        score -= min(40, len(flagged_phrases) * 5)  # -5 per non-conversational phrase, max -40
        if not has_natural_flow:
            score -= 20
        if bullet_ratio < 0.6:
            score -= 20
        score = max(0.0, round(score, 1))

        return {
            "flagged_phrases": flagged_phrases[:10],  # cap at 10
            "flagged_count": len(flagged_phrases),
            "title_natural_flow": has_natural_flow,
            "conversational_bullets": conversational_bullets,
            "total_bullets": len(self.bullets),
            "conversational_ratio": round(bullet_ratio, 2),
            "voice_readiness_score": score,
        }

    # ------------------------------------------------------------------
    # Module 8: Video Arc Strategy (original)
    # ------------------------------------------------------------------

    def _analyze_videos(self) -> list[dict[str, Any]]:
        """Evaluate each video for 9:16 aspect ratio and Problem→Solution narrative arc."""
        reports = []
        for video in self.videos:
            title = sanitize_text(video.get("title", ""))
            desc = sanitize_text(video.get("description", ""))
            aspect = video.get("aspect_ratio", "16:9")
            combined = (title + " " + desc).lower()

            is_vertical = aspect in ("9:16", "vertical")
            has_problem = any(w in combined for w in VIDEO_PROBLEM_KEYWORDS)
            has_solution = any(w in combined for w in VIDEO_SOLUTION_KEYWORDS)
            has_ps_arc = has_problem and has_solution

            score = 0.0
            if is_vertical:
                score += 50
            if has_ps_arc:
                score += 40
            elif has_solution:
                score += 20
            score = min(100.0, score)

            recommendations = []
            if not is_vertical:
                recommendations.append("Convert to 9:16 vertical format (mobile-first for Rufus carousel)")
            if not has_problem:
                recommendations.append("Open video with a customer pain point / problem scenario")
            if not has_solution:
                recommendations.append("Close video with clear solution narrative and product CTA")

            reports.append({
                "video_title": title,
                "aspect_ratio": aspect,
                "is_vertical_9x16": is_vertical,
                "has_problem_arc": has_problem,
                "has_solution_arc": has_solution,
                "has_ps_arc": has_ps_arc,
                "video_score": score,
                "recommendations": recommendations,
            })
        return reports

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> "Skill06":
        """
        Execute the Full Mobile Audit pipeline.

        Steps:
            1. Title mobile analysis (First-70 Rule)
            2. Bullet truncation analysis
            3. Image stack order scoring
            4. Swipe-depth analysis
            5. Mobile A+ fold analysis
            6. Touch-target CTA audit
            7. Voice-search readiness
            8. Video strategy evaluation
            9. Weighted composite score

        Returns:
            self (for method chaining)
        """
        log_step("SKILL06_START", f"ASIN={self.asin}")

        # Module 1: Title
        log_step("SKILL06_TITLE")
        title_analysis = self._analyze_title_mobile()

        # Module 2: Bullet Truncation
        log_step("SKILL06_BULLETS", f"{len(self.bullets)} bullets")
        bullet_analysis = self._analyze_bullet_truncation()

        # Module 3: Image Order
        log_step("SKILL06_IMAGES", f"{len(self.images)} images")
        image_order = self._analyze_image_order()

        # Module 4: Swipe Depth
        log_step("SKILL06_SWIPE")
        swipe_depth = self._analyze_swipe_depth()

        # Module 5: A+ Fold
        log_step("SKILL06_FOLD", f"{len(self.modules)} modules")
        aplus_fold = self._analyze_aplus_fold()

        # Module 6: Touch Targets
        log_step("SKILL06_TOUCH")
        touch_targets = self._analyze_touch_targets()

        # Module 7: Voice Readiness
        log_step("SKILL06_VOICE")
        voice_ready = self._analyze_voice_readiness()

        # Module 8: Videos
        log_step("SKILL06_VIDEOS", f"{len(self.videos)} videos")
        video_reports = self._analyze_videos()

        # Composite score (weighted)
        title_score = title_analysis["title_score"]
        bullet_score = bullet_analysis["avg_bullet_score"]
        image_score = image_order["order_score"]
        swipe_score = swipe_depth["swipe_depth_score"]
        fold_score = aplus_fold["fold_score"]
        touch_score = touch_targets["touch_target_score"]
        voice_score = voice_ready["voice_readiness_score"]
        video_avg = (
            sum(v["video_score"] for v in video_reports) / len(video_reports)
            if video_reports else 50.0
        )

        composite = round(
            title_score * 0.20
            + bullet_score * 0.20
            + image_score * 0.15
            + swipe_score * 0.10
            + fold_score * 0.10
            + touch_score * 0.05
            + voice_score * 0.10
            + video_avg * 0.10,
            1,
        )
        grade = score_to_grade(composite)

        self._result = {
            "skill_id": self.SKILL_ID,
            "skill_name": self.SKILL_NAME,
            "asin": self.asin,
            "title_analysis": title_analysis,
            "bullet_truncation": bullet_analysis,
            "image_order": image_order,
            "swipe_depth": swipe_depth,
            "aplus_fold": aplus_fold,
            "touch_targets": touch_targets,
            "voice_readiness": voice_ready,
            "video_analysis": video_reports,
            "scores": {
                "title_score": title_score,
                "bullet_truncation_score": bullet_score,
                "image_order_score": image_score,
                "swipe_depth_score": swipe_score,
                "aplus_fold_score": fold_score,
                "touch_target_score": touch_score,
                "voice_readiness_score": voice_score,
                "video_avg_score": round(video_avg, 1),
                "composite_mobile_score": composite,
                "grade": grade,
            },
        }

        log_step("SKILL06_DONE", f"composite={composite} grade={grade}")
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
    parser = argparse.ArgumentParser(description="Skill06 — Mobile Habitat Optimization (Full Audit)")
    parser.add_argument("--input", "-i", help="Input JSON file or string")
    parser.add_argument("--output", "-o", help="Output JSON file path")
    parser.add_argument("--asin", default="UNKNOWN")
    return parser


def _run_cli(args: argparse.Namespace) -> None:
    if args.input:
        data = load_json_input(args.input)
    elif not sys.stdin.isatty():
        data = json.load(sys.stdin)
    else:
        print("Error: provide --input or pipe JSON.", file=sys.stderr)
        sys.exit(1)

    skill = Skill06(
        title=data.get("title", ""),
        videos=data.get("videos", []),
        category=data.get("category", ""),
        asin=args.asin or data.get("asin", "UNKNOWN"),
        bullets=data.get("bullets", []),
        images=data.get("images", []),
        modules=data.get("modules", []),
    )
    result = skill.to_json()

    if args.output:
        out_path = save_json_output(result, args.output)
        print(f"Output written to: {out_path}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        _run_cli(_build_cli_parser().parse_args())
    else:
        sample = {
            "asin": "B0EXAMPLE6",
            "title": "Portable Power Bank 20000mAh Fast Charging USB-C PD 65W for iPhone Android Laptop Travel Camping",
            "category": "Electronics",
            "bullets": [
                "20000mAh high-capacity portable power bank charges iPhone 15 Pro Max 4.5 times on a single charge",
                "65W USB-C PD 3.0 fast charging output — charge your MacBook Pro to 50% in just 30 minutes",
                "IPX5 water-resistant with aircraft-grade aluminum chassis and drop-tested to MIL-STD-810G standards",
                "TSA-approved 74Wh battery meets FAA carry-on regulations with LED percentage display",
                "Includes: VoltCharge PowerCore 20000, USB-C cable, travel pouch, and 18-month warranty",
            ],
            "videos": [
                {
                    "title": "Stop struggling with dead batteries while camping",
                    "description": "Solve your power problem with our 20000mAh power bank. Finally enjoy all-day power anywhere.",
                    "aspect_ratio": "9:16",
                },
            ],
            "images": [
                {"filename": "main.jpg", "image_type": "main"},
                {"filename": "specs.jpg", "image_type": "infographic"},
                {"filename": "lifestyle.jpg", "image_type": "lifestyle"},
                {"filename": "comparison.jpg", "image_type": "infographic"},
            ],
            "modules": [
                {"type": "comparison_table", "content": "Capacity: 20000mAh | Output: 65W USB-C PD"},
                {"type": "faq", "content": "Q: Is it waterproof? A: Yes, IPX5."},
            ],
        }

        skill = Skill06(
            title=sample["title"],
            videos=sample["videos"],
            category=sample["category"],
            asin=sample["asin"],
            bullets=sample["bullets"],
            images=sample["images"],
            modules=sample["modules"],
        )
        print(json.dumps(skill.to_json(), ensure_ascii=False, indent=2))
