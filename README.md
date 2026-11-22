# phonics

[![CI](https://github.com/eastyou/phonics/actions/workflows/ci.yml/badge.svg)](https://github.com/eastyou/phonics/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB.svg)](https://www.python.org/)

自然拼读（Phonics）教学工具：内置 56 条字母组合发音规则与 280 个常见单词，支持按单词反查字母组合、按分类浏览规则，并可生成可直接打印的规则表、四选一测验、配对练习和单条规则卡片。仅依赖 Python 标准库，适合英语课堂、课后练习与自学。

## 功能

- **规则库**：56 条规则，覆盖短元音（a/e/i/o/u）、magic e 长元音（a_e/i_e/o_e/u_e）、元音组合（ai/ay、ee/ea、oa/ow、oo 两种读音、ou/ow、oi/oy、au/aw）、辅音组合（sh/ch/th 清浊/wh/ph/ck/ng/nk）、19 组辅音连缀与 r 控制元音（ar/er/ir/or/ur）。
- **单词归组**：280 个常见单词显式映射到规则；`word_rule()` 对未收录单词也会按最长字母组合匹配，`ship → sh`、`cake → a_e`。
- **分类查询**：分类支持中英文别名，如 `short`、`long vowel`、`digraph`、`blend`、`r-controlled`。
- **练习生成**：四选一测验（给单词选字母组合，或给字母组合选发音/例词）、字母组合—例词配对；支持随机种子复现，干扰项自动去重并过滤“同样正确”的选项。
- **可打印页面**：规则表、A4 双列测验、配对练习与大字卡片，全部内置 `@page { size: A4 }` 与 `@media print` 样式，动态文本均经过 HTML 转义。
- **零依赖**：仅使用 Python 标准库，兼容 Python 3.9 至 3.15。

## 安装

需要 Python 3.9 或更高版本。

```bash
git clone https://github.com/eastyou/phonics.git
cd phonics
python -m pip install -e .
```

也可以不安装，直接在仓库根目录用 `python -m phonics` 运行。

## CLI 示例

```bash
phonics rule sh
```

```text
字母组合：sh
分类：辅音组合
发音：/ʃ/ 嘘
例词：ship、shop、fish、wish、shell
说明：sh 读「嘘」音，如 ship。
```

```bash
phonics word cake
```

```text
单词：cake
字母组合：a_e
分类：长元音
发音：/eɪ/（字母音 A）
说明：magic e：结尾的 e 不发音，前面的 a 读字母音。
```

```bash
phonics words sh
```

```text
sh 的例词（共 5 个）：ship、shop、fish、wish、shell
```

```bash
phonics kind 短元音
phonics quiz --count 10 --seed 5 -o examples/quiz.html
phonics match --count 8 --seed 3 -o examples/match.html
phonics chart -o examples/chart.html
phonics card a_e -o examples/card.html
```

带 `-o` 时只写文件并打印：

```text
已生成：examples/quiz.html
```

完整命令：

| 命令 | 说明 |
| --- | --- |
| `rule <字母组合>` | 查看单条规则的发音、例词与说明 |
| `words <字母组合>` | 列出该规则的例词 |
| `word <单词>` | 反查单词所属的字母组合 |
| `kind <分类>` | 列出某个分类下的全部规则 |
| `quiz --count N --seed S [--kind 分类] [-o 文件]` | 生成四选一测验 |
| `match --count N --seed S [-o 文件]` | 生成配对练习 |
| `chart [-o 文件]` | 输出完整规则表 |
| `card <字母组合> [-o 文件]` | 输出单条规则卡片 |

## 库用法

```python
from phonics import all_rules, find_rule, kind_of, match_items, quiz_items, word_rule
from phonics.render import card_html, chart_html, match_html, quiz_html

print(len(all_rules()))          # 56
print(word_rule("cake"))         # a_e
print(word_rule("book"))         # oo（短）
print(kind_of("sh"))             # 辅音组合
print(find_rule("sh").sound)     # /ʃ/ 嘘

items = quiz_items(10, seed=5)
pairs = match_items(8, seed=3)

with open("quiz.html", "w", encoding="utf-8") as handle:
    handle.write(quiz_html(items, "自然拼读测验", with_answers=True))
with open("chart.html", "w", encoding="utf-8") as handle:
    handle.write(chart_html(all_rules()))
with open("match.html", "w", encoding="utf-8") as handle:
    handle.write(match_html(pairs, "自然拼读配对练习"))
with open("card.html", "w", encoding="utf-8") as handle:
    handle.write(card_html(find_rule("a_e")))
```

所有对外函数均有完整的参数与返回值类型注解；类型错误抛出 `TypeError`，取值错误抛出 `ValueError`，错误消息为中文。

## 示例页

`examples/` 下的页面均由 CLI 真实生成，可直接用浏览器打开或打印为 A4：

- `examples/chart.html`：56 条规则分类总表。
- `examples/quiz.html`：10 道四选一测验，答案单独分页。
- `examples/match.html`：8 组字母组合—例词配对练习。
- `examples/card.html`：`a_e` 规则大字卡片，适合投屏。

## 测试

测试全部使用标准库 `unittest`，共 **140** 个测试，覆盖数据校验、查询、练习生成、HTML 转义、CLI 参数与文件导出。

```bash
python -m unittest discover -s tests -v
```

双版本实测结果（输出中的耗时会随机器波动）：

```text
# Python 3.9.6（/usr/bin/python3）
Ran 140 tests
OK

# Python 3.15.2（python3）
Ran 140 tests
OK
```

## 许可

MIT © 2026 eastyou
