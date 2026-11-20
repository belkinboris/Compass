# -*- coding: utf-8 -*-
"""Дособраны факты по уже опубликованной карточке «АО «Деловые связи» купило
100% ООО «Аппетит»» (g00f36bab) — найдены при разборе дубля-черновика
g3f3023cb (Mergers.ru, 20 ноября 2026, перепечатка той же статьи «Делового
Петербурга»). Черновик снят как дубль (drop_pending.py), а новое из него и из
собственного чтения реестра — сюда, без правки руками `pending.json`/
`deals_promoted.json` напрямую (review.py для этих полей не подходит: цитата
не из статьи на диске, а из ЕГРЮЛ — docs/card_editing_scripts.md, «Когда
review.py не подходит»).

ЧТО НАШЛОСЬ. Ни ИНН покупателя и предмета, ни точный день сделки, ни второй
продавец в статье не названы (второе чтение 9 ноября 2026 это и зафиксировало
— `accepted_notes.no_inn`, дата осталась годом). Прямой поиск в реестре
(datanewton, Playwright — curl отдает JS-заглушку, см. docs/card_parties.md)
закрывает все три:

  ООО «АППЕТИТ» (операционное юрлицо сети Uppetit) — ИНН 7813681528,
  ОГРН 1247800072740, Санкт-Петербург. История участников
  (https://datanewton.ru/api/v2/history?ogrn=1247800072740&startDate=2000-01-01&attributes=OWNERS):
  на 2026-06-25 запись "было → стало" — ДУЛОВ АНТОН СЕРГЕЕВИЧ (82,8%) и
  МАГОМЕДОВ ВАДИМ ХУСАИНОВИЧ (17,2%) вышли, 100% получило АО «ДЕЛОВЫЕ СВЯЗИ»
  (ОГРН 1197847182444). День записи — день закрытой сделки (тот же прием,
  что на Wylsacom/«Иммортал», docs/intake_run.md, «Шаг 8: статья называет
  ООО...»): перепроверено — к этой дате ни до, ни после этого единственного
  события в истории нет, то есть смена разовая и совпадает по смыслу со
  статьей («сеть перешла к непубличному АО»).

  АО «ДЕЛОВЫЕ СВЯЗИ» — ИНН 7805755960, ОГРН 1197847182444, Санкт-Петербург,
  зарегистрировано 6 сентября 2019 года (совпадает со статьей: «создано в
  2019 году»). Акционеров АО реестр не раскрывает (card_parties.md, «У АО
  акционеров реестр не показывает») — версия с Павлом Пригожиным остается
  неподтвержденной оговоркой в eco.context, как и было у второго чтения; это
  правкой не трогается.

ВАЖНО О ЧУВСТВИТЕЛЬНОСТИ. Евгений Пригожин, упомянутый в статье как погибший
основатель ГК «Конкорд» и ЧВК «Вагнер», — это Евгений Викторович Пригожин,
учредитель ЧВК «Вагнер» (figурирует в санкционных списках США/ЕС/Великобритании
как учредитель и бенефициар ЧВК «Вагнер»; погиб в авиакатастрофе в августе
2023 года). Статья называет его сына Павла Пригожина лишь версией покупателя
по словам двух неназванных источников «Делового Петербурга» — не фактом;
карточка эту оговорку уже несет в eco.context с атрибуцией и без усиления.
Прямой правкой этот файл версию с Пригожиным не трогает и не проверяет лично
Павла Пригожина по санкционным спискам — он сам не назван формальным
покупателем ни в одном источнике (формальный покупатель — АО «Деловые связи»,
чьи акционеры реестром не раскрыты), так что `pipeline/sanctions_match.py` по
имени Павла Пригожина сверять нечего: в базе как сторона сделки стоит
юрлицо, а не человек.

Без ключа — сухой прогон (только печать), запись — `--write`.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
REGISTRY_PY = os.path.join(ROOT, 'pipeline', 'fns_registry.py')

CARD_ID = 'g00f36bab'
TARGET_ID = 'gcb6d7b28'   # ООО «Аппетит»
BUYER_ID = 'g5c2aeb3b'    # АО «Деловые связи»

TARGET_HIST_URL = ('https://datanewton.ru/api/v2/history?ogrn=1247800072740'
                    '&startDate=2000-01-01&attributes=OWNERS')

TARGET_INN, TARGET_OGRN = '7813681528', '1247800072740'
BUYER_INN, BUYER_OGRN = '7805755960', '1197847182444'


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    base = json.loads(raw)
    cards = {d['id']: d for d in base['deals']}
    comps = base['companies']
    card = cards[CARD_ID]

    assert card.get('date') == '2026', card.get('date')
    assert card.get('date_basis') is None, card.get('date_basis')
    assert card.get('seller') == 'Антон Дулов', card.get('seller')
    assert comps[TARGET_ID].get('inn') is None, comps[TARGET_ID]
    assert comps[BUYER_ID].get('inn') is None, comps[BUYER_ID]

    card['date'] = '2026-06-25'
    card['date_basis'] = 'registry'
    card['seller'] = 'Антон Дулов и Вадим Магомедов'
    pe_seller = card.setdefault('party_evidence', {}).setdefault('seller', [])
    pe_seller.append({'value': 'Вадим Магомедов', 'field': 'seller', 'method': 'registry_owner_history',
                      'url': TARGET_HIST_URL})
    # Первая запись (Дулов) была подтверждена заголовком статьи; оставляем ее
    # методом как есть и дописываем, чем подтверждена дата/вторая доля.
    for row in pe_seller:
        if row.get('value') == 'Антон Дулов' and 'ogrn' not in row:
            row['note'] = 'доля на дату сделки (82,8%) и выход из участников — тот же реестр, что у Магомедова'
    src = card.setdefault('src', [])
    if not any(u == TARGET_HIST_URL for _, u in (s for s in src if len(s) > 1)):
        src.append(['ЕГРЮЛ (datanewton): история участников ООО «Аппетит»', TARGET_HIST_URL])

    notes = card.setdefault('accepted_notes', {})
    no_inn = notes.get('no_inn') or {}
    no_inn.pop('buyer', None)
    no_inn.pop('target', None)
    if no_inn:
        notes['no_inn'] = no_inn
    else:
        notes.pop('no_inn', None)
    no_profile = notes.get('no_profile') or {}
    if 'seller' in no_profile:
        no_profile['seller'] = (
            'продавцы — физические лица (Антон Дулов 82,8% и Вадим Магомедов 17,2% на дату сделки), '
            'профиль компании не заводится. История участников ООО «Аппетит» проверена по ОГРН '
            '1247800072740 (datanewton): 25 июня 2026 года оба вышли, 100% получило АО «Деловые связи».')
        notes['no_profile'] = no_profile

    comps[TARGET_ID]['inn'] = TARGET_INN
    comps[TARGET_ID]['ogrn'] = TARGET_OGRN
    comps[TARGET_ID]['legal_short'] = 'ООО «Аппетит»'
    comps[BUYER_ID]['inn'] = BUYER_INN
    comps[BUYER_ID]['ogrn'] = BUYER_OGRN
    comps[BUYER_ID]['legal_short'] = 'АО «Деловые связи»'

    print('%s: date -> %s (%s), seller -> %s' % (CARD_ID, card['date'], card['date_basis'], card['seller']))
    print('%s: inn -> %s, ogrn -> %s' % (TARGET_ID, TARGET_INN, TARGET_OGRN))
    print('%s: inn -> %s, ogrn -> %s' % (BUYER_ID, BUYER_INN, BUYER_OGRN))

    if write:
        open(DATA, 'w', encoding='utf-8').write(
            json.dumps(base, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))
        print('deals_promoted.json записан')

    # Реестр решений «профиль -> юрлицо», тем же блоком, что ставит приемка
    # (pipeline/ingest/accept_card.py:add_registry_row), но текстом сюда —
    # ИНН найден прямым поиском в datanewton, а не автосовпадением имени.
    reg_src = open(REGISTRY_PY, encoding='utf-8').read()
    marker = "\n\ndef by_company_id() -> dict[str, dict]:"
    assert marker in reg_src, 'не нашли конец REGISTRY в fns_registry.py'
    block = '\n'.join([
        '', '',
        '# Правка карточки %s по реестру — 2026-11-20 (pipeline/archive/2026-11/'
        'enrich_appetit_delovye_svyazi_2026_11_20.py).' % CARD_ID,
        'REGISTRY += [',
        "    {\"company_id\": %r, \"decision\": \"confirmed\", \"inn\": %r," % (TARGET_ID, TARGET_INN),
        "     \"reason\": 'ООО «Аппетит» (операционное юрлицо сети Uppetit, Санкт-Петербург) найдено прямым "
        "поиском в datanewton по названию и городу; ОГРН 1247800072740 подтвержден историей участников — "
        "25.06.2026 100% перешло от Дулова (82,8%) и Магомедова (17,2%) к АО «Деловые связи», как в карточке.',",
        "     \"date\": '2026-11-20'},",
        "    {\"company_id\": %r, \"decision\": \"confirmed\", \"inn\": %r," % (BUYER_ID, BUYER_INN),
        "     \"reason\": 'АО «Деловые связи» найдено прямым поиском в datanewton по названию и городу; ОГРН "
        "1197847182444, дата регистрации 06.09.2019 совпадает со статьей («создано в 2019 году»); история "
        "участников ООО «Аппетит» показывает именно это АО как получателя 100% на 25.06.2026.',",
        "     \"date\": '2026-11-20'},",
        ']',
    ])
    if write:
        open(REGISTRY_PY, 'w', encoding='utf-8').write(reg_src.replace(marker, block + marker, 1))
        print('fns_registry.py записан')
    else:
        print('--- fns_registry.py (сухой прогон, не записано) ---')
        print(block)


if __name__ == '__main__':
    main('--write' in sys.argv)
