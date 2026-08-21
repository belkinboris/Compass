# -*- coding: utf-8 -*-
"""«Интеррос»/Росбанк/Societe Generale (`ge32bd008`): месячный дообыск
нашёл два крупных, поздних факта — обещанная «Интерросом» преемственность
управленческой команды во главе с Ильёй Поляковым (уже зафиксирована в
`law.terms`) продержалась только 5 месяцев (ушёл в октябре 2022, с
1 ноября 2022 банк возглавила Наталья Воеводина), а сам Росбанк 1 января
2025 года перестал существовать как отдельный банк — присоединился к
Т-Банку. Оба факта из ДВУХ разных источников (interfax.ru/business/901558
и ria.ru/20250101/banki-1992228779.html), а `eco.context` уже занято
одним предложением из третьего источника (SocGen) — дословно объединить
в одну цитату для `review.py` нельзя, поэтому три факта из трёх
источников сшиваются одним разовым скриптом, тем же приёмом, что и
`fix_mvideo_control_denial_field.py`/`fix_atom_valuation_field.py` в
этом же прогоне.

Запуск: python3 pipeline/fix_rosbank_followup_context.py           # проверка
        python3 pipeline/fix_rosbank_followup_context.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'ge32bd008'
OLD_CONTEXT = (
    'Как сообщила в начале мая SocGen, российский бизнес в первом '
    'квартале 2022 года принес группе убыток в размере 113 млн евро.')
NEW_CONTEXT = OLD_CONTEXT + (
    ' Обещанная преемственность управленческой команды не удержалась: '
    'в октябре 2022 года Илья Поляков, проработав в банке 10 лет, '
    'покинул пост председателя правления, а с 1 ноября 2022 года '
    'Росбанк возглавила Наталья Воеводина. Сам Росбанк не сохранился '
    'как отдельный банк — 1 января 2025 года он завершил присоединение '
    'к Т-Банку в качестве филиала.')


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card['eco'].get('context') == OLD_CONTEXT, (
        'eco.context изменился с ожидаемого: %r' % card['eco'].get('context'))
    src = card.setdefault('src', [])
    new_srcs = [
        ['Интерфакс', 'https://www.interfax.ru/business/901558'],
        ['РИА Новости', 'https://ria.ru/20250101/banki-1992228779.html'],
    ]
    to_add = [s for s in new_srcs if s not in src]
    print('ПРАВИМ  %s: eco.context — уход Полякова и присоединение к Т-Банку' % CARD_ID)
    print('ДОБАВИМ %s: %d новых источника в src' % (CARD_ID, len(to_add)))
    if write:
        card['eco']['context'] = NEW_CONTEXT
        src.extend(to_add)
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
