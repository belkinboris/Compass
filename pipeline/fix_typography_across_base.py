# -*- coding: utf-8 -*-
"""Типографика и пунктуация по всей базе: четыре класса, найденные вычиткой.

НАЙДЕНО вычиткой 15 случайных карточек 15 августа 2026 (просьба владельца:
«вычитай на русский язык, на грамматику»). В каждом классе сначала замер по
всей базе, потом правка — и только там, где правка ничего не сочиняет.

1. ПРЯМЫЕ КАВЫЧКИ ВМЕСТО ЁЛОЧЕК. `ООО "Траст Птицеводческий холдинг"`,
   `ООО "Юг-бизнеспартнер"` — 938 пар по базе. Меняются ТОЛЬКО те, что
   похожи на название: содержимое без переносов, не начинается и не
   заканчивается пробелом или знаком препинания. Остальные 135 —
   обрывки цитат из новостей (`", - сказал "`, `"будут использованы для
   финансовых и коммерческих целей "`) и следы разъехавшихся вложенных
   кавычек (`"УК "`, `"Научно-производственное объединение "`) — их
   механически чинить нельзя, там потерян не символ, а структура.

2. ТОЧКА ВМЕСТО ЗАПЯТОЙ В ЧИСЛЕ. `14.8 млн т`, `3.6 млрд`, `47.9%` — в
   русском тексте десятичный разделитель запятая. Правится только там, где
   за числом стоит единица измерения (млн/млрд/тыс/%/т/га/кв), — иначе под
   правило попали бы номера версий и адреса.

3. НЕЗАКРЫТАЯ СКОБКА В `law.adv`. `«юридическое сопровождение сделки на
   стороне покупателя (Группа «Черкизово»` — 32 ячейки, у всех строка
   обрывается на середине: при импорте её обрезали по длине. Закрываем то,
   что уже написано, — ровно тот же приём и та же граница, что у уже
   принятой правки вложенных кавычек (CLAUDE.md, «Вложенное название
   закрывается два раза, если открыто два раза»): дописать НЕДОСТАЮЩИЙ
   ЗНАК ПРЕПИНАНИЯ можно, дописать потерянный текст — нельзя.

4. НЕЗАКРЫТАЯ ЁЛОЧКА В ТЕКСТОВОМ ПОЛЕ. Тот же дефект, что 3, но в прозе:
   открывающих «больше, чем закрывающих». Закрывается только этот
   перекос; обратный (закрывающих больше — потеряно НАЧАЛО фразы) не
   трогается, там дописывать нечего.

Запуск:
    python3 pipeline/fix_typography_across_base.py            # сухой прогон
    python3 pipeline/fix_typography_across_base.py --write    # запись
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

ECO_FIELDS = ('rationale', 'context', 'share', 'val', 'target_fin', 'fin', 'sum', 'finadv')
LAW_FIELDS = ('struct', 'appr', 'terms')

# Пара прямых кавычек, содержимое которой похоже на НАЗВАНИЕ, а не на кусок
# фразы: не пусто, не начинается/не заканчивается пробелом, не заканчивается
# знаком препинания, внутри нет разрыва предложения.
NAME_IN_QUOTES = re.compile(r'"([^"\s](?:[^"]*[^"\s,;:\-–—])?)"')

# Десятичная точка перед единицей измерения.
DECIMAL_DOT = re.compile(r'(?<![\d.,\w])(\d+)\.(\d+)(?=\s*(?:млн|млрд|тыс|%|т\b|га\b|кв\b))')


def fix_quotes(text):
    """Прямые кавычки вокруг названия -> ёлочки. Остальные не трогаются."""
    def repl(m):
        inner = m.group(1)
        if '. ' in inner:          # внутри целое предложение — это цитата, не имя
            return m.group(0)
        return '«%s»' % inner
    return NAME_IN_QUOTES.sub(repl, text)


def fix_decimals(text):
    return DECIMAL_DOT.sub(lambda m: '%s,%s' % (m.group(1), m.group(2)), text)


def close_parens(text):
    """Дописать недостающие ')' в конец — только если открывающих больше."""
    gap = text.count('(') - text.count(')')
    return text + ')' * gap if gap > 0 else text


def close_guillemets(text):
    """Дописать недостающие '»' в конец — только если открывающих больше."""
    gap = text.count('«') - text.count('»')
    return text + '»' * gap if gap > 0 else text


def _self_check():
    # кавычки: название меняется, цитата и обрывок — нет
    assert fix_quotes('ООО "Траст Холдинг" купило') == 'ООО «Траст Холдинг» купило'
    assert fix_quotes('газета "Ъ" сообщила') == 'газета «Ъ» сообщила'
    assert fix_quotes('сказал он, "будут использованы для целей "') == \
        'сказал он, "будут использованы для целей "', 'обрывок цитаты трогать нельзя'
    assert fix_quotes('"Первое предложение. Второе"') == '"Первое предложение. Второе"', \
        'цитату из двух предложений трогать нельзя'
    # числа: правится только перед единицей измерения
    assert fix_decimals('запасы 14.8 млн т') == 'запасы 14,8 млн т'
    assert fix_decimals('доля 47.9%') == 'доля 47,9%'
    assert fix_decimals('версия 2.10 программы') == 'версия 2.10 программы', \
        'число без единицы измерения — не сумма'
    # скобки и ёлочки: дописывается только недостающее закрывающее
    assert close_parens('текст (Группа «Х»') == 'текст (Группа «Х»)'
    assert close_parens('текст (полный)') == 'текст (полный)'
    assert close_guillemets('ООО «Датана') == 'ООО «Датана»'
    assert close_guillemets('текст Датана»') == 'текст Датана»', \
        'потерянное НАЧАЛО дописывать нечем'


def main(argv):
    _self_check()
    data = json.load(open(DATA, encoding='utf-8'))

    stats = {'кавычки': 0, 'числа': 0, 'ёлочки': 0, 'скобки в law.adv': 0}
    touched = set()

    for d in data['deals']:
        # --- текстовые поля: кавычки, числа, ёлочки ---
        pairs = [('extra', None)] + [('eco', k) for k in ECO_FIELDS] + \
                [('law', k) for k in LAW_FIELDS]
        for group, key in pairs:
            holder = d if key is None else d.get(group)
            if not isinstance(holder, dict) and key is not None:
                continue
            name = 'extra' if key is None else key
            value = holder.get(name) if key is not None else d.get('extra')
            if not isinstance(value, str) or not value:
                continue
            new = fix_quotes(value)
            if new != value:
                stats['кавычки'] += 1
            step = fix_decimals(new)
            if step != new:
                stats['числа'] += 1
            new = step
            step = close_guillemets(new)
            if step != new:
                stats['ёлочки'] += 1
            new = step
            if new != value:
                touched.add(d['id'])
                if key is None:
                    d['extra'] = new
                else:
                    holder[name] = new

        # --- law.adv: незакрытые скобки ---
        for row in (d.get('law') or {}).get('adv') or []:
            for i, cell in enumerate(row):
                if isinstance(cell, str) and cell:
                    fixed = close_parens(cell)
                    if fixed != cell:
                        row[i] = fixed
                        stats['скобки в law.adv'] += 1
                        touched.add(d['id'])

    print('Правок по классам:')
    for k, v in stats.items():
        print('  %-18s %d полей' % (k, v))
    print('Затронуто карточек: %d' % len(touched))

    if '--write' not in argv:
        print('\nСухой прогон (изменения в памяти не сохранены). Запись — с ключом --write.')
        return 0

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
