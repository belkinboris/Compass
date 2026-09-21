# -*- coding: utf-8 -*-
"""Документы, которые читает КАЖДЫЙ прогон, не должны расти сами.

PRODUCT_ROADMAP.md и CLAUDE.md — постоянная стоимость любой работы: их
читают все три рутины каждый час. Поэтому у них есть потолок, а у бэклога —
правило «здесь только открытая работа». Тесты ниже не про красоту файла, а
про счёт: без них файл отрастает обратно, и налог на каждый следующий
прогон растёт сам собой (это уже случалось с журналом работ).
"""
import io
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
ROADMAP = io.open(os.path.join(ROOT, "PRODUCT_ROADMAP.md"), encoding="utf-8").read()
CLAUDE = io.open(os.path.join(ROOT, "CLAUDE.md"), encoding="utf-8").read()
BACKLOG = ROADMAP[ROADMAP.index("## 4. Бэклог"):ROADMAP.index("## 5. Журнал работ")]
JOURNAL = ROADMAP[ROADMAP.index("## 5. Журнал работ"):]

# Замер 20 сентября 2026 — 168 798 знаков после переноса закрытого в архив.
# Запас взят небольшой намеренно: как только он выбран, это сигнал сдвинуть
# журнал (`roadmap_archive.py --journal --write`), а не поднять потолок.
ROADMAP_LIMIT = 200_000
CLAUDE_LIMIT = 110_000
VERDICT = re.compile(r"\b(ЗАКРЫТ|СДЕЛАН|ПРОВЕРЕН|СНЯТ|ИСЧЕРПАН)[А-ЯЁ]*\b")
# Вердикт о готовности пишут жирным («**СДЕЛАНО 30 августа**»). Те же слова
# в обычном тексте — про подвопрос внутри ещё открытой задачи («вопрос закрыт
# чтением источника»), и это не повод считать задачу сделанной.
BOLD_VERDICT = re.compile(r"\*\*\s*(ЗАКРЫТ|СДЕЛАН|ПРОВЕРЕН|ГОТОВ)[А-ЯЁ]*\b")


def _items(text):
    """Пункты бэклога. Пункт кончается на следующем пункте ИЛИ на заголовке
    блока: последний пункт блока иначе «съедает» заголовок соседнего вместе
    с его вступлением — ровно так 20 сентября 2026 пропал блок «E. Живая
    база», и тот же промах сначала был в этой проверке."""
    starts = [m.start() for m in re.finditer(r"^- ", text, re.M)]
    out = []
    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else len(text)
        body = text[s:e]
        head = re.search(r"^#{2,3} ", body[1:], re.M)
        if head:
            body = body[:1 + head.start()]
        out.append(body)
    return out


def test_roadmap_stays_within_its_budget():
    assert len(ROADMAP) <= ROADMAP_LIMIT, (
        "PRODUCT_ROADMAP.md вырос до %d знаков при потолке %d — сдвиньте журнал "
        "и закрытые пункты в архив: python3 pipeline/roadmap_archive.py "
        "--journal --write" % (len(ROADMAP), ROADMAP_LIMIT))


def test_claude_md_stays_within_its_budget():
    assert len(CLAUDE) <= CLAUDE_LIMIT, (
        "CLAUDE.md вырос до %d знаков при потолке %d — здесь живут правила, "
        "а не очереди и не журнал" % (len(CLAUDE), CLAUDE_LIMIT))


def test_known_issues_stays_within_its_budget():
    """У третьего документа потолка не было, и он рос как первые два.

    18 сентября 2026 CLAUDE.md ужали с 541 до 113 тыс. знаков, вынеся баги в
    KNOWN_ISSUES.md, — и новый файл сразу начал расти теми же темпами (276
    тыс. к 21 сентября), только теперь без всякого предела. Потолок здесь
    мягче, чем у CLAUDE.md: этот файл читают не каждым прогоном, а поиском по
    слову, когда чинят похожий баг. Но без предела он повторит ту же историю.
    Запас смотреть заранее: python3 pipeline/docs_budget.py --stats
    """
    known = io.open(os.path.join(ROOT, "KNOWN_ISSUES.md"), encoding="utf-8").read()
    assert len(known) <= 320_000, (
        "KNOWN_ISSUES.md вырос до %d знаков при потолке %d — запись это «симптом, "
        "причина в одну фразу, чем починено», без хроники поиска" % (len(known), 320_000))


def test_a_finished_item_does_not_pretend_to_be_open():
    """Хуже зачёркнутого пункта только незачёркнутый, который уже сделан.

    20 сентября 2026 в бэклоге стояли открытыми G12 и G13, а внутри у обоих
    было написано «СДЕЛАНО 30 августа». Читатель бэклога видел работу,
    которой нет."""
    liars = []
    for item in _items(BACKLOG):
        if item.startswith("- ~~"):
            continue
        head = item.split("\n")[0]
        if BOLD_VERDICT.search(item) and not VERDICT.search(head):
            liars.append(re.sub(r"\s+", " ", head)[:80])
    assert not liars, "пункт не зачёркнут, но внутри вердикт о готовности: %s" % liars


def test_a_closed_item_leaves_only_a_line():
    """Закрытый пункт остаётся строкой-напоминанием, а разбор уезжает в архив."""
    long = []
    for item in _items(BACKLOG):
        if item.startswith("- ~~") and len(item) > 700:
            long.append(re.sub(r"\s+", " ", item)[:80])
    assert not long, ("закрытый пункт всё ещё несёт разбор (>700 знаков): %s — "
                      "перенесите: python3 pipeline/roadmap_archive.py --archive "
                      "--write" % long)


def test_every_backlog_block_keeps_its_heading():
    """Заголовок блока — не украшение: по нему видно, какое направление ещё
    открыто, а какое пройдено целиком.

    20 сентября 2026 моя разовая правка заглушки последнего пункта блока A
    забрала с собой заголовок «E. Живая база» и абзац о том, как устроен
    приток: регулярка `.*?(?=^- |\Z)` дотянулась до следующего ПУНКТА, а
    между ними стоял заголовок соседнего блока. Четыре открытых пункта E
    после этого читались как пункты A. Список ниже меняется только
    осознанно — когда направление закрыто целиком и блок убран руками."""
    blocks = re.findall(r"^### ([A-ZА-Я])\.", BACKLOG, re.M)
    assert blocks == ["A", "E", "B", "C", "D", "F", "G"], blocks


def test_the_journal_in_the_main_file_is_short():
    days = sorted({m.group(1) for m in
                   re.finditer(r"^### (\d{4}-\d{2}-\d{2})", JOURNAL, re.M)})
    assert len(days) <= 3, (
        "в основном файле журнал за %d дней (%s…%s) — сдвиньте старые записи: "
        "python3 pipeline/roadmap_archive.py --journal --write"
        % (len(days), days[0], days[-1]))
