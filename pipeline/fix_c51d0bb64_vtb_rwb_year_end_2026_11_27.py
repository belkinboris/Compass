# -*- coding: utf-8 -*-
"""Карточка `c51d0bb64` (ВТБ собирается купить долю в WB Банке): новый срок.

Приток 27 ноября 2026: Интерфакс, слова первого зампреда ВТБ Дмитрия Пьянова —
допэмиссию и покупку доли в финтех-активах RWB банк постарается завершить до
конца года; открытые вопросы с партнером остаются. Ворота новость с карточкой
не связали («не установлен предмет сделки»), она лежала в сомнительном сырье
(d27761009). Это не этап из `POSTWORTHY_MILESTONE_KINDS` (не одобрение, не
закрытие, не срыв) — отдельный пост не нужен, обычное дополнение ленты сделки.

Почему не через таблицу FIXES: events[] review.py не читает, а eco.context —
добавление к длинному полю, которое check() сверяет с цитатой целиком (тот же
случай, что pipeline/archive/2026-11/c51d0bb64_vtb_wb_subscription_open_2026_11_12.py).
Источник в `src` — записью FIXES (fixes/c51d0bb64_vtb_rwb_year_end_2026_11_27.py).

Источник дочитан по data/inbox/raw/2026-11-27-articles.jsonl:
  Интерфакс  https://www.interfax.ru/business/1131781

Запуск: без ключа — сухой прогон, с --write — запись.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, '..', 'static', 'data', 'deals_promoted.json')

CARD_ID = 'c51d0bb64'
INTERFAX = ['Интерфакс', 'https://www.interfax.ru/business/1131781']
OLD_TAIL = ('ВТБ получил бы около 547 млрд рублей, хотя менеджмент по-прежнему ориентирует '
            'на нижнюю часть диапазона.')
ADDED_CONTEXT = (' 27 ноября 2026 года Пьянов назвал новый срок: и допэмиссию, и покупку доли в '
                 'финтех-активах RWB банк постарается завершить до конца года. По его словам, '
                 'нерешенные вопросы с партнером еще остаются, и ВТБ рассчитывает снять их к '
                 '30 ноября, когда закончится прием заявок от действующих акционеров; итоги этого '
                 'этапа банк обещает назвать через два-три дня. Состав якорных инвесторов, цена и '
                 'ожидаемая сумма размещения не меняются.')
NEW_EVENT = {
    'kind': 'negotiations', 'date': '2026-11-27',
    'title': 'ВТБ рассчитывает закрыть сделку до конца года',
    'note': ('В целом мы будем стараться до конца года завершить и процедуру дополнительной эмиссии, '
             'и приобретение доли в финтех-активах группы RWB.'),
    'source': list(INTERFAX),
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))      # читается прямо перед записью
    card = next((d for d in data['deals'] if d['id'] == CARD_ID), None)
    if card is None:
        sys.exit('ОТКАЗ: карточки %s нет в базе' % CARD_ID)
    ctx = card['eco']['context']
    if ADDED_CONTEXT.strip() in ctx:
        print('%s: уже дописано — делать нечего' % CARD_ID)
        return 0
    assert ctx.endswith(OLD_TAIL), 'конец eco.context изменился: %r' % ctx[-120:]
    assert card['events'][-1]['date'] == '2026-11-12', card['events'][-1]
    print('ПРАВКА %s\n  eco.context : +%r\n  events      : +negotiations 2026-11-27' % (CARD_ID, ADDED_CONTEXT))
    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0
    card['eco']['context'] = ctx + ADDED_CONTEXT
    card['events'].append(NEW_EVENT)
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('\nЗАПИСАНО: static/data/deals_promoted.json')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
