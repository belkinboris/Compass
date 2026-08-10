# -*- coding: utf-8 -*-
"""У карточки `g7ad4e39d` («Консорциум российских инвесторов приобретает
российский бизнес Henkel») ЕДИНСТВЕННЫЙ источник — статья «Ведомостей» про
продажу финской SRV Group своего актива в России (торговый центр «Охта
Молл»): другая компания, другая сделка, ни слова о Henkel, Харитонине,
Таврине или консорциуме. Источник карточку не подтверждает вовсе — тот же
класс дефекта, что и `g2544a5cb` (см. CLAUDE.md), только источник не просто
неточен, а о совершенно другой сделке.

Содержание самой карточки (Харитонин/Таврин/Кульков/Крюков, 11 заводов
Henkel, Persil/Losk/Ласка, оценка ~600 млн €) при этом дословно совпадает с
реальной историей — просто взято из статьи, которая при импорте не
сохранилась как источник. Названный консорциум впервые встречается в
открытых источниках не раньше конца марта 2023 года (RBC и ADPASS,
28.03.2023 — «Компания находится на завершающей стадии продажи своих
российских активов, однако соглашение между сторонами пока не подписано»,
дословно совпадает со статусом карточки «Обсуждается»); прежняя дата
`2022-11-01` — заглушка компактного импорта (первое число месяца, тот же
класс дефекта, что `fix_placeholder_dates.py`), а не подтверждённый источником
день. Отдельный, уже существующий `g6f4a071a` (2023-05-04, «Закрыта») — более
поздняя стадия той же истории (сделка закрыта); эта карточка снимает более
раннюю стадию («Обсуждается», соглашение не подписано) и намеренно не
сливается с ней в этом прогоне — слияние дублей делает отдельный
match_keys-скрипт, а не чтение карточки.

Почему не через review.py: FIXES проверяет дословное вхождение НОВОГО
значения в закэшированный сырой текст источника; у нас нет закэшированного
сырого текста ADPASS (сеть в этой сессии отдаёт статью только через
WebFetch, который сам пересказывает контент через модель — не дословный
кэш), а перенос сделки в другой год review.py осознанно не поддерживает
(см. запись в CLAUDE.md после `fix_osnova_sviblovo_date.py`). Меняются
только `src` и `date`; текстовые поля (rationale/extra/sum/eco) не
трогаются — их содержание уже соответствует реальной истории.

Запуск: python3 pipeline/fix_henkel_consortium_source_and_date.py
        python3 pipeline/fix_henkel_consortium_source_and_date.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g7ad4e39d'
OLD_SRC = [
    ['Ведомости',
     'https://www.vedomosti.ru/realty/articles/2022/11/21/951250-finskaya-srv-group-prodala-svoi-aktiv-v-rossii'],
]
NEW_SRC = [
    ['ADPASS',
     'https://adpass.ru/mezhdu-lekarstvami-i-media-proizoshla-himiya-viktor-haritonin-ivan-tavrin-i-elbrus-kapital-podelyat-henkel-v-rossii/'],
]
OLD_DATE = '2022-11-01'
NEW_DATE = '2023-03-28'


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    if card['src'] == NEW_SRC and card['date'] == NEW_DATE:
        print('УЖЕ ПРИМЕНЕНО %s' % CARD_ID)
        return
    assert card['src'] == OLD_SRC, '%s: src уже другой' % CARD_ID
    assert card['date'] == OLD_DATE, '%s: date уже другая' % CARD_ID
    print('ПРАВИМ  %s src: SRV Group/«Охта Молл» -> ADPASS про Henkel' % CARD_ID)
    print('ПРАВИМ  %s date: «%s» -> «%s»' % (CARD_ID, OLD_DATE, NEW_DATE))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    card['src'] = NEW_SRC
    card['date'] = NEW_DATE
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
