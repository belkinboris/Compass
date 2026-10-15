# -*- coding: utf-8 -*-
"""Карточка g62577a1d («Карат»/Павловский молочный завод): enrich.py на
прогоне 17:20 нашёл TAdviser как новый источник и предложил три правки —
src (новый источник), sum (2 млрд ₽, поле было пусто) и event (второй
«closed» этап, дата 2026-10-15). Первые две — настоящая находка, беру.
Третью не беру: `events[0]` уже держит закрытие (РБК, 2026-10-14) — тот
же этап, другая дата из-за даты публикации TAdviser, а не второго
закрытия; добавление создало бы дубль «Сделка завершена» в ленте
карточки. К тому же текст предложенной заметки — служебная вики-
разметка TAdviser («это Россия предприятие пищевая промышленность») —
тот же класс, что `tadviser_markup` в `accept_card.findings()`.

Заодно пишет `eco.sum` тем же значением, что и `sum` — тот же пробел,
что чинили сегодня у g0158e326/g253252c4/gbe13372d
(`test_the_sum_on_the_overview_is_the_sum_in_the_economist`).

Запуск:
    python3 pipeline/fix_g62577a1d_enrich_sum_skip_bad_event_2026_10_15.py            # сухой прогон
    python3 pipeline/fix_g62577a1d_enrich_sum_skip_bad_event_2026_10_15.py --write    # применить
"""
import json
import sys

DATA = '/home/user/Compass/static/data/deals_promoted.json'
CARD_ID = 'g62577a1d'
NEW_SRC = ['TAdviser', 'https://www.tadviser.ru/a/967457']
NEW_SUM = '2 млрд ₽'


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    assert card.get('sum') is None, 'sum уже не пуст: %r' % card.get('sum')
    assert card['eco']['sum'] == '—', 'eco.sum уже не прочерк: %r' % card['eco']['sum']
    assert NEW_SRC not in (card.get('src') or []), 'источник уже стоит'
    print('sum <- %r' % NEW_SUM)
    print('eco.sum <- %r' % NEW_SUM)
    print('src += %r' % NEW_SRC)
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(DATA, encoding='utf-8'))
    fresh_card = next(d for d in fresh['deals'] if d['id'] == CARD_ID)
    assert fresh_card.get('sum') is None, 'sum поменяли параллельно — перечитайте'
    assert fresh_card['eco']['sum'] == '—', 'eco.sum поменяли параллельно — перечитайте'
    fresh_card['sum'] = NEW_SUM
    fresh_card['eco']['sum'] = NEW_SUM
    fresh_card.setdefault('src', []).append(NEW_SRC)
    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
