# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
gd246f586 (Яндекс купил kidtech-платформу «Сказбука», закрыта 27
сентября 2023) — платформа встроена в детскую опцию Яндекс Плюс, имя
сохранено.

Проверено лично прямым WebFetch (Retail-Loyalty.org,
https://retail-loyalty.org/news/yandeks-plyus-dobavil-razvivayushchie-igry-ot-skazbuki-v-detskuyu-optsiyu-/):
«Теперь подписчикам Детской опции в Яндекс Плюсе доступны игры для
детей в «Сказбуке»», контент (40 мини-игр, более 1000 заданий) сохранён
для детей 3-6 лет — «Сказбука» не заменена и не переименована, а
встроена контент-блоком в опцию «Плюс Детям» наряду с приложением
«Кубокот» и разделами Кинопоиска/Музыки.

НЕ ВКЛЮЧЕНО: судьба основателя Иннокентия Скирневского после Яндекса —
саб-агент нашёл косвенный, не подтверждённый прямой цитатой сигнал о
его уходе с руководящей должности «в корпорации» (без явного названия
компании) ради собственного игрового проекта; связь с Яндексом
правдоподобна по контексту, но не доказана дословно — не переношу как
факт; метрики самой «Сказбуки» (число пользователей, выручка) за
2024-2026 — публикуются только в целом по «Яндекс Плюс», отдельных
цифр по «Сказбуке» источники не дают; официальная сумма сделки —
по-прежнему не раскрыта, только экспертная оценка «до 120 млн ₽»,
уже стоящая в карточке.

Запуск: python3 pipeline/fix_yandex_skazbuka_integration.py
        python3 pipeline/fix_yandex_skazbuka_integration.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gd246f586'

OLD_EXTRA = (
    'Приобретение Яндексом образовательной платформы Сказбука. Команда '
    'платформы перейдет в Яндекс, платформа продолжит работу под тем '
    'же названием.'
)
NEW_EXTRA = OLD_EXTRA + (
    ' «Сказбука» встроена контент-блоком в детскую опцию «Плюс Детям» '
    'Яндекс Плюс: собственное имя сохранено, контент (40 мини-игр) '
    'доступен подписчикам опции наряду с приложением «Кубокот» и '
    'разделами Кинопоиска и Музыки.'
)

NEW_SRC = [
    ['Retail-Loyalty.org', 'https://retail-loyalty.org/news/yandeks-plyus-dobavil-razvivayushchie-igry-ot-skazbuki-v-detskuyu-optsiyu-/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['extra'] == OLD_EXTRA

    new_src = deal['src'] + NEW_SRC

    print('=== extra: станет ===')
    print(NEW_EXTRA)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['extra'] = NEW_EXTRA
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
