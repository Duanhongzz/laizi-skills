#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
重写语料库构建：更好的清洗 + 质量评分 + 模糊检索（v2）
v2.0: 别名扩展 + 子串模糊回退 + 精确匹配优先
"""
import json, re
import argparse
from functools import lru_cache
from pathlib import Path

try:
    from pypinyin import lazy_pinyin
except ImportError:
    lazy_pinyin = None

# =============================================================================
# 别名词典 —— 从 SKILL.md 提取的所有人物/事件名变体
# =============================================================================
ALIASES = {
    # 人物：本名 ↔ 外号/别称
    '小林酱': ['小林将', '小林酱'],
    '小林将': ['小林酱', '小林将'],
    '谢小亮': ['解小亮', '谢小亮'],
    '解小亮': ['谢小亮', '解小亮'],
    '陈小咩': ['抛子', '陈小咩', '小咩'],
    '抛子':   ['陈小咩', '抛子', '小咩'],
    '小咩':   ['陈小咩', '抛子', '小咩'],
    '寒溟':   ['拐子', '寒溟', '寒冥', '韩明'],
    '寒冥':   ['拐子', '寒溟', '寒冥', '韩明'],
    '韩明':   ['拐子', '寒溟', '寒冥', '韩明'],
    '拐子':   ['寒溟', '寒冥', '韩明', '拐子'],
    '晓风':   ['枫卿十一', '枫卿十', '枫哥', '晓风'],
    '枫卿十一': ['晓风', '枫卿十一', '枫卿十', '枫哥'],
    '枫卿十': ['晓风', '枫卿十一', '枫卿十', '枫哥'],
    '枫哥': ['晓风', '枫卿十一', '枫卿十', '枫哥'],
    '天月':   ['穆天月', '天月啾啾', '天月'],
    '穆天月': ['天月', '天月啾啾', '穆天月'],
    '天月啾啾': ['天月', '穆天月', '天月啾啾'],
    '369':    ['歪牜', '歪牛', '369', '小炫', '小炫quq'],
    '歪牜':   ['369', '歪牛', '歪牜', '小炫', '小炫quq'],
    '歪牛':   ['369', '歪牛', '歪牜', '小炫', '小炫quq'],
    '小炫':   ['369', '歪牛', '歪牜', '小炫', '小炫quq'],
    '小炫quq': ['369', '歪牛', '歪牜', '小炫', '小炫quq'],
    '鸭哥':   ['压哥', '鸭哥', '鴨哥'],
    '压哥':   ['鸭哥', '压哥', '鴨哥'],
    '鴨哥':   ['鸭哥', '压哥', '鴨哥'],
    '赖子':   ['老赖', '赖总', '赖老板', '赖哥', '赖格', '赖的', '赖子'],
    '老赖':   ['赖子', '赖总', '赖老板', '赖哥', '赖格', '赖的', '老赖'],
    '赖总':   ['赖子', '老赖', '赖老板', '赖哥', '赖格', '赖的', '赖总'],
    '赖老板': ['赖子', '老赖', '赖总', '赖哥', '赖格', '赖的', '赖老板'],
    '赖哥':   ['赖子', '老赖', '赖总', '赖老板', '赖格', '赖的', '赖哥'],
    '赖格':   ['赖子', '老赖', '赖总', '赖老板', '赖哥', '赖的', '赖格'],
    '赖的':   ['赖子', '老赖', '赖总', '赖老板', '赖哥', '赖格', '赖的'],
    '苟立国': ['苟立国', '苟利国', '苟老板'],
    '苟利国': ['苟立国', '苟利国', '苟老板'],
    '苟老板': ['苟立国', '苟利国', '苟老板'],
    '叶凡':   ['叶凡', '叶老板'],
    '叶老板': ['叶凡', '叶老板'],
    '念我纪': ['念我纪', '赖孝女念我纪'],
    '暮上澜归': ['暮上澜归', '暮上'],
    '长戈':   ['长戈', '长戈与伴'],
    '长戈与伴': ['长戈', '长戈与伴'],
    '南屿':   ['南屿', '南屿帮会', '南屿联盟'],
    '南屿帮会': ['南屿', '南屿帮会', '南屿联盟'],
    '张大进': ['张大进', '大进'],
    '大进':   ['张大进', '大进'],
    '舒小晴': ['舒小晴', '舒小'],
    '默泽':   ['默泽', '阵营之蛆'],
    '阵营之蛆': ['默泽', '阵营之蛆'],
    '凌雪瑶': ['凌雪瑶', '雪瑶'],
    '莫念':   ['莫念', '莫念帮主'],
    '不太甜': ['不太甜', '不太甜老板'],
    '冷月':   ['冷月', '冷月妹子', '小小冷月'],
    '虎跳跳': ['虎跳跳', '跳跳', '虎跳跳跳跳跳'],
    '孤寺寺': ['孤寺寺', '顾寺寺', '古寺寺'],
    '顾寺寺': ['孤寺寺', '顾寺寺', '古寺寺'],
    '古寺寺': ['孤寺寺', '顾寺寺', '古寺寺'],
    '双塘': ['双塘', '双唐', '双糖', '笑糖', '双膛', '双堂'],
    '双唐': ['双塘', '双唐', '双糖', '笑糖', '双膛', '双堂'],
    '双糖': ['双塘', '双唐', '双糖', '笑糖', '双膛', '双堂'],
    '笑糖': ['双塘', '双唐', '双糖', '笑糖', '双膛', '双堂'],
    '双膛': ['双塘', '双唐', '双糖', '笑糖', '双膛', '双堂'],
    '双堂': ['双塘', '双唐', '双糖', '笑糖', '双膛', '双堂'],
    # 事件/地名
    '反攻双梦': ['反攻双梦', '反攻双梦运动', '双梦反攻'],
    '四季大和解': ['四季大和解', '四季和解', '大和解'],
    '帮会联赛': ['帮会联赛', '联赛', '第一届联赛'],
    '落赖坡': ['落赖坡', '白龙口'],
    # 梗
    '鱼香肉丝': ['鱼香肉丝', '外卖店', '甜口鱼香肉丝'],
    '开天眼': ['开天眼', '塞007', '天眼007'],
    '邪门CP':  ['邪门CP', '赖子369'],
    # 秦子37集新人物（2025-2026赛季）
    '岳将臣': ['岳将臣', '乐将陈', '越降城', '岳老板', '岳壤陈', '岳酱臣', '乐老板', '尔江'],
    '乐将陈': ['乐将陈', '岳将臣', '越降城', '岳老板', '岳壤陈', '岳酱臣', '乐老板', '尔江'],
    '越降城': ['乐将陈', '岳将臣', '越降城', '岳老板', '岳壤陈', '岳酱臣', '乐老板', '尔江'],
    '岳老板': ['乐将陈', '岳将臣', '越降城', '岳老板', '岳壤陈', '岳酱臣', '乐老板', '尔江'],
    '乐老板': ['乐将陈', '岳将臣', '越降城', '岳老板', '岳壤陈', '岳酱臣', '乐老板', '尔江'],
    '岳壤陈': ['乐将陈', '岳将臣', '越降城', '岳老板', '岳壤陈', '岳酱臣', '乐老板', '尔江'],
    '岳酱臣': ['乐将陈', '岳将臣', '越降城', '岳老板', '岳壤陈', '岳酱臣', '乐老板', '尔江'],
    '尔江': ['乐将陈', '岳将臣', '越降城', '岳老板', '岳壤陈', '岳酱臣', '乐老板', '尔江'],
    '浅忆兮': ['浅忆兮', '浅忆兮（大佐）', '浅爆组合'],
    '龙泡泡': ['龙泡泡', '龙泡泡（纵月老板）'],
    '邱一龙': ['邱一龙', '邱一龙（眉间雪老板）'],
    'SWW': ['SWW', 'sww', 'Sww', '沈婉婉', '沈晚晚'],
    'sww': ['SWW', 'sww', 'Sww', '沈婉婉', '沈晚晚'],
    'Sww': ['SWW', 'sww', 'Sww', '沈婉婉', '沈晚晚'],
    '沈婉婉': ['SWW', 'sww', 'Sww', '沈婉婉', '沈晚晚'],
    '沈晚晚': ['SWW', 'sww', 'Sww', '沈婉婉', '沈晚晚'],
    # ASR转录常见同音错字映射
    '爆流': ['暴流', '爆流', '爆刘', '爆45'],
    '暴流': ['爆流', '暴流', '爆刘', '爆45'],
    '爆刘': ['爆流', '暴流', '爆刘', '爆45'],
    '爆45': ['爆流', '暴流', '爆刘', '爆45'],
    '雪云峰': ['雪云峰', '雪云风', '雪云凤', '雪老狗'],
    '雪云风': ['雪云峰', '雪云风', '雪云凤', '雪老狗'],
    '雪云凤': ['雪云峰', '雪云风', '雪云凤', '雪老狗'],
}

MANUAL_ALIAS_ENTRIES = [
    {
        'text': '赖子、老赖、赖总、赖老板、赖哥、赖格、赖的都是同一个人名组。',
        'quality': 30,
        'source': 'manual-alias-赖子',
        'entity': '赖子',
    },
    {
        'text': '369、歪牜、歪牛、小炫、小炫quq是同一个人名组。按项目规则，问歪牜、歪牛、小炫或小炫quq都回到369，不拆成下属关系。',
        'quality': 30,
        'source': 'manual-alias-369',
        'entity': '369',
    },
    {
        'text': '双塘、双唐、双糖、笑糖、双膛、双堂是同一个人名组，都是天龙明星指挥双塘的错写、近音或同音写法。',
        'quality': 30,
        'source': 'manual-alias-双塘',
        'entity': '双塘',
    },
    {
        'text': '寒溟、寒冥、韩明、拐子是同一个人名组。拐子就是寒溟，南屿总指挥。',
        'quality': 30,
        'source': 'manual-alias-寒溟',
        'entity': '寒溟',
    },
    {
        'text': '苟立国、苟利国、苟老板是同一个人名组，指天龙人集团核心老板。',
        'quality': 30,
        'source': 'manual-alias-苟立国',
        'entity': '苟立国',
    },
    {
        'text': '岳将臣、乐将陈、越降城、岳老板、岳壤陈、岳酱臣、乐老板、尔江是同一个人名组，指华乾浩气老板。',
        'quality': 30,
        'source': 'manual-alias-岳将臣',
        'entity': '岳将臣',
    },
    {
        'text': '爆流、暴流、爆刘、爆45是同一个人名组。',
        'quality': 30,
        'source': 'manual-alias-爆流',
        'entity': '爆流',
    },
    {
        'text': '雪云峰、雪云风、雪云凤、雪老狗是同一个人名组。',
        'quality': 30,
        'source': 'manual-alias-雪云峰',
        'entity': '雪云峰',
    },
    {
        'text': '孤寺寺、顾寺寺、古寺寺是同一个人名组。',
        'quality': 30,
        'source': 'manual-alias-孤寺寺',
        'entity': '孤寺寺',
    },
    {
        'text': 'SWW、sww、沈婉婉、沈晚晚是同一个人名组，指唯满侠浩气女老板/金主，也是赖子唯满侠旧怨里的关键老板人物。',
        'quality': 30,
        'source': 'manual-alias-SWW',
        'entity': 'SWW',
    },
]

REFERENCE_ENTRY_QUALITY = 20
AUTO_ALIAS_ENTRY_QUALITY = 5
QUESTION_CHARS = set("是谁啥什么怎么哪吗啊呢的了过被和与在")
QUERY_NOISE_CHARS = set("是谁啥什么怎哪吗啊呢")
CURATED_SOURCE_MARKERS = ('manual', '手工', '精选', '四川方言', 'curated', 'alias')

# 停用词：中文常见虚词/疑问词——不参与检索
CN_STOP_WORDS = {
    '是谁', '什么', '怎么回事', '是什么', '为什么', '谁啊',
    '老板', '老板是', '老板是谁', '板是', '板是谁',
    '怎么样', '哪里', '哪了', '干嘛', '怎么', '哪个',
    '是啥', '有人', '还有', '真的', '不过', '这个',
    '那个', '这些', '那些', '可以', '还是', '就是',
    '一个', '一下', '没有', '不是', '已经', '因为',
    '所以', '如果', '虽然', '但是', '而且', '然后',
    '之前', '之后', '现在', '当时', '其实',
    '来着', '应该', '可能', '一定', '觉得',
    '知道', '看到', '听到', '感觉', '记得', '忘记',
}

def extract_chinese_terms(text):
    """
    提取中文检索词：滑动窗口 2-4 字 + 过滤停用词。
    修复 BUG: 原 regex [\u4e00-\u9fff]{2,} 贪婪匹配整段中文，
    导致 "小林酱是谁" → 拆成6字整坨 → 无法匹配任何别名。
    现在 "小林酱是谁" → {"小林","林酱","小林酱"} + 过滤停用词。
    """
    terms = set()
    def keep_term(w):
        return w not in CN_STOP_WORDS and not any(ch in QUERY_NOISE_CHARS for ch in w)

    for match in re.finditer(r'[\u4e00-\u9fff]{2,}', text):
        seq = match.group()
        # 2字窗口
        for i in range(len(seq) - 1):
            w = seq[i:i+2]
            if keep_term(w):
                terms.add(w)
        # 3字窗口（人名常用）
        for i in range(len(seq) - 2):
            w = seq[i:i+3]
            if keep_term(w):
                terms.add(w)
        # 4字窗口（事件/地名）
        for i in range(len(seq) - 3):
            w = seq[i:i+4]
            if keep_term(w):
                terms.add(w)
    return terms

def normalize_pinyin_key(text):
    """把拼音输入归一成无空格小写 key: shuang tang -> shuangtang。"""
    return re.sub(r'[^a-z0-9]', '', text.lower())

def to_pinyin_key(text):
    """中文名转拼音 key。pypinyin 不存在时返回空串，保留普通别名检索。"""
    if lazy_pinyin is None:
        return ""
    parts = []
    for ch in text:
        if '\u4e00' <= ch <= '\u9fff':
            parts.extend(lazy_pinyin(ch, errors='ignore'))
        elif ch.isalnum():
            parts.append(ch.lower())
    key = ''.join(parts)
    return normalize_pinyin_key(key)

def clean_entity_name(raw):
    """清理 markdown 表格/加粗里抽出的候选实体名。"""
    name = raw.strip().strip('*` ')
    name = re.sub(r'<[^>]+>', '', name)
    name = re.sub(r'[（(].*?[）)]', '', name).strip()
    name = name.strip(' ：:，,。；;|')
    return name

def looks_like_entity_name(name):
    """只收窄到人名/短实体，避免把整句加入拼音索引。"""
    if not name or len(name) < 2 or len(name) > 8:
        return False
    if any(ch in name for ch in "。！？：:，,；;、[]【】"):
        return False
    if name in {
        '人物', '角色', '事件', '详情', '关系', '说明', '服务器', '阵营',
        '来源', '细节', '类型', '证据', '备注', '状态', '搜索结果', '验证结果',
    }:
        return False
    if name.isdigit() and name != '369':
        return False
    if re.match(r'^第\d+集$', name):
        return False
    return bool(re.search(r'[\u4e00-\u9fff0-9]', name))

def looks_like_alias_name(name):
    """ALIASES 是人工维护的强词典，允许比自动抽取实体更长的带括号别名。"""
    if not name or len(name) > 20:
        return False
    if name.isdigit() and name != '369':
        return False
    return bool(re.search(r'[\u4e00-\u9fff0-9A-Za-z]', name))

def should_pinyin_expand_term(term):
    """只对像人名的查询片段做拼音扩展，降低普通问句误召回。"""
    if not looks_like_entity_name(term):
        return False
    return not any(ch in QUESTION_CHARS for ch in term)

def extract_entity_query_terms(query):
    """从“某某是谁/某某怎么回事”等问法中抽出整个人名。"""
    compact = re.sub(r'[^\u4e00-\u9fffA-Za-z0-9]+', '', query)
    terms = set()
    suffixes = [
        '是谁啊', '是谁', '是誰', '是啥', '是什么人', '是什么',
        '什么来头', '怎么回事', '哪位', '哪个',
    ]
    for suffix in suffixes:
        if compact.endswith(suffix) and len(compact) > len(suffix):
            candidate = compact[:-len(suffix)]
            if looks_like_entity_name(candidate):
                terms.add(candidate)
    return terms

def extract_ascii_query_terms(query):
    """支持用户直接输入 shuangtang / shuang tang 这类拼音。"""
    terms = set()
    for raw in re.findall(r'[A-Za-z][A-Za-z0-9\s_-]{1,60}', query):
        key = normalize_pinyin_key(raw)
        if len(key) >= 4:
            terms.add(key)
    return terms

PROJECT = Path(__file__).resolve().parents[1]
TRANS_DIR = PROJECT / "references/sources/transcripts"
REFERENCES_DIR = PROJECT / "references"
INDEX_FILE = PROJECT / "laizi_corpus.json"

@lru_cache(maxsize=1)
def load_reference_entity_entries():
    """从 references/*.md 抽取短人物/实体说明，作为只读检索补充。"""
    entries = []
    seen = set()
    for fp in sorted(REFERENCES_DIR.glob("*.md")):
        try:
            lines = fp.read_text(encoding='utf-8-sig').splitlines()
        except UnicodeDecodeError:
            lines = fp.read_text(encoding='utf-8', errors='ignore').splitlines()

        for lineno, line in enumerate(lines, 1):
            candidates = []

            # - **笑糖**：铁锤联盟指挥...
            m = re.match(r'\s*[-*]\s*\*\*([^*]{2,20})\*\*[：:]\s*(.+)$', line)
            if m:
                candidates.append((m.group(1), m.group(2)))

            # | 双塘 | 下属/搭档 | 天龙明星指挥... |
            if line.lstrip().startswith('|') and '---' not in line:
                cells = [c.strip() for c in line.strip().strip('|').split('|')]
                if len(cells) >= 3:
                    candidates.append((cells[0], '；'.join(cells[1:])))

            for raw_name, desc in candidates:
                name = clean_entity_name(raw_name)
                if not looks_like_entity_name(name):
                    continue
                desc = re.sub(r'\s+', ' ', desc).strip()
                if not desc or desc in {'关系；说明', '---'}:
                    continue
                text = f"{name}：{desc}"
                key = (name, text[:100])
                if key in seen:
                    continue
                seen.add(key)
                entries.append({
                    'text': text,
                    'quality': REFERENCE_ENTRY_QUALITY,
                    'source': f"reference:{fp.name}:{lineno}",
                    'entity': name,
                })
    return entries

@lru_cache(maxsize=1)
def build_auto_alias_entries():
    """为 ALIASES 中尚无手工说明的组生成兜底条目，避免拼音映射后无内容可命中。"""
    entries = []
    seen_groups = set()
    manual_entities = {entry.get('entity') for entry in MANUAL_ALIAS_ENTRIES}

    for base, aliases in ALIASES.items():
        group = {base, *aliases}
        group_key = tuple(sorted(group))
        if group_key in seen_groups:
            continue
        seen_groups.add(group_key)

        if base in manual_entities:
            continue

        ordered = sorted(group, key=lambda x: (len(x), x))
        text = f"{'、'.join(ordered)}是同一个人名或关键词组，用于纠正同音、近音、错别字和ASR转写偏差。"
        entries.append({
            'text': text,
            'quality': AUTO_ALIAS_ENTRY_QUALITY,
            'source': f"auto-alias-{base}",
            'entity': base,
        })

    return entries

@lru_cache(maxsize=1)
def build_pinyin_entity_index():
    """所有已知人名/短实体按拼音聚合，用来召回同音错字。"""
    index = {}
    alias_names = set()
    reference_names = set()

    for base, aliases in ALIASES.items():
        alias_names.add(base)
        alias_names.update(aliases)

    for entry in load_reference_entity_entries():
        name = entry.get('entity')
        if name:
            reference_names.add(name)

    def add_name(name):
        key = to_pinyin_key(name)
        if key and len(key) >= 4:
            index.setdefault(key, set()).add(name)

    for name in alias_names:
        if not looks_like_alias_name(name):
            continue
        add_name(name)

    for name in reference_names:
        if not looks_like_entity_name(name):
            continue
        add_name(name)

    return {k: sorted(v, key=len, reverse=True) for k, v in index.items()}

def expand_query_terms(terms, query_text=""):
    """用别名词典 + 人名拼音索引扩展查询词，精确匹配权重保留给原词。"""
    expanded = {}  # term -> weight (1.0 = exact, 0.8 = alias)

    def alias_group_for_term(term):
        group = {term}
        if term in ALIASES:
            group.update(ALIASES[term])
        for base, aliases in ALIASES.items():
            if term == base or term in aliases:
                group.add(base)
                group.update(aliases)
        return group

    def add_term(term, weight):
        if term not in expanded or weight > expanded[term]:
            expanded[term] = weight
        alias_weight = min(weight, 0.8)
        for alias in alias_group_for_term(term):
            if alias == term:
                continue
            if alias not in expanded or alias_weight > expanded[alias]:
                expanded[alias] = alias_weight

    for t in terms:
        add_term(t, 1.0)

    pinyin_index = build_pinyin_entity_index()
    # 已有人为确认的强别名只走 ALIASES，避免被同音但不同人的名字抢召回。
    pinyin_candidates = {t for t in terms if should_pinyin_expand_term(t) and t not in ALIASES}
    pinyin_candidates.update(t for t in extract_entity_query_terms(query_text) if t not in ALIASES)

    for t in pinyin_candidates:
        key = to_pinyin_key(t)
        for alias in pinyin_index.get(key, []):
            add_term(alias, 0.7)

    for key in extract_ascii_query_terms(query_text):
        for alias in pinyin_index.get(key, []):
            add_term(alias, 0.7)

    return expanded

@lru_cache(maxsize=None)
def alias_terms_for_entity(entity):
    """manual-alias 条目只允许本组别名触发，防止“指挥/老板”泛词抢位。"""
    terms = {entity}
    if entity in ALIASES:
        terms.update(ALIASES[entity])
    for key, aliases in ALIASES.items():
        if entity == key or entity in aliases:
            terms.add(key)
            terms.update(aliases)
    return terms

def fuzzy_match_term(term, text):
    """
    模糊匹配：term 在 text 中出现？
    返回 (weight, found) — weight 精确=1.0, 别名=0.8, 子串模糊=0.5
    """
    # 1. 精确匹配
    if term in text:
        return 1.0, True

    # 2. 子串模糊：3-4字名 → 拆成连续2字（bigram），至少命中2个才算匹配
    if 3 <= len(term) <= 4:
        bigrams = [term[i:i+2] for i in range(len(term)-1)]
        hits = sum(1 for b in bigrams if b in text)
        # 3字词只命中一个 bigram 太宽，会让“赖老板”凭“老板”误中所有老板。
        if hits >= max(2, len(bigrams) - 1):
            return 0.5, True

    return 0.0, False

def search_corpus_with_references(corpus):
    """普通 corpus + references 里抽取的实体条目。"""
    items = list(corpus)

    def extend_missing(extra_entries):
        existing_sources = {str(p.get('source', '')) for p in items}
        for entry in extra_entries:
            source = str(entry.get('source', ''))
            if source not in existing_sources:
                items.append(entry)
                existing_sources.add(source)

    def has_existing_group_coverage(group_terms):
        for item in items:
            source = str(item.get('source', ''))
            if source.startswith('auto-alias-'):
                continue
            haystack = f"{item.get('text', '')} {source} {item.get('entity', '')}"
            if any(term and term in haystack for term in group_terms):
                return True
        return False

    extend_missing(MANUAL_ALIAS_ENTRIES)
    extend_missing(load_reference_entity_entries())

    auto_entries = []
    for entry in build_auto_alias_entries():
        if not has_existing_group_coverage(alias_terms_for_entity(entry.get('entity', ''))):
            auto_entries.append(entry)
    extend_missing(auto_entries)
    return items

def is_curated_entry(entry):
    """人工整理条目必须永久保留，不受 quality 分数影响。"""
    if entry.get('manual') is True or entry.get('source_type') == 'curated':
        return True
    source = str(entry.get('source', '')).lower()
    return any(marker.lower() in source for marker in CURATED_SOURCE_MARKERS)

SZ_MARKERS = [
    "兄弟", "好吧", "我操", "他妈的", "废物", "傻逼", "对不对", "知道吧",
    "听我说", "话语权", "打不掉", "懂吧", "日历来骂", "活气巴盖",
    "就这么简单", "行吗", "赶紧退", "自己打", "就像一张白纸",
    "不承认", "首当其冲", "不离不弃", "三年前", "三年",
    "苍澜", "浩气", "恶人", "攻防", "指挥", "帮会", "封号",
    "老板", "工资", "恰钱", "飞机", "显卡", "网管"
]

NOISE_WORDS = [
    "打打打打", "走走走", "报令报令", "飞飞飞", "摔死摔死",
    "来来来", "别动别动", "停下停下", "快打快打", "GG",
    "解散开", "杀人杀杀", "杀杀杀", "打BOSS", "打boss", "BOSS",
    "买雷买飞机", "复活点", "所有人散开", "所有人全部", "飞死攻",
    "大车", "小车", "躺尸", "死了补", "原地起",
]

def quality_score(text):
    """评分段落质量：赖子说话 vs 杂音/战斗指令"""
    if len(text) < 80:
        return 0
    sz_score = sum(1 for m in SZ_MARKERS if m in text)
    noise_score = sum(1 for n in NOISE_WORDS if n in text)
    # 赖子标志词越多越好，战斗杂音越多越差
    return sz_score * 3 - noise_score

def clean_transcript(filepath):
    """清洗转录文件，返回纯文本"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    out = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('Duration') or \
           line.startswith('Transcription') or line.startswith('Realtime') or \
           line.startswith('Segments') or line.startswith('Time:') or line == '---':
            continue
        # 去所有[]格式的时间戳
        line = re.sub(r'\[[\d:.\s\-,]+\]', '', line)
        line = line.strip()
        if line:
            out.append(line)
    return ' '.join(out)

def chunk_text(text, size=500):
    """智能切段——尽量在句号/逗号处断"""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            # 尝试在最近的分隔符处断
            for sep in ['。', '！', '？', '.', '!', '?', '，']:
                pos = text.rfind(sep, start, end)
                if pos > start + 200:
                    end = pos + 1
                    break
        chunk = text[start:end].strip()
        if len(chunk) >= 80:
            chunks.append(chunk)
        start = end
    return chunks

def build():
    """构建语料库：从转录重建 + 合并已有人工/精选条目。"""
    # 1. 加载已有手动条目
    manual_entries = []
    if INDEX_FILE.exists():
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        manual_entries = [p for p in existing if is_curated_entry(p)]
        print(f"已有人工/精选条目: {len(manual_entries)}")

    # 2. 从转录重建
    all_chunks = []

    for fp in sorted(TRANS_DIR.glob("*.txt")):
        text = clean_transcript(fp)
        if len(text) < 200:
            continue
        chunks = chunk_text(text, 500)
        for c in chunks:
            qs = quality_score(c)
            if qs >= 2:  # 质量门槛
                all_chunks.append({
                    'text': c,
                    'quality': qs,
                    'source': fp.stem[:60]
                })

    print(f"转录段落: {len(all_chunks)}")

    # 3. 合并去重：转录条目 + 手动条目（手动优先保留）
    seen = set()
    unique = []

    # 先加手动条目（优先级最高）
    for p in manual_entries:
        key = p['text'][:80]
        if key not in seen:
            seen.add(key)
            unique.append(p)

    # 再加转录条目
    for p in all_chunks:
        key = p['text'][:80]
        if key not in seen:
            seen.add(key)
            unique.append(p)

    print(f"合并后: {len(unique)} (手动{len(manual_entries)} + 转录{len(unique)-len(manual_entries)})")

    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)

    return unique

def search(query, corpus, top_k=3):
    """
    模糊检索（v2）：别名扩展 + 子串回退 + 停用词过滤 + 精确优先
    - 精确匹配: 权重 1.0（原词直接命中）
    - 别名扩展: 权重 0.8（通过别名词典命中）
    - 子串模糊: 权重 0.5（3-4字名拆bigram命中）
    - 停用词先过滤，不计入检索词
    - 至少一个有意义词命中才计分（纯停用词或0命中 → 0分）
    """
    # 中文词：滑动窗口 2-4 字 + 过滤停用词（修复贪婪匹配 BUG）
    q_terms_raw = extract_chinese_terms(query)
    exact_query_terms = set(q_terms_raw)
    # 数字 2+ 位
    for w in re.findall(r'\d{2,}', query):
        q_terms_raw.add(w)
        exact_query_terms.add(w)
    # 已知别名如果原样出现在查询里，直接加入，支持“爆45”这类中英数混合名。
    for alias in ALIASES:
        if alias in query:
            q_terms_raw.add(alias)
            exact_query_terms.add(alias)
    # 英文 2+ 字母

    # 别名扩展 → {term: base_weight}
    q_terms_expanded = expand_query_terms(q_terms_raw, query)

    explicit_alias_terms = {
        alias for alias in ALIASES
        if alias in query
    }
    explicit_alias_terms.update(extract_entity_query_terms(query))

    scored = []
    for p in search_corpus_with_references(corpus):
        text = p.get('text', '')
        source = p.get('source', '')
        entity = p.get('entity', '')
        haystack = f"{text} {source}"
        manual_alias_terms = alias_terms_for_entity(entity) if str(source).startswith('manual-alias-') else None
        s = 0.0
        meaningful_hits = 0

        if manual_alias_terms is not None:
            off_group_terms = {
                term for term in explicit_alias_terms
                if term and term not in manual_alias_terms
            }
            if off_group_terms:
                continue

        for term, base_weight in q_terms_expanded.items():
            if manual_alias_terms is not None and term not in manual_alias_terms:
                continue
            match_weight, found = fuzzy_match_term(term, haystack)
            if not found:
                continue

            combined_weight = base_weight * match_weight
            text_count = text.count(term)
            source_count = source.count(term)
            count = text_count + source_count

            if count > 0:
                # 正文命中最强，标题/source 命中次之
                s += text_count * 3 * combined_weight
                s += source_count * 2 * combined_weight
                if entity == term:
                    # reference 人物条目的实体名命中，比说明文字里顺带提到更可靠。
                    if term in exact_query_terms:
                        s += 12 * combined_weight
                    else:
                        s += 10 * combined_weight
                meaningful_hits += 1
            elif match_weight < 1.0:
                # 纯模糊命中（bigram 匹配但 term 字面不在文本中）
                # 给底分 1.5，避免模糊命中形同虚设
                s += 1.5 * combined_weight
                meaningful_hits += 1

        # 至少命中一个有意义词才计分 + 质量加成
        if meaningful_hits > 0:
            s += p.get('quality', 0) * 0.8
            if str(source).startswith('manual'):
                # 人工维护的纠错/别名条目优先于自动抽取的 reference 行和 ASR 转录。
                s += 18
            scored.append((s, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_k]


# 保留旧版精确检索供对照（已加停用词过滤）
def search_exact(query, corpus, top_k=3):
    """词级+数字+英文检索（精确子串匹配，v1 对照版，使用滑动窗口分词）"""
    q_terms = extract_chinese_terms(query)
    for w in re.findall(r'\d{2,}', query):
        q_terms.add(w)
    for w in re.findall(r'[a-zA-Z]{2,}', query):
        q_terms.add(w.upper())

    scored = []
    for p in corpus:
        text = p['text']
        s = sum(text.count(t)*3 for t in q_terms)
        s += p.get('quality', 0)
        if s > 0:
            scored.append((s, p))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_k]

def load_corpus():
    with open(INDEX_FILE, 'r', encoding='utf-8-sig') as f:
        return json.load(f)

def run_smoke_tests(corpus):
    """只读回归测试；不重建、不写 corpus。"""
    tests = [
        # 精确匹配（应有高分）
        ("指挥厉害吗", "exact"),
        ("双梦浩气为什么会输", "exact"),
        ("唯满侠那次怎么回事", "exact"),
        ("为什么被封号", "exact"),

        # 别名匹配（应通过别名词典命中，略低分）
        ("小林酱是谁", "alias"),
        ("小林将是谁", "alias_exact"),
        ("抛子是谁", "alias"),
        ("拐子是谁", "alias"),
        ("歪牜是谁", "alias"),
        ("歪牛是谁", "alias"),
        ("369是谁", "alias"),
        ("压哥是谁", "alias"),
        ("老赖是谁", "alias"),
        ("苟利国是谁", "alias"),
        ("韩明是谁", "alias"),
        ("寒冥是谁", "alias"),
        ("岳壤陈是谁", "alias"),
        ("爆刘是谁", "alias"),
        ("雪云凤是谁", "alias"),
        ("阵营之蛆是谁", "alias"),
        ("白龙口是什么", "alias"),
        ("双塘是谁", "pinyin_entity"),
        ("双唐是谁", "pinyin_typo"),
        ("双糖是谁", "pinyin_asr"),
        ("笑糖是谁", "phonetic_alias"),
        ("shuangtang是谁", "pinyin_input"),
        ("xiaotang是谁", "pinyin_phonetic_alias"),

        # 模糊匹配（子串回退，低分但应命中）
        ("谢小亮是谁", "fuzzy"),
        ("解小亮是谁", "fuzzy_exact"),
        ("枫卿十一", "fuzzy"),

        # 旧版对比测试
        ("369是谁", "exact"),
        ("外卖店是什么梗", "exact"),
        ("天月是谁", "exact"),
        ("反攻双梦", "exact"),
    ]

    print(f"\n{'='*70}")
    print(f"检索测试 v2（只读） | corpus={len(corpus)}条")
    print(f"{'='*70}")

    for q, cat in tests:
        res = search(q, corpus)
        if res:
            s, p = res[0]
            tag = (
                "OK-exact" if s >= 6 else
                "OK-alias" if s >= 3 else
                "OK-fuzzy"
            )
            print(f'{tag} [{q:16s}] -> 得分{s:5.1f} | {p["text"][:100]}...')
        else:
            print(f'NO-MATCH [{q:16s}] -> 无匹配')

    # v1 vs v2 对比
    print(f"\n{'='*70}")
    print(f"v1（精确）vs v2（模糊）对比")
    print(f"{'='*70}")

    compare = ["小林酱是谁", "解小亮是谁", "拐子是谁", "白龙口是什么"]
    for q in compare:
        r1 = search_exact(q, corpus)
        r2 = search(q, corpus)
        s1 = r1[0][0] if r1 else 0
        s2 = r2[0][0] if r2 else 0
        status = "UP" if s2 > s1 else "SAME" if s2 == s1 else "DOWN"
        print(f'  {q:16s} -> v1精确:{s1:5.1f} | v2模糊:{s2:5.1f} | {status}')

def main():
    parser = argparse.ArgumentParser(description="赖子语料构建/只读检索测试")
    parser.add_argument('--build', action='store_true', help='重建并写回 laizi_corpus.json')
    parser.add_argument('--patch-manual', action='store_true', help='构建前先运行 patch_corpus_names.py')
    parser.add_argument('--test', action='store_true', help='运行只读检索测试')
    args = parser.parse_args()

    if args.build:
        if args.patch_manual:
            import subprocess, sys
            print("检查手动条目...")
            patch_script = str(PROJECT / "scripts/patch_corpus_names.py")
            subprocess.run([sys.executable, patch_script], check=True)
            print()
        print("重建语料库（含人工/精选条目合并）...")
        corpus = build()
        if args.test:
            run_smoke_tests(corpus)
        return

    # 默认只读，避免误运行脚本时改写 corpus。
    run_smoke_tests(load_corpus())

if __name__ == '__main__':
    main()
