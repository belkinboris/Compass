# -*- coding: utf-8 -*-
"""Новая карточка: «Робинзон Логистикс» Вячеслава Шикулова (уже владевшая
70% ООО «Чемодан Про» — бывшего российского юрлица Samsonite) выкупила
оставшиеся 30% у партнера Андрея Языкова и стала единственным владельцем.
Консолидация миноритарного пакета, не первая сделка с этим активом (первая —
переход бизнеса от Samsonite топ-менеджерам в 2022 году, за рамками этой
карточки: о ней нет отдельного официального раскрытия цены, и она не
становится отдельной карточкой — упомянута как история в eco.context).

Источники (прочитаны полностью):
  Коммерсантъ  https://www.kommersant.ru/doc/9025097 (доступен не из этой сессии —
               цитаты даны саб-агентом, независимо нашедшим и прочитавшим статью;
               дословные куски не переносятся без собственного кэша, прозу пишем
               по смыслу, не копируя)
  RETAILER.ru  https://retailer.ru/byvshij-biznes-samsonite-smenil-vladelca-v-rossii/
               (кэш — data/inbox/raw/2026-10-13-articles.jsonl)

Запуск:
    python3 build_chemodan_pro_2026_10_13.py            # сухой прогон
    python3 build_chemodan_pro_2026_10_13.py --write    # применить
"""
import json
import os
import sys
from datetime import datetime, timezone

ROOT = '/home/user/Compass'
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import promote  # noqa: E402

PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

CARD_ID = 'g83ad1f72'
SRC_KOMMERSANT = ['Коммерсантъ', 'https://www.kommersant.ru/doc/9025097']
SRC_RETAILER = ['RETAILER.ru', 'https://retailer.ru/byvshij-biznes-samsonite-smenil-vladelca-v-rossii/']

DRAFT = {
    'id': CARD_ID,
    'date': '2026-10-13',
    'title': 'Шикулов выкупил остаток «Чемодан Про» — бывшего российского бизнеса Samsonite',
    'ind': 'Розничная торговля',
    'type': 'M&A',
    'status': 'Закрыта',
    'src': [SRC_KOMMERSANT, SRC_RETAILER],
    'buyer_name': '«Робинзон Логистикс» (Вячеслав Шикулов)',
    'seller': 'Андрей Языков',
    'asset': '30% ООО «Чемодан Про»',
}


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    if any(c['id'] == CARD_ID for c in data['cards']):
        print('ОТКАЗ: карточка %s уже есть' % CARD_ID)
        return 1

    card = promote.to_card(DRAFT, CARD_ID)
    card['eco']['share'] = (
        '«Робинзон Логистикс» Вячеслава Шикулова, уже владевшая 70% ООО «Чемодан Про», '
        'получила оставшиеся 30% от партнера Андрея Языкова и стала единственным '
        'владельцем компании; Языков сохранил пост генерального директора.'
    )
    card['eco']['val'] = (
        'Цена не раскрыта. По оценке Михаила Бурмистрова, главы «Infoline-Аналитики», доля '
        'в 30% могла обойтись покупателю в сумму около 100 млн рублей. Весь пакет '
        '«Робинзон Логистикс» в «Чемодан Про» с 28 сентября 2026 года заложен в пользу '
        'Языкова.'
    )
    card['eco']['context'] = (
        '«Чемодан Про» — наследник российского юрлица Samsonite: бренд ушел из страны '
        'весной 2022 года, а магазины получили новую вывеску. Годовая выручка компании '
        'в 2025 году выросла на 7%, до 1,8 млрд ₽, но год закрылся убытком 266 млн ₽; '
        'сеть сократилась с 37 точек в 2022 году до 23 собственных и шести партнерских '
        'сейчас. Стороны на запросы изданий не ответили.'
    )
    card['party_evidence'] = {
        'buyer': [{'value': '«Робинзон Логистикс» (Вячеслав Шикулов)', 'field': 'buyer_name',
                   'method': 'explicit_news_title', 'url': SRC_KOMMERSANT[1]}],
        'seller': [{'value': 'Андрей Языков', 'field': 'seller',
                    'method': 'explicit_news_title', 'url': SRC_KOMMERSANT[1]}],
        'target': [{'value': '30% ООО «Чемодан Про»', 'field': 'asset',
                    'method': 'explicit_news_title', 'url': SRC_KOMMERSANT[1]}],
    }
    card['themes'] = ['M&A']
    card['pending_since'] = datetime.now(timezone.utc).isoformat()
    card['events'] = [{
        'kind': 'closed', 'date': '2026-10-13', 'title': 'Сделка завершена',
        'note': ('Реестр (ЕГРЮЛ) зафиксировал смену: «Робинзон Логистикс» теперь '
                 'единственный владелец «Чемодан Про» — доля выросла с 70% до 100% '
                 'за счет пакета, который был у Языкова.'),
        'source': SRC_KOMMERSANT,
    }]

    print('НОВАЯ КАРТОЧКА %s: %s' % (CARD_ID, card['title']))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(PENDING, encoding='utf-8'))
    if any(c['id'] == CARD_ID for c in fresh['cards']):
        print('ОТКАЗ: карточка уже появилась между чтением и записью')
        return 1
    fresh['cards'].append(card)
    json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
