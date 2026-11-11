# -*- coding: utf-8 -*-
"""«Совладельцы «Адаманта» купили доли в двух пышечных сети Ginza Project» (g1c060772):
профили купленных обществ, ИНН в реестре ФНС, дата по ЕГРЮЛ.

ПОЧЕМУ. Карточка вышла без профилей предмета и без ИНН: приток записал «ИНН не
нашли» после двух веб-поисков по имени, хотя правило (docs/company_data.md, «ИНН
ищется и в интернете») требует искать минимум в пяти источниках. Без ИНН на
сайте нет отчетности ФНС, а «Анализ Компаса» считал цену по выручке только
одной пышечной из текста карточки (18,5 млн ₽) как будто за всю сделку.

ЧТО НАШЛИ (11 ноября 2026):
  ООО «Пышечка на Грибоедова» — ИНН 7838131935, ОГРН 1257800061243;
  ООО «Пышечка №1»            — ИНН 7801723854, ОГРН 1237800063313.
Источники перечислены в причине записи реестра (SOURCES ниже). Контрольная
сумма обоих ИНН сходится; выручка и прибыль 2025 года по ГИР БО совпадают со
статьей «Делового Петербурга» до тысячи рублей.

ПОЧЕМУ ДВА ПРОФИЛЯ, А НЕ ЛОТ. Лот (`lot: true`, решение реестра `lot`) прячет
отчетность ФНС: блок ФНС у лота не рисуется (app/fns.py, `hidden = decision in
("person", "lot")`), и оценке цены не на что опереться. Здесь не пакет одного
продавца, а две покупки у двух разных владелиц с разными долями: у каждого
общества свой ИНН и своя отчетность. Карточка уже умеет два профиля предмета —
`target` и `asset_id` (так стоит Wildberries/Russ, gf424fa11); вкладка
«Финансы» показывает отчетность обоих (`finParties` в static/index.html).
`target` — «Пышечка №1» (выручка вдвое больше), `asset_id` — «Пышечка на
Грибоедова».

ДАТА. История участников ЕГРЮЛ (Датаньютон, обе компании) записала смену
участников 6 ноября 2026 — день вместо голого «2026», `date_basis: registry`.

    python3 pipeline/archive/2026-11/pyshechka_targets_g1c060772_2026_11_11.py [--write]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402
import fns_registry  # noqa: E402
import accept_card  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
REG = os.path.join(ROOT, 'pipeline', 'fns_registry.py')
DEAL = 'g1c060772'
DAY = '2026-11-11'
ARTICLE = 'https://www.dp.ru/a/2026/11/10/sovladelci-adamanta-vikupili'

GRIB = {
    'name': 'Пышечка на Грибоедова', 'legal': 'ООО «Пышечка на Грибоедова»',
    'inn': '7838131935', 'ogrn': '1257800061243',
    'desc': ('Пышечная на канале Грибоедова в Петербурге, работает под брендом ресторанного холдинга '
             'Ginza Project; общество зарегистрировано в июле 2025 года. Юрлицо — ООО «Пышечка на Грибоедова».'),
    'keys': ['пышечка на грибоедова', 'пышечки на грибоедова'],
    'history': ('https://datanewton.ru/api/v2/history?ogrn=1257800061243&startDate=2000-01-01&attributes=OWNERS'),
}
NO1 = {
    'name': 'Пышечка №1', 'legal': 'ООО «Пышечка №1»',
    'inn': '7801723854', 'ogrn': '1237800063313',
    'desc': ('Пышечная в Петербурге, работает под брендом ресторанного холдинга Ginza Project; общество '
             'зарегистрировано в мае 2023 года. Юрлицо — ООО «Пышечка №1».'),
    'keys': ['пышечка №1', 'пышечки №1'],
    'history': ('https://datanewton.ru/api/v2/history?ogrn=1237800063313&startDate=2000-01-01&attributes=OWNERS'),
}

SOURCES = {
    '7838131935': (
        'Предмет сделки g1c060772 (дп.ру, 10.11.2026). ООО «Пышечка на Грибоедова», ИНН 7838131935, ОГРН '
        '1257800061243, ОКВЭД «Деятельность ресторанов и услуги по доставке продуктов питания». Совпало в '
        'независимых источниках: (1) поиск Датаньютона по имени (datanewton.ru/search) — ИНН и ОГРН, '
        'регистрация в июле 2025 года, как в статье; (2) СПАРК-Интерфакс, поиск по ИНН '
        '(spark-interfax.ru/search?Query=7838131935) — то же имя и ОГРН, адрес наб. канала Грибоедова, '
        '56-58, гендиректор Наталья Бондарчук — продавец по статье; (3) история участников ЕГРЮЛ на '
        'Датаньютоне по ОГРН (api/v2/history, OWNERS) — запись 06.11.2026: Бондарчук Н. А. 100% вышла, '
        'вошли Баженов М. В. 45%, Гуревич Е. М. 45%, Галдава А. Б. 10% — состав и доли как в статье; '
        '(4) ГИР БО (API-ФНС, метод bo) — выручка 2025 года 18,49 млн ₽, чистая прибыль 433 тыс. ₽, как в '
        'статье. Контрольная сумма ИНН сходится. Искали еще: веб-поиск по самому ИНН (ни одной карточки '
        'в выдаче), saby.ru/sbis.ru, egrul.nalog.ru (сброс соединения из контейнера), tbank.ru '
        '(ошибка сертификата из контейнера), companies.rbc.ru (401).'),
    '7801723854': (
        'Предмет сделки g1c060772 (дп.ру, 10.11.2026). ООО «Пышечка №1», ИНН 7801723854, ОГРН '
        '1237800063313, ОКВЭД «Деятельность ресторанов и услуги по доставке продуктов питания». Совпало в '
        'независимых источниках: (1) поиск Датаньютона по имени и по ИНН (datanewton.ru/search) — ИНН и '
        'ОГРН, регистрация 31.05.2023, как в статье («с мая 2023 года»), руководитель Абдрахманова А. В.; '
        '(2) СПАРК-Интерфакс, поиск по ИНН (spark-interfax.ru/search?Query=7801723854) — то же имя и ОГРН, '
        'адрес Большой пр. В.О., 19, гендиректор Алла Абдрахманова — продавец по статье; (3) история '
        'участников ЕГРЮЛ на Датаньютоне по ОГРН (api/v2/history, OWNERS) — запись 06.11.2026: '
        'Абдрахманова А. В. 100% вышла, вошли Баженов М. В. 32,5%, Гуревич Е. М. 32,5%, Дмитриев В. В. 25%, '
        'Иваненко М. Д. 10% — состав и доли как в статье; (4) ГИР БО (API-ФНС, метод bo) — выручка 2025 '
        'года 38,9 млн ₽ (2024 — 25,8 млн ₽, рост на половину), чистая прибыль 442 тыс. ₽, как в статье. '
        'Контрольная сумма ИНН сходится. Искали еще: веб-поиск по самому ИНН (ни одной карточки в выдаче), '
        'saby.ru/sbis.ru, egrul.nalog.ru (сброс соединения из контейнера), tbank.ru (ошибка сертификата '
        'из контейнера), companies.rbc.ru (401).'),
}

OLD_TARGET_NOTE_START = 'предмет — доли двух ООО, профиль не заводится'
DATE_QUOTE = ('ЕГРЮЛ, история участников (Датаньютон, OWNERS), запись от 2026-11-06: ООО «Пышечка на '
              'Грибоедова» — БОНДАРЧУК НАТАЛЬЯ АНАТОЛЬЕВНА 100% удалена, добавлены БАЖЕНОВ МИХАИЛ ВИКТОРОВИЧ '
              '45%, ГУРЕВИЧ ЕВГЕНИЙ МИХАЙЛОВИЧ 45%, ГАЛДАВА АВТАНДИЛ БИЧИКОЕВИЧ 10%; ООО «Пышечка №1» — '
              'АБДРАХМАНОВА АЛЛА ВИКТОРОВНА 100% удалена, добавлены БАЖЕНОВ 32,5%, ГУРЕВИЧ 32,5%, ДМИТРИЕВ '
              'ВАДИМ ВАДИМОВИЧ 25%, ИВАНЕНКО МАРИНА ДЖЕМАЛИЕВНА 10%.')


def apply(data, registry):
    comps, mk = data['companies'], data.setdefault('match_keys', {})
    card = next(x for x in data['deals'] if x['id'] == DEAL)
    # Старые значения — ровно те, что были на карточке при выходе поста.
    assert card['title'] == 'Совладельцы «Адаманта» купили доли в двух пышечных сети Ginza Project'
    assert not card.get('target') and not card.get('asset_id'), (card.get('target'), card.get('asset_id'))
    assert card['date'] == '2026' and not card.get('date_basis'), (card['date'], card.get('date_basis'))
    assert card['events'][0]['date'] == '2026' and card['events'][0]['kind'] == 'closed'
    assert card['accepted_notes']['no_profile']['target'].startswith(OLD_TARGET_NOTE_START)
    assert 'ООО «Пышечка на Грибоедова»' in card['asset'] and 'ООО «Пышечка №1»' in card['asset']
    reg_ids = {r['company_id'] for r in registry}
    reg_inns = {r.get('inn') for r in registry if r.get('inn')}
    names = {str(c.get('name') or '').lower() for c in comps.values()}
    ids = {}
    for p in (NO1, GRIB):
        assert fns_registry.inn_is_valid(p['inn']), p['inn']
        assert p['inn'] not in reg_inns, 'ИНН %s уже в реестре' % p['inn']
        assert p['name'].lower() not in names, 'профиль %s уже есть' % p['name']
        cid = accept_card._new_profile_id(data, p['name'])
        assert cid not in reg_ids
        comps[cid] = {'name': p['name'], 'ind': card['ind'], 'desc': p['desc'], 'kpi': [],
                      'legal_short': p['legal']}
        mk[cid] = list(p['keys'])
        ids[p['inn']] = cid
    card['target'] = ids[NO1['inn']]
    card['asset_id'] = ids[GRIB['inn']]
    # Дата — по ЕГРЮЛ: обе смены участников записаны 6 ноября 2026 года.
    card['date'] = '2026-11-06'
    card['date_basis'] = 'registry'
    card['events'][0]['date'] = '2026-11-06'
    fact_edit_guard.log(card, 'date', '2026-11-06', DATE_QUOTE, NO1['history'], 'pyshechka_targets_g1c060772_2026_11_11', DAY)
    notes = card['accepted_notes']
    del notes['no_profile']['target']
    notes['no_profile']['seller'] = notes['no_profile']['seller'].replace(
        ' — datanewton не требуется', ' — сверена с историей участников ЕГРЮЛ (Датаньютон, 06.11.2026)')
    notes.setdefault('searched', []).extend([
        'Датаньютон: поиск по имени и ИНН, история участников по ОГРН 1257800061243 и 1237800063313',
        'СПАРК-Интерфакс: поиск по ИНН 7838131935 и 7801723854',
        'ГИР БО (API-ФНС): отчетность 2025 года обоих обществ совпала со статьей',
        'веб-поиск по ИНН; saby.ru, egrul.nalog.ru, tbank.ru, companies.rbc.ru — из контейнера недоступны',
    ])
    rows = [{'company_id': ids[p['inn']], 'decision': 'confirmed', 'inn': p['inn'],
             'reason': SOURCES[p['inn']], 'date': DAY} for p in (NO1, GRIB)]
    return card, rows


def registry_block(rows):
    lines = ['', '', '# Предмет сделки g1c060772 (две пышечные Ginza Project) — %s '
             '(pipeline/archive/2026-11/pyshechka_targets_g1c060772_2026_11_11.py).' % DAY, 'REGISTRY += [']
    for r in rows:
        lines += ['    {"company_id": %r, "decision": "confirmed", "inn": %r,' % (r['company_id'], r['inn']),
                  '     "reason": %r,' % r['reason'],
                  '     "date": %r},' % r['date']]
    lines.append(']')
    return '\n'.join(lines)


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    reg_src = open(REG, encoding='utf-8').read()
    old, data = json.loads(raw), json.loads(raw)
    card, rows = apply(data, list(fns_registry.REGISTRY))
    print('target  ->', card['target'], data['companies'][card['target']]['name'])
    print('asset_id->', card['asset_id'], data['companies'][card['asset_id']]['name'])
    print('date    ->', card['date'], card['date_basis'])
    for r in rows:
        print('реестр  +', r['company_id'], r['inn'])
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    bad = fact_edit_guard.unbacked(old, data)
    assert not bad, bad
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    # База перечитывается прямо перед записью: чужой пуш между чтением и записью не стирается.
    fresh_raw = open(DATA, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    apply(fresh, list(fns_registry.REGISTRY))
    assert open(REG, encoding='utf-8').read() == reg_src, 'реестр изменился во время прогона — перезапустите'
    marker = "\n\ndef by_company_id() -> dict[str, dict]:"
    assert marker in reg_src
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
    with open(REG, 'w', encoding='utf-8') as f:
        f.write(reg_src.replace(marker, registry_block(rows) + marker, 1))
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
