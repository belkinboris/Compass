# -*- coding: utf-8 -*-
"""Сколько места осталось в документах и что пропадёт, если их почистить.

ЗАЧЕМ. Документы, которые читает каждый прогон, — постоянный налог на любую
работу: CLAUDE.md и PRODUCT_ROADMAP.md за лето выросли до 541 и 2,9 млн
знаков, и 98% стоимости часовой рутины уходило на их перечитывание. Чистки
уже было две: 18 сентября 2026 CLAUDE.md 541 → 113 тыс. знаков (вынесено в
KNOWN_ISSUES.md), 20 сентября бэклог 117 → 81 тыс. (закрытое — в архив).
Обе делались вручную и «по ощущению, что пора».

Этот файл отвечает на два вопроса, которые после каждой такой чистки
задаёт владелец:

  1. СКОЛЬКО ОСТАЛОСЬ ЗАПАСА — `--stats`. Потолок ловит превышение постфактум,
     когда прогон уже сломан; здесь видно заранее, у какого файла запас
     кончается, и какой командой его чистят.

  2. НЕ ПОТЕРЯЛИ ЛИ ЛИШНЕГО — `--anchors <коммит>`. Сравнивает «якоря»
     (имена скриптов, тестов, id карточек), на которые ссылался документ
     ДО чистки, с тем, что есть во всех документах ПОСЛЕ. Это не сравнение
     текстов — при чистке текст переписывают, и построчный diff бесполезен;
     якорь же либо остался адресуемым, либо исчез. Исчезнувший якорь —
     не приговор (одноразовый скрипт правки одной карточки помнить незачем),
     а список для глаз: смотрим, нет ли среди пропавших правила.

Проверено этим же способом на чистке 18 сентября: из 131 имени скрипта
пропало 29 (все — одноразовые `fix_*.py` по конкретным карточкам), из 64
тестов — 12 (сами тесты в репозитории на месте, со своими докстроками, то
есть знание переехало в код), из 98 id карточек — 50 (хроника «у карточки X
был дефект Y», сам дефект починен).

    python3 pipeline/docs_budget.py --stats
    python3 pipeline/docs_budget.py --anchors 806deb14^ --doc CLAUDE.md
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# файл -> (потолок, чем чистят). Потолки держит test_docs.py — здесь они
# повторены только для отчёта; единственный источник правды там.
DOCS = {
    'CLAUDE.md': (110_000, 'вручную: правила остаются, баги — в KNOWN_ISSUES.md, '
                           'очереди — в консоль (send_open_questions.py)'),
    'PRODUCT_ROADMAP.md': (200_000, 'python3 pipeline/roadmap_archive.py --journal --write'),
    'KNOWN_ISSUES.md': (320_000, 'вручную: запись «симптом — причина — чем починено», '
                                 'без хроники поиска'),
}
ARCHIVES = ('PRODUCT_ROADMAP_ARCHIVE.md',)

ANCHORS = {
    'скрипты': r'\b[a-z_]{4,}\.py\b',
    'тесты': r'\btest_[a-z_]{6,}\b',
    'карточки': r'\bg[0-9a-f]{8}\b',
}


def _read(path: str) -> str:
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        return ''
    with open(full, encoding='utf-8') as fh:
        return fh.read()


def stats() -> int:
    print('%-28s %9s %9s %6s  %s' % ('документ', 'знаков', 'потолок', 'занято', 'запас'))
    tight = []
    for name, (limit, _how) in DOCS.items():
        n = len(_read(name))
        share = n / limit
        left = limit - n
        mark = '⚠️ ' if share >= 0.85 else '   '
        print('%s%-25s %9d %9d %5.0f%%  %+d' % (mark, name, n, limit, share * 100, left))
        if share >= 0.85:
            tight.append((name, share))
    for name in ARCHIVES:
        n = len(_read(name))
        if n:
            print('   %-25s %9d %9s %6s  архив, прогоны его не читают' % (name, n, '—', '—'))
    if not tight:
        print('\nЗапас есть у всех — чистить нечего.')
        return 0
    print('\nЗапас кончается — чистить до того, как потолок уронит прогон:')
    for name, share in tight:
        print('  • %s (%.0f%%) — %s' % (name, share * 100, DOCS[name][1]))
    print('\nПеред чисткой и после неё: python3 pipeline/docs_budget.py --anchors <коммит до>')
    return 0


def anchors(commit: str, doc: str) -> int:
    old = subprocess.run(['git', 'show', '%s:%s' % (commit, doc)],
                         capture_output=True, text=True, cwd=ROOT).stdout
    if not old.strip():
        print('Не удалось прочитать %s на коммите %s' % (doc, commit))
        return 1
    now = ''.join(_read(n) for n in list(DOCS) + list(ARCHIVES))
    print('Якоря %s на %s против всех сегодняшних документов:\n' % (doc, commit))
    for kind, pat in ANCHORS.items():
        was, has = set(re.findall(pat, old)), set(re.findall(pat, now))
        gone = sorted(was - has)
        print('%-12s было %4d, осталось %4d, исчезло %4d' % (kind, len(was), len(was & has), len(gone)))
        for x in gone[:25]:
            print('      %s' % x)
        if len(gone) > 25:
            print('      … ещё %d' % (len(gone) - 25))
    print('\nИсчезнувший якорь — повод прочитать, а не признак потери: одноразовые\n'
          'скрипты правок и id починенных карточек помнить не нужно, а вот правило\n'
          'или живой тест в этом списке означают, что знание осталось без адреса.')
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--stats', action='store_true')
    ap.add_argument('--anchors', default='', metavar='КОММИТ')
    ap.add_argument('--doc', default='CLAUDE.md')
    a = ap.parse_args(argv)
    if a.anchors:
        return anchors(a.anchors, a.doc)
    return stats()


if __name__ == '__main__':
    sys.exit(main())
