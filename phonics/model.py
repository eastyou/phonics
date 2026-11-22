"""自然拼读数据模型：字母组合规则、单词库与练习题目生成。

数据全部内置，仅依赖 Python 标准库。所有对外函数都会校验输入：
类型错误抛出 :class:`TypeError`，取值错误抛出 :class:`ValueError`。
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

__all__ = [
    "Rule",
    "all_rules",
    "examples_of",
    "find_rule",
    "kind_of",
    "match_items",
    "quiz_items",
    "rules_of",
    "word_rule",
]

_KIND_ORDER: Tuple[str, ...] = (
    "短元音",
    "长元音",
    "元音组合",
    "辅音组合",
    "辅音连缀",
    "r 控制",
)

_KIND_ALIASES: Dict[str, str] = {
    "短元音": "短元音",
    "短": "短元音",
    "short": "短元音",
    "short vowel": "短元音",
    "长元音": "长元音",
    "长": "长元音",
    "long": "长元音",
    "long vowel": "长元音",
    "元音组合": "元音组合",
    "元音": "元音组合",
    "vowel team": "元音组合",
    "vowel-team": "元音组合",
    "辅音组合": "辅音组合",
    "双辅音": "辅音组合",
    "digraph": "辅音组合",
    "consonant digraph": "辅音组合",
    "辅音连缀": "辅音连缀",
    "连缀": "辅音连缀",
    "blend": "辅音连缀",
    "consonant blend": "辅音连缀",
    "r 控制": "r 控制",
    "r控制": "r 控制",
    "r音节": "r 控制",
    "r-controlled": "r 控制",
    "r controlled": "r 控制",
}

_VOWELS: str = "aeiou"


@dataclass(frozen=True)
class Rule:
    """一条自然拼读规则。"""

    pattern: str
    sound: str
    kind: str
    examples: Tuple[str, ...]
    note: str


def _require_text(value: object, label: str) -> str:
    """校验非空字符串，返回去除首尾空白后的文本。"""
    if not isinstance(value, str):
        raise TypeError("%s必须是字符串，不能是 %s" % (label, type(value).__name__))
    text = value.strip()
    if not text:
        raise ValueError("%s不能为空" % label)
    return text


def _require_int(value: object, label: str) -> int:
    """校验整数输入，显式排除 bool。"""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("%s必须是整数，不能是 %s" % (label, type(value).__name__))
    return value


def _require_optional_int(value: Optional[int], label: str) -> Optional[int]:
    """校验可为空的整数（例如随机种子）。"""
    if value is None:
        return None
    return _require_int(value, label)


def _normalize_kind(kind: object) -> str:
    """把分类名称或别名规范化为标准分类。"""
    text = _require_text(kind, "分类")
    key = " ".join(text.lower().split())
    if key not in _KIND_ALIASES:
        raise ValueError(
            "未知分类：%s；可用分类：%s" % (text, "、".join(_KIND_ORDER))
        )
    return _KIND_ALIASES[key]


def _is_magic_e(pattern: str, word: str) -> bool:
    """判断单词是否符合「元音 + 单个辅音 + e」的 magic e 结构。"""
    parts = pattern.split("_")
    if len(parts) != 2:
        return False
    prefix, suffix = parts
    if not prefix or not suffix:
        return False
    if len(word) < 3 or not word.endswith(suffix):
        return False
    if word[-3] != prefix:
        return False
    middle = word[-2]
    return middle.isalpha() and middle not in _VOWELS


def _grapheme(pattern: str) -> str:
    """取出规则中真正参与拼写的字母部分。"""
    return pattern.split("（")[0]


def _rule_matches_word(rule: Rule, word: str) -> bool:
    """判断规则是否出现在单词中（magic e 规则单独处理）。"""
    grapheme = _grapheme(rule.pattern)
    if "_" in grapheme:
        return _is_magic_e(grapheme, word)
    return grapheme in word


def _pattern_weight(rule: Rule) -> int:
    """计算匹配优先级：magic e 权重最高，其余按字母数。"""
    grapheme = _grapheme(rule.pattern)
    if "_" in grapheme:
        return 3
    return len(grapheme)


def _validate_rules(rules: Sequence[Rule]) -> Tuple[Rule, ...]:
    """校验内置规则数据，发现错误立即抛出 ValueError。"""
    if not rules:
        raise ValueError("拼读规则数据不能为空")
    seen: Dict[str, str] = {}
    for rule in rules:
        if not isinstance(rule, Rule):
            raise TypeError("规则数据必须是 Rule 对象")
        if rule.pattern != rule.pattern.strip().lower():
            raise ValueError("规则 pattern 必须小写且不含首尾空格：%r" % rule.pattern)
        if rule.pattern in seen:
            raise ValueError("规则 pattern 重复：%s" % rule.pattern)
        seen[rule.pattern] = rule.pattern
        if rule.kind not in _KIND_ORDER:
            raise ValueError("规则 %s 的分类不合法：%s" % (rule.pattern, rule.kind))
        if not isinstance(rule.sound, str) or not rule.sound.strip():
            raise ValueError("规则 %s 的发音说明不能为空" % rule.pattern)
        if not isinstance(rule.note, str) or not rule.note.strip():
            raise ValueError("规则 %s 的说明不能为空" % rule.pattern)
        if not isinstance(rule.examples, tuple):
            raise TypeError("规则 %s 的例词必须是元组" % rule.pattern)
        if len(rule.examples) < 3 or len(rule.examples) > 5:
            raise ValueError("规则 %s 的例词数量必须在 3 到 5 之间" % rule.pattern)
        for example in rule.examples:
            if not isinstance(example, str):
                raise TypeError("规则 %s 的例词必须是字符串" % rule.pattern)
            if example != example.strip().lower():
                raise ValueError("规则 %s 的例词必须小写：%r" % (rule.pattern, example))
            if not example.isascii() or not example.isalpha():
                raise ValueError("规则 %s 的例词只能包含英文字母：%r" % (rule.pattern, example))
    return tuple(rules)


_RULES: Tuple[Rule, ...] = _validate_rules(
    (
        # 短元音（CVC）
        Rule("a", "/æ/（短「哎」）", "短元音", ("cat", "map", "bag", "hat", "jam"),
             "CVC 结构中的 a 通常读短音，如 cat。"),
        Rule("e", "/e/（短「诶」）", "短元音", ("bed", "pen", "red", "ten", "hen"),
             "嘴形扁平、舌位中前，如 bed。"),
        Rule("i", "/ɪ/（短「衣」）", "短元音", ("pig", "sit", "big", "six", "lip"),
             "短促的「衣」，不要拖成长音，如 pig。"),
        Rule("o", "/ɒ/（短「奥」）", "短元音", ("dog", "hot", "box", "mop", "pot"),
             "英式短 o，嘴形圆，如 dog。"),
        Rule("u", "/ʌ/（短「啊」）", "短元音", ("cup", "bus", "sun", "run", "mug"),
             "短促的「啊」，如 cup。"),
        # 长元音（magic e）
        Rule("a_e", "/eɪ/（字母音 A）", "长元音", ("cake", "name", "lake", "game", "tape"),
             "magic e：结尾的 e 不发音，前面的 a 读字母音。"),
        Rule("i_e", "/aɪ/（字母音 I）", "长元音", ("bike", "kite", "time", "five", "ride"),
             "magic e：i 读字母音，如 bike。"),
        Rule("o_e", "/oʊ/（字母音 O）", "长元音", ("home", "nose", "rope", "bone", "hope"),
             "magic e：o 读字母音，如 home。"),
        Rule("u_e", "/juː/（字母音 U）", "长元音", ("cube", "cute", "tube", "mute", "huge"),
             "magic e：u 多读 /juː/，如 cube；少数词读 /uː/。"),
        # 元音组合
        Rule("ai", "/eɪ/", "元音组合", ("rain", "tail", "wait", "mail", "paint"),
             "ai 多出现在词中，如 rain；词尾常用 ay。"),
        Rule("ay", "/eɪ/", "元音组合", ("day", "play", "stay", "may", "gray"),
             "ay 多出现在词尾，如 day。"),
        Rule("ee", "/iː/", "元音组合", ("bee", "tree", "see", "feet", "green"),
             "ee 通常读长音「衣」，如 bee。"),
        Rule("ea", "/iː/", "元音组合", ("tea", "sea", "read", "meat", "eat"),
             "ea 常读长音「衣」，但 bread 等词读短音 /e/。"),
        Rule("oa", "/oʊ/", "元音组合", ("boat", "coat", "road", "soap", "goat"),
             "oa 常读字母音 O，如 boat。"),
        Rule("ow", "/oʊ/", "元音组合", ("snow", "grow", "show", "low", "yellow"),
             "ow 在 snow、grow 中读 /oʊ/；在 cow 中读 /aʊ/。"),
        Rule("oo", "/uː/", "元音组合", ("moon", "food", "zoo", "room", "boot"),
             "oo 在 moon 中读长音 /uː/。"),
        Rule("oo（短）", "/ʊ/", "元音组合", ("book", "look", "cook", "good", "foot"),
             "oo 在 book、good、foot 中读短音 /ʊ/，常见于 k、d 前。"),
        Rule("ou", "/aʊ/", "元音组合", ("out", "loud", "cloud", "mouse", "house"),
             "ou 常读 /aʊ/，如 out；在 you 中读 /uː/。"),
        Rule("ow（/aʊ/）", "/aʊ/", "元音组合", ("cow", "how", "now", "town", "brown"),
             "ow 在 cow、now 中读 /aʊ/，与 snow 的 /oʊ/ 不同。"),
        Rule("oi", "/ɔɪ/", "元音组合", ("coin", "join", "oil", "soil", "point"),
             "oi 多出现在词中，如 coin。"),
        Rule("oy", "/ɔɪ/", "元音组合", ("boy", "toy", "joy", "enjoy", "royal"),
             "oy 多出现在词尾，如 boy。"),
        Rule("au", "/ɔː/", "元音组合", ("sauce", "pause", "author", "launch", "audio"),
             "au 常读长音「奥」，如 sauce。"),
        Rule("aw", "/ɔː/", "元音组合", ("saw", "paw", "draw", "straw", "lawn"),
             "aw 常读长音「奥」，如 saw。"),
        # 辅音组合（digraph）
        Rule("sh", "/ʃ/ 嘘", "辅音组合", ("ship", "shop", "fish", "wish", "shell"),
             "sh 读「嘘」音，如 ship。"),
        Rule("ch", "/tʃ/ 吃", "辅音组合", ("chip", "chop", "chin", "lunch", "chick"),
             "ch 常读「吃」音，如 chair；school 中读 /k/。"),
        Rule("th", "/θ/ 咬舌清音", "辅音组合", ("thin", "think", "bath", "math", "thumb"),
             "舌尖轻触上齿，送气但不振动声带，如 thin。"),
        Rule("th（浊）", "/ð/ 咬舌浊音", "辅音组合", ("this", "that", "then", "them", "these"),
             "舌尖轻触上齿，振动声带，如 this。"),
        Rule("wh", "/w/ 呜", "辅音组合", ("when", "what", "whip", "which", "whim"),
             "wh 多读 /w/，如 when；who 中读 /h/。"),
        Rule("ph", "/f/ 夫", "辅音组合", ("phone", "photo", "graph", "dolphin", "elephant"),
             "ph 读 /f/，多来自希腊语，如 phone。"),
        Rule("ck", "/k/ 克", "辅音组合", ("duck", "sock", "kick", "rock", "black"),
             "ck 只出现在短元音后，如 duck。"),
        Rule("ng", "/ŋ/ 嗡", "辅音组合", ("sing", "ring", "long", "king", "song"),
             "ng 是鼻音，如 sing；不要读成 /n/ 加 /g/。"),
        Rule("nk", "/ŋk/", "辅音组合", ("bank", "pink", "trunk", "sink", "wink"),
             "nk 读 /ŋk/，如 bank。"),
        # 辅音连缀（blend）
        Rule("bl", "/bl/", "辅音连缀", ("blue", "block", "blush", "blast", "blend"),
             "b 与 l 快速连读，中间不要加元音。"),
        Rule("cl", "/kl/", "辅音连缀", ("clap", "clock", "climb", "class", "club"),
             "c 与 l 快速连读，如 clap。"),
        Rule("fl", "/fl/", "辅音连缀", ("flag", "flap", "flip", "flat", "floss"),
             "f 与 l 快速连读，如 flag。"),
        Rule("gl", "/gl/", "辅音连缀", ("glad", "glass", "glue", "gloss", "glum"),
             "g 与 l 快速连读，如 glad。"),
        Rule("pl", "/pl/", "辅音连缀", ("plan", "plus", "plant", "plug", "plum"),
             "p 与 l 快速连读，如 plan。"),
        Rule("sl", "/sl/", "辅音连缀", ("slip", "sled", "slim", "slot", "slam"),
             "s 与 l 快速连读，如 slip。"),
        Rule("br", "/br/", "辅音连缀", ("bring", "brush", "brick", "brisk", "brag"),
             "b 与 r 快速连读，如 bring。"),
        Rule("cr", "/kr/", "辅音连缀", ("crab", "cry", "cross", "crash", "crisp"),
             "c 与 r 快速连读，如 crab。"),
        Rule("dr", "/dr/", "辅音连缀", ("drum", "dress", "drop", "dragon", "drip"),
             "d 与 r 快速连读，如 drum。"),
        Rule("fr", "/fr/", "辅音连缀", ("frog", "fresh", "frost", "frill", "frank"),
             "f 与 r 快速连读，如 frog。"),
        Rule("gr", "/gr/", "辅音连缀", ("grass", "grab", "grand", "grin", "grill"),
             "g 与 r 快速连读，如 grass。"),
        Rule("pr", "/pr/", "辅音连缀", ("print", "press", "prop", "prep", "prim"),
             "p 与 r 快速连读，如 print。"),
        Rule("tr", "/tr/", "辅音连缀", ("try", "truck", "trip", "track", "trash"),
             "t 与 r 快速连读，如 try。"),
        Rule("st", "/st/", "辅音连缀", ("stop", "step", "stick", "stamp", "stump"),
             "s 与 t 快速连读，如 stop。"),
        Rule("sp", "/sp/", "辅音连缀", ("spin", "spot", "spill", "spell", "spend"),
             "s 与 p 快速连读，如 spin。"),
        Rule("sk", "/sk/", "辅音连缀", ("skip", "sky", "skin", "skill", "skull"),
             "s 与 k 快速连读，如 skip。"),
        Rule("sm", "/sm/", "辅音连缀", ("small", "smell", "smart", "smash", "smog"),
             "s 与 m 快速连读，如 small。"),
        Rule("sn", "/sn/", "辅音连缀", ("snap", "snack", "sniff", "snug", "snub"),
             "s 与 n 快速连读，如 snap。"),
        Rule("sw", "/sw/", "辅音连缀", ("swim", "swan", "swing", "swift", "swell"),
             "s 与 w 快速连读，如 swim。"),
        # r 控制元音
        Rule("ar", "/ɑːr/ 啊儿", "r 控制", ("car", "star", "farm", "park", "hard"),
             "ar 常读 /ɑːr/，如 car。"),
        Rule("er", "/ər/ 儿", "r 控制", ("her", "teacher", "sister", "dinner", "water"),
             "er 在词尾常读弱化的 /ər/，如 sister。"),
        Rule("ir", "/ɜːr/", "r 控制", ("bird", "girl", "shirt", "skirt", "first"),
             "ir 常读 /ɜːr/，如 bird。"),
        Rule("or", "/ɔːr/", "r 控制", ("fork", "horse", "corn", "short", "storm"),
             "or 常读 /ɔːr/，如 fork。"),
        Rule("ur", "/ɜːr/", "r 控制", ("turn", "burn", "hurt", "nurse", "purple"),
             "ur 常读 /ɜːr/，如 turn。"),
    )
)

_WORD_GROUPS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("a", ("cat", "map", "bag", "hat", "jam")),
    ("e", ("bed", "pen", "red", "ten", "hen")),
    ("i", ("pig", "sit", "big", "six", "lip")),
    ("o", ("dog", "hot", "box", "mop", "pot")),
    ("u", ("cup", "bus", "sun", "run", "mug")),
    ("a_e", ("cake", "name", "lake", "game", "tape")),
    ("i_e", ("bike", "kite", "time", "five", "ride")),
    ("o_e", ("home", "nose", "rope", "bone", "hope")),
    ("u_e", ("cube", "cute", "tube", "mute", "huge")),
    ("ai", ("rain", "tail", "wait", "mail", "paint")),
    ("ay", ("day", "play", "stay", "may", "gray")),
    ("ee", ("bee", "tree", "see", "feet", "green")),
    ("ea", ("tea", "sea", "read", "meat", "eat")),
    ("oa", ("boat", "coat", "road", "soap", "goat")),
    ("ow", ("snow", "grow", "show", "low", "yellow")),
    ("oo", ("moon", "food", "zoo", "room", "boot")),
    ("oo（短）", ("book", "look", "cook", "good", "foot")),
    ("ou", ("out", "loud", "cloud", "mouse", "house")),
    ("ow（/aʊ/）", ("cow", "how", "now", "town", "brown")),
    ("oi", ("coin", "join", "oil", "soil", "point")),
    ("oy", ("boy", "toy", "joy", "enjoy", "royal")),
    ("au", ("sauce", "pause", "author", "launch", "audio")),
    ("aw", ("saw", "paw", "draw", "straw", "lawn")),
    ("sh", ("ship", "shop", "fish", "wish", "shell")),
    ("ch", ("chip", "chop", "chin", "lunch", "chick")),
    ("th", ("thin", "think", "bath", "math", "thumb")),
    ("th（浊）", ("this", "that", "then", "them", "these")),
    ("wh", ("when", "what", "whip", "which", "whim")),
    ("ph", ("phone", "photo", "graph", "dolphin", "elephant")),
    ("ck", ("duck", "sock", "kick", "rock", "black")),
    ("ng", ("sing", "ring", "long", "king", "song")),
    ("nk", ("bank", "pink", "trunk", "sink", "wink")),
    ("bl", ("blue", "block", "blush", "blast", "blend")),
    ("cl", ("clap", "clock", "climb", "class", "club")),
    ("fl", ("flag", "flap", "flip", "flat", "floss")),
    ("gl", ("glad", "glass", "glue", "gloss", "glum")),
    ("pl", ("plan", "plus", "plant", "plug", "plum")),
    ("sl", ("slip", "sled", "slim", "slot", "slam")),
    ("br", ("bring", "brush", "brick", "brisk", "brag")),
    ("cr", ("crab", "cry", "cross", "crash", "crisp")),
    ("dr", ("drum", "dress", "drop", "dragon", "drip")),
    ("fr", ("frog", "fresh", "frost", "frill", "frank")),
    ("gr", ("grass", "grab", "grand", "grin", "grill")),
    ("pr", ("print", "press", "prop", "prep", "prim")),
    ("tr", ("try", "truck", "trip", "track", "trash")),
    ("st", ("stop", "step", "stick", "stamp", "stump")),
    ("sp", ("spin", "spot", "spill", "spell", "spend")),
    ("sk", ("skip", "sky", "skin", "skill", "skull")),
    ("sm", ("small", "smell", "smart", "smash", "smog")),
    ("sn", ("snap", "snack", "sniff", "snug", "snub")),
    ("sw", ("swim", "swan", "swing", "swift", "swell")),
    ("ar", ("car", "star", "farm", "park", "hard")),
    ("er", ("her", "teacher", "sister", "dinner", "water")),
    ("ir", ("bird", "girl", "shirt", "skirt", "first")),
    ("or", ("fork", "horse", "corn", "short", "storm")),
    ("ur", ("turn", "burn", "hurt", "nurse", "purple")),
)


def _validate_word_groups(
    groups: Sequence[Tuple[str, Tuple[str, ...]]], rules: Sequence[Rule]
) -> Dict[str, str]:
    """校验单词库，返回「小写单词 -> pattern」映射。"""
    lookup = {rule.pattern: rule for rule in rules}
    mapping: Dict[str, str] = {}
    for pattern, words in groups:
        if pattern not in lookup:
            raise ValueError("单词库引用了不存在的规则：%s" % pattern)
        if not isinstance(words, tuple):
            raise TypeError("规则 %s 的单词库必须是元组" % pattern)
        rule = lookup[pattern]
        for word in words:
            if not isinstance(word, str):
                raise TypeError("单词库中的单词必须是字符串")
            if word != word.strip().lower():
                raise ValueError("单词库中的单词必须小写：%r" % word)
            if not word.isascii() or not word.isalpha():
                raise ValueError("单词库中的单词只能包含英文字母：%r" % word)
            if not _rule_matches_word(rule, word):
                raise ValueError("单词 %s 与规则 %s 不匹配" % (word, pattern))
            previous = mapping.get(word)
            if previous is not None and previous != pattern:
                raise ValueError(
                    "单词 %s 同时映射到 %s 和 %s" % (word, previous, pattern)
                )
            mapping[word] = pattern
    if len(mapping) < 120:
        raise ValueError("单词库至少需要 120 个单词，当前只有 %d 个" % len(mapping))
    return mapping


_WORD_RULES: Dict[str, str] = _validate_word_groups(_WORD_GROUPS, _RULES)


def all_rules() -> List[Rule]:
    """返回全部拼读规则（按内置顺序）。"""
    return list(_RULES)


def rules_of(kind: str) -> List[Rule]:
    """按分类返回规则，分类支持中英文别名。"""
    normalized = _normalize_kind(kind)
    return [rule for rule in _RULES if rule.kind == normalized]


def find_rule(pattern: str) -> Rule:
    """按字母组合查找规则，大小写不敏感。"""
    text = _require_text(pattern, "字母组合")
    key = text.lower()
    for rule in _RULES:
        if rule.pattern.lower() == key:
            return rule
    raise ValueError(
        "未知字母组合：%s；可用字母组合：%s"
        % (text, "、".join(rule.pattern for rule in _RULES))
    )


def _require_word(word: object) -> str:
    """校验并规范化单词输入。"""
    text = _require_text(word, "单词")
    key = text.lower()
    if not key.isascii() or not key.isalpha():
        raise ValueError("单词只能包含英文字母：%s" % text)
    return key


def word_rule(word: str) -> str:
    """返回单词所属的字母组合 pattern（最长匹配优先）。"""
    key = _require_word(word)
    mapped = _WORD_RULES.get(key)
    if mapped is not None:
        return mapped
    matches = [rule for rule in _RULES if _rule_matches_word(rule, key)]
    if not matches:
        raise ValueError("未收录的单词：%s" % key)
    matches.sort(key=_pattern_weight, reverse=True)
    return matches[0].pattern


def examples_of(pattern: str) -> List[str]:
    """返回某个字母组合的例词列表。"""
    return list(find_rule(pattern).examples)


def kind_of(pattern: str) -> str:
    """返回某个字母组合所属的分类。"""
    return find_rule(pattern).kind


def _unique_strings(values: Iterable[str]) -> List[str]:
    """按出现顺序去重，返回字符串列表。"""
    seen = set()
    result: List[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _pick_options(rng: random.Random, answer: str, pool: Sequence[str]) -> List[str]:
    """从候选池中挑出三个干扰项，和答案一起打乱。"""
    candidates = [value for value in _unique_strings(pool) if value != answer]
    if len(candidates) < 3:
        raise ValueError("干扰项不足，无法生成四选一题目")
    options = [answer] + rng.sample(candidates, 3)
    rng.shuffle(options)
    return options


def quiz_items(
    count: int,
    seed: Optional[int] = None,
    kind: Optional[str] = None,
) -> List[Dict[str, object]]:
    """生成四选一练习题。

    题目有两种形式：给出单词选字母组合，或给出字母组合选发音 / 例词。
    """
    count_value = _require_int(count, "题目数量")
    if count_value < 1 or count_value > 40:
        raise ValueError("题目数量必须在 1 到 40 之间，当前为 %d" % count_value)
    seed_value = _require_optional_int(seed, "随机种子")
    if kind is None:
        pool = all_rules()
    else:
        pool = rules_of(kind)
    if len(pool) < 4:
        raise ValueError("可选规则不足 4 条，无法生成四选一题目")
    rng = random.Random(seed_value)
    items: List[Dict[str, object]] = []
    for index in range(1, count_value + 1):
        rule = rng.choice(pool)
        if rng.random() < 0.5:
            word = rng.choice(list(rule.examples))
            answer = rule.pattern
            distractors = [
                other.pattern
                for other in _RULES
                if other.pattern != answer and not _rule_matches_word(other, word)
            ]
            options = _pick_options(rng, answer, distractors)
            question = "单词 “%s” 中属于「%s」的字母组合是？" % (word, rule.kind)
            explanation = "“%s”中的 %s 读作 %s。" % (word, answer, rule.sound)
        else:
            if rng.random() < 0.5:
                answer = rule.sound
                distractors = [
                    other.sound for other in _RULES if other.sound != answer
                ]
                options = _pick_options(rng, answer, distractors)
                question = "字母组合 %s 通常读作？" % rule.pattern
                explanation = "%s 读作 %s。例词：%s。" % (
                    rule.pattern,
                    rule.sound,
                    "、".join(rule.examples),
                )
            else:
                answer = rng.choice(list(rule.examples))
                distractors = []
                for other in _RULES:
                    if other.pattern == rule.pattern:
                        continue
                    for example in other.examples:
                        if not _rule_matches_word(rule, example):
                            distractors.append(example)
                options = _pick_options(rng, answer, distractors)
                question = "下列哪个单词包含字母组合 %s？" % rule.pattern
                explanation = "“%s”包含 %s，读作 %s。" % (
                    answer,
                    rule.pattern,
                    rule.sound,
                )
        answer_index = options.index(answer)
        items.append(
            {
                "index": index,
                "question": question,
                "options": options,
                "answer_index": answer_index,
                "answer": answer,
                "explanation": explanation,
            }
        )
    return items


def match_items(count: int, seed: Optional[int] = None) -> List[Tuple[str, str]]:
    """生成「字母组合 — 例词」配对题。"""
    count_value = _require_int(count, "配对数量")
    if count_value < 1 or count_value > 20:
        raise ValueError("配对数量必须在 1 到 20 之间，当前为 %d" % count_value)
    seed_value = _require_optional_int(seed, "随机种子")
    rng = random.Random(seed_value)
    chosen = rng.sample(list(_RULES), count_value)
    pairs: List[Tuple[str, str]] = []
    used_words = set()
    for rule in chosen:
        candidates = [word for word in rule.examples if word not in used_words]
        if not candidates:
            raise ValueError("配对题例词不足：%s" % rule.pattern)
        word = rng.choice(candidates)
        used_words.add(word)
        pairs.append((rule.pattern, word))
    return pairs
