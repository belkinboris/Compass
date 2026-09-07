# -*- coding: utf-8 -*-
"""Приток 7 сентября 2026 (16:23) — карточка g6952efe4 прошла ворота, но
не подходит под продукт по существу, а не по ошибке разбора: «Президент
«ЭР-Телеком холдинга» купил старинную усадьбу в Москве за 553 млн
рублей» (TAdviser, биографическая справка о персоне) — это ЛИЧНАЯ
покупка недвижимости физическим лицом (Андрей Кузяев), не сделка M&A: не
меняется контроль над компанией, нет сторон-юрлиц, нет предмета в виде
бизнеса или пакета акций. CLAUDE.md, раздел «Как владелец решает»:
«Жилая недвижимость — почти всегда мимо... Пропускает — если покупатель
или предмет сам по себе значим» — здесь ни усадьба не названа как
известный объект/памятник, ни сама покупка не структурирована как
сделка с бизнесом; это класс «продажа личного предмета», уже
встречавшийся в решениях владельца.

Снята тем же приёмом (discarded_urls), до отправки в консоль.

Запуск: python3 pipeline/fix_discard_erteleco_president_estate.py [--write]
"""
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE_PATH = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

URL = 'https://www.tadviser.ru/a/70407'
CARD_ID = 'g6952efe4'


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

    print(f'Снята карточка {CARD_ID} (личная покупка недвижимости физлицом, не M&A).')

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
