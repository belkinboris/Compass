# -*- coding: utf-8 -*-
"""Сколько места осталось в документах, что пропадёт при чистке и где что искать.

ЗАЧЕМ. Документы, которые читает каждый прогон, — постоянный налог на любую
работу: CLAUDE.md и PRODUCT_ROADMAP.md за лето выросли до 541 и 2,9 млн
знаков, и 98% стоимости часовой рутины уходило на их перечитывание. Чистки
уже было две: 18 сентября 2026 CLAUDE.md 541 → 113 тыс. знаков (вынесено в
KNOWN_ISSUES.md), 20 сентября бэклог 117 → 81 тыс. (закрытое — в архив).
Обе делались вручную и «по ощущению, что пора».

ДЕЛЕНИЕ, ОТ КОТОРОГО ЗАВИСИТ ВСЁ ОСТАЛЬНОЕ (21 сентября 2026). Документы
бывают двух видов, и правило у них противоположное:

  ЧИТАЕТСЯ ЦЕЛИКОМ КАЖДЫЙ ПРОГОН (`READ_WHOLE`) — CLAUDE.md, PRODUCT_ROADMAP.md.
  Здесь каждый знак умножается на число прогонов, поэтому стоит жёсткий
  потолок, и потолок — не бюрократия, а единственное, что заставляет
  переписывать длинное короче. Сюда идут ПРАВИЛА и ОТКРЫТАЯ работа.

  ИЩЕТСЯ ПО ЗАПРОСУ (`SEARCHED`) — KNOWN_ISSUES.md, PRODUCT_ROADMAP_ARCHIVE.md.
  Здесь размер не стоит НИЧЕГО, пока за один вопрос читают одну запись, а не
  весь файл. Потолок тут вреден прямо: место кончится — новый баг не запишут,
  и следующий прогон выведет его заново за те же токены, ради экономии
  которых потолок и ставили. Поэтому потолка нет, а вместо него — инвариант
  «одна запись = один ответ» (`test_docs.py`) и команда `--find`.

ТРЕТИЙ ВИД — ЧИТАЕТСЯ НА ШАГЕ (24 сентября 2026). `routines/*.md` —
порядок работы одной рутины, его читает только она; `docs/*.md` —
устройство подсистемы, открывается, когда работа её касается. Сюда же
переехало всё, что CLAUDE.md держал «на всякий случай» (97 → 17 тыс.
знаков): правило, нужное одной рутине, больше не оплачивают остальные
пять. Потолок здесь есть, но смысл у него другой, чем у CLAUDE.md: он
сигнал РАЗДЕЛИТЬ документ по темам, а не вычищать его.

Отсюда три вопроса, на которые отвечает этот файл:

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

  3. ГДЕ ПРО ЭТО УЖЕ НАПИСАНО — `--find <слова>`. Ищет по ЗАПИСЯМ, а не по
     строкам: находит заголовок, под которым лежит ответ, и показывает начало
     записи. Это и есть способ читать KNOWN_ISSUES.md и архив — открыть одну
     запись на 2 тыс. знаков вместо файла на 276 тыс. Пока такой команды не
     было, оба файла приходилось либо читать целиком (дорого), либо не читать
     вовсе (архив, 238 записей с замерами и отвергнутыми гипотезами, никто не
     открывал ни разу).

Проверено способом (2) на чистке 18 сентября: из 131 имени скрипта
пропало 29 (все — одноразовые `fix_*.py` по конкретным карточкам), из 64
тестов — 12 (сами тесты в репозитории на месте, со своими докстроками, то
есть знание переехало в код), из 98 id карточек — 50 (хроника «у карточки X
был дефект Y», сам дефект починен).

    python3 pipeline/docs_budget.py --stats
    python3 pipeline/docs_budget.py --find "падеж предмета сделки"
    python3 pipeline/docs_budget.py --anchors 806deb14^ --doc CLAUDE.md
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Читается ЦЕЛИКОМ каждый прогон -> файл -> (потолок, чем чистят).
# Потолки держит test_docs.py — здесь они повторены только для отчёта;
# единственный источник правды там.
READ_WHOLE = {
    'CLAUDE.md': (30_000, 'перенести правило туда, где его читают: одной рутины — в '
                          'routines/, подсистемы — в docs/, баг — в KNOWN_ISSUES.md, '
                          'очередь — в консоль (send_open_questions.py)'),
    'PRODUCT_ROADMAP.md': (200_000, 'python3 pipeline/roadmap_archive.py --journal --write'),
}
DOCS = READ_WHOLE  # прежнее имя: им пользуются --anchors и старые вызовы

# Читается на шаге: папка -> (потолок на ОДИН файл, что делать у потолка).
# Держит test_docs.py; здесь повторено для отчёта.
READ_ON_STEP = {
    'routines': (20_000, 'вынести устройство в docs/, в файле рутины оставить шаги'),
    'docs': (30_000, 'разделить документ по темам на два — не вычищать'),
}


def step_docs():
    """Все файлы, которые читаются на шаге: [(путь, потолок, что делать)]."""
    out = []
    for folder, (limit, how) in READ_ON_STEP.items():
        base = os.path.join(ROOT, folder)
        if not os.path.isdir(base):
            continue
        for name in sorted(os.listdir(base)):
            if name.endswith('.md') and not name.startswith('launch_texts_'):
                out.append(('%s/%s' % (folder, name), limit, how))
    return out

# Ищется по запросу -> файл -> (уровень заголовка записи, зачем он нужен).
# Потолка нет намеренно: см. «ДЕЛЕНИЕ» в шапке.
SEARCHED = {
    'KNOWN_ISSUES.md': ('##', 'баг, который уже ловили: симптом, причина, чем починено'),
    'PRODUCT_ROADMAP_ARCHIVE.md': ('###', 'закрытая работа и замеры: что мерили, что вышло, '
                                          'что отвергли и почему'),
}
ARCHIVES = tuple(SEARCHED)

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
    print('ЧИТАЕТСЯ ЦЕЛИКОМ каждый прогон — здесь знаки стоят денег, потолок обязателен')
    print('%-28s %9s %9s %6s  %s' % ('документ', 'знаков', 'потолок', 'занято', 'запас'))
    tight = []
    for name, (limit, _how) in READ_WHOLE.items():
        n = len(_read(name))
        share = n / limit
        mark = '⚠️ ' if share >= 0.85 else '   '
        print('%s%-25s %9d %9d %5.0f%%  %+d' % (mark, name, n, limit, share * 100, limit - n))
        if share >= 0.85:
            tight.append((name, share))
    print('\nЧИТАЕТСЯ НА ШАГЕ — одной рутиной или когда работа касается темы')
    for name, limit, how in step_docs():
        n = len(_read(name))
        share = n / limit
        mark = '⚠️ ' if share >= 0.85 else '   '
        print('%s%-25s %9d %9d %5.0f%%  %+d' % (mark, name, n, limit, share * 100, limit - n))
        if share >= 0.85:
            tight.append((name, share))
    print('\nИЩЕТСЯ ПО ЗАПРОСУ (--find) — размер не важен, важен размер ОДНОЙ записи')
    print('%-28s %9s %9s  %s' % ('документ', 'знаков', 'записей', 'запись в среднем'))
    for name, (level, _what) in SEARCHED.items():
        text = _read(name)
        if not text:
            continue
        entries = _entries(name, text)
        avg = sum(len(e[2]) for e in entries) // max(1, len(entries))
        print('   %-25s %9d %9d  %d знаков' % (name, len(text), len(entries), avg))
    if not tight:
        print('\nЗапас есть у всех — чистить нечего.')
        return 0
    print('\nЗапас кончается — чистить до того, как потолок уронит прогон:')
    for name, share in tight:
        how = READ_WHOLE[name][1] if name in READ_WHOLE else next(
            h for n, _l, h in step_docs() if n == name)
        print('  • %s (%.0f%%) — %s' % (name, share * 100, how))
    print('\nПеред чисткой и после неё: python3 pipeline/docs_budget.py --anchors <коммит до>')
    return 0


def _entries(name: str, text: str = None):
    """[(строка, заголовок, текст записи)] — разбор документа на записи.

    Запись — кусок от своего заголовка до следующего того же уровня. Именно
    она, а не файл, — единица ответа: `--find` показывает запись, и цена
    вопроса не зависит от того, сколько записей накопилось рядом.
    """
    if text is None:
        text = _read(name)
    level = SEARCHED.get(name, ('##',))[0]
    out, cur, start, head = [], [], 0, ''
    for i, line in enumerate(text.split('\n'), 1):
        if line.startswith(level + ' ') and not line.startswith(level + '#'):
            if head:
                out.append((start, head, '\n'.join(cur)))
            start, head, cur = i, line[len(level):].strip(), []
        elif head:
            cur.append(line)
    if head:
        out.append((start, head, '\n'.join(cur)))
    return out


def find(words: str, limit: int = 6) -> int:
    """Показать записи, где про это уже написано.

    Счёт устроен так, чтобы не выигрывала длина. Длинная запись журнала
    набирает совпадения просто потому, что в ней много слов, — поэтому
    сначала требуются ВСЕ слова запроса, потом считается, сколько их попало
    в ЗАГОЛОВОК (заголовок называет симптом — это и есть ответ на «про это
    уже писали?»), и только при равенстве побеждает та запись, где слова
    стоят плотнее. Слова ищутся по началу: «падеж» находит «падежом».
    """
    terms = [w.lower() for w in re.findall(r'\w{3,}', words)]
    if not terms:
        print('Нечего искать: нужны слова длиннее двух знаков.')
        return 1
    # по основе слова: запрос «падеж предмета» должен находить «падежом предмета»
    stems = [t[:max(4, len(t) - 2)] for t in terms]
    hits = []
    for name in list(SEARCHED) + [n for n, _l, _h in step_docs()]:
        for line, head, body in _entries(name):
            low_head, low_body = head.lower(), body.lower()
            hay = low_head + '\n' + low_body
            if not all(s in hay for s in stems):
                continue
            in_head = sum(1 for s in stems if s in low_head)
            density = sum(hay.count(s) for s in stems) / max(300, len(hay)) * 1000
            hits.append((in_head, round(density, 2), name, line, head, body))
    hits.sort(key=lambda h: (-h[0], -h[1]))
    hits = [(0,) + h[2:] for h in hits]
    if not hits:
        print('Ничего не нашлось по словам: %s' % ', '.join(terms))
        print('Это не значит «такого не было» — попробуйте другое слово из симптома.')
        return 0
    print('Нашлось записей: %d, показаны %d.\n' % (len(hits), min(limit, len(hits))))
    for _score, name, line, head, body in hits[:limit]:
        print('%s:%d' % (name, line))
        print('  %s' % head)
        snippet = ' '.join(body.split())[:500]
        print('  %s%s\n' % (snippet, '…' if len(' '.join(body.split())) > 500 else ''))
    if len(hits) > limit:
        print('… ещё %d записей послабее. Читать запись целиком — по адресу '
              '«файл:строка» выше.' % (len(hits) - limit))
    return 0


def anchors(commit: str, doc: str) -> int:
    old = subprocess.run(['git', 'show', '%s:%s' % (commit, doc)],
                         capture_output=True, text=True, cwd=ROOT).stdout
    if not old.strip():
        print('Не удалось прочитать %s на коммите %s' % (doc, commit))
        return 1
    now = ''.join(_read(n) for n in list(DOCS) + list(ARCHIVES)
                  + [n for n, _l, _h in step_docs()])
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
    ap.add_argument('--find', default='', metavar='СЛОВА')
    ap.add_argument('--limit', type=int, default=6)
    a = ap.parse_args(argv)
    if a.find:
        return find(a.find, a.limit)
    if a.anchors:
        return anchors(a.anchors, a.doc)
    return stats()


if __name__ == '__main__':
    sys.exit(main())
