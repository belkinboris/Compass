# -*- coding: utf-8 -*-
"""У карточки `ge5782922` («Ростелеком получил контроль над «Булатом»,
Ростех вышел из СП») единственным источником стояла статья cnews.ru от
28 апреля 2022 года про создание СОВСЕМ ДРУГОГО совместного предприятия
(«Вестелком»/НПЦ «Элвис», микроэлектроника) — слово «Булат» в этой статье
не встречается вовсе. Обязательный поиск (WebSearch) нашёл настоящий
источник: cnews.ru от 31 мая 2023 года, дословно подтверждающий все факты
карточки (доля «Коммит Кэпитал» выросла с 37,5% до 51%, НИИ «Масштаб»
вышел, 38% перешли к НПЦ «Элвис», доля «Кьютек» сократилась до 11%).

Родня уже записанного урока «рабочая ссылка на чужую страницу хуже
видимого 404»: неверный источник хуже отсутствующего, поэтому здесь —
единственное в этой сессии исключение из правила «src аддитивное, старый
не убираем» — старый источник не просто неполон, он не о том вообще.

Запуск: python3 pipeline/fix_bulat_wrong_source.py
        python3 pipeline/fix_bulat_wrong_source.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

CARD_ID = 'ge5782922'
WRONG_SRC = ['CNews', 'https://www.cnews.ru/news/top/2022-04-28_na_rossijskom_rynke_poyavilsya']
RIGHT_SRC = ['CNews', 'https://www.cnews.ru/news/top/2023-05-31_rostelekom_zapoluchil_kontrol']


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    srcs = card.get('src') or []

    if srcs == [RIGHT_SRC]:
        print('УЖЕ ПРИМЕНЕНО')
        return
    assert srcs == [WRONG_SRC], 'src уже другой: %r' % srcs

    print('ПРАВИМ  %s src: неверный источник (не о «Булате» вовсе) заменён '
          'на настоящий' % CARD_ID)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    card['src'] = [RIGHT_SRC]
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
