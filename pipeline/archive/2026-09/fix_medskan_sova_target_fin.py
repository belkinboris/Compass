# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
g9ec93147 («ГК «Медскан» может купить сеть клиник «Сова»», июнь 2023,
статус «Обсуждается») — финансы предмета не были заполнены.

Проверено лично прямым WebFetch (Коммерсантъ,
https://www.kommersant.ru/doc/6069284): «В 2022 году выручка «Совы»
составила 611 млн руб., убыток — 194 млн руб.»

НЕ ВКЛЮЧЕНО: исход сделки. Полная разведка (WebSearch + WebFetch по
Коммерсанту, РБК, Vademecum, Forbes, Frank Media, medvestnik за
2024-2026 годы) не нашла ни подтверждения закрытия, ни подтверждения
срыва — ни один источник не пишет об исходе вовсе, сайт сети
(sovamed.ru) продолжает работать под тем же брендом. Реестровая
находка (смена состава участников ООО «МК «Сова»: 27.01.2025 —
«Сбербанк Инвестиции» вошли напрямую; 23.12.2025 — вошло АО
«Мединвест-СК», ИНН 9709096595, зарегистрировано 20.07.2023) —
недостаточное основание для правки: ни один источник не связывает
«Мединвест-СК» с «Медсканом», Туголуковым или Росатомом, а совпадение
по времени регистрации само по себе не доказательство. Записано в
CLAUDE.md как «Известная проблема» для решения человеком, а не в
карточку. `sum`/`status`/`eco.rationale` не менялись.

Запуск: python3 pipeline/fix_medskan_sova_target_fin.py
        python3 pipeline/fix_medskan_sova_target_fin.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g9ec93147'

OLD_TARGET_FIN = '—'
NEW_TARGET_FIN = 'Выручка (2022) — 611 млн ₽, убыток — 194 млн ₽.'

NEW_SRC = [
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/6069284'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['target_fin'] == OLD_TARGET_FIN

    new_src = deal['src'] + NEW_SRC

    print('=== eco.target_fin: станет ===')
    print(NEW_TARGET_FIN)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['target_fin'] = NEW_TARGET_FIN
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
