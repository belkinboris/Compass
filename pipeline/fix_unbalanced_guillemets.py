# -*- coding: utf-8 -*-
"""Каталог вычитки, класс C2: несбалансированные «» — 18 полей (подмножество
«лишняя открывающая», найдены прошлым кругом; 61 поле «лишняя закрывающая»
из того же замера НЕ трогается — по прецеденту CLAUDE.md такие не
восстанавливаются, начало фразы потеряно безвозвратно).

ДВЕ ПРИЧИНЫ, РАЗНЫЙ РЕЦЕПТ.

1. ВЛОЖЕННОЕ НАЗВАНИЕ ЗАКРЫТО ОДИН РАЗ ВМЕСТО ДВУХ — уже задокументированный
   в CLAUDE.md паттерн («Санаторий «Россиянка»» → без второй » текст читается
   как «Санаторий «Россиянка» купил...», хотя открыто дважды: родовое слово
   («Издательство», «Группа компаний», «СК», «ГК», «ТД», «ТК», «СПП», «СФО»)
   плюс вложенное имя. Механическая правка: `«X«Y»` без второй » сразу после
   → `«X«Y»»`. 14 полей, 16 срабатываний (у g8b512496 и ge9b4ba4d — по два
   вложенных имени в одном поле). Правило проверено на себе: НЕ трогает уже
   корректно закрытые вложенные имена и НЕ трогает независимые пары («Россети
   Урал» ... «Форвард энерго» — два разных названия подряд, не вложенность).

2. ЧЕТЫРЕ ОТДЕЛЬНЫХ СЛУЧАЯ, каждый — свой дефект, чинится точечно:
   * gdab53817 (eco.rationale) — цитата гендиректора занимает весь остаток
     поля и не закрывается вовсе; закрывающая » ставится в конце поля, без
     дополнительной точки снаружи (по образцу уже сбалансированных полей той
     же формы в базе — «...руб.»» без точки после, когда цитата и есть конец
     поля: g3ef24264, gcdd2b6de, g334b5760).
   * g8e9d37ba (eco.val) — та же болезнь, что и у g71aec6a5 из класса C1:
     закрывающая » набрана ASCII-кавычкой (") вместо ёлочки. Заменяется одна
     конкретная подстрока.
   * gc10da566 (law.struct) — «Деметра -Холдинг) без закрывающей » и с лишним
     пробелом перед дефисом; правильное написание («Деметра-Холдинг», без
     пробела) подтверждено 9 другими карточками той же компании в этой же
     базе (g42e11ded, ga7232033, g38ce6e22 и др.) — это не новый факт, а
     приведение к уже установленному в базе написанию.
   * g3bebdacf (eco.share) — «Фортум) без закрывающей » перед скобкой.

Запуск:
    python3 pipeline/fix_unbalanced_guillemets.py            # сухой прогон
    python3 pipeline/fix_unbalanced_guillemets.py --write    # запись
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

ECO_FIELDS = ('rationale', 'context', 'share', 'val', 'target_fin', 'fin', 'sum', 'finadv')
LAW_FIELDS = ('struct', 'appr', 'terms')

NESTED = re.compile(r'«([^«»]*)«([^«»]*)»(?!»)')

NESTED_NAME_FIELDS = {
    ('gf9932079', 'eco.target_fin'),
    ('g5dc6cb47', 'law.struct'),
    ('gafc80ee1', 'eco.context'),
    ('gd3ba954d', 'eco.target_fin'),
    ('gc215d8b0', 'eco.context'),
    ('g6520943f', 'law.terms'),
    ('g97d9fa60', 'law.appr'),
    ('g9a575c07', 'eco.context'),
    ('g97f0244e', 'eco.rationale'),
    ('c6b5fb9f3', 'law.struct'),
    ('cacdb5edc', 'eco.target_fin'),
    ('g8e9d37ba', 'eco.context'),
    ('g8b512496', 'law.struct'),
    ('ge9b4ba4d', 'eco.rationale'),
}

SPECIAL = [
    ('gdab53817', 'eco.rationale',
     'достиг 14,5 трлн рублей.',
     'достиг 14,5 трлн рублей.»'),
    ('g8e9d37ba', 'eco.val',
     'дойти до 30%", - заявила Яруллина.',
     'дойти до 30%», - заявила Яруллина.'),
    ('gc10da566', 'law.struct',
     '(входит в состав «Деметра -Холдинг) приобрела',
     '(входит в состав «Деметра-Холдинг») приобрела'),
    ('g3bebdacf', 'eco.share',
     'назывался ПАО «Фортум).',
     'назывался ПАО «Фортум»).'),
]


def fix_nested(text):
    return NESTED.sub(r'«\1«\2»»', text)


def _self_check():
    assert fix_nested(
        'Выручка АО «Издательство «Просвещение» по РСБУ в 2024 году составила 51,1 млрд руб.'
    ) == 'Выручка АО «Издательство «Просвещение»» по РСБУ в 2024 году составила 51,1 млрд руб.'

    assert fix_nested(
        '(АО «ТД «Усачевский», ООО «ТК «Южный», «Киселевский рынок» и проч.)'
    ) == '(АО «ТД «Усачевский»», ООО «ТК «Южный»», «Киселевский рынок» и проч.)'

    # два вложенных имени в одном поле — оба чинятся, независимая пара нет
    assert fix_nested(
        'Владелец ООО «Сельскохозяйственное производственное предприятие «Юг» '
        '— компания «Объединенный капитал», собственником которой является '
        'Сергей Галицкий. Руководителем ООО «СПП «Юг» числится Владимир '
        'Хашиг, он же является гендиректором ФК «Краснодар».'
    ) == (
        'Владелец ООО «Сельскохозяйственное производственное предприятие «Юг»» '
        '— компания «Объединенный капитал», собственником которой является '
        'Сергей Галицкий. Руководителем ООО «СПП «Юг»» числится Владимир '
        'Хашиг, он же является гендиректором ФК «Краснодар».'
    )

    # независимые пары названий подряд — не трогать
    unchanged = 'Компания «Россети Урал» выкупила комплекс у ПАО «Форвард энерго».'
    assert fix_nested(unchanged) == unchanged

    # уже корректно дважды закрытое — не трогать (не добавлять третью »)
    already = 'Санаторий «Россиянка»» продан инвестору.'
    assert fix_nested(already) == already


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
    by_id = {d['id']: d for d in data['deals']}

    plan = []
    for deal in data['deals']:
        pairs = [('extra', deal.get('extra'))]
        pairs += [('eco.' + k, (deal.get('eco') or {}).get(k)) for k in ECO_FIELDS]
        pairs += [('law.' + k, (deal.get('law') or {}).get(k)) for k in LAW_FIELDS]
        for field, value in pairs:
            if (deal['id'], field) not in NESTED_NAME_FIELDS:
                continue
            if not isinstance(value, str) or not value:
                continue
            new = fix_nested(value)
            if new != value:
                plan.append((deal, field, value, new))

    for cid, field, old, _new in SPECIAL:
        current = get_field(by_id[cid], field)
        assert old in current, '%s.%s: подстрока уже другая, ожидали %r' % (cid, field, old[:50])

    print('Вложенных названий (regex): %d полей' % len(plan))
    for deal, field, old, new in plan:
        print('  %s %-16s %r -> %r' % (deal['id'], field, old[:36], new[:40]))
    print('Точечных правок: %d' % len(SPECIAL))
    for cid, field, old, new in SPECIAL:
        print('  %s %-16s %r -> %r' % (cid, field, old, new))

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    for deal, field, _old, new in plan:
        set_field(deal, field, new)
    for cid, field, old, new in SPECIAL:
        current = get_field(by_id[cid], field)
        set_field(by_id[cid], field, current.replace(old, new))

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
