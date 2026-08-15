# -*- coding: utf-8 -*-
"""Откат собственной ошибки: прямые кавычки ВТОРОГО уровня — не дефект.

`fix_typography_across_base.py` менял прямые кавычки на ёлочки по всей базе
и в 38 полях испортил то, что было верно: `ООО «Группа "Полипластик"»`
превратилось в `ООО «Группа «Полипластик»»`, а цитата `«"Авиапарк" — один
из немногих…»` — в `««Авиапарк» — один из немногих…»`.

Это прямо описано в CLAUDE.md: «вложенные кавычки второго уровня — это не
дефект (там внутренняя кавычка ПРЯМАЯ и баланс уже верный)». Правило
конвертации было написано для кавычек ПЕРВОГО уровня и не спрашивало, где
именно оно срабатывает, — тот же класс, что уже записанный урок «Запрет,
написанный для головы словосочетания, нельзя проверять на всей фразе»:
спрашивать надо не только «что менять», но и «ГДЕ это менять».

ЧТО ДЕЛАЕТ СКРИПТ. Берёт значение поля до прогона типографики (из git HEAD),
прогоняет по нему ИСПРАВЛЕННОЕ правило — которое считает глубину ёлочек и
внутрь `«…»` не лезет, — и записывает результат. Прочие правки того же
прогона (десятичная запятая, закрытие висячей ёлочки) применяются к нему
же, чтобы ничего не потерялось.

Затрагиваются только поля, где ошибка реально произошла: те, в которых
появились `««` или `»»`, которых не было до прогона.

Запуск:
    python3 pipeline/fix_nested_quote_overreach.py            # сухой прогон
    python3 pipeline/fix_nested_quote_overreach.py --write    # запись
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

NAME_IN_QUOTES = re.compile(r'"([^"\s](?:[^"]*[^"\s,;:\-–—])?)"')
DECIMAL_DOT = re.compile(r'(?<![\d.,\w])(\d+)\.(\d+)(?=\s*(?:млн|млрд|тыс|%|т\b|га\b|кв\b))')


def fix_quotes_first_level_only(text):
    """Прямые кавычки -> ёлочки ТОЛЬКО вне уже открытой ёлочки.

    Глубина считается по ходу строки: пока открыта «, внутренние прямые
    кавычки — законный второй уровень, их не трогаем."""
    out, depth, i = [], 0, 0
    while i < len(text):
        ch = text[i]
        if ch == '«':
            depth += 1
            out.append(ch)
            i += 1
            continue
        if ch == '»':
            depth = max(0, depth - 1)
            out.append(ch)
            i += 1
            continue
        if ch == '"' and depth == 0:
            m = NAME_IN_QUOTES.match(text, i)
            if m and '. ' not in m.group(1):
                out.append('«%s»' % m.group(1))
                i = m.end()
                continue
        out.append(ch)
        i += 1
    return ''.join(out)


def fix_decimals(text):
    return DECIMAL_DOT.sub(lambda m: '%s,%s' % (m.group(1), m.group(2)), text)


def close_guillemets(text):
    gap = text.count('«') - text.count('»')
    return text + '»' * gap if gap > 0 else text


def _self_check():
    # первый уровень — меняется
    assert fix_quotes_first_level_only('ООО "Кама" купило') == 'ООО «Кама» купило'
    # второй уровень внутри ёлочек — НЕ меняется
    assert fix_quotes_first_level_only('ООО «Группа "Полипластик"» создано') == \
        'ООО «Группа "Полипластик"» создано'
    assert fix_quotes_first_level_only('«"Авиапарк" — трофейный актив»') == \
        '«"Авиапарк" — трофейный актив»'
    # смешанный случай: снаружи меняем, внутри нет
    assert fix_quotes_first_level_only('"Первый" и ООО «ХК "Второй"» вместе') == \
        '«Первый» и ООО «ХК "Второй"» вместе'


def head_version():
    raw = subprocess.run(['git', 'show', 'HEAD:static/data/deals_promoted.json'],
                         capture_output=True, text=True, cwd=ROOT).stdout
    return {d['id']: d for d in json.loads(raw)['deals']}


def text_fields(deal):
    out = []
    if isinstance(deal.get('extra'), str):
        out.append(('extra', None, deal['extra']))
    for group in ('eco', 'law'):
        for key, value in (deal.get(group) or {}).items():
            if isinstance(value, str):
                out.append((group, key, value))
    return out


def main(argv):
    _self_check()
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    old = head_version()

    todo = []
    for cid, deal in by_id.items():
        if cid not in old:
            continue
        was = {(g, k): v for g, k, v in text_fields(old[cid])}
        for group, key, current in text_fields(deal):
            before = was.get((group, key))
            if before is None:
                continue
            if ('««' in current and '««' not in before) or \
               ('»»' in current and '»»' not in before):
                fixed = close_guillemets(fix_decimals(fix_quotes_first_level_only(before)))
                if fixed != current:
                    todo.append((cid, group, key, current, fixed))

    print('Полей с испорченной вложенной кавычкой: %d (у %d карточек)'
          % (len(todo), len({t[0] for t in todo})))
    for cid, group, key, cur, fixed in todo[:6]:
        name = group if key is None else '%s.%s' % (group, key)
        print('  %s %s' % (cid, name))
        print('    стало было: %s' % cur[:88])
        print('    станет    : %s' % fixed[:88])

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    for cid, group, key, _cur, fixed in todo:
        if key is None:
            by_id[cid]['extra'] = fixed
        else:
            by_id[cid][group][key] = fixed

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('ЗАПИСАНО: %d полей.' % len(todo))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
