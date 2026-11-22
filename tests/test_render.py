"""HTML 渲染测试：结构、打印样式与转义。"""

from __future__ import annotations

import unittest

from phonics.model import Rule, all_rules, find_rule, match_items, quiz_items
from phonics.render import card_html, chart_html, match_html, quiz_html


class ChartHtmlTests(unittest.TestCase):
    """规则表页面。"""

    def test_chart_default_title(self) -> None:
        page = chart_html(all_rules())
        self.assertIn("<h1>自然拼读规则表</h1>", page)

    def test_chart_contains_kinds(self) -> None:
        page = chart_html(all_rules())
        for rule in all_rules():
            with self.subTest(kind=rule.kind):
                self.assertIn(rule.kind, page)

    def test_chart_contains_patterns_and_examples(self) -> None:
        page = chart_html(all_rules())
        self.assertIn("a_e", page)
        self.assertIn("cake", page)
        self.assertIn("oo（短）", page)

    def test_chart_rule_count(self) -> None:
        page = chart_html(all_rules())
        self.assertIn("共 %d 条规则" % len(all_rules()), page)

    def test_chart_print_css(self) -> None:
        page = chart_html(all_rules())
        self.assertIn("@page { size: A4", page)
        self.assertIn("@media print", page)

    def test_chart_empty_error(self) -> None:
        with self.assertRaises(ValueError):
            chart_html([])

    def test_chart_invalid_item(self) -> None:
        with self.assertRaises(TypeError):
            chart_html(["sh"])  # type: ignore[list-item]

    def test_chart_empty_title(self) -> None:
        with self.assertRaises(ValueError):
            chart_html(all_rules(), "  ")

    def test_chart_escapes_dynamic_text(self) -> None:
        rule = Rule("<p>", "<s>", "短元音", ("<a>", "<b>", "<c>"), "<note>")
        page = chart_html([rule], "<title>")
        self.assertNotIn("<p>", page)
        self.assertNotIn("<s>", page)
        self.assertNotIn("<note>", page)
        self.assertIn("&lt;p&gt;", page)
        self.assertIn("&lt;title&gt;", page)


class QuizHtmlTests(unittest.TestCase):
    """练习题页面。"""

    def test_quiz_contains_questions(self) -> None:
        items = quiz_items(4, seed=21)
        page = quiz_html(items, "自然拼读测验")
        for item in items:
            self.assertIn(str(item["question"]), page)

    def test_quiz_no_answers_by_default(self) -> None:
        page = quiz_html(quiz_items(3, seed=22), "测验")
        self.assertNotIn("参考答案", page)

    def test_quiz_with_answers(self) -> None:
        page = quiz_html(quiz_items(3, seed=23), "测验", with_answers=True)
        self.assertIn("参考答案", page)

    def test_quiz_answers_page_break(self) -> None:
        page = quiz_html(quiz_items(3, seed=24), "测验", with_answers=True)
        self.assertIn("page-break-before: always", page)
        self.assertIn('class="answers"', page)

    def test_quiz_two_columns(self) -> None:
        page = quiz_html(quiz_items(3, seed=25), "测验")
        self.assertIn("column-count: 2", page)

    def test_quiz_a4(self) -> None:
        page = quiz_html(quiz_items(2, seed=26), "测验")
        self.assertIn("@page { size: A4", page)

    def test_quiz_empty_error(self) -> None:
        with self.assertRaises(ValueError):
            quiz_html([], "测验")

    def test_quiz_item_not_dict(self) -> None:
        with self.assertRaises(TypeError):
            quiz_html(["bad"], "测验")  # type: ignore[list-item]

    def test_quiz_missing_field(self) -> None:
        with self.assertRaises(ValueError):
            quiz_html([{"index": 1}], "测验")  # type: ignore[list-item]

    def test_quiz_duplicate_options(self) -> None:
        item = {
            "index": 1,
            "question": "题目",
            "options": ["A", "A", "B", "C"],
            "answer_index": 0,
            "answer": "A",
            "explanation": "解析",
        }
        with self.assertRaises(ValueError):
            quiz_html([item], "测验")

    def test_quiz_answer_index_out_of_range(self) -> None:
        item = {
            "index": 1,
            "question": "题目",
            "options": ["A", "B", "C", "D"],
            "answer_index": 4,
            "answer": "A",
            "explanation": "解析",
        }
        with self.assertRaises(ValueError):
            quiz_html([item], "测验")

    def test_quiz_answer_mismatch(self) -> None:
        item = {
            "index": 1,
            "question": "题目",
            "options": ["A", "B", "C", "D"],
            "answer_index": 0,
            "answer": "B",
            "explanation": "解析",
        }
        with self.assertRaises(ValueError):
            quiz_html([item], "测验")

    def test_quiz_with_answers_type_error(self) -> None:
        with self.assertRaises(TypeError):
            quiz_html(quiz_items(2, seed=27), "测验", with_answers="yes")  # type: ignore[arg-type]

    def test_quiz_escapes_dynamic_text(self) -> None:
        item = {
            "index": 1,
            "question": "<script>alert(1)</script>",
            "options": ["<b>A</b>", "<i>B</i>", "C", "D"],
            "answer_index": 0,
            "answer": "<b>A</b>",
            "explanation": "<img src=x>",
        }
        page = quiz_html([item], "<标题>", with_answers=True)
        self.assertNotIn("<script>alert", page)
        self.assertNotIn("<img src=x>", page)
        self.assertIn("&lt;script&gt;", page)
        self.assertIn("&lt;标题&gt;", page)


class MatchHtmlTests(unittest.TestCase):
    """配对练习页面。"""

    def test_match_contains_pairs(self) -> None:
        pairs = match_items(5, seed=31)
        page = match_html(pairs, "配对练习")
        for pattern, word in pairs:
            self.assertIn(pattern, page)
            self.assertIn(word, page)

    def test_match_bank_sorted(self) -> None:
        page = match_html([("sh", "wish"), ("ch", "chip")], "配对练习")
        self.assertLess(page.index("<li>chip</li>"), page.index("<li>wish</li>"))

    def test_match_answers(self) -> None:
        page = match_html([("sh", "ship")], "配对练习")
        self.assertIn("参考答案", page)
        self.assertIn("page-break-before: always", page)

    def test_match_escapes_dynamic_text(self) -> None:
        page = match_html([("<p>", "<w>")], "<t>")
        self.assertNotIn("<p>", page)
        self.assertNotIn("<w>", page)
        self.assertIn("&lt;p&gt;", page)
        self.assertIn("&lt;t&gt;", page)

    def test_match_empty_error(self) -> None:
        with self.assertRaises(ValueError):
            match_html([], "配对练习")

    def test_match_bad_pair(self) -> None:
        with self.assertRaises(TypeError):
            match_html([("sh",)], "配对练习")  # type: ignore[list-item]

    def test_match_duplicate_pattern(self) -> None:
        with self.assertRaises(ValueError):
            match_html([("sh", "ship"), ("sh", "shop")], "配对练习")

    def test_match_duplicate_word(self) -> None:
        with self.assertRaises(ValueError):
            match_html([("sh", "ship"), ("ch", "ship")], "配对练习")

    def test_match_empty_title(self) -> None:
        with self.assertRaises(ValueError):
            match_html([("sh", "ship")], "")


class CardHtmlTests(unittest.TestCase):
    """单条规则卡片。"""

    def test_card_contains_fields(self) -> None:
        rule = find_rule("sh")
        page = card_html(rule)
        self.assertIn(rule.pattern, page)
        self.assertIn(rule.sound, page)
        self.assertIn(rule.kind, page)
        self.assertIn(rule.note, page)
        for word in rule.examples:
            self.assertIn(word, page)

    def test_card_big_class(self) -> None:
        page = card_html(find_rule("a_e"))
        self.assertIn('class="big"', page)
        self.assertIn("chips", page)

    def test_card_escapes_dynamic_text(self) -> None:
        rule = Rule("<x>", "<s>", "短元音", ("<a>", "<b>", "<c>"), "<n>")
        page = card_html(rule)
        self.assertNotIn("<x>", page)
        self.assertNotIn("<s>", page)
        self.assertNotIn("<n>", page)
        self.assertIn("&lt;x&gt;", page)

    def test_card_invalid_type(self) -> None:
        with self.assertRaises(TypeError):
            card_html("sh")  # type: ignore[arg-type]

    def test_card_print_css(self) -> None:
        page = card_html(find_rule("ar"))
        self.assertIn("@page { size: A4", page)
        self.assertIn("@media print", page)


class PageBasicsTests(unittest.TestCase):
    """所有页面共有的基础结构。"""

    def test_doctype_and_charset(self) -> None:
        pages = [
            chart_html(all_rules()),
            quiz_html(quiz_items(2, seed=41), "测验"),
            match_html(match_items(3, seed=42), "配对"),
            card_html(find_rule("sh")),
        ]
        for page in pages:
            with self.subTest(page=page[:30]):
                self.assertTrue(page.startswith("<!DOCTYPE html>"))
                self.assertIn('<meta charset="utf-8">', page)
                self.assertIn('<html lang="zh-CN">', page)


if __name__ == "__main__":
    unittest.main()
