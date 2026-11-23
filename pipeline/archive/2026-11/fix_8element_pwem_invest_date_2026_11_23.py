# -*- coding: utf-8 -*-
"""Карточка g30404c73 (ГК «8 элемент» купила PWeM Invest, очередь второго чтения):
дата сделки — 28 августа 2026 года (регистрация в ЕГРЮЛ), а не 13 ноября 2026 года
(день публикации статьи-источника). Найдено при втором чтении 23 ноября 2026.

Было: date=2026-11-13, date_basis=announcement — день, когда Mergers.ru напечатал
новость. Правило (docs/card_status_dates.md, «Дата — день события, о котором
статус»): у закрытой сделки дата — закрытие или регистрация перехода доли в ЕГРЮЛ,
а не публикация и не объявление. Запись `date_basis=announcement` сделана той же
приемкой 23 ноября 2026 (pipeline/ingest/fixes/second_review_2026_11_23_three_cards.py),
которая В ТОЙ ЖЕ ПРАВКЕ переносит в law.struct и seller фразу «смена участников
зарегистрирована в ЕГРЮЛ 28 августа 2026 года, до публичного объявления о сделке» —
дата закрытия уже была найдена и записана в карточку, но не перенесена в date/date_basis
(обоснование date_basis=announcement говорило только «дня закрытия в СТАТЬЕ нет»,
не учтя, что день есть в самой карточке из отдельного запроса к реестру).

ДОКАЗАТЕЛЬСТВО — история участников ЕГРЮЛ PWeM Invest (ООО ИК «Управление частным
капиталом», ОГРН 1215200023103), проверено повторно напрямую (без ключа):
    curl 'https://datanewton.ru/api/v2/history?ogrn=1215200023103&startDate=2000-01-01&attributes=OWNERS'
    -> {"history_items":[{"type":"OWNERS","updated_at":"2026-08-28",
        "values":[{"old":"КОНЮХОВА ЯНА ВЛАДИМИРОВНА … 30.0%","new":null},
                  {"old":"КУТЬИН ДМИТРИЙ ГЕННАДЬЕВИЧ … 70.0%","new":null},
                  {"old":null,"new":"БУТЕНКО СЕРГЕЙ ВАЛЕРЬЕВИЧ … 100.0%"}]}]}
Тот же день (28 августа 2026) уже назван словами в law.struct карточки: «смена
участников зарегистрирована в ЕГРЮЛ 28 августа 2026 года, до публичного объявления
о сделке».

Год не меняется (2026 -> 2026), но день и месяц расходятся с датой, которую видел
review.py (у него для этого поля нет доступа к datanewton — не кэш статьи), поэтому
правка — разовым скриптом с assert на старое значение, а не записью FIXES.
Карточка лежит в очереди предпросмотра (static/data/pending.json), не в базе.

    python3 pipeline/archive/2026-11/fix_8element_pwem_invest_date_2026_11_23.py [--write]

После записи карточка становится «stale» (accepted_hash не совпадет с отпечатком) —
нужна переприемка (accept_card.py) и повторное второе чтение (second_reading.py).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402

PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
CID, OLD, NEW = 'g30404c73', '2026-11-13', '2026-08-28'
OLD_BASIS, NEW_BASIS = 'announcement', 'registry'
URL = 'https://datanewton.ru/api/v2/history?ogrn=1215200023103&startDate=2000-01-01&attributes=OWNERS'
QUOTE = ('datanewton, история участников ЕГРЮЛ PWeM Invest (ОГРН 1215200023103): '
         'updated_at "2026-08-28" — Конюхова Я.В. (30%) и Кутьин Д.Г. (70%) выбыли, '
         'Бутенко С.В. стал единственным участником с долей 100%; то же событие уже '
         'названо словами в law.struct карточки: «смена участников зарегистрирована в '
         'ЕГРЮЛ 28 августа 2026 года, до публичного объявления о сделке».')


def main(write):
    pending = json.load(open(PENDING, encoding='utf-8'))      # читается прямо перед записью
    c = next(d for d in pending['cards'] if d['id'] == CID)
    if c['date'] == NEW and c.get('date_basis') == NEW_BASIS:
        print('Уже применено.')
        return 0
    assert c['date'] == OLD and c.get('date_basis') == OLD_BASIS and c['status'] == 'Закрыта', \
        (c['date'], c.get('date_basis'), c['status'])
    assert '28 августа 2026 года' in c['law']['struct']
    c['date'] = NEW
    c['date_basis'] = NEW_BASIS
    fact_edit_guard.log(c, 'date', NEW, QUOTE, URL, 'second_reading_8element_pwem', '2026-11-23')
    fact_edit_guard.log(c, 'date_basis', NEW_BASIS, QUOTE, URL, 'second_reading_8element_pwem', '2026-11-23')
    c['notes'] = (str(c.get('notes') or '').rstrip() + ('\n\n' if c.get('notes') else '') +
                  'Второе чтение 23 ноября 2026: дата перенесена с дня публикации (13 ноября) на день '
                  'регистрации перехода доли в ЕГРЮЛ (28 августа 2026, datanewton) — тот же день уже '
                  'назван в law.struct; date_basis announcement -> registry.').strip()
    print('%s: date %s -> %s, date_basis %s -> %s' % (CID, OLD, NEW, OLD_BASIS, NEW_BASIS))
    if write:
        json.dump(pending, open(PENDING, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
