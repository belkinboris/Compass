# -*- coding: utf-8 -*-
"""Почасовой приток 5 сентября 2026 (12:20) — ложная карточка «Новгородское
хозяйство вложило более 23 миллионов рублей в модернизацию» прошла ворота:
предмет "модернизация" и покупатель "Новгородское хозяйство" — оба не
имена, а вырезанные из заголовка общие слова. Полный текст (СПК «Колхоз
«Россия»» в Солецком округе реконструирует помещение для молодняка и
модернизирует зерносушильню) подтверждает: это капитальные вложения
предприятия в СОБСТВЕННУЮ инфраструктуру, а не сделка M&A — ни продавца,
ни покупателя другой компании тут нет в принципе. Снимается тем же
способом, что и предыдущие ложные карточки в этом окне (discarded_urls),
чтобы адрес не разобрался заново под новым id.

Запуск: python3 pipeline/fix_discard_novgorod_modernization_capex.py [--write]
"""
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE_PATH = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

URL = ('https://abnews.ru/szfo/news/velikiy-novgorod/2026/9/5/'
       'novgorodskoe-hozyajstvo-vlozhilo-bolee-23-millionov-rublej-v-modernizacziyu')
CARD_ID = 'g99659d10'


def main(write=False):
    with open(PENDING_PATH, encoding='utf-8') as f:
        pending = json.load(f)
    with open(STATE_PATH, encoding='utf-8') as f:
        state = json.load(f)

    matches = [c for c in pending['cards'] if c['id'] == CARD_ID]
    assert len(matches) == 1, f'ожидалась ровно одна карточка {CARD_ID}, найдено {len(matches)}'
    card = matches[0]
    assert any(len(s) > 1 and s[1] == URL for s in (card.get('src') or []))
    assert URL not in state.get('discarded_urls', {})

    pending['cards'] = [c for c in pending['cards'] if c['id'] != CARD_ID]
    state.setdefault('discarded_urls', {})[URL] = {
        'id': CARD_ID, 'title': card.get('title'),
        'at': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
    }

    print(f'Снята карточка {CARD_ID} (капвложения в собственную инфраструктуру, не M&A).')

    if write:
        with open(PENDING_PATH, 'w', encoding='utf-8') as f:
            json.dump(pending, f, ensure_ascii=False, indent=1)
            f.write('\n')
        with open(STATE_PATH, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('(сухой прогон, для записи — --write)')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
