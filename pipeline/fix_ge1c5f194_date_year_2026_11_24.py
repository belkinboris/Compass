# -*- coding: utf-8 -*-
"""ge1c5f194 (УК «Либра Капитал»/«РВМ Капитал», офисы на Новорязанской, 24) —
дата сделки несла день публикации, а не день события.

ЧТО СЛОМАНО. `date` и `events[0].date` стояли «2026-11-18» при статусе
«Закрыта». Единственный источник карточки — Коммерсантъ,
https://www.kommersant.ru/doc/9112084, опубликован 18.11.2026 в 01:57. В
статье нет ни одной фразы с конкретным днем закрытия, регистрации перехода
права или подписания договора: гендиректор «РВМ Капитала» Феликс Блинов
подтвердил сам факт сделки без даты, а покупатель на запрос не ответил,
консультант (Ricci) от комментариев отказался. «2026-11-18» — это день,
когда Коммерсантъ ВЫПУСТИЛ статью по неофициальным данным источников, а не
день, который источник называет днем сделки (docs/card_status_dates.md,
«Дата публикации не уточняет дату сделки»). Поиск другого источника с точной
датой (Frank Media — пересказ того же Коммерсанта; реестр ЦБ по ОГРН
покупателя; spark-interfax; сайт УК «Либра Капитал») дня сделки не дал —
только подтверждение сторон и реквизитов, уже отраженное в
`accepted_notes.searched` карточки.

ПОЧЕМУ НЕ ЧЕРЕЗ `review.py`. `date_is_supported()` принимает только полную
дату ГГГГ-ММ-ДД, подтвержденную цитатой с днем и месяцем словами, — здесь
обратная операция: снять день, которого в источнике нет, оставив известный
год. Снятие дня до года — отдельный одноразовый скрипт с `assert` на старое
значение (тот же случай, что и перенос года, docs/card_status_dates.md,
«`review.py` год не переносит», образец — `fix_osnova_sviblovo_date.py`).

ПОЧЕМУ ГОД, А НЕ ПОЛНАЯ ДАТА. День события в источниках не назван вовсе
(ни месяц отдельно от дня публикации, ни дата из реестра/документа) —
подставить любой день значило бы выдумать его. Год «2026» сомнений не
вызывает (публикация того же года, профиль покупателя подтвержден по ОГРН
без признаков более раннего периода), поэтому меняется только день, а не
год.

ПОДТВЕРЖДЕНИЕ ФАКТА (`fact_edit_guard.py`, обязательно с 11 ноября 2026).
Правка поля-факта `date` у карточки, уже бывшей в базе, требует цитаты —
записываем `fact_log` тем же прогоном: цитата честно говорит, что источник
НЕ называет день, а не выдает несуществующую цитату дня за подтверждение.

Запуск:
    python3 pipeline/fix_ge1c5f194_date_year_2026_11_24.py            # сухой прогон
    python3 pipeline/fix_ge1c5f194_date_year_2026_11_24.py --write    # записать
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fact_edit_guard  # noqa: E402

DATA = 'static/data/deals_promoted.json'
DEAL_ID = 'ge1c5f194'
OLD_DATE = '2026-11-18'
NEW_DATE = '2026'
URL = 'https://www.kommersant.ru/doc/9112084'
QUOTE = ('Коммерсантъ, 18.11.2026, 01:57 (прочитан целиком, кэш data/inbox/raw в рабочем дереве '
         'пуст — WebFetch): в статье нет фразы с конкретным днем закрытия, регистрации перехода '
         'права или подписания договора — единственная дата материала это время его публикации. '
         'Гендиректор «РВМ Капитала» Феликс Блинов подтвердил «Ъ» сам факт сделки без даты, '
         'покупатель на запрос не ответил, Ricci от комментариев отказался; поиск других '
         'источников (Frank Media, cbr.ru/finorg, spark-interfax, сайт УК) дня сделки не дал. '
         '«2026-11-18» было днем выхода статьи, не днем события — оставлен только бесспорный год.')
BY = 'accept_card_ge1c5f194_2026_11_24'


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    deal = by_id.get(DEAL_ID)
    assert deal is not None, 'нет сделки %s' % DEAL_ID
    already_logged = any(r.get('field') == 'date' and r.get('new') == NEW_DATE
                         for r in deal.get('fact_log') or [])
    if deal.get('date') == NEW_DATE and already_logged:
        print('Уже применено.')
        return
    assert deal.get('date') in (OLD_DATE, NEW_DATE), \
        'дата неожиданная: %r' % deal.get('date')
    events = deal.get('events') or []
    assert events and events[0].get('date') in (OLD_DATE, NEW_DATE), \
        'events[0].date неожиданная: %r' % (events[0].get('date') if events else None)

    print('%s: date %r -> %r (fact_log: %s)' % (DEAL_ID, deal.get('date'), NEW_DATE,
                                                 'есть' if already_logged else 'добавится'))
    print('  источник: %s — день закрытия не назван, только время публикации' % URL)

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    deal['date'] = NEW_DATE
    events[0]['date'] = NEW_DATE
    if not already_logged:
        fact_edit_guard.log(deal, 'date', NEW_DATE, QUOTE, URL, BY, date='2026-11-24')
    assert deal['date'] == NEW_DATE and events[0]['date'] == NEW_DATE, 'дата не записалась'

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
