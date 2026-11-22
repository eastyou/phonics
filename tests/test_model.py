"""数据模型测试：规则、单词库、查询与练习生成。"""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from phonics.model import (
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


class RuleDataTests(unittest.TestCase):
    """内置规则数据的基本约束。"""

    def test_rule_count(self) -> None:
        self.assertGreaterEqual(len(all_rules()), 42)

    def test_rule_patterns_unique(self) -> None:
        patterns = [rule.pattern for rule in all_rules()]
        self.assertEqual(len(patterns), len(set(pattern.lower() for pattern in patterns)))

    def test_rule_fields_non_empty(self) -> None:
        for rule in all_rules():
            with self.subTest(pattern=rule.pattern):
                self.assertTrue(rule.pattern)
                self.assertTrue(rule.sound)
                self.assertTrue(rule.kind)
                self.assertTrue(rule.note)

    def test_rule_kinds_are_known(self) -> None:
        allowed = {"短元音", "长元音", "元音组合", "辅音组合", "辅音连缀", "r 控制"}
        for rule in all_rules():
            with self.subTest(pattern=rule.pattern):
                self.assertIn(rule.kind, allowed)

    def test_rule_examples_length(self) -> None:
        for rule in all_rules():
            with self.subTest(pattern=rule.pattern):
                self.assertGreaterEqual(len(rule.examples), 3)
                self.assertLessEqual(len(rule.examples), 5)

    def test_rule_examples_lowercase_ascii(self) -> None:
        for rule in all_rules():
            for word in rule.examples:
                with self.subTest(pattern=rule.pattern, word=word):
                    self.assertEqual(word, word.lower())
                    self.assertTrue(word.isascii())
                    self.assertTrue(word.isalpha())

    def test_rule_examples_unique_across_rules(self) -> None:
        words = [word for rule in all_rules() for word in rule.examples]
        self.assertEqual(len(words), len(set(words)))
        self.assertGreaterEqual(len(words), 120)

    def test_all_rules_returns_new_list(self) -> None:
        first = all_rules()
        first.clear()
        self.assertGreaterEqual(len(all_rules()), 42)


class RulesOfTests(unittest.TestCase):
    """按分类查询规则。"""

    def test_rules_of_short_vowels(self) -> None:
        self.assertEqual(len(rules_of("短元音")), 5)

    def test_rules_of_long_vowels(self) -> None:
        self.assertEqual(len(rules_of("长元音")), 4)

    def test_rules_of_consonant_blends(self) -> None:
        self.assertEqual(len(rules_of("辅音连缀")), 19)

    def test_rules_of_r_controlled(self) -> None:
        self.assertEqual(len(rules_of("r 控制")), 5)

    def test_rules_of_aliases(self) -> None:
        self.assertEqual(len(rules_of("short")), 5)
        self.assertEqual(len(rules_of("Long Vowel")), 4)
        self.assertEqual(len(rules_of("R-CONTROLLED")), 5)
        self.assertEqual(len(rules_of("digraph")), 9)

    def test_rules_of_unknown_kind(self) -> None:
        with self.assertRaises(ValueError) as context:
            rules_of("颜色")
        self.assertIn("可用分类", str(context.exception))

    def test_rules_of_empty_kind(self) -> None:
        with self.assertRaises(ValueError):
            rules_of("   ")

    def test_rules_of_type_error(self) -> None:
        with self.assertRaises(TypeError):
            rules_of(3)  # type: ignore[arg-type]

    def test_rules_of_bool_type_error(self) -> None:
        with self.assertRaises(TypeError):
            rules_of(True)  # type: ignore[arg-type]

    def test_rules_of_returns_new_list(self) -> None:
        first = rules_of("短元音")
        first.clear()
        self.assertEqual(len(rules_of("短元音")), 5)


class FindRuleTests(unittest.TestCase):
    """按字母组合查找单条规则。"""

    def test_find_rule_sh(self) -> None:
        rule = find_rule("sh")
        self.assertEqual(rule.kind, "辅音组合")
        self.assertEqual(rule.examples[0], "ship")

    def test_find_rule_magic_e(self) -> None:
        self.assertEqual(find_rule("a_e").kind, "长元音")
        self.assertIn("cake", find_rule("a_e").examples)

    def test_find_rule_case_insensitive(self) -> None:
        self.assertEqual(find_rule("SH").pattern, "sh")
        self.assertEqual(find_rule("A_E").pattern, "a_e")
        self.assertEqual(find_rule("Th（浊）").pattern, "th（浊）")

    def test_find_rule_short_oo(self) -> None:
        self.assertEqual(find_rule("oo").sound, "/uː/")
        self.assertEqual(find_rule("oo（短）").sound, "/ʊ/")

    def test_find_rule_unknown(self) -> None:
        with self.assertRaises(ValueError) as context:
            find_rule("zz")
        message = str(context.exception)
        self.assertIn("未知字母组合", message)
        self.assertIn("sh", message)

    def test_find_rule_empty(self) -> None:
        with self.assertRaises(ValueError):
            find_rule("  ")

    def test_find_rule_type_error(self) -> None:
        with self.assertRaises(TypeError):
            find_rule(None)  # type: ignore[arg-type]

    def test_find_rule_padding(self) -> None:
        self.assertEqual(find_rule("  sh  ").pattern, "sh")


class WordRuleTests(unittest.TestCase):
    """单词归组与最长匹配。"""

    def test_word_rule_cake(self) -> None:
        self.assertEqual(word_rule("cake"), "a_e")

    def test_word_rule_ship(self) -> None:
        self.assertEqual(word_rule("ship"), "sh")

    def test_word_rule_short_oo(self) -> None:
        self.assertEqual(word_rule("book"), "oo（短）")
        self.assertEqual(word_rule("foot"), "oo（短）")

    def test_word_rule_ow_sounds(self) -> None:
        self.assertEqual(word_rule("snow"), "ow")
        self.assertEqual(word_rule("cow"), "ow（/aʊ/）")

    def test_word_rule_case_insensitive(self) -> None:
        self.assertEqual(word_rule("CAKE"), "a_e")
        self.assertEqual(word_rule("Ship"), "sh")

    def test_word_rule_padding(self) -> None:
        self.assertEqual(word_rule("  book  "), "oo（短）")

    def test_word_rule_unknown(self) -> None:
        with self.assertRaises(ValueError) as context:
            word_rule("xyz")
        self.assertIn("未收录的单词", str(context.exception))

    def test_word_rule_invalid_characters(self) -> None:
        with self.assertRaises(ValueError):
            word_rule("cake1")
        with self.assertRaises(ValueError):
            word_rule("ice cream")

    def test_word_rule_type_error(self) -> None:
        with self.assertRaises(TypeError):
            word_rule(12)  # type: ignore[arg-type]

    def test_word_rule_empty(self) -> None:
        with self.assertRaises(ValueError):
            word_rule("")

    def test_word_library_size(self) -> None:
        words = {word for rule in all_rules() for word in rule.examples}
        self.assertGreaterEqual(len(words), 120)
        for word in words:
            self.assertIn(word_rule(word), {rule.pattern for rule in all_rules()})

    def test_every_example_word_maps_to_its_rule(self) -> None:
        for rule in all_rules():
            for word in rule.examples:
                with self.subTest(pattern=rule.pattern, word=word):
                    self.assertEqual(word_rule(word), rule.pattern)


class ExamplesAndKindTests(unittest.TestCase):
    """例词与分类辅助函数。"""

    def test_examples_of(self) -> None:
        self.assertEqual(examples_of("sh"), ["ship", "shop", "fish", "wish", "shell"])

    def test_examples_of_copy(self) -> None:
        first = examples_of("sh")
        first.append("extra")
        self.assertNotIn("extra", examples_of("sh"))

    def test_examples_of_unknown(self) -> None:
        with self.assertRaises(ValueError):
            examples_of("zz")

    def test_kind_of(self) -> None:
        self.assertEqual(kind_of("sh"), "辅音组合")
        self.assertEqual(kind_of("a_e"), "长元音")
        self.assertEqual(kind_of("ar"), "r 控制")

    def test_kind_of_unknown(self) -> None:
        with self.assertRaises(ValueError):
            kind_of("zz")

    def test_rule_is_frozen(self) -> None:
        rule = find_rule("sh")
        with self.assertRaises(FrozenInstanceError):
            rule.pattern = "xx"  # type: ignore[misc]


class QuizItemsTests(unittest.TestCase):
    """四选一题目生成。"""

    def test_quiz_items_count(self) -> None:
        items = quiz_items(12, seed=3)
        self.assertEqual(len(items), 12)
        self.assertEqual([item["index"] for item in items], list(range(1, 13)))

    def test_quiz_items_deterministic(self) -> None:
        self.assertEqual(quiz_items(8, seed=7), quiz_items(8, seed=7))

    def test_quiz_items_different_seeds(self) -> None:
        self.assertNotEqual(quiz_items(10, seed=1), quiz_items(10, seed=2))

    def test_quiz_items_structure(self) -> None:
        keys = {"index", "question", "options", "answer_index", "answer", "explanation"}
        for item in quiz_items(20, seed=5):
            with self.subTest(index=item["index"]):
                self.assertEqual(set(item.keys()), keys)
                self.assertIsInstance(item["question"], str)
                self.assertTrue(item["question"])
                self.assertIsInstance(item["options"], list)
                self.assertEqual(len(item["options"]), 4)
                self.assertIsInstance(item["answer"], str)
                self.assertTrue(item["answer"])
                self.assertIsInstance(item["explanation"], str)
                self.assertTrue(item["explanation"])

    def test_quiz_items_options_unique(self) -> None:
        for item in quiz_items(30, seed=11):
            options = item["options"]
            self.assertIsInstance(options, list)
            if isinstance(options, list):
                self.assertEqual(len(options), len(set(options)))

    def test_quiz_items_answer_consistent(self) -> None:
        for item in quiz_items(30, seed=13):
            options = item["options"]
            answer_index = item["answer_index"]
            self.assertIsInstance(options, list)
            self.assertIsInstance(answer_index, int)
            if isinstance(options, list) and isinstance(answer_index, int):
                self.assertGreaterEqual(answer_index, 0)
                self.assertLess(answer_index, len(options))
                self.assertEqual(options[answer_index], item["answer"])

    def test_quiz_items_kind_filter(self) -> None:
        patterns = {rule.pattern for rule in rules_of("短元音")}
        for item in quiz_items(15, seed=17, kind="短元音"):
            question = str(item["question"])
            if question.startswith("单词"):
                self.assertIn("「短元音」", question)
            else:
                self.assertTrue(any(pattern in question for pattern in patterns))

    def test_quiz_items_kind_alias(self) -> None:
        items = quiz_items(6, seed=19, kind="short")
        self.assertEqual(len(items), 6)

    def test_quiz_items_count_too_small(self) -> None:
        with self.assertRaises(ValueError):
            quiz_items(0)

    def test_quiz_items_count_too_large(self) -> None:
        with self.assertRaises(ValueError):
            quiz_items(41)

    def test_quiz_items_count_bool(self) -> None:
        with self.assertRaises(TypeError):
            quiz_items(True)  # type: ignore[arg-type]

    def test_quiz_items_count_float(self) -> None:
        with self.assertRaises(TypeError):
            quiz_items(3.5)  # type: ignore[arg-type]

    def test_quiz_items_seed_bool(self) -> None:
        with self.assertRaises(TypeError):
            quiz_items(3, seed=True)

    def test_quiz_items_seed_float(self) -> None:
        with self.assertRaises(TypeError):
            quiz_items(3, seed=1.5)

    def test_quiz_items_unknown_kind(self) -> None:
        with self.assertRaises(ValueError):
            quiz_items(3, kind="颜色")


class MatchItemsTests(unittest.TestCase):
    """配对题生成。"""

    def test_match_items_count(self) -> None:
        self.assertEqual(len(match_items(10, seed=2)), 10)

    def test_match_items_deterministic(self) -> None:
        self.assertEqual(match_items(8, seed=4), match_items(8, seed=4))

    def test_match_items_structure(self) -> None:
        for pair in match_items(12, seed=6):
            self.assertIsInstance(pair, tuple)
            self.assertEqual(len(pair), 2)
            self.assertIsInstance(pair[0], str)
            self.assertIsInstance(pair[1], str)

    def test_match_items_unique(self) -> None:
        pairs = match_items(20, seed=8)
        patterns = [pattern for pattern, _ in pairs]
        words = [word for _, word in pairs]
        self.assertEqual(len(patterns), len(set(patterns)))
        self.assertEqual(len(words), len(set(words)))

    def test_match_items_words_from_library(self) -> None:
        for pattern, word in match_items(20, seed=10):
            rule = find_rule(pattern)
            self.assertIn(word, rule.examples)

    def test_match_items_count_too_small(self) -> None:
        with self.assertRaises(ValueError):
            match_items(0)

    def test_match_items_count_too_large(self) -> None:
        with self.assertRaises(ValueError):
            match_items(21)

    def test_match_items_count_bool(self) -> None:
        with self.assertRaises(TypeError):
            match_items(True)  # type: ignore[arg-type]

    def test_match_items_seed_float(self) -> None:
        with self.assertRaises(TypeError):
            match_items(3, seed=2.5)


class RuleTypeTests(unittest.TestCase):
    """Rule 构造与类型约束。"""

    def test_rule_examples_must_be_tuple(self) -> None:
        rule = Rule("zz", "/z/", "辅音组合", ("zip", "zap", "zoo"), "测试规则。")
        self.assertIsInstance(rule.examples, tuple)

    def test_find_rule_returns_rule(self) -> None:
        self.assertIsInstance(find_rule("sh"), Rule)


if __name__ == "__main__":
    unittest.main()
