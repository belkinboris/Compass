# -*- coding: utf-8 -*-
"""Синхронизация таблицы `FIXES` с базой после сплошных прогонов вычитки.

ЗАЧЕМ. `test_review_table_is_applied_and_not_pending` требует, чтобы КАЖДАЯ
запись таблицы `pipeline/ingest/fixes/*.py` совпадала с текущим состоянием
базы: иначе непонятно, применена правка или потерялась. Прогоны вычитки
15 августа 2026 изменили значения полей, которые эти записи описывают:

  * `strip_import_service_tails.py` снял служебные хвосты («Сумма: …»,
    «(X (инвестор))») — текст поля стал короче записи в таблице;
  * `fix_rationale_duplicating_extra.py` удалил `eco.rationale`,
    дублировавший `extra`, — поля больше нет вовсе;
  * `fix_proofreading_round1.py` перевёл 33 поля с английского и немецкого —
    текст поля другой целиком.

Типографские расхождения (кавычки, тире, десятичный знак) ловить не нужно:
их с этого же дня складывает `review.typo_flat()` внутри `already_applied` —
503 записи из 585 закрылись именно так. Здесь остаются 65 записей, где
изменилось СОДЕРЖАНИЕ, а не знаки.

ЧТО ДЕЛАЕТ СКРИПТ. Для каждой разошедшейся записи переписывает в исходнике
`new=` на текущее значение поля, а если поле удалено — убирает запись
целиком. Это ровно та практика, что уже описана в CLAUDE.md для правок,
ложащихся на одно поле дважды: «правки СЛИВАЮТСЯ в одну запись… `new` —
итоговое значение», а история остаётся в комментарии — здесь роль
комментария играет этот файл.

ПОЧЕМУ ЧЕРЕЗ `ast`, А НЕ РЕГУЛЯРКОЙ. Первая версия искала границы значения
`new=` сканированием скобок вручную и сломала синтаксис в 8 файлах из 17:
внутри значений есть и скобки, и апострофы, и переносы строк, а строки
собраны неявной конкатенацией. `ast` даёт точные границы узла
(`lineno`/`col_offset`/`end_*`), и правки применяются с КОНЦА файла к
началу, чтобы смещения не поехали. После записи каждый файл проверяется
компиляцией — скрипт падает, если сам себя сломал.

ЧЕСТНАЯ ОГОВОРКА ПРО ПЕРЕВОДЫ. У 33 переведённых полей `quote` остаётся
на языке оригинала, а `new` становится русским, — дословная выводимость
значения из цитаты для них больше не выполняется. Это осознанная цена
перевода, а не недосмотр: русскоязычному читателю нельзя показывать
английский абзац, а машинной проверки «перевод верен» у нас нет. Числа
перевода сверены с оригиналом отдельным `assert` в
`fix_proofreading_round1.py`.

Запуск:
    python3 pipeline/sync_fixes_table_after_cleanup.py            # сухой прогон
    python3 pipeline/sync_fixes_table_after_cleanup.py --write    # запись
"""
import ast
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))

import review                                              # noqa: E402

FIXES_DIR = os.path.join(ROOT, 'pipeline', 'ingest', 'fixes')
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')


def offsets(src_bytes):
    """Смещение начала каждой строки В БАЙТАХ.

    `col_offset` у `ast` — смещение в БАЙТАХ utf-8, а не в символах. На
    кириллице (2 байта на букву) разница удваивается, и первая версия
    скрипта, считавшая символы, резала значение посреди соседнего аргумента
    — файл переставал компилироваться. Поэтому весь разбор и склейка идут
    по `bytes`, а в текст результат переводится один раз в конце."""
    out, pos = [0], 0
    for line in src_bytes.split(b'\n'):
        pos += len(line) + 1
        out.append(pos)
    return out


def node_span(starts, node):
    return (starts[node.lineno - 1] + node.col_offset,
            starts[node.end_lineno - 1] + node.end_col_offset)


def wrapped_literal(value, indent):
    """Строковый литерал Python — ОДНОЙ строкой, без переноса.

    Соседние записи в файлах свёрстаны неявной конкатенацией по 70 знаков, и
    первая версия так же резала новое значение на куски. Это ломало файл:
    `repr` выбирает кавычку по содержимому КУСКА, и при переносе рядом
    оказывались литералы с разными кавычками, а внутри текста есть и `'`, и
    `"`, и «ёлочки». Один `repr` на всё значение всегда корректен —
    длинная строка некрасива, но синтаксис важнее вёрстки."""
    return repr(str(value))


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    pending = json.load(open(PENDING, encoding='utf-8'))
    cards = {d['id']: d for d in data['deals']}
    cards.update({c['id']: c for c in pending['cards']})

    stale = {(f['id'], f['field']) for f in review.FIXES
             if cards.get(f['id']) and not review.already_applied(f, cards[f['id']])}
    print('Записей, разошедшихся с базой по СОДЕРЖАНИЮ: %d' % len(stale))

    updated, dropped, seen = 0, 0, set()
    results = {}

    for fn in sorted(os.listdir(FIXES_DIR)):
        if not fn.endswith('.py') or fn.startswith('__'):
            continue
        path = os.path.join(FIXES_DIR, fn)
        src = open(path, encoding='utf-8').read().encode('utf-8')
        tree = ast.parse(src)
        starts = offsets(src)
        edits = []

        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and getattr(node.func, 'id', '') == 'dict'):
                continue
            kw = {k.arg: k.value for k in node.keywords}
            if 'id' not in kw or 'field' not in kw:
                continue
            try:
                cid = ast.literal_eval(kw['id'])
                field = ast.literal_eval(kw['field'])
            except ValueError:
                continue
            if (cid, field) not in stale or (cid, field) in seen:
                continue
            seen.add((cid, field))
            current = review.get_field(cards[cid], field)

            if current is None:
                # Поле удалено (дубль «Цели сделки») — запись больше не о чём.
                s, e = node_span(starts, node)
                line_start = src.rfind(b'\n', 0, s) + 1
                tail = e
                while tail < len(src) and src[tail:tail + 1] == b',':
                    tail += 1
                # До конца ЭТОЙ строки включая перевод — не дальше: иначе
                # съедаем отступ следующей записи, если она идёт сразу следом
                # (нашлось по факту — 29 строк `dict(...)` в fixes/*.py
                # потеряли отступ ровно там, где перед ними стояла снятая
                # запись).
                while tail < len(src) and src[tail:tail + 1] == b' ':
                    tail += 1
                if tail < len(src) and src[tail:tail + 1] == b'\n':
                    tail += 1
                edits.append((line_start, tail, b''))
                dropped += 1
            else:
                s, e = node_span(starts, kw['new'])
                edits.append((s, e, wrapped_literal(current, 0).encode('utf-8')))
                updated += 1

        if edits:
            for s, e, text in sorted(edits, reverse=True):
                src = src[:s] + text + src[e:]
            compile(src, path, 'exec')            # падаем сразу, а не в тестах
            results[path] = src.decode('utf-8')

    print('  переписано new=: %d' % updated)
    print('  снято записей (поле удалено): %d' % dropped)
    print('  затронуто файлов: %d' % len(results))
    missed = stale - seen
    if missed:
        print('  НЕ НАЙДЕНО в исходниках: %s' % sorted(missed))

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    for path, src in results.items():
        open(path, 'w', encoding='utf-8').write(src)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
