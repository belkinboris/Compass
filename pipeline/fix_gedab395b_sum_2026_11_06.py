# -*- coding: utf-8 -*-
"""Карточка gedab395b («Дом Петеревского» в Ярославле) — sum/eco.sum = «1 ₽».

ПОЧЕМУ НЕ ЧЕРЕЗ review.py FIXES. `review.sum_is_supported()` разбирает
значение регэкспом, который ОБЯЗАТЕЛЬНО требует единицу «млн»/«млрд» —
«1 ₽» без них в этот формат не укладывается никак (проверено на себе:
ни один FIXES-пример в базе не ставит sum в такую форму иначе, чем через
автоматический разбор draft.py по ЦИФРЕ «1» прямо в заголовке источника,
см. g4b78d957/g896a22ba — там в заголовке источника «за 1 рубль»). Источник
этой карточки (Abnews.ru) пишет цену словом: «стартовая цена установлена
на уровне одного рубля» — цифры «1» в тексте нет, draft.py её не поймал.

ПОЧЕМУ ЭТО ВСЁ РАВНО НАДО ЗАПИСАТЬ. Второе чтение (чтение карточки целиком,
как её видит подписчик) нашло находку `coherent`: «Обзор» показывал
«Начальная цена лота: Не раскрыта», а двумя экранами ниже, в «Экономисте»,
прямо написано «стартовая цена конкурса — один рубль» — это не честная
пустота, а два экрана одной карточки спорят друг с другом о том, известна
цена или нет. Цена известна и подтверждена дословно в источнике (как и в
прозе eco.val) — значение переносится тем же способом, что и перевод
иноязычной цитаты (docs/card_editing.md, «Как записывать перевод
иноязычного источника»): одноразовый скрипт с assert на старое значение,
а не через таблицу, которая этот формат механически не пропускает.

Источник: https://abnews.ru/center/news/yaroslavl/2026/11/6/starinnyj-dom-peterevskogo-v-yaroslavle-prodadut-za-rubl
Цитата: «В соответствии с федеральным законом о приватизации стартовая
цена установлена на уровне одного рубля.»

Применено 6 ноября 2026. Запуск (повторный прогон идемпотентен — assert
не сработает, если значение уже стоит): python3 pipeline/fix_gedab395b_sum_2026_11_06.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__)).rsplit(os.sep + 'pipeline', 1)[0]
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

CARD_ID = 'gedab395b'
NEW_VALUE = '1 ₽'


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next((c for c in data['cards'] if c['id'] == CARD_ID), None)
    if card is None:
        print('карточки %s нет в очереди — возможно, уже отправлена; значение, скорее всего, уже применено' % CARD_ID)
        return 0
    if card.get('sum') == NEW_VALUE and (card.get('eco') or {}).get('sum') == NEW_VALUE:
        print('уже применено')
        return 0
    assert card.get('sum') is None, 'sum уже не None: %r' % card.get('sum')
    assert (card.get('eco') or {}).get('sum') == '—', 'eco.sum уже не "—": %r' % (card.get('eco') or {}).get('sum')
    print('ПРАВИМ   %s sum      %r -> %r' % (CARD_ID, card.get('sum'), NEW_VALUE))
    print('ПРАВИМ   %s eco.sum  %r -> %r' % (CARD_ID, card['eco']['sum'], NEW_VALUE))
    if write:
        card['sum'] = NEW_VALUE
        card['eco']['sum'] = NEW_VALUE
        json.dump(data, open(PENDING, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('ЗАПИСАНО')
    else:
        print('Сухой прогон. Запись — с ключом --write.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
