# -*- coding: utf-8 -*-
"""Тема «Клод», 27 ноября 2026: партнер переслал сообщение РБК «„Циан“ сменил
ключевых акционеров» (компании Дмитрия Крюкова, Дмитрия Демина и Максима
Мельникова продали чуть более 52% голосующих акций; ни у одного покупателя
нет больше 30%).

ПОЧЕМУ ВРУЧНУЮ. Фильтр (triage.py) дал пересказу «Ведомостей» вердикт
not_a_deal: заголовок «РБК: „Циан“ сменил основных акционеров» без глагола
покупки и без сторон. В теле сделка названа прямо, поэтому карточка
собирается вручную — образец pipeline/archive/2026-11/
add_depo_computers_card_2026_11_09.py.

ПОЧЕМУ ОТДЕЛЬНАЯ КАРТОЧКА. В базе три карточки о «Циане» этого месяца:
g9b4c2e71 (предложение «Т-Технологий» всем акционерам), g4290fc7a (слух об
Альфа-банке), gd1bf6d5e (Леван Назаров, около 20%). Здесь другой предмет
(52%), названы продавцы, покупателей несколько и они не названы — это не
этап ни одной из трех, карточки связаны через related_deal_ids.

ИСТОЧНИКИ. Полный текст РБК закрыт подпиской: на диске — открытая часть и
сообщение издания в его канале (save_source.py), плюс пересказ «Ведомостей»
(data/inbox/raw). Других изданий с новыми фактами на 00:40 МСК 27 ноября
поиск не нашел.

Собрано в pending.json: дальше обычный путь accept_card.py ->
second_reading.py -> ship_card.py.

Запуск: python3 pipeline/add_cian_core_holders_exit_card_2026_11_27.py [--write]
"""
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
INGEST = os.path.join(HERE, 'ingest')
if INGEST not in sys.path:
    sys.path.insert(0, INGEST)

RBC = ('РБК', 'https://www.rbc.ru/business/27/11/2026/6b0879f6d31da4b02bb5fea9')
VED = ('Ведомости', 'https://www.vedomosti.ru/investments/news/2026/11/27/1415827-tsian-smenil-aktsionerov')

# id — константой после первого сухого запуска (docs/intake_gates.md,
# «id ручной сборки — константой»).
DEAL_ID = 'g1a8709ea'


def main(write):
    import promote

    pending = promote.load_pending()          # читается прямо перед записью
    base = json.load(open(promote.DATA, encoding='utf-8'))
    existing_ids = {c['id'] for c in pending['cards']} | {c['id'] for c in base['deals']}
    for c in pending['cards'] + base['deals']:
        assert RBC[1] not in json.dumps(c.get('src', [])), 'статья уже привязана к %s' % c['id']
    new_id = DEAL_ID if DEAL_ID and DEAL_ID not in existing_ids else promote.new_id(existing_ids)

    draft = {
        'date': '2026-11-27',
        'title': 'Основные акционеры «Циана» продали 52% акций компании',
        'ind': 'ИТ и интернет',
        'type': 'M&A',
        'status': 'Закрыта',
        'seller': 'Основные акционеры «Циана»',
        'asset': '52% голосующих акций МКПАО «Циан»',
        'src': [RBC, VED],
        'events': [
            {'kind': 'closed', 'date': '2026-11-27',
             'title': 'Основные акционеры «Циана» продали свои пакеты',
             'note': 'По данным пяти собеседников РБК, компании Дмитрия Крюкова, Дмитрия '
                     'Демина и Максима Мельникова продали чуть более 52% голосующих акций.',
             'source': list(RBC)},
        ],
    }
    card = promote.to_card(draft, new_id)
    card['events'] = draft['events']
    card['target'] = 'g163cfc8b'
    card['date_basis'] = 'publication'
    card['related_deal_ids'] = ['gd1bf6d5e', 'g9b4c2e71', 'g4290fc7a']
    card['eco']['sum'] = 'Не раскрыта'
    card['eco']['share'] = 'Чуть более 52% голосующих акций МКПАО «Циан».'
    card['law']['struct'] = (
        'По данным пяти собеседников РБК, компании Дмитрия Крюкова, Дмитрия Демина и Максима '
        'Мельникова продали свои акции «Циана» — вместе чуть более 52% голосующих акций. '
        'Продавали не напрямую покупателям. Двое собеседников издания уточняют, что ни у одного '
        'из покупателей не набралось больше 30%: с таким пакетом новый владелец по закону обязан '
        'предложить остальным акционерам выкупить их акции. Кто купил акции и по какой цене, '
        'издание не сообщает.'
    )
    card['eco']['context'] = (
        'За два дня до этого «Коммерсантъ» сообщил, что крупный пакет «Циана», около 20%, собрал '
        'предприниматель Леван Назаров — через ООО «Технологии недвижимости».\n\n'
        'Одновременно действует добровольное предложение «Т-Технологий»: 24 ноября группа '
        'направила «Циану» предложение купить все 77 670 490 акций по 993,05 ₽ за штуку, то есть '
        'за 77,13 млрд ₽ за всю компанию. Продать по нему бумаги акционеры могут до конца февраля '
        '2027 года.'
    )
    card['pending_since'] = datetime.now(timezone.utc).isoformat(timespec='seconds')

    pending['cards'].append(card)
    print('Добавлена карточка %s в pending.json: %s' % (new_id, card['title']))
    if write:
        promote.save_pending(pending)
        print('Записано.')
    else:
        print('(сухой прогон, для записи — --write)')


if __name__ == '__main__':
    main('--write' in sys.argv)
