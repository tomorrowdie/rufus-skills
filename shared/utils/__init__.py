"""
utils package for Rufus Optimization Skills Library.
Exposes shared helper functions for all skill modules.
"""

from .helpers import (
    sanitize_text,
    rotate_connector,
    load_json_input,
    save_json_output,
    truncate_to_chars,
    count_noun_phrases,
    flatten_dict,
    slugify,
    score_to_grade,
    log_step,
)

__all__ = [
    "sanitize_text",
    "rotate_connector",
    "load_json_input",
    "save_json_output",
    "truncate_to_chars",
    "count_noun_phrases",
    "flatten_dict",
    "slugify",
    "score_to_grade",
    "log_step",
]