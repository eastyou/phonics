"""phonics：自然拼读规则、单词归组与可打印练习页。"""

from __future__ import annotations

from .model import (
    Rule,
    all_rules,
    examples_of,
    find_rule,
    kind_of,
    match_items,
    quiz_items,
    rules_of,
    word_rule,
)
from .render import card_html, chart_html, match_html, quiz_html

__version__ = "0.1.0"

__all__ = [
    "Rule",
    "__version__",
    "all_rules",
    "card_html",
    "chart_html",
    "examples_of",
    "find_rule",
    "kind_of",
    "match_html",
    "match_items",
    "quiz_html",
    "quiz_items",
    "rules_of",
    "word_rule",
]
