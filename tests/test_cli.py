"""命令行测试：参数、输出与文件导出。"""

from __future__ import annotations

import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from typing import Sequence, Tuple

from phonics.cli import main


def _run_cli(argv: Sequence[str]) -> Tuple[int, str, str]:
    """运行 CLI，返回退出码、标准输出与标准错误。"""
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


class BasicCommandTests(unittest.TestCase):
    """无需写文件的基础命令。"""

    def test_no_args_prints_help(self) -> None:
        code, out, _ = _run_cli([])
        self.assertEqual(code, 0)
        self.assertIn("usage: phonics", out)
        self.assertIn("自然拼读", out)

    def test_help_flag(self) -> None:
        with self.assertRaises(SystemExit) as context:
            _run_cli(["--help"])
        self.assertEqual(context.exception.code, 0)

    def test_version_flag(self) -> None:
        with self.assertRaises(SystemExit) as context:
            _run_cli(["--version"])
        self.assertEqual(context.exception.code, 0)

    def test_rule_command(self) -> None:
        code, out, _ = _run_cli(["rule", "sh"])
        self.assertEqual(code, 0)
        self.assertIn("字母组合：sh", out)
        self.assertIn("辅音组合", out)
        self.assertIn("ship", out)

    def test_rule_unknown(self) -> None:
        code, out, err = _run_cli(["rule", "zz"])
        self.assertEqual(code, 2)
        self.assertIn("错误：", err)
        self.assertIn("未知字母组合", err)
        self.assertEqual(out, "")

    def test_words_command(self) -> None:
        code, out, _ = _run_cli(["words", "sh"])
        self.assertEqual(code, 0)
        self.assertIn("ship", out)
        self.assertIn("共 5 个", out)

    def test_words_unknown(self) -> None:
        code, _, err = _run_cli(["words", "zz"])
        self.assertEqual(code, 2)
        self.assertIn("未知字母组合", err)

    def test_word_command(self) -> None:
        code, out, _ = _run_cli(["word", "cake"])
        self.assertEqual(code, 0)
        self.assertIn("字母组合：a_e", out)
        self.assertIn("长元音", out)

    def test_word_uppercase(self) -> None:
        code, out, _ = _run_cli(["word", "CAKE"])
        self.assertEqual(code, 0)
        self.assertIn("a_e", out)

    def test_word_unknown(self) -> None:
        code, _, err = _run_cli(["word", "zzz"])
        self.assertEqual(code, 2)
        self.assertIn("未收录的单词", err)

    def test_kind_command(self) -> None:
        code, out, _ = _run_cli(["kind", "短元音"])
        self.assertEqual(code, 0)
        self.assertIn("短元音（共 5 条）", out)
        self.assertIn("cat", out)

    def test_kind_alias(self) -> None:
        code, out, _ = _run_cli(["kind", "short"])
        self.assertEqual(code, 0)
        self.assertIn("短元音（共 5 条）", out)

    def test_kind_unknown(self) -> None:
        code, _, err = _run_cli(["kind", "颜色"])
        self.assertEqual(code, 2)
        self.assertIn("可用分类", err)

    def test_chart_stdout(self) -> None:
        code, out, _ = _run_cli(["chart"])
        self.assertEqual(code, 0)
        self.assertIn("自然拼读规则表", out)
        self.assertIn("【辅音组合】", out)

    def test_card_stdout(self) -> None:
        code, out, _ = _run_cli(["card", "sh"])
        self.assertEqual(code, 0)
        self.assertIn("自然拼读卡片", out)
        self.assertIn("字母组合：sh", out)

    def test_card_unknown(self) -> None:
        code, _, err = _run_cli(["card", "zz"])
        self.assertEqual(code, 2)
        self.assertIn("未知字母组合", err)

    def test_main_accepts_tuple(self) -> None:
        code, out, _ = _run_cli(("word", "cake"))
        self.assertEqual(code, 0)
        self.assertIn("a_e", out)


class QuizCommandTests(unittest.TestCase):
    """测验命令。"""

    def test_quiz_stdout(self) -> None:
        code, out, _ = _run_cli(["quiz", "--count", "5", "--seed", "5"])
        self.assertEqual(code, 0)
        self.assertIn("1. ", out)
        self.assertIn("参考答案与解析", out)

    def test_quiz_deterministic(self) -> None:
        first = _run_cli(["quiz", "--count", "6", "--seed", "9"])
        second = _run_cli(["quiz", "--count", "6", "--seed", "9"])
        self.assertEqual(first, second)

    def test_quiz_kind_filter(self) -> None:
        code, out, _ = _run_cli(
            ["quiz", "--count", "4", "--seed", "3", "--kind", "短元音"]
        )
        self.assertEqual(code, 0)
        self.assertIn("短元音", out)

    def test_quiz_invalid_count(self) -> None:
        code, _, err = _run_cli(["quiz", "--count", "0"])
        self.assertEqual(code, 2)
        self.assertIn("题目数量必须在 1 到 40 之间", err)

    def test_quiz_count_too_large(self) -> None:
        code, _, err = _run_cli(["quiz", "--count", "41"])
        self.assertEqual(code, 2)
        self.assertIn("题目数量", err)

    def test_quiz_unknown_kind(self) -> None:
        code, _, err = _run_cli(["quiz", "--count", "3", "--kind", "颜色"])
        self.assertEqual(code, 2)
        self.assertIn("可用分类", err)

    def test_quiz_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "quiz.html")
            code, out, _ = _run_cli(
                ["quiz", "--count", "4", "--seed", "5", "-o", path]
            )
            self.assertEqual(code, 0)
            self.assertIn("已生成：%s" % path, out)
            with open(path, "r", encoding="utf-8") as handle:
                content = handle.read()
            self.assertTrue(content.startswith("<!DOCTYPE html>"))
            self.assertIn("参考答案", content)


class MatchCommandTests(unittest.TestCase):
    """配对命令。"""

    def test_match_stdout(self) -> None:
        code, out, _ = _run_cli(["match", "--count", "5", "--seed", "2"])
        self.assertEqual(code, 0)
        self.assertIn("配对练习", out)
        self.assertIn("参考答案", out)

    def test_match_invalid_count(self) -> None:
        code, _, err = _run_cli(["match", "--count", "21"])
        self.assertEqual(code, 2)
        self.assertIn("配对数量必须在 1 到 20 之间", err)

    def test_match_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "match.html")
            code, out, _ = _run_cli(["match", "--count", "5", "--seed", "2", "-o", path])
            self.assertEqual(code, 0)
            self.assertIn("已生成：", out)
            with open(path, "r", encoding="utf-8") as handle:
                content = handle.read()
            self.assertIn("match-grid", content)
            self.assertIn("参考答案", content)


class ExportCommandTests(unittest.TestCase):
    """规则表与卡片导出。"""

    def test_chart_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "chart.html")
            code, out, _ = _run_cli(["chart", "-o", path])
            self.assertEqual(code, 0)
            self.assertIn("已生成：%s" % path, out)
            with open(path, "r", encoding="utf-8") as handle:
                content = handle.read()
            self.assertIn("短元音", content)
            self.assertIn("cake", content)

    def test_card_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "card.html")
            code, out, _ = _run_cli(["card", "a_e", "-o", path])
            self.assertEqual(code, 0)
            self.assertIn("已生成：", out)
            with open(path, "r", encoding="utf-8") as handle:
                content = handle.read()
            self.assertIn('class="big"', content)
            self.assertIn("cake", content)

    def test_output_creates_parent_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "nested", "chart.html")
            code, _, _ = _run_cli(["chart", "-o", path])
            self.assertEqual(code, 0)
            self.assertTrue(os.path.isfile(path))

    def test_output_to_directory_reports_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            code, _, err = _run_cli(["chart", "-o", directory])
            self.assertEqual(code, 2)
            self.assertIn("无法写入文件", err)

    def test_output_empty_path(self) -> None:
        code, _, err = _run_cli(["chart", "-o", "   "])
        self.assertEqual(code, 2)
        self.assertIn("输出路径不能为空", err)


if __name__ == "__main__":
    unittest.main()
