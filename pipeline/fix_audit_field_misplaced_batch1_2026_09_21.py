# -*- coding: utf-8 -*-
"""Очередь аудита: FIELD_MISPLACED, первая партия — 100+ дословных переносов
между полями одной карточки (без обращения к первоисточнику): партия
supplement_2026-09-21.json + остаток исходных 2420 находок 13 сентября.

Разбор вёлся так же, как прошлой ночью (см. CLAUDE.md, «Очередь аудита
адреса фактов — подпитывается, а не вычерпывается»): для каждой находки
прочитан «problem» и «action», выбран КОНКРЕТНЫЙ путь назначения (когда
action давал варианты через «или» — конкретное поле выбрано по смыслу
семантики поля из READER_BRIEF_2026_09_21.md), и находки, требующие
большего, чем перенос дословного текста, — сюда НЕ вошли:
  - перенос в профиль КОМПАНИИ (другой объект, не карточка сделки) —
    buyer_profile.desc/target_profile.desc;
  - структурные переименования (buyer_name, извлечение суммы в sum/eco.sum);
  - переписывание/сочинение текста заново (rewrite:...);
  - находки с двумя равноправно взаимоисключающими адресами и риском
    случайного дубля (уже похожая формулировка лежит в назначении);
  - находка без action (g23ff3a09) — решать индивидуально;
  - конфликт между ДВУМЯ находками на одну и ту же цитату одной карточки
    (gmru-sollers-jf-mould, law.struct «У предприятия нет активов...») —
    оставлена только более подходящая по смыслу (eco.rationale), вторая
    (eco.val) не применяется, чтобы не спорить сама с собой.

Для этих отложенных находок очередь (`audit_queue.py --queue --class
FIELD_MISPLACED --no-source`) не тронута — они останутся ждать разбора.

    python3 pipeline/fix_audit_field_misplaced_batch1_2026_09_21.py
    python3 pipeline/fix_audit_field_misplaced_batch1_2026_09_21.py --write
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "static" / "data" / "deals_promoted.json"
sys.path.insert(0, str(ROOT))

from pipeline import audit_queue as aq  # noqa: E402
from pipeline.fix_audit_move_utils import (  # noqa: E402
    apply_move, extend_to_sentences, get_field, set_field,
)

BATCH_FILE = ROOT / "pipeline" / "audit_field_placement" / "supplement_2026-09-21.json"

# Короткие имена поля, которыми пользовался исходный аудит 13 сентября —
# без префикса eco./law. Дописывается здесь, а не в самой очереди: у
# supplement_2026-09-21.json они уже полные, здесь только для findings.json.
SHORT_FIELD = {
    "fin": "eco.fin", "context": "eco.context", "struct": "law.struct",
    "rationale": "eco.rationale", "target_fin": "eco.target_fin",
    "share": "eco.share", "val": "eco.val", "terms": "law.terms",
    "appr": "law.appr", "adv": "law.adv", "finadv": "eco.finadv",
}


def norm_field(field: str) -> str:
    return SHORT_FIELD.get(field, field)


# key -> путь назначения (см. обоснование в docstring и в самой находке —
# audit_queue.py --queue --class FIELD_MISPLACED покажет problem/action по key).
KEY_DST = {
    "e95d11aaac89": "extra",
    "ce6fd39474d0": "eco.target_fin",
    "12cfd0caa68b": "eco.share",
    "bff84b4eb760": "eco.context",
    "4f737f26d595": "eco.context",
    "460e785d0783": "eco.context",
    "4694101ef013": "eco.fin",
    "429fbbfa26ff": "eco.context",
    "5b420349fcb1": "eco.target_fin",
    "6da2c32d9687": "eco.context",
    "a94fef4a942c": "eco.rationale",
    "c9bfe2d781df": "eco.val",
    "b2debd7f9967": "eco.fin",
    "5cbf571fd6fc": "eco.target_fin",
    "800472fd95ef": "eco.rationale",
    "1578f35a0e49": "eco.context",
    "114deb4ca71b": "law.terms",
    "a71fe2f461f6": "eco.fin",
    "67b760e8e1e5": "eco.context",
    "953af8df14bc": "eco.context",
    "6d0401223483": "eco.context",
    "3d9f500be46b": "eco.context",
    "549469cb3b9e": "eco.target_fin",
    "e8fe126245d7": "eco.target_fin",
    "0b7c0c506010": "law.struct",
    "2dfcd911591d": "extra",
    "499cc8181adb": "eco.context",
    "dde6f5c4cb4e": "eco.context",
    "8816c59af44f": "eco.rationale",
    "c1cf004fdb54": "eco.fin",
    "28e81ec88a8a": "law.adv",
    "fa56ab899be1": "eco.rationale",
    "bd1ec52dde8d": "law.struct",
    "63c3f2bd3ddf": "eco.context",
    "2b7958d78841": "eco.fin",
    "eb94d90e0914": "eco.context",
    "40c2a3431891": "eco.share",
    "1ea52bbcf0f2": "eco.share",
    "bc93f9bd9dfc": "law.adv",
    "77c30e21b0e2": "eco.context",
    "49071107385d": "eco.fin",
    "874212f47616": "eco.context",
    "2daf3e07c5b3": "extra",
    "5a6f3ed90c28": "extra",
    "d7d6944bc2a4": "eco.context",
    # 1e2811b50c17 (gd73fd825, «Консорциум.Первый / Яндекс») НЕ включена —
    # analytics_gold.json's «why» дословно цитирует этот текст eco.share
    # («первый этап — 68%») как пример НЕустановленной по этапу доли —
    # перенос стёр бы доказательную базу методического решения.
    "2bd3fbf53eb3": "eco.context",
    "90a4eed8a362": "eco.context",
    "7c904b78b00a": "law.terms",
    "63e2d1ec2bfe": "law.terms",
    "202a92ff9e85": "eco.fin",
    "e72dd9adbc86": "eco.context",
    "5848972b4799": "eco.context",
    "66bb79f76274": "eco.context",
    "127ca89b0da4": "eco.context",
    "903eddd7b6c9": "eco.context",
    "b8b8153b4b7c": "eco.context",
    "85c98913a37d": "law.struct",
    "81d3b6c45f3c": "eco.share",
    # 1e2811b50c17 (gd73fd825) и 77dcc4b3f8e8 (g0201b97a) НЕ включены:
    # analytics_gold.json's «why» для обеих карточек дословно цитирует
    # именно этот текст eco.share как пример, почему доля НЕ равна доле
    # промежуточного этапа/доле реструктуризации покупателя (методика
    # stakeEstablished — «первый этап 68%» и «100% долей головной компании
    # перешли к…»). Перенос этого текста стёр бы доказательную базу
    # методического решения, а не просто переставил абзац по смыслу поля.
    "24b1a8d03950": "law.struct",
    "5fbbbd7b081f": "eco.context",
    "cf724f2e9e0a": "eco.fin",
    "38347b5b7b2a": "eco.fin",
    "322a65c85991": "eco.context",
    "1bfbb72fec3e": "eco.fin",
    "7d291b4a60b3": "eco.context",
    "2b1f66646efe": "eco.context",
    "56dc3ea548b9": "eco.context",
    "fecd24c755da": "eco.target_fin",
    "900a110aa5fd": "eco.share",
    "fbc814b9a089": "eco.target_fin",
    "d0db4a925fe2": "eco.context",
    "c70492928d85": "eco.context",
    "68727feef308": "eco.context",
    "60e3bae7d7c6": "eco.context",
    "2fe3f4d23fcb": "eco.rationale",
    "e7f4db8d7a81": "eco.context",
    "83203c17c9dc": "law.struct",
    "31b5955eefda": "eco.context",
    "d655600dbc16": "eco.context",
    "c2ba68fef109": "eco.context",
    "dc8de03552d0": "eco.share",
    "299d06720e24": "eco.context",
    "95dad5f948ea": "eco.context",
    "664daf41a1b5": "eco.context",
    "e1a97a9c3fb5": "eco.fin",
    "c76de6f151d2": "eco.context",
    "cff7e44ab353": "eco.context",
    "41d46454fe25": "eco.val",
    "d12b02a06ddc": "eco.context",
    "c1c5429bce34": "eco.fin",
    "3b13f8c3b315": "eco.context",
    "1fc4ac91ad6c": "eco.context",
    "11c8c5a9246b": "law.struct",
    "e826621c8192": "extra",
    "1238b2d40d5b": "extra",
    "620a46c8df3c": "law.appr",
    "db3f80cb4b26": "law.appr",
    "693d8e2716dc": "law.terms",
    "8a2798eb9754": "eco.context",
    "260ca4cc9429": "law.appr",
    "afc7cb1b3a68": "eco.context",
    "2f85b3b1c226": "eco.share",
    "9e431af3e671": "eco.context",
    "2fc0f1bc1379": "law.struct",
    "753c55e4e3d8": "eco.context",
    "e68981afd3ec": "extra",
    "727989300a69": "extra",
    "bff9cccad963": "law.terms",
    "85a094071099": "eco.fin",
    "11da2c42eb6e": "eco.target_fin",
    "116668cc108d": "eco.target_fin",
    "1717fb691981": "eco.context",
    "61d2dd32885e": "eco.context",
    "e6796f6cee83": "eco.context",
    "572e4ccd1521": "eco.context",
    # 77dcc4b3f8e8 (g0201b97a, «Ингосстрах Банк») НЕ включена —
    # analytics_gold.json's «why» дословно цитирует этот текст eco.share
    # («100% долей головной компании перешли к…») как пример НЕустановленной
    # доли (реструктуризация покупателя, а не доля сделки) — доля задана
    # отдельным явным полем stake_acquired именно из-за этого предложения.
    "2cfa75f8b42f": "eco.val",
    "82ff55d3de6e": "eco.val",
    "683ebffe5d64": "eco.fin",
    "03bd43f72f10": "eco.target_fin",
    "89219781bc45": "eco.context",
    "8a705f09718b": "eco.context",
    "d8370232b28d": "eco.share",
    # 741a165bd126 (gd73a6964) НЕ включена: eco.target_fin — одно
    # предложение через точку с запятой («выручка… при прибыли…; аналитик
    # оценивал мультипликатор…») — extend_to_sentences не режет по «;» и
    # увела бы ВМЕСТЕ с мультипликатором законную цифру выручки/прибыли.
    # Нужен ручной раздел предложения, не механический перенос.
    "f90170c22ea9": "eco.rationale",
    "835b4f57cbe0": "eco.context",
    "3761f93af2a2": "eco.share",
    "55709adc2074": "eco.context",
    "7d6d7e727be4": "eco.context",
    "b5e71b8e1ae9": "eco.rationale",
    "3187fec01492": "extra",
}

# Перенос без назначения (дублирует уже сказанное в другом месте карточки
# или в профиле компании дословно/по смыслу) — просто убрать из источника.
DELETE_ONLY = {"c96634d11d35", "f2c5e5d20476", "8829fb743906", "81f9d731c5a3"}

# Карточка g92107ce6 (ключ находки c678c82fb0c4): находка с ДВУМЯ стрелками
# в одном action — сначала освободить eco.target_fin (переложив то, что там
# лежит сейчас, в extra), потом заполнить eco.target_fin настоящими цифрами
# предмета из eco.context.
TWO_STEP_CARD = "g92107ce6"


def apply_delete(card: dict, src_path: str, quote: str, write: bool,
                 decided: set, card_id: str, log: list) -> bool:
    src_text = get_field(card, src_path) or ""
    if quote not in src_text:
        log.append("%s: цитата не найдена в %s — пропущено" % (card_id, src_path))
        return False
    if (card_id, src_path) in decided:
        log.append("%s: %s решено читателем — пропущено" % (card_id, src_path))
        return False
    chunk = extend_to_sentences(src_text, quote)
    new_src = src_text.replace(chunk, "").strip()
    new_src = re.sub(r"\s+", " ", new_src)
    log.append("%s: %s — дубль убран без переноса «%s…»" % (card_id, src_path, chunk[:50]))
    if write:
        set_field(card, src_path, new_src if new_src else "—")
    return True


def main(write: bool) -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    cards = {d["id"]: d for d in data["deals"]}
    decided = aq.decided_by_a_reader()
    findings = {}
    for f in json.loads(BATCH_FILE.read_text(encoding="utf-8"))["findings"]:
        findings[aq.key_of(f)] = f
    orig = json.loads(
        (ROOT / "pipeline" / "audit_field_placement" / "findings.json").read_text(encoding="utf-8")
    )["findings"]
    for f in orig:
        findings.setdefault(aq.key_of(f), f)

    log: list = []
    applied = 0
    skipped = 0

    for key, dst in KEY_DST.items():
        f = findings.get(key)
        if f is None:
            log.append("%s: находка не найдена в источниках — пропущено" % key)
            skipped += 1
            continue
        cid = f["card_id"]
        if cid not in cards:
            log.append("%s (%s): карточки нет в базе — пропущено" % (key, cid))
            skipped += 1
            continue
        src = norm_field(f["field"])
        ok = apply_move(cards[cid], src, f["quote"], dst, write, decided, cid, log)
        applied += int(ok)
        skipped += int(not ok)

    for key in DELETE_ONLY:
        f = findings.get(key)
        if f is None:
            log.append("%s: находка не найдена — пропущено" % key)
            skipped += 1
            continue
        cid = f["card_id"]
        if cid not in cards:
            skipped += 1
            continue
        src = norm_field(f["field"])
        ok = apply_delete(cards[cid], src, f["quote"], write, decided, cid, log)
        applied += int(ok)
        skipped += int(not ok)

    # Карточка g92107ce6 — вращение eco.target_fin ↔ extra ↔ eco.context.
    card = cards.get(TWO_STEP_CARD)
    if card is not None:
        old_target_fin_quote = (
            "В результате Cosmos Hotel Group удвоила номерной фонд — до более "
            "9 500 номеров; выручка группы по итогам 2023 года составила 12 млрд ₽."
        )
        # extra УЖЕ несёт этот же факт (с добавленным «(рост в 2,4 раза год к
        # году)») — apply_move сюда создал бы дубль текста внутри extra
        # (точка после «12 млрд ₽.» не совпадает дословно с «12 млрд ₽ (рост…»,
        # поэтому встроенная в apply_move защита от дубля не сработала бы).
        # Верно убрать без переноса, а не переложить рядом с почти тем же.
        ok1 = apply_delete(card, "eco.target_fin", old_target_fin_quote,
                           write, decided, TWO_STEP_CARD, log)
        applied += int(ok1)
        skipped += int(not ok1)
        # Теперь ищем в eco.context реальные цифры предмета (10 отелей) и
        # переносим их в освобождённый eco.target_fin.
        ctx = get_field(card, "eco.context") or ""
        needle = "Совокупный номерной фонд приобретённых отелей"
        if needle in ctx and (TWO_STEP_CARD, "eco.context") not in decided and \
           (TWO_STEP_CARD, "eco.target_fin") not in decided:
            chunk = extend_to_sentences(ctx, needle)
            log.append("%s: eco.context → eco.target_fin «%s…»"
                       % (TWO_STEP_CARD, chunk[:50]))
            applied += 1
            if write:
                cur = get_field(card, "eco.target_fin") or ""
                new_val = chunk if not cur or cur in ("—", "-") else cur + " " + chunk
                set_field(card, "eco.target_fin", new_val)
                new_ctx = ctx.replace(chunk, "").strip()
                new_ctx = re.sub(r"\s+", " ", new_ctx)
                set_field(card, "eco.context", new_ctx if new_ctx else "—")
        else:
            log.append("%s: eco.context не содержит ожидаемый фрагмент о номерах отелей — пропущено"
                       % TWO_STEP_CARD)
            skipped += 1

    print("Применено: %d, пропущено: %d" % (applied, skipped))
    for line in log:
        print("   " + line)

    if not write:
        print("\n(сухой прогон; чтобы записать — --write)")
        return 0
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nзаписано")
    return 0


if __name__ == "__main__":
    sys.exit(main("--write" in sys.argv))
