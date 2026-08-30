# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
g97679d43 (ВТБ продаёт аграрные активы) — ПЯТАЯ подряд карточка в этой
рутине с ошибочным годом: единственный источник карточки сам датирован
2026-м, а не 2024-м. Уже отмечено комментарием в `pipeline/ingest/
fixes/batch_b_2024.py` более ранним прогоном, но год сам не переносился
— переносится этим скриптом. Проверено лично прямым WebFetch.

Год сделки (2024 → 2026) — НЕ через `review.py` (смена года — отдельный
скрипт). Единственный источник карточки — kommersant.ru/doc/8572213 —
сам датирован «08.04.2026, 23:04» и называет именно ту оценку (55 млрд
₽), что уже стоит в карточке: «Общая оценочная стоимость активов
превышает 55 млрд руб.» Собственные поля карточки уже противоречили
дате 2024: `eco.rationale` говорит о регулировании ЦБ «с 1 апреля 2027
года», `eco.context` — о декабрьском 2025 года интервью Костина Reuters
— обе даты НЕВОЗМОЖНЫ для карточки 2024 года.

Статус «Обсуждается» НЕ меняется — карточка сама говорит, что сделка «на
стадии поиска покупателей, завершение планируется до 2027 года», и
источник (апрель 2026) подтверждает: «реализовать активы ВТБ
рассчитывает к 2027 году».

Запуск: python3 pipeline/fix_vtb_agro_assets_year.py
        python3 pipeline/fix_vtb_agro_assets_year.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g97679d43'

OLD_DATE = '2024'
NEW_DATE = '2026'


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['date'] == OLD_DATE

    print('=== date: станет ===')
    print(NEW_DATE)

    if write:
        deal['date'] = NEW_DATE
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
