# -*- coding: utf-8 -*-
"""Карточка gb0f1f736 («Альфа-Банк» купил WhoIsBlogger): дата сделки — 29 октября 2025 года,
а не 2 сентября 2026 года (сверка с сайтом Advance Capital, бэклог E17, 14 ноября 2026).

Было: дата 2026-09-02 — день, когда Альфа-Банк объявил о покупке (Sostav, Bankinform, TAdviser).
Правило (docs/card_status_dates.md, «Дата — день события, о котором статус»): у закрытой сделки
дата — закрытие или запись о переходе доли в ЕГРЮЛ, а не объявление.

ДОКАЗАТЕЛЬСТВО — два независимых источника с одним днем:
  * ЕГРЮЛ (уже в «Как устроена сделка» карточки, вычитка m219): 29 октября 2025 года из ООО
    «Даблюайби» вышли все пять участников, 100% перешли к АО «Софтхолдинг» (с сентября 2026 года —
    АО «А-Селлер Холдинг»);
  * пресс-релиз консультанта компании Advance Capital, датированный 29 октября 2025 года
    (https://advancecapital.ru/news/news/press-releases/454/): «Advance Capital рад объявить об
    успешном закрытии сделки по продаже Альфа-Банку ведущей SaaS-платформы для поиска и аналитики
    блогеров – WhoIsBlogger».
Год меняется (2026 -> 2025), поэтому не через review.py (он год не переносит), а разовым скриптом
с assert на старое значение. Два события «Сделка завершена» от 2 и 3 сентября 2026 года описывают
объявление банка («объявил о приобретении») — им возвращено настоящее имя.

    python3 pipeline/archive/2026-11/fix_whoisblogger_date_2026_11_14.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
CID, OLD, NEW = 'gb0f1f736', '2026-09-02', '2025-10-29'
PR = 'https://advancecapital.ru/news/news/press-releases/454/'
QUOTE = ('29 октября / 2025 Пресс-релиз Advance Capital рад объявить об успешном закрытии сделки по продаже '
         'Альфа-Банку ведущей SaaS-платформы для поиска и аналитики блогеров – WhoIsBlogger.')


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))      # читается прямо перед записью
    c = next(d for d in data['deals'] if d['id'] == CID)
    if c['date'] == NEW:
        print('Уже применено.')
        return 0
    assert c['date'] == OLD and c['status'] == 'Закрыта', (c['date'], c['status'])
    assert '29 октября 2025 года' in c['law']['struct']
    c['date'] = NEW
    c['date_basis'] = 'registry'
    fact_edit_guard.log(c, 'date', NEW, QUOTE, PR, 'fix_whoisblogger_date', '2026-11-14')
    for ev in c.get('events') or []:
        if ev.get('kind') == 'closed' and ev.get('date') in ('2026-09-02', '2026-09-03'):
            assert 'объявил о приобретении' in ev['note'], ev['note']
            ev['kind'] = 'announced'
            ev['title'] = 'Альфа-Банк объявил о покупке'
    if not any(s[1] == PR for s in c['src']):
        c['src'].append(['Advance Capital', PR])
    print('%s: дата %s -> %s, основание — реестр; события сентября 2026 года названы объявлением' % (CID, OLD, NEW))
    if write:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
