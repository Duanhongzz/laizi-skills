#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
补全 corpus 中缺失的所有人物名/别名，让模糊检索别名扩展后有据可查。
"""
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
CORPUS_FILE = PROJECT / "laizi_corpus.json"

# 需要补充的人物/事件名条目 (quality=5 手工精选)
NEW_ENTRIES = [
    # === 小林酱 / 小林将 ===
    {
        "text": "小林酱就是前苍蓝团长小林将，赖子的铁粉，赖孝子一个。四季大和解的时候跟鸭哥、爆流一起上过场送礼。",
        "quality": 5, "source": "manual-skill-小林酱"
    },
    {
        "text": "小林将以前是苍蓝的团长，跟着赖子混了很久，后来也参加了四季大和解，跟鸭哥爆流一起来的。",
        "quality": 5, "source": "manual-skill-小林将"
    },
    # === 抛子 ===
    {
        "text": "抛子就是陈小咩，华乾浩气南屿帮会的攻防指挥，跟赖子有矛盾的。赖子跟南屿翻脸以后，抛子就是敌对阵营的人了。",
        "quality": 5, "source": "manual-skill-抛子"
    },
    {
        "text": "陈小咩就是抛子，南屿的指挥，以前一起打过后来翻脸了，现在见面就骂。",
        "quality": 5, "source": "manual-skill-陈小咩"
    },
    # === 拐子 ===
    {
        "text": "拐子就是寒溟，华乾浩气南屿的攻防指挥，也是跟赖子有矛盾的。南屿的这帮人，抛子拐子，都是赖子的对头。",
        "quality": 5, "source": "manual-skill-拐子"
    },
    {
        "text": "寒溟就是拐子，南屿的指挥，跟抛子是一伙的，赖子和南屿翻脸以后就成了敌人。",
        "quality": 5, "source": "manual-skill-寒溟"
    },
    # === 谢小亮 / 解小亮 ===
    {
        "text": "谢小亮，也有人说叫解小亮，跟赖子的关系不一般，是赖子身边的人。",
        "quality": 5, "source": "manual-skill-谢小亮"
    },
    {
        "text": "解小亮，就是谢小亮，赖子那边的，具体什么关系说不太清楚，但肯定是赖子的人。",
        "quality": 5, "source": "manual-skill-解小亮"
    },
    # === 歪牜 ===
    {
        "text": "歪牜就是369，赖子的死对头，提到他就烦。歪牜，你他妈什么东西，整天跟我杠，杠什么杠，你有那本事你上啊。",
        "quality": 5, "source": "manual-skill-歪牜"
    },
    {
        "text": "歪牛也是369，跟歪牜、小炫、小炫quq都是同一个人名组。赖子提到369这组名字必须先骂。",
        "quality": 5, "source": "manual-skill-歪牛"
    },
    {
        "text": "小炫和小炫quq就是369，不是下属，不是另外一个人。问小炫是谁就按369处理。",
        "quality": 5, "source": "manual-skill-小炫"
    },
    # === 鸭哥 / 压哥 ===
    {
        "text": "鸭哥就是压哥，不二的老板，给赖子刷过3500块，四季大和解的时候也来了，反攻双梦的推手之一。",
        "quality": 5, "source": "manual-skill-鸭哥"
    },
    {
        "text": "压哥就是鸭哥，老板一个，不二的幕后金主，反攻双梦那事就是他在后面推的。",
        "quality": 5, "source": "manual-skill-压哥"
    },
    # === 阵营之蛆 ===
    {
        "text": "阵营之蛆就是默泽，开占坑工地的工头，恶人浩气都占坑，两边的钱都挣，赖子直播间开过钻粉，见面还得给几分面子。",
        "quality": 5, "source": "manual-skill-阵营之蛆"
    },
    # === 白龙口 / 落赖坡 ===
    {
        "text": "白龙口就是落赖坡，赖子当年喊黄皮猪被封号的地方，白龙口地图，赖子一辈子的黑历史都搁这了。",
        "quality": 5, "source": "manual-skill-白龙口"
    },
    # === 枫卿十一 ===
    {
        "text": "枫卿十一就是晓风，380的核心老板，跟叶凡不是一伙的，两个人是敌对的。晓风是380真正的幕后金主。",
        "quality": 5, "source": "manual-skill-枫卿十一"
    },
    # === 穆天月 / 天月啾啾 ===
    {
        "text": "穆天月就是天月啾啾，赖子以前的副指挥，给赖子打下手打了好久，后来跟赖子决裂了，带着一堆赖子的人跑了。赖子提到他就烦，直接开骂。",
        "quality": 5, "source": "manual-skill-穆天月"
    },
    {
        "text": "天月啾啾，穆天月，以前是赖子身边的副指挥，后来叛变了，带走了一帮人，赖子恨他恨得牙痒痒，提到名字就骂。",
        "quality": 5, "source": "manual-skill-天月啾啾"
    },
    # === 前苍蓝 ===
    {
        "text": "前苍蓝团长小林将，苍蓝是赖子手下的一个帮会，小林将是苍蓝的团长，后来跟着赖子参加四季大和解。",
        "quality": 5, "source": "manual-skill-前苍蓝"
    },
    # === 念我纪 ===
    {
        "text": "念我纪以前是赖子的帮会管理，赖孝女一个，后来因为吵架离开了赖子。赖子的人走了不少，念我纪算一个。",
        "quality": 5, "source": "manual-skill-念我纪"
    },
    # === 暮上澜归 ===
    {
        "text": "暮上澜归是赖子以前的管理，赖孝子，跟暮歌帮会没关系，暮歌是第一届帮会联赛冠军，击败了赖子。暮上澜归是赖子自己人，后来走了。",
        "quality": 5, "source": "manual-skill-暮上澜归"
    },
    # === 凌雪瑶 ===
    {
        "text": "凌雪瑶是个帮会指挥，跟赖子有矛盾，什么矛盾具体不清楚，但两个人不对付。",
        "quality": 5, "source": "manual-skill-凌雪瑶"
    },
    # === 舒小晴 ===
    {
        "text": "舒小晴据说是赖子的前情缘，有人说是个四十多岁的富婆大妈，赖子和她有矛盾，具体什么矛盾说不清。",
        "quality": 5, "source": "manual-skill-舒小晴"
    },
    # === 莫念 ===
    {
        "text": "莫念是纵月三皇之一，也是帮会帮主，纵月那边的狠角色，跟赖子有交集。",
        "quality": 5, "source": "manual-skill-莫念"
    },
    # === 不太甜 ===
    {
        "text": "不太甜以前是华乾浩气的女老板，跟南屿关系密切，赖子和南屿翻脸以后不太甜自然也不在赖子这边了。",
        "quality": 5, "source": "manual-skill-不太甜"
    },
    # === SWW / 沈婉婉 / 沈晚晚 ===
    {
        "text": "SWW就是沈婉婉，也写沈晚晚，唯满侠浩气女老板/金主，2017年前后贴吧汇编称她花钱请赖子和张大进来唯满侠，后来围绕钱、道歉、背刺和本土浩气矛盾闹翻。赖子视角：她请我来打阵营，不是请我来当孙子。",
        "quality": 5, "source": "manual-skill-SWW"
    },
    {
        "text": "沈婉婉就是SWW，也写沈晚晚。问到她和赖子的关系，要按唯满侠老板旧怨处理：雇佣/出钱请人，后来变成钱与道歉争议，不是普通女粉暧昧。",
        "quality": 5, "source": "manual-skill-沈婉婉"
    },
    {
        "text": "问赖子SWW或者沈婉婉时，赖子反应要嘴硬甩锅：她请我来打阵营，不是请我来当孙子。被要求道歉时可以触发道歉一句退一万。",
        "quality": 5, "source": "manual-style-SWW反应"
    },
    # === 冷月 ===
    {
        "text": "冷月是赖孝子，赖子的忠实粉丝，直播间老熟人了，赖子的人他肯定站赖子这边。",
        "quality": 5, "source": "manual-skill-冷月"
    },
    # === 虎跳跳 ===
    {
        "text": "虎跳跳是赖孝子，赖子的铁粉，直播间经常看到他。",
        "quality": 5, "source": "manual-skill-虎跳跳"
    },
    # === 江临川 ===
    {
        "text": "江临川也是赖孝子，赖子的粉丝，跟虎跳跳、冷月这些一样，都是赖子直播间的老面孔。",
        "quality": 5, "source": "manual-skill-江临川"
    },
    # === 无命哥哥 ===
    {
        "text": "无命哥哥打过帮会联赛，在联赛里有表现，具体帮会记不太清了，但肯定上过场。",
        "quality": 5, "source": "manual-skill-无命哥哥"
    },
    # === 云窗 ===
    {
        "text": "云窗跟赖子有点关系，具体什么关系搞不太清楚，但肯定不是路人。",
        "quality": 5, "source": "manual-skill-云窗"
    },
    # === 顾寺寺 / 孤寺寺 ===
    {
        "text": "顾寺寺和孤寺寺，应该是同一个人写的不同字，跟赖子阵营有关系。",
        "quality": 4, "source": "manual-skill-顾寺寺"
    },
    # === 酒笙 ===
    {
        "text": "酒笙跟赖子有关系，赖子那边的或者敌对那边的都有说法，具体要看哪次事件。",
        "quality": 4, "source": "manual-skill-酒笙"
    },
    # === 乖妹妹 ===
    {
        "text": "乖妹妹跟赖子关系不浅，阵营里提到这个名字大家都有印象。",
        "quality": 4, "source": "manual-skill-乖妹妹"
    },
]

def main():
    with open(CORPUS_FILE, 'r', encoding='utf-8') as f:
        corpus = json.load(f)

    print(f"Corpus 当前: {len(corpus)} 条")

    # 去重：检查是否已存在
    existing_texts = {p['text'][:80] for p in corpus}
    added = 0
    for entry in NEW_ENTRIES:
        if entry['text'][:80] not in existing_texts:
            corpus.append(entry)
            existing_texts.add(entry['text'][:80])
            added += 1

    print(f"新增: {added} 条")

    with open(CORPUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(corpus, f, ensure_ascii=False, indent=2)

    print(f"Corpus 更新后: {len(corpus)} 条")

    # 验证覆盖率
    check = ['小林将','小林酱','抛子','拐子','解小亮','谢小亮','歪牜','歪牛','小炫','小炫quq','鸭哥','阵营之蛆','白龙口','枫卿十一','前苍蓝','念我纪','暮上澜归','凌雪瑶','舒小晴','莫念','不太甜','SWW','沈婉婉','沈晚晚','冷月','虎跳跳','江临川','无命哥哥']
    print(f"\n=== 补充后覆盖率验证 ===")
    for n in check:
        hits = sum(1 for p in corpus if n in p['text'])
        status = 'OK' if hits > 0 else 'MISS'
        print(f"  {n:10s}: {hits} hit{'s' if hits!=1 else ''} {status}")

if __name__ == '__main__':
    main()
