# -*- coding: utf-8 -*-
"""Дневная очередь дочитывания (G7, первый уровень, полный обыск),
19 сентября 2026: карточка `gb1cd8142` («ИБ-компания Metascan купила 24,5%
платформы для подготовки корпоративных ИБ-команд Defbox») — единственным
источником был TAdviser (пересказ пресс-релиза); CISOCLUB (cisoclub.ru,
ранее в `src` не значился) публикует тот же пресс-релиз с дополнительными
подробностями об устройстве самого инвестиционного механизма.

Найдено и дословно проверено лично прямым WebFetch: сделка прошла не
напрямую от Metascan, а через СОВМЕСТНЫЙ ФОНД с ФРИИ — фонд создан в июле
2026 года, объёмом 600 млн ₽, профинансирован партнёрами поровну, ориентирован
на российские B2B-компании в кибербезопасности с готовым продуктом и
диапазоном чека 5–100 млн ₽. Это уточняет уже стоящее в `eco.share` упоминание
«в рамках совместного фонда с ФРИИ» — раньше в карточке не было ни размера
фонда, ни даты его создания, ни диапазона инвестиций.

Запуск: python3 pipeline/fix_metascan_defbox_fund_details.py           # проверка
        python3 pipeline/fix_metascan_defbox_fund_details.py --write   # запись
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gb1cd8142'

OLD_SHARE = (
    'Российский разработчик решений в сфере информационной безопасности '
    'Metascan инвестировал 10 млн рублей в платформу для подготовки ИБ-'
    'специалистов Defbox в рамках совместного фонда с ФРИИ. Сделка прошла '
    'в формате инвестиций в капитал: Metascan получил 24,5% компании. Об '
    'этом было объявлено в середине сентября 2026 года.'
)

QUOTE = (
    'В июле 2026 года партнеры создали специализированный фонд объемом '
    '600 млн рублей, профинансировав его в равных долях. Фонд ориентирован '
    'на российские B2B-компании в сфере кибербезопасности с готовым '
    'продуктом, первыми клиентами или подтвержденным спросом; размер '
    'инвестиций может составлять от 5 до 100 млн рублей.'
)
ADD_SHARE = QUOTE

CISOCLUB_URL = (
    'https://cisoclub.ru/metascan-i-frii-investirovali-10-mln-rublej-v-'
    'defbox-platformu-dlja-podgotovki-korporativnyh-ib-komand'
)


def flat(s):
    return re.sub(r'[^0-9a-zа-яё]+', '', str(s or '').lower().replace('ё', 'е'))


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в deals_promoted.json' % CARD_ID
    assert card['eco'].get('share') == OLD_SHARE, (
        'eco.share уже другой: %r' % card['eco'].get('share'))
    assert flat(ADD_SHARE) in flat(QUOTE), 'ADD_SHARE не лежит дословно в цитате'

    new_share = OLD_SHARE + ' ' + ADD_SHARE
    print('НОВОЕ eco.share:')
    print(new_share)

    if not write:
        print()
        print('Сухой прогон. Запись — с ключом --write.')
        return

    card['eco']['share'] = new_share
    urls = {s[1] for s in (card.get('src') or []) if isinstance(s, list) and len(s) > 1}
    if CISOCLUB_URL not in urls:
        card.setdefault('src', []).append(['CISOCLUB', CISOCLUB_URL])
    json.dump(data, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
