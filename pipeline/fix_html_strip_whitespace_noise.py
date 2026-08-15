# -*- coding: utf-8 -*-
"""Каталог вычитки, класс E4: пробел на месте вырезанного HTML-тега.

Найдено чтением у g57a44f07 (круг 4): «...инженеры , высокий уровень...
«« Газпром нефть »»» — при разборе источника со ссылками внутри текста
(имя, обёрнутое в <a href="...">) удаление тега оставляет пробел на его
месте: «текст <a href="...">Слово</a> , ещё» -> «текст Слово , ещё».
Сплошной прогон нашёл тот же дефект в шести формах: перед запятой, перед
точкой, сразу внутри « » и сразу внутри ( ) — источник один и тот же,
разница только в том, какой знак препинания или скобка была рядом со
снятой ссылкой.

Правило анкерит букву/цифру/закрывающую скобку ПЕРЕД одиночным пробелом
и знаком препинания сразу после — тройное многоточие, нормальные
сокращения («т. д.», где пробел ПОСЛЕ точки, а не перед) и десятичные
дроби («12,5» пишутся без пробела в этой базе) под правило не попадают.

Запуск:
    python3 pipeline/fix_html_strip_whitespace_noise.py            # сухой прогон
    python3 pipeline/fix_html_strip_whitespace_noise.py --write    # запись
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

ECO_FIELDS = ('rationale', 'context', 'share', 'val', 'target_fin', 'fin', 'sum', 'finadv')
LAW_FIELDS = ('struct', 'appr', 'terms')

RULES = [
    (re.compile(r'([а-яёА-ЯЁa-zA-Z0-9)»%]) ,'), r'\1,'),
    # Не трогать «домене .RU»: точка перед доменной зоной/сокращением —
    # не конец предложения, если сразу после неё буква или цифра.
    (re.compile(r'([а-яёА-ЯЁa-zA-Z0-9)»%]) \.(?![а-яёА-ЯЁa-zA-Z0-9.])'), r'\1.'),
    (re.compile(r'« ([а-яёА-ЯЁa-zA-Z])'), r'«\1'),
    (re.compile(r'([а-яёА-ЯЁa-zA-Z0-9]) »'), r'\1»'),
    (re.compile(r'\( ([а-яёА-ЯЁa-zA-Z.])'), r'(\1'),
    (re.compile(r'([а-яёА-ЯЁa-zA-Z0-9]) \)'), r'\1)'),
]


def fix_field(text):
    for pat, repl in RULES:
        text = pat.sub(repl, text)
    return text


def _self_check():
    assert fix_field('инженеры , высокий уровень') == 'инженеры, высокий уровень'
    assert fix_field('Полина Яковлевна Шарова .') == 'Полина Яковлевна Шарова.'
    assert fix_field('Оператор « Вымпелком », который') == 'Оператор «Вымпелком», который'
    assert fix_field('собеседник « Ведомостей ».') == 'собеседник «Ведомостей».'
    assert fix_field('акционеров ( Организаторы ) по') == 'акционеров (Организаторы) по'
    assert fix_field('«Ъ» от 7 июня 2022 года ).') == '«Ъ» от 7 июня 2022 года).'
    # не трогать: сокращение с пробелом ПОСЛЕ точки, троеточие, нормальный текст
    unchanged = 'и т. д. по всем пунктам... готово.'
    assert fix_field(unchanged) == unchanged
    unchanged2 = 'ставка 12,5% годовых (пример)'
    assert fix_field(unchanged2) == unchanged2
    # не трогать: точка перед доменной зоной — не конец предложения
    unchanged3 = 'рынка хостинга в домене .RU, количество клиентов'
    assert fix_field(unchanged3) == unchanged3
    # скобка вокруг расширения файла — обе стороны чинятся одинаково
    assert fix_field('В пресс-релизе ( .pdf ) дополняется') == \
        'В пресс-релизе (.pdf) дополняется'


def get_field(card, path):
    obj = card
    for part in path.split('.'):
        if not isinstance(obj, dict):
            return None
        obj = obj.get(part)
    return obj


def set_field(card, path, value):
    parts = path.split('.')
    obj = card
    for part in parts[:-1]:
        obj = obj.setdefault(part, {})
    obj[parts[-1]] = value


def main(argv):
    _self_check()
    data = json.load(open(DATA, encoding='utf-8'))

    plan = []
    for deal in data['deals']:
        pairs = [('extra', deal.get('extra'))]
        pairs += [('eco.' + k, (deal.get('eco') or {}).get(k)) for k in ECO_FIELDS]
        pairs += [('law.' + k, (deal.get('law') or {}).get(k)) for k in LAW_FIELDS]
        for field, value in pairs:
            if not isinstance(value, str) or not value:
                continue
            new = fix_field(value)
            if new != value:
                plan.append((deal, field, value, new))

    print('Полей с пробелом на месте вырезанного тега: %d' % len(plan))
    for deal, field, old, new in plan[:12]:
        print('  %s %-13s %r -> %r' % (deal['id'], field, old[:44], new[:44]))

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    for deal, field, _old, new in plan:
        set_field(deal, field, new)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
