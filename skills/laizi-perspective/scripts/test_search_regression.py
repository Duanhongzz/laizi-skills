#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""只读检索回归测试：不重建、不写 corpus。"""

import importlib.util
import json
import re
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = PROJECT / "scripts/build_corpus.py"
CORPUS_FILE = PROJECT / "laizi_corpus.json"


def load_build_module():
    spec = importlib.util.spec_from_file_location("build_corpus", BUILD_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_corpus():
    with open(CORPUS_FILE, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def assert_top_source(module, corpus, query, expected_source_prefix):
    results = module.search(query, corpus, top_k=3)
    assert results, f"{query}: no results"
    score, item = results[0]
    source = item.get("source", "")
    assert source.startswith(expected_source_prefix), (
        f"{query}: top source {source!r}, expected prefix {expected_source_prefix!r}; "
        f"text={item.get('text', '')[:120]!r}; score={score}"
    )


def assert_top_text_contains(module, corpus, query, expected_text):
    results = module.search(query, corpus, top_k=3)
    assert results, f"{query}: no results"
    score, item = results[0]
    text = item.get("text", "")
    assert expected_text in text, (
        f"{query}: top text misses {expected_text!r}; "
        f"source={item.get('source', '')!r}; text={text[:160]!r}; score={score}"
    )


def main():
    module = load_build_module()
    corpus = load_corpus()

    source_cases = {
        "歪牜是谁": "manual-alias-369",
        "歪牛是谁": "manual-alias-369",
        "369是谁": "manual-alias-369",
        "小炫是谁": "manual-alias-369",
        "小炫quq是谁": "manual-alias-369",
        "xiaoxuan是谁": "manual-alias-369",
        "xiaoxuanquq是谁": "manual-alias-369",
        "双唐是谁": "manual-alias-双塘",
        "双堂是谁": "manual-alias-双塘",
        "笑糖是谁": "manual-alias-双塘",
        "xiaotang是谁": "manual-alias-双塘",
        "shuangtang是谁": "manual-alias-双塘",
        "韩明是谁": "manual-alias-寒溟",
        "寒冥是谁": "manual-alias-寒溟",
        "拐子是谁": "manual-alias-寒溟",
        "苟利国是谁": "manual-alias-苟立国",
        "苟老板是谁": "manual-alias-苟立国",
        "岳酱臣是谁": "manual-alias-岳将臣",
        "乐老板是谁": "manual-alias-岳将臣",
        "爆45是谁": "manual-alias-爆流",
        "爆刘是谁": "manual-alias-爆流",
        "baoliu是谁": "manual-alias-爆流",
        "雪云凤是谁": "manual-alias-雪云峰",
        "xueyunfeng是谁": "manual-alias-雪云峰",
        "顾寺寺是谁": "manual-alias-孤寺寺",
        "老赖是谁": "manual-alias-赖子",
        "SWW是谁": "manual-alias-SWW",
        "sww是谁": "manual-alias-SWW",
        "沈婉婉是谁": "manual-alias-SWW",
        "沈晚晚是谁": "manual-alias-SWW",
        "shenwanwan是谁": "manual-alias-SWW",
        "小林将是谁": "manual-skill-",
        "butaitianlaoban是谁": "manual-skill-不太甜",
        "qianyixidazuo是谁": "manual-秦子-浅忆兮",
        "tianyan007是谁": "manual-梗-开天眼",
        "qiuyilongmeijianxuelaoban是谁": "manual-秦子-邱一龙",
        "longpaopaozongyuelaoban是谁": "manual-秦子-龙泡泡",
        "zhuangzhuangzhuozhuangchengzhang是谁": "reference:剑网三阵营编年史.md",
    }
    skipped = 0
    if module.lazy_pinyin is None:
        original_count = len(source_cases)
        source_cases = {q: v for q, v in source_cases.items() if not re.search(r"[a-z]{4,}", q)}
        skipped = original_count - len(source_cases)
    for query, source_prefix in source_cases.items():
        assert_top_source(module, corpus, query, source_prefix)

    text_cases = {
        "外卖店是什么梗": "外卖",
        "为什么被封号": "封号",
        "赖子和SWW什么关系": "请我来打阵营",
        "赖子和沈婉婉什么关系": "老板旧怨",
    }
    for query, expected_text in text_cases.items():
        assert_top_text_contains(module, corpus, query, expected_text)

    assert module.search("是谁", corpus, top_k=3) == [], "pure stopword query should not match"
    assert module.search("为什么", corpus, top_k=3) == [], "pure stopword fragment query should not match"

    print(f"PASS search regression cases={len(source_cases) + len(text_cases) + 2}; skipped_pinyin={skipped}")


if __name__ == "__main__":
    main()
