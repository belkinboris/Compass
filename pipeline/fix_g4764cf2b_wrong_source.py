# -*- coding: utf-8 -*-
"""Единственный источник карточки — статья совсем о другой сделке.

ЧТО СЛОМАНО. У `g4764cf2b` («Яндекс выкупил долю Uber в MLU B.V.») в `src`
стояла ссылка `kommersant.ru/amp/5941195` — но эта статья («"Балтийский
берег" вернулся в родную гавань») целиком о выкупе рыбоперерабатывающей
компании Михаилом Бобровым у Сбербанка, ни слова про Яндекс, Uber или
такси. Похоже на техническую ошибку разбора: URL совпадает по домену и
формату с настоящей статьёй о сделке, но ведёт не туда. Найдено при
обязательном для этого прогона WebSearch по сторонам сделки — вместо
чтения источника карточки поиск сразу же показал, что дословных цитат про
Яндекс/Uber там нет и быть не может.

ЧТО ДЕЛАЕМ. Заменяем на настоящую статью «Ъ» об этой сделке
(`kommersant.ru/doc/5951573`, «"Яндекс" выкупил долю Uber в группе компаний
"Яндекс Такси"», 21.04.2023) — проверено чтением, дословно описывает именно
эту сделку и датировано днём объявления. Правка через `review.py`
field='src' здесь не годится: это поле аддитивное (только дописывает), а
удалить неверную ссылку им нельзя — без прямой правки она осталась бы в
базе рядом с верной и продолжала бы вводить в заблуждение.

ЧЕГО НЕ ДЕЛАЕМ. Не трогаем остальные поля карточки — контент, добавленный
по новому верному источнику, идёт отдельными записями в
`pipeline/ingest/fixes/batch_c_2023.py` через `review.py`, как обычно.

Запуск:
    python3 pipeline/fix_g4764cf2b_wrong_source.py            # сухой прогон
    python3 pipeline/fix_g4764cf2b_wrong_source.py --write    # записать
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'
DID = 'g4764cf2b'
OLD_SRC = [['Коммерсантъ', 'https://www.kommersant.ru/amp/5941195']]
NEW_SRC = [['Коммерсантъ', 'https://www.kommersant.ru/doc/5951573']]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}
    d = by_id[DID]

    actual = d.get('src')
    assert actual == OLD_SRC, f'{DID}.src: ожидали {OLD_SRC!r}, нашли {actual!r}'

    print(f'{DID} [src]: {actual!r} -> {NEW_SRC!r}')
    if write:
        d['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print('\nЗАПИСАНО в', PATH)
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
