# -*- coding: utf-8 -*-
"""Карточка g88b148ea («Бадаевский центр» купила у Capital Group офисный
блок в «Бадаевском») получила в приемке профиль покупателя (`buyer`:
`gd5c19b39`, имя профиля то же — «Бадаевский центр»), и по конвенции
«имя берется из профиля» поле `buyer_name` сброшено в `None`. Это смена
формы (имя не изменилось, просто перестало быть отдельным текстовым
полем), но fact_edit_guard не прощает такую смену для `buyer_name` (только
для самого `buyer` — см. `_party_name`/`PARTY_FIELDS` в
`pipeline/fact_edit_guard.py`), поэтому `prepush_check.py` отказал пушить:
«правка факта без подтверждающей цитаты у 1 поля (g88b148ea buyer_name)».

Единственный источник самого имени — репост в Telegram-канале @dealsma
(застройщик в официальном пресс-релизе покупателя не называет; это уже
записано в `party_evidence.buyer` карточки с тем же url). Этот скрипт
дописывает недостающую запись в `card['fact_log']` — значение поля уже
стоит верно (`None`), меняется только подтверждение.

Запуск: python3 pipeline/fact_log_g88b148ea_2026_11_24.py --write
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import fact_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
CARD_ID = 'g88b148ea'
URL = 'https://t.me/dealsma/7514'
BY = 'приток, 24 ноября 2026'
QUOTE = ('Имя покупателя «Бадаевский центр» — только из репоста Telegram-канала @dealsma; '
         'застройщик покупателя в своем пресс-релизе не называет. Заведен профиль того же имени '
         '(gd5c19b39) — текстовое поле buyer_name больше не нужно, имя теперь берется из профиля.')


def apply(data):
    card = next(c for c in data['deals'] if c['id'] == CARD_ID)
    assert card.get('buyer') == 'gd5c19b39', 'buyer: ожидали gd5c19b39, стоит %r' % card.get('buyer')
    assert card.get('buyer_name') is None, 'buyer_name: ожидали None, стоит %r' % card.get('buyer_name')
    fact_edit_guard.log(card, 'buyer_name', None, QUOTE, URL, BY)


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    apply(data)
    print('подтверждение добавлено: buyer_name')
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    data = json.load(open(DATA, encoding='utf-8'))
    apply(data)
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main('--write' in sys.argv[1:]))
