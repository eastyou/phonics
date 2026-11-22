"""HTML 渲染：规则表、练习题、配对题与单条规则卡片。

生成的页面均为单文件、可直接打开或打印，内置 A4 打印样式。
"""

from __future__ import annotations

import html
from typing import Dict, List, Sequence, Tuple

from .model import Rule

__all__ = ["card_html", "chart_html", "match_html", "quiz_html"]

_BASE_CSS = """
* { box-sizing: border-box; }
body {
  margin: 0;
  padding: 20px;
  background: #f2f5f8;
  color: #1f2933;
  font-family: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
  line-height: 1.65;
}
main {
  max-width: 980px;
  margin: 0 auto;
  padding: 30px 34px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 8px 28px rgba(31, 41, 51, 0.08);
}
h1 { margin: 0 0 6px; font-size: 28px; letter-spacing: 0.02em; }
h2 { margin: 26px 0 10px; font-size: 20px; color: #17324d; }
h3 { margin: 0 0 6px; font-size: 17px; }
p { margin: 6px 0; }
.meta { color: #627d98; font-size: 14px; margin-bottom: 18px; }
.count { color: #829ab1; font-size: 13px; font-weight: 400; margin-left: 6px; }
table { width: 100%; border-collapse: collapse; margin: 8px 0 18px; }
th, td { border: 1px solid #cbd5e1; padding: 7px 10px; text-align: left; vertical-align: top; }
th { background: #eef4fa; font-weight: 600; white-space: nowrap; }
td.pattern, .pattern { font-family: Georgia, "Times New Roman", serif; font-weight: 700; font-size: 18px; }
.quiz { column-count: 2; column-gap: 28px; }
.question { break-inside: avoid; page-break-inside: avoid; margin: 0 0 18px; padding: 0 0 10px; border-bottom: 1px dashed #d9e2ec; }
.question .stem { font-weight: 600; margin: 0 0 8px; }
.option { display: flex; gap: 8px; padding: 2px 0; font-size: 15px; }
.letter { flex: 0 0 20px; font-weight: 700; color: #17324d; }
.answers { page-break-before: always; break-before: page; }
.answers td, .answers th { font-size: 14px; }
.match-grid { display: flex; gap: 30px; align-items: flex-start; }
.match-grid > div { flex: 1 1 0; }
.match-grid ol, .match-grid ul { margin: 8px 0 0; padding-left: 24px; }
.match-grid li { margin: 7px 0; }
.bank { list-style: none; padding-left: 0; }
.bank li { border: 1px solid #cbd5e1; border-radius: 999px; padding: 4px 12px; margin: 6px 0; background: #f8fafc; }
.card { border: 3px solid #17324d; border-radius: 18px; padding: 34px; text-align: center; }
.card .kind { color: #486581; letter-spacing: 0.3em; font-size: 14px; }
.card .big { font-family: Georgia, "Times New Roman", serif; font-size: 92px; font-weight: 700; line-height: 1.1; margin: 10px 0 4px; color: #102a43; }
.card .sound { font-size: 26px; color: #0b6e4f; margin: 0 0 20px; }
.chips { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; margin: 16px 0; padding: 0; list-style: none; }
.chips li { background: #e6f1f8; border-radius: 999px; padding: 7px 18px; font-size: 18px; }
.card .note { color: #52606d; margin-top: 16px; font-size: 15px; }
@page { size: A4; margin: 14mm; }
@media print {
  body { background: #ffffff; padding: 0; }
  main { max-width: none; padding: 0; border-radius: 0; box-shadow: none; }
  h2 { break-after: avoid; page-break-after: avoid; }
  tr { break-inside: avoid; page-break-inside: avoid; }
  .question { border-bottom: 1px solid #d9e2ec; }
}
"""


def _text(value: object, label: str) -> str:
    """校验非空字符串。"""
    if not isinstance(value, str):
        raise TypeError("%s必须是字符串，不能是 %s" % (label, type(value).__name__))
    text = value.strip()
    if not text:
        raise ValueError("%s不能为空" % label)
    return text


def _sequence(value: object, label: str) -> List[object]:
    """把输入转换为列表，拒绝字符串和不可迭代对象。"""
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise TypeError("%s必须是序列" % label)
    try:
        return list(value)
    except TypeError as exc:
        raise TypeError("%s必须是序列" % label) from exc


def _rule(value: object) -> Rule:
    """校验单个规则对象。"""
    if not isinstance(value, Rule):
        raise TypeError("规则必须是 Rule 对象")
    return value


def _rule_list(value: object) -> List[Rule]:
    """校验规则序列，拒绝空列表。"""
    items = _sequence(value, "规则列表")
    if not items:
        raise ValueError("规则列表不能为空")
    return [_rule(item) for item in items]


def _int_value(value: object, label: str) -> int:
    """校验非负整数，排除 bool。"""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("%s必须是整数，不能是 %s" % (label, type(value).__name__))
    if value < 0:
        raise ValueError("%s不能是负数" % label)
    return value


def _quiz_list(value: object) -> List[Dict[str, object]]:
    """校验题目列表的结构与取值。"""
    items = _sequence(value, "题目列表")
    if not items:
        raise ValueError("题目列表不能为空")
    checked: List[Dict[str, object]] = []
    for position, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise TypeError("第 %d 题必须是字典" % position)
        for key in ("index", "question", "options", "answer_index", "answer", "explanation"):
            if key not in item:
                raise ValueError("第 %d 题缺少字段：%s" % (position, key))
        index = _int_value(item["index"], "题号")
        if index < 1:
            raise ValueError("题号必须从 1 开始")
        question = _text(item["question"], "题目")
        answer = _text(item["answer"], "答案")
        explanation = _text(item["explanation"], "解析")
        raw_options = item["options"]
        options = _sequence(raw_options, "选项")
        if len(options) < 2:
            raise ValueError("第 %d 题至少需要两个选项" % position)
        clean_options: List[str] = []
        for option in options:
            clean_options.append(_text(option, "选项"))
        if len(set(clean_options)) != len(clean_options):
            raise ValueError("第 %d 题的选项必须唯一" % position)
        answer_index = _int_value(item["answer_index"], "答案序号")
        if answer_index >= len(clean_options):
            raise ValueError("第 %d 题的答案序号越界" % position)
        if clean_options[answer_index] != answer:
            raise ValueError("第 %d 题的答案与选项不一致" % position)
        checked.append(
            {
                "index": index,
                "question": question,
                "options": clean_options,
                "answer_index": answer_index,
                "answer": answer,
                "explanation": explanation,
            }
        )
    return checked


def _pair_list(value: object) -> List[Tuple[str, str]]:
    """校验配对题数据。"""
    items = _sequence(value, "配对列表")
    if not items:
        raise ValueError("配对列表不能为空")
    pairs: List[Tuple[str, str]] = []
    seen_patterns = set()
    seen_words = set()
    for position, item in enumerate(items, start=1):
        if not isinstance(item, (tuple, list)) or len(item) != 2:
            raise TypeError("第 %d 组配对必须是二元组" % position)
        pattern = _text(item[0], "字母组合")
        word = _text(item[1], "例词")
        if pattern in seen_patterns:
            raise ValueError("配对题中的字母组合重复：%s" % pattern)
        if word in seen_words:
            raise ValueError("配对题中的例词重复：%s" % word)
        seen_patterns.add(pattern)
        seen_words.add(word)
        pairs.append((pattern, word))
    return pairs


def _page(title: str, body: str) -> str:
    """拼接完整 HTML 页面。"""
    safe_title = html.escape(title)
    return (
        "<!DOCTYPE html>\n"
        '<html lang="zh-CN">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n"
        "<style>%s</style>\n"
        "</head>\n"
        "<body>\n"
        "<main>\n"
        "%s\n"
        "</main>\n"
        "</body>\n"
        "</html>\n"
    ) % (safe_title, _BASE_CSS, body)


def chart_html(rules: Sequence[Rule], title: str = "自然拼读规则表") -> str:
    """把规则按分类渲染为可打印的规则表。"""
    title_text = _text(title, "标题")
    items = _rule_list(rules)
    groups: Dict[str, List[Rule]] = {}
    for item in items:
        groups.setdefault(item.kind, []).append(item)
    sections: List[str] = []
    for kind, group in groups.items():
        rows: List[str] = []
        for item in group:
            examples = "、".join(html.escape(word) for word in item.examples)
            rows.append(
                "<tr><td class=\"pattern\">%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                % (
                    html.escape(item.pattern),
                    html.escape(item.sound),
                    examples,
                    html.escape(item.note),
                )
            )
        sections.append(
            "<section>\n"
            "<h2>%s<span class=\"count\">%d 条</span></h2>\n"
            "<table>\n"
            "<thead><tr><th>字母组合</th><th>发音</th><th>例词</th><th>说明</th></tr></thead>\n"
            "<tbody>\n%s\n</tbody>\n"
            "</table>\n"
            "</section>"
            % (html.escape(kind), len(group), "\n".join(rows))
        )
    header = (
        "<h1>%s</h1>\n<p class=\"meta\">共 %d 条规则，按分类整理，可直接打印张贴。</p>"
        % (html.escape(title_text), len(items))
    )
    return _page(title_text, header + "\n" + "\n".join(sections))


def quiz_html(
    items: Sequence[Dict[str, object]],
    title: str,
    with_answers: bool = False,
) -> str:
    """渲染 A4 双列四选一练习题，答案可单独分页。"""
    title_text = _text(title, "标题")
    if not isinstance(with_answers, bool):
        raise TypeError("with_answers 必须是布尔值")
    checked = _quiz_list(items)
    letters = "ABCDEFGH"
    questions: List[str] = []
    for item in checked:
        options = item["options"]
        if not isinstance(options, list):
            raise TypeError("选项必须是列表")
        option_lines: List[str] = []
        for position, option in enumerate(options):
            marker = letters[position] if position < len(letters) else str(position + 1)
            option_lines.append(
                '<div class="option"><span class="letter">%s</span><span>%s</span></div>'
                % (marker, html.escape(str(option)))
            )
        questions.append(
            '<article class="question">\n'
            '<p class="stem">%s. %s</p>\n'
            "%s\n"
            "</article>"
            % (
                item["index"],
                html.escape(str(item["question"])),
                "\n".join(option_lines),
            )
        )
    header = (
        "<h1>%s</h1>\n<p class=\"meta\">共 %d 题 · 四选一 · 姓名：__________　日期：__________</p>"
        % (html.escape(title_text), len(checked))
    )
    body = header + '\n<section class="quiz">\n' + "\n".join(questions) + "\n</section>"
    if with_answers:
        rows: List[str] = []
        for item in checked:
            answer_index = item["answer_index"]
            if not isinstance(answer_index, int):
                raise TypeError("答案序号必须是整数")
            marker = (
                letters[answer_index] if answer_index < len(letters) else str(answer_index + 1)
            )
            rows.append(
                "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                % (
                    item["index"],
                    marker,
                    html.escape(str(item["answer"])),
                    html.escape(str(item["explanation"])),
                )
            )
        body += (
            '\n<section class="answers">\n'
            "<h2>参考答案</h2>\n"
            "<table>\n"
            "<thead><tr><th>题号</th><th>选项</th><th>答案</th><th>解析</th></tr></thead>\n"
            "<tbody>\n%s\n</tbody>\n"
            "</table>\n"
            "</section>"
            % "\n".join(rows)
        )
    return _page(title_text, body)


def match_html(pairs: Sequence[Tuple[str, str]], title: str) -> str:
    """渲染「字母组合 — 例词」配对练习。"""
    title_text = _text(title, "标题")
    checked = _pair_list(pairs)
    left: List[str] = []
    for pattern, _ in checked:
        left.append("<li><span class=\"pattern\">%s</span></li>" % html.escape(pattern))
    bank_words = sorted(word for _, word in checked)
    bank: List[str] = []
    for word in bank_words:
        bank.append("<li>%s</li>" % html.escape(word))
    answers: List[str] = []
    for pattern, word in checked:
        answers.append(
            "<tr><td class=\"pattern\">%s</td><td>%s</td></tr>"
            % (html.escape(pattern), html.escape(word))
        )
    header = (
        "<h1>%s</h1>\n<p class=\"meta\">共 %d 组 · 把左侧字母组合与右侧例词连线。</p>"
        % (html.escape(title_text), len(checked))
    )
    grid = (
        '<section class="match-grid">\n'
        "<div><h2>字母组合</h2><ol>%s</ol></div>\n"
        "<div><h2>例词</h2><ul class=\"bank\">%s</ul></div>\n"
        "</section>"
        % ("\n".join(left), "\n".join(bank))
    )
    answer_section = (
        '\n<section class="answers">\n'
        "<h2>参考答案</h2>\n"
        "<table><thead><tr><th>字母组合</th><th>例词</th></tr></thead>\n"
        "<tbody>%s</tbody></table>\n"
        "</section>" % "\n".join(answers)
    )
    return _page(title_text, header + "\n" + grid + answer_section)


def card_html(rule: Rule) -> str:
    """渲染单条规则的大字卡片，适合投屏或打印。"""
    item = _rule(rule)
    title = "自然拼读卡片：%s" % item.pattern
    chips: List[str] = []
    for word in item.examples:
        chips.append("<li>%s</li>" % html.escape(word))
    body = (
        '<section class="card">\n'
        '<div class="kind">%s</div>\n'
        '<div class="big">%s</div>\n'
        '<div class="sound">%s</div>\n'
        "<ul class=\"chips\">%s</ul>\n"
        '<p class="note">%s</p>\n'
        "</section>"
        % (
            html.escape(item.kind),
            html.escape(item.pattern),
            html.escape(item.sound),
            "".join(chips),
            html.escape(item.note),
        )
    )
    return _page(title, body)
