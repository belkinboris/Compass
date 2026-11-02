# -*- coding: utf-8 -*-
"""Вычитка базы, партия «j» (2 ноября 2026): то, что таблица FIXES не умеет.
Пара к pipeline/ingest/fixes/reread_2026_11_02_j.py.

- g39fc7468 («Телтекс Системс»/«Липецкое мясо»): предмет «70% ООО «Липецкое
  мясо»» → «50% ООО «Липецкое мясо»». По истории участников ЕГРЮЛ (datanewton,
  ОГРН 1214800015022) «Телтекс Системс» получила 20% еще 13 июля 2026 года
  (доли Сергея Медведева 65% → 50% и Сергея Оганова 32,5% → 27,5%), а 27
  октября 2026 года — оставшиеся 50% Медведева, после чего у нее 70%. Сделка
  карточки (дата 27 октября, продавец Медведев) — переход 50%; 70% — итоговый
  пакет, он назван в eco.share. Через таблицу нельзя: дословной цитаты «50%
  ООО «Липецкое мясо»» нет ни в статье, ни в реестре. Снятое — в
  retracted.asset (иначе enrich.py вернет «70%» из статьи Абирега), отпечаток
  прежней записи asset (structural_g39fc7468_2026_10_31.py) — в
  proofread_absorbed, доказательство предмета — реестр.
- g1edb1b9d (UniCredit/«ЮниКредит Банк»): находка приемки buyer_search —
  где искали покупателя, в accepted_notes.no_profile.buyer; заметка этапа
  «Президент разрешил…» повторяла построение фразы Lenta.ru (near_copy) —
  переписана своими словами (этап не удаляется: docs/card_editing.md).

    python3 pipeline/archive/2026-11/fix_reread_2026_11_02_j.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import review  # noqa: E402

BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
REGISTRY = 'https://datanewton.ru/api/v2/history?ogrn=1214800015022&startDate=2000-01-01&attributes=OWNERS'


def set_val(obj, key, old, new):
    assert obj.get(key) == old, (key, obj.get(key), old)
    obj[key] = new


def retract(card, field, value):
    lst = card.setdefault('retracted', {}).setdefault(field, [])
    if value not in lst:
        lst.append(value)


def absorb(card, field):
    """Поле правится мимо таблицы, а у него есть запись FIXES: ее отпечаток —
    в proofread_absorbed (docs/card_editing.md), иначе запись сочтут непримененной."""
    marks = card.setdefault('proofread_absorbed', {}).setdefault(field, [])
    for f in review.FIXES:
        if f['id'] == card['id'] and f['field'] == field and f.get('new') is not None:
            fp = review.fix_fingerprint(f['new'])
            if fp not in marks:
                marks.append(fp)


def main(argv):
    raw = open(BASE, encoding='utf-8').read()
    data = json.loads(raw)
    deals = {d['id']: d for d in data['deals']}

    # g39fc7468
    c = deals['g39fc7468']
    old_asset, new_asset = '70% ООО «Липецкое мясо»', '50% ООО «Липецкое мясо»'
    absorb(c, 'asset')
    set_val(c, 'asset', old_asset, new_asset)
    retract(c, 'asset', old_asset)
    assert c['party_evidence']['target'][0]['value'] == old_asset, c['party_evidence']['target']
    c['party_evidence']['target'] = [{'value': new_asset, 'field': 'asset', 'method': 'registry_owner_history',
                                      'url': REGISTRY}]
    assert c['seller'] == 'Сергей Медведев' and c['date'] == '2026-10-27'

    # g1edb1b9d
    c = deals['g1edb1b9d']
    assert c.get('buyer') is None and not c.get('buyer_name')
    np = c.setdefault('accepted_notes', {}).setdefault('no_profile', {})
    assert 'buyer' not in np, np
    np['buyer'] = ('покупатель — неназванный частный инвестор из ОАЭ: имени не раскрывают пресс-релиз UniCredit '
                   '(7 мая 2026), Коммерсантъ, Ведомости, The Insider, Reuters (18 июня 2026, через The Moscow '
                   'Times и The Insider) и Lenta.ru (распоряжение президента 5 октября 2026); Asas Capital, Mada '
                   'Capital и Inweasta упоминались как претенденты в 2025 году, но то, что покупатель по майскому '
                   'соглашению — одна из них, ни один источник не подтверждает')

    ev = c['events'][1]
    assert ev['kind'] == 'approval' and ev['note'].startswith('Владимир Путин подписал распоряжение, разрешающее'), ev['note']
    ev['note'] = 'Распоряжением Владимира Путина разрешены покупка всех акций «ЮниКредит Банка» и реорганизация банка.'

    print('g39fc7468: предмет 70% → 50% ООО «Липецкое мясо» (retracted, proofread_absorbed, party_evidence)')
    print('g1edb1b9d: accepted_notes.no_profile.buyer — где искали покупателя; заметка этапа одобрения своими словами')
    if '--write' not in argv:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    assert open(BASE, encoding='utf-8').read() == raw, 'база изменилась во время прогона — перезапустите'
    out = json.dumps(data, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else '')
    open(BASE, 'w', encoding='utf-8').write(out)
    print('записано')


if __name__ == '__main__':
    main(sys.argv[1:])
