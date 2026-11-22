"""命令行入口：规则查询、单词归组、练习生成与 HTML 导出。"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

from . import __version__
from .model import (
    Rule,
    all_rules,
    examples_of,
    find_rule,
    match_items,
    quiz_items,
    rules_of,
    word_rule,
)
from .render import card_html, chart_html, match_html, quiz_html

__all__ = ["main"]


def _ensure_utf8_console() -> None:
    """尽力把标准输出与标准错误切换为 UTF-8，失败时静默跳过。"""
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass


def _int_arg(text: str) -> int:
    """把命令行文本解析为整数，失败时抛出中文参数错误。"""
    try:
        return int(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("必须是整数：%s" % text) from exc


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="phonics",
        description="自然拼读：字母组合发音规则、单词归组与可打印练习页。",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="phonics %s" % __version__,
    )
    subparsers = parser.add_subparsers(dest="command", metavar="命令")

    rule_parser = subparsers.add_parser("rule", help="查看某条字母组合规则")
    rule_parser.add_argument("pattern", help="字母组合，例如 sh、a_e、oo（短）")

    words_parser = subparsers.add_parser("words", help="列出某条规则的例词")
    words_parser.add_argument("pattern", help="字母组合")

    word_parser = subparsers.add_parser("word", help="查询单词所属的字母组合")
    word_parser.add_argument("word", help="英文单词")

    kind_parser = subparsers.add_parser("kind", help="按分类列出规则")
    kind_parser.add_argument("kind", help="分类，例如 短元音、辅音组合、r 控制")

    quiz_parser = subparsers.add_parser("quiz", help="生成四选一练习")
    quiz_parser.add_argument("--count", type=_int_arg, default=10, help="题目数量（1-40）")
    quiz_parser.add_argument("--seed", type=_int_arg, default=None, help="随机种子")
    quiz_parser.add_argument("--kind", default=None, help="只使用某个分类的规则")
    quiz_parser.add_argument("-o", "--output", default=None, help="输出 HTML 文件")

    match_parser = subparsers.add_parser("match", help="生成字母组合—例词配对练习")
    match_parser.add_argument("--count", type=_int_arg, default=6, help="配对数量（1-20）")
    match_parser.add_argument("--seed", type=_int_arg, default=None, help="随机种子")
    match_parser.add_argument("-o", "--output", default=None, help="输出 HTML 文件")

    chart_parser = subparsers.add_parser("chart", help="生成完整规则表")
    chart_parser.add_argument("-o", "--output", default=None, help="输出 HTML 文件")

    card_parser = subparsers.add_parser("card", help="生成单条规则卡片")
    card_parser.add_argument("pattern", help="字母组合")
    card_parser.add_argument("-o", "--output", default=None, help="输出 HTML 文件")

    return parser


def _write_output(path: str, content: str) -> None:
    """以 UTF-8 写入文件，失败时转换为中文 ValueError。"""
    if not isinstance(path, str):
        raise TypeError("输出路径必须是字符串")
    if not isinstance(content, str):
        raise TypeError("输出内容必须是字符串")
    target = path.strip()
    if not target:
        raise ValueError("输出路径不能为空")
    directory = os.path.dirname(os.path.abspath(target))
    try:
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(target, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
    except OSError as exc:
        detail = exc.strerror or str(exc)
        raise ValueError("无法写入文件 %s：%s" % (target, detail)) from exc
    print("已生成：%s" % target)


def _print_rule(rule: Rule) -> None:
    print("字母组合：%s" % rule.pattern)
    print("分类：%s" % rule.kind)
    print("发音：%s" % rule.sound)
    print("例词：%s" % "、".join(rule.examples))
    print("说明：%s" % rule.note)


def _print_words(pattern: str) -> None:
    rule = find_rule(pattern)
    words = examples_of(pattern)
    print("%s 的例词（共 %d 个）：%s" % (rule.pattern, len(words), "、".join(words)))


def _print_word(word: str) -> None:
    pattern = word_rule(word)
    rule = find_rule(pattern)
    print("单词：%s" % word.strip().lower())
    print("字母组合：%s" % pattern)
    print("分类：%s" % rule.kind)
    print("发音：%s" % rule.sound)
    print("说明：%s" % rule.note)


def _print_kind(kind: str) -> None:
    rules = rules_of(kind)
    print("%s（共 %d 条）" % (rules[0].kind, len(rules)))
    for index, rule in enumerate(rules, start=1):
        print(
            "%2d. %-8s %s　例词：%s"
            % (index, rule.pattern, rule.sound, "、".join(rule.examples))
        )


def _print_chart() -> None:
    rules = all_rules()
    print("自然拼读规则表（共 %d 条）" % len(rules))
    groups: Dict[str, List[Rule]] = {}
    for rule in rules:
        groups.setdefault(rule.kind, []).append(rule)
    for kind, group in groups.items():
        print("")
        print("【%s】" % kind)
        for rule in group:
            print(
                "  %-8s %-16s %s"
                % (rule.pattern, rule.sound, "、".join(rule.examples))
            )


def _print_quiz(items: Sequence[Dict[str, object]]) -> None:
    letters = "ABCDEFGH"
    for item in items:
        print("%s. %s" % (item["index"], item["question"]))
        options = item["options"]
        if isinstance(options, (list, tuple)):
            for position, option in enumerate(options):
                marker = letters[position] if position < len(letters) else str(position + 1)
                print("   %s. %s" % (marker, option))
        print("")
    print("参考答案与解析")
    for item in items:
        answer_index = item["answer_index"]
        if isinstance(answer_index, int):
            marker = (
                letters[answer_index]
                if answer_index < len(letters)
                else str(answer_index + 1)
            )
        else:
            marker = "?"
        print("%s. %s. %s" % (item["index"], marker, item["answer"]))
        print("   解析：%s" % item["explanation"])


def _print_match(pairs: Sequence[Tuple[str, str]]) -> None:
    print("字母组合—例词配对练习（共 %d 组）" % len(pairs))
    for index, (pattern, _) in enumerate(pairs, start=1):
        print("%2d. %s —— ____________" % (index, pattern))
    print("")
    print("参考答案")
    for index, (pattern, word) in enumerate(pairs, start=1):
        print("%2d. %s — %s" % (index, pattern, word))


def _run(args: argparse.Namespace) -> int:
    command = args.command
    if command == "rule":
        _print_rule(find_rule(args.pattern))
        return 0
    if command == "words":
        _print_words(args.pattern)
        return 0
    if command == "word":
        _print_word(args.word)
        return 0
    if command == "kind":
        _print_kind(args.kind)
        return 0
    if command == "quiz":
        items = quiz_items(args.count, args.seed, args.kind)
        if args.output is not None:
            _write_output(args.output, quiz_html(items, "自然拼读测验", with_answers=True))
        else:
            _print_quiz(items)
        return 0
    if command == "match":
        pairs = match_items(args.count, args.seed)
        if args.output is not None:
            _write_output(args.output, match_html(pairs, "自然拼读配对练习"))
        else:
            _print_match(pairs)
        return 0
    if command == "chart":
        if args.output is not None:
            _write_output(args.output, chart_html(all_rules()))
        else:
            _print_chart()
        return 0
    if command == "card":
        rule = find_rule(args.pattern)
        if args.output is not None:
            _write_output(args.output, card_html(rule))
        else:
            print("自然拼读卡片")
            print("")
            _print_rule(rule)
        return 0
    raise ValueError("未知命令：%s" % command)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """命令行主函数，成功返回 0，输入错误返回 2。"""
    _ensure_utf8_console()
    try:
        parser = _build_parser()
        args = parser.parse_args(argv)
        if args.command is None:
            parser.print_help()
            return 0
        return _run(args)
    except (TypeError, ValueError) as exc:
        print("错误：%s" % exc, file=sys.stderr)
        return 2
