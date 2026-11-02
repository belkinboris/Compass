# -*- coding: utf-8 -*-
"""Вычитка базы, партия «h» (2 ноября 2026): то, что таблица FIXES не умеет.
Пара к pipeline/ingest/fixes/reread_2026_11_02_h.py.

Каждая статья открыта заново и сохранена save_source.py
(data/inbox/triage/sources_2026-11-02.json).

- g1f8414a3 («ЭсЭфАй»/«Агропромкредит»): продавец — Российская Федерация
  (распоряжение правительства № 2763-р от 2 октября 2026 года: 50% акций
  банка, 100% ООО «Блаусент» и «Дэнсиборг» — федеральное имущество по указу
  № 693; ПСБ — организатор продажи, The Insider: «ПСБ будет организовывать
  продажу от имени государства»). seller_id Промсвязьбанка снимается (пара
  «ссылка + текст» правится вместе; профиля «Российская Федерация» нет и
  ради одной сделки не заводится), «ПСБ» — в retracted.seller; этап
  закрытия — 26 октября (день аукциона по ГИС Торги, AK&M), заметка этапа —
  без «ПСБ продал».
- gb986603e (Golden Brick Capital/ДАК): статус «Обсуждается» → «Закрыта»,
  дата — 29 сентября 2026 года (запись в ЕГРЮЛ: Vision Investment Limited
  вошла с 49%, Коммерсантъ по СПАРК — «получила 49%»); review.py статус не
  берет — «получила» нет в STATUS_WORDS, дата — из реестра, а не из слов
  статьи. Доказательство продавца (ООО «НСЗК»: капитал 1 млн ₽ не менялся,
  номинал доли НСЗК 1 млн → 510 тыс. ₽) — party_evidence.seller; заметка
  приемки «продавца поэтому не вписываем» исправлена.
- gf03916a4, g861c5553: legal_short продавцов вручную — party_legal_names.py
  на вложенных кавычках дает «АО «ВЦКБ "полюс»» и «ПАО «Банк «Уралсиб»»
  (без закрывающей «елочки»), поэтому --write для этих карточек не запускать.

    python3 pipeline/archive/2026-11/fix_reread_2026_11_02_h.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
ORDER_URL = 'https://pravo.ppt.ru/rasporyazheniye/356495'
KOM_DAK = 'https://www.kommersant.ru/doc/9063195'
REG_DAK = 'https://projectcompass.ru/api/companies/g1e3e41bf/fns'


def set_val(obj, key, old, new):
    assert obj.get(key) == old, (key, obj.get(key), old)
    obj[key] = new


def retract(card, field, value):
    lst = card.setdefault('retracted', {}).setdefault(field, [])
    if value not in lst:
        lst.append(value)


def main(argv):
    raw = open(BASE, encoding='utf-8').read()          # перечитать прямо перед записью
    data = json.loads(raw)
    deals = {d['id']: d for d in data['deals']}
    comps = data['companies']

    # g1f8414a3
    c = deals['g1f8414a3']
    set_val(c, 'seller_id', 'g8bafde28', None)          # Промсвязьбанк — организатор, не собственник
    c.pop('seller_id')
    retract(c, 'seller', 'ПСБ')
    assert c['party_evidence']['seller'][0]['value'] == 'ПСБ'
    c['party_evidence']['seller'] = [{'value': 'Российская Федерация', 'field': 'seller',
                                      'method': 'human_review', 'url': ORDER_URL}]
    ev = c['events'][0]
    assert ev['kind'] == 'closed' and ev['note'].startswith('ПСБ продал на повторных торгах')
    set_val(ev, 'date', '2026-10-27', '2026-10-26')
    ev['note'] = ('Повторный аукцион 26 октября выиграло ПАО «ЭсЭфАй»: 50% акций банка и две компании, '
                  'которым принадлежит остальная половина, ушли за 1,427 млрд ₽ — вдвое ниже стартовой цены.')

    # gb986603e
    c = deals['gb986603e']
    set_val(c, 'status', 'Обсуждается', 'Закрыта')
    set_val(c, 'date', '2026-10-29', '2026-09-29')
    assert c.get('date_basis') is None
    c['date_basis'] = 'registry'
    c['party_evidence']['seller'] = [{'value': 'ООО «Новый сухопутный зерновой коридор»', 'field': 'seller',
                                      'method': 'registry', 'url': REG_DAK},
                                     {'value': 'ООО «Новый сухопутный зерновой коридор»', 'field': 'seller',
                                      'method': 'human_review', 'url': KOM_DAK}]
    notes = c['accepted_notes']['notes']
    old_tail = 'продавца поэтому не вписываем'
    assert old_tail in notes
    c['accepted_notes']['notes'] = notes + (
        ' Вычитка 2 ноября 2026 (партия h): вывод «продавца не вписываем» снят — по ЕГРЮЛ уставный капитал '
        'ДАК не менялся (1 млн ₽ при создании и после 29 сентября 2026 года), номинал доли НСЗК уменьшился '
        'с 1 млн до 510 тыс. ₽, 490 тыс. ₽ перешли к Vision Investment: доля продана участником, продавец — '
        'ООО «Новый сухопутный зерновой коридор»; сделка записана в реестре 29 сентября — статус «Закрыта».')

    # legal_short продавцов (party_legal_names.py ломает вложенные кавычки)
    assert comps['g4e5fdb4a'].get('legal_short') is None
    comps['g4e5fdb4a']['legal_short'] = 'АО «ВЦКБ «Полюс»»'
    assert comps['gc8bb35e1'].get('legal_short') is None
    comps['gc8bb35e1']['legal_short'] = 'ПАО «Банк Уралсиб»'

    if '--write' not in argv:
        print('Сухой прогон: g1f8414a3 (продавец без ссылки на ПСБ, этап 26.10), gb986603e (Закрыта, '
              '2026-09-29, доказательство продавца), legal_short двух продавцов. Запись — --write.')
        return 0
    fresh = open(BASE, encoding='utf-8').read()
    assert fresh == raw, 'база изменилась во время прогона — перезапустить'
    out = json.dumps(data, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else '')
    open(BASE, 'w', encoding='utf-8').write(out)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
