# -*- coding: utf-8 -*-
"""Новые карточки по находкам проверки базы G46 (26–27 ноября 2026).

ЧТО БЫЛО. Помощники вычитки G46 (отчеты report_1..4) нашли в прозе уже
опубликованных карточок сделки, у которых своей карточки в базе нет: факт
стоит строкой в «Контексте» или «Структуре» чужой карточки. Каждая проверена
по базе (стороны, предмет, `match_keys`) и по `docs/intake_gates.md`
(объявление без покупателя, торги без итога, перекладка внутри группы — не
сделки). Здесь — только те, что прошли.

ЧТО ДЕЛАЕТ СКРИПТ. Кладет карточку в `static/data/pending.json` со
структурными полями из первоисточника; основания суммы и даты, доля, доп.
источники и проза — партиями FIXES (`pipeline/ingest/fixes/g46new_*.py`)
через `review.py --write` / `write_card.py`; профили сторон — приемкой
(`accept_card.py`). По одной карточке за запуск: `--only <ключ>`.

Цитаты (первоисточники лежат в кэше притока / data/inbox/triage):
  troika   — «Коммерсантъ», 01.04.2026, https://www.kommersant.ru/doc/8553146:
             «Концерн «Энерготехнологии», развивающий магазин мебели и интерьеров
             «Кубатура» в Санкт-Петербурге, заключил сделку с «Кама Капитал» по
             покупке торгцентра «Тройка» общей площадью 152 тыс. кв. м…»
  edison   — ЕГРЮЛ (datanewton, ОГРН 1117746617416): 21.12.2023 100% ООО
             «Эдисонэнерго» — от ООО «ВТБ Индустриальная недвижимость» к ООО
             «Место встречи»; РИА Недвижимость 11.01.2024.
  saturn   — «Ведомости», 10.06.2026: «Фирма Сатурн» победила на торгах РАД
             (1,98 млрд руб.); ЕГРЮЛ (ОГРН 1102650001277): 08.07.2026 100% —
             от Российской Федерации к ООО «ФХ «Фирма Сатурн».
  vsk      — Указ Президента от 24.08.2026 № 601 (rulaws.ru): акции восьми АО —
             имущественным взносом РФ в ППК «Военно-строительная компания».
  praxair  — ЕГРЮЛ (ОГРН 5087746091956): 10.08.2026 100% ООО «Праксэа Рус» — от
             ООО «РусХимАльянс» к ПАО «Куйбышевазот»; Интерфакс 11.08.2026.
  softline — АК&М (отчетность ГК Softline за 2025 год): 20.04.2023 Боровиков
             передал 100% ООО «Алварус Капитал» (ООО «Аталайя»), владеющего 100%
             ПАО «Софтлайн», в ЗПИФ «Аксиома Капитал» под управлением ООО «Тэтис
             Кэпитал»; ComNews и Anti-Malware 07.04.2023.
  moex     — «Ведомости», 01.11.2025: Мосбиржа выкупила у Sezar Group порядка
             30 000 кв. м в башне «Сити-4».
  eurasia  — ЕГРЮЛ (ОГРН 1247700232890): 08.04.2025 доля ООО «Евразия-Логистика»
             в ООО «Евразия Трейдинг» 99% -> 59%, Халилов 30%, Курдюмов 10%;
             «Коммерсантъ», 23.05.2025.
  radish   — E1.RU, 10.11.2026: здание и участок на Радищева, 21 — у ООО
             «Возрождение Екатеринбурга» (учредитель АО «Форум-Групп») с августа
             2026 года по ЕГРН.

Запуск:
    python3 pipeline/fix_add_g46_new_cards_2026_11_27.py                 # сухой, все
    python3 pipeline/fix_add_g46_new_cards_2026_11_27.py --only troika --write
"""
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'ingest'))

DATA = os.path.join(ROOT, '..', 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, '..', 'static', 'data', 'pending.json')


def gid(key):
    return 'g' + hashlib.sha1(key.encode('utf-8')).hexdigest()[:8]


def ev(role, value, field, url):
    return {role: [{'value': value, 'field': field, 'method': 'manual_source_review', 'url': url}]}


K_TROIKA = 'https://www.kommersant.ru/doc/8553146'
NR_TROIKA = 'https://new-retail.ru/novosti/retail/tts_troyka_snova_smenil_sobstvennika/'
DN_EDISON = 'https://datanewton.ru/api/v2/history?ogrn=1117746617416&startDate=2000-01-01&attributes=OWNERS'
RIA_EDISON = 'https://realty.ria.ru/20240111/kinoteatry-1920705314.html'
V_SATURN = 'https://www.vedomosti.ru/business/articles/2026/06/10/1204804-rosimuschestvo-prodalo'
DN_PMK = 'https://datanewton.ru/api/v2/history?ogrn=1102650001277&startDate=2000-01-01&attributes=OWNERS'
UKAZ_601 = 'https://rulaws.ru/president/Ukaz-Prezidenta-RF-ot-24.08.2026-N-601/'
IF_PRAXAIR = 'https://www.interfax.ru/russia/1108610'
DN_PRAXAIR = 'https://datanewton.ru/api/v2/history?ogrn=5087746091956&startDate=2000-01-01&attributes=OWNERS'
AKM_SOFTLINE = 'https://www.akm.ru/news/softlayn_opublikoval_dannye_po_m_a_za_2025_god/'
CN_SOFTLINE = 'https://www.comnews.ru/content/225286/2023-04-07/2023-w14/softline-smenit-vladelca'
V_MOEX = 'https://www.vedomosti.ru/realty/articles/2025/11/01/1151869-mosbirzha-zakrila'
DN_EURASIA = 'https://datanewton.ru/api/v2/history?ogrn=1247700232890&startDate=2000-01-01&attributes=OWNERS'
K_EURASIA = 'https://kommersant.ru/doc/7738635'
E1_RADISH = 'https://www.e1.ru/text/realty/2026/11/10/76748043/'

EMPTY_ECO = {'sum': 'Не раскрыта', 'share': '—', 'val': '—', 'target_fin': '—', 'fin': '—',
             'rationale': '—', 'context': '—', 'finadv': '—'}
EMPTY_LAW = {'struct': '—', 'appr': '—', 'adv': [], 'terms': '—'}

CARDS = {
    'troika': dict(
        key='energotechnologii-troika-kama-capital-2026-04-01',
        date='2026-04-01',
        title='Концерн «Энерготехнологии» купил торговый центр «Тройка» в Москве',
        buyer_name='АО «Концерн «Энерготехнологии»',
        asset='Торговый центр «Тройка» у метро «Красносельская» в Москве',
        seller='«Кама Капитал», ОАО «Первый хладокомбинат» и ООО «Ле Монлид»',
        seller_id='g77f87dcc',
        ind='Недвижимость', type='M&A', status='Закрыта',
        src=[['Коммерсантъ', K_TROIKA], ['New Retail', NR_TROIKA]],
        evidence={**ev('buyer', 'АО «Концерн «Энерготехнологии»', 'buyer_name', K_TROIKA),
                  **ev('seller', 'Инвестиционный холдинг «Кама Капитал»', 'seller', K_TROIKA)},
    ),
    'edison': dict(
        key='mesto-vstrechi-edisonenergo-vtb-2023-12-21',
        date='2023-12-21',
        title='«Место встречи» купило «Эдисонэнерго» у структуры ВТБ',
        buyer_name='ООО «Место встречи»',
        target='gd8a4d27c',
        seller='ООО «ВТБ Индустриальная недвижимость»',
        ind='Недвижимость', type='M&A', status='Закрыта',
        src=[['РИА Недвижимость', RIA_EDISON], ['ЕГРЮЛ: история участников ООО «Эдисонэнерго»', DN_EDISON]],
        evidence={**ev('buyer', 'ООО «Место встречи»', 'buyer_name', RIA_EDISON),
                  **ev('target', 'ООО «Эдисонэнерго»', 'target', RIA_EDISON),
                  **ev('seller', 'ООО «ВТБ Индустриальная недвижимость»', 'seller', RIA_EDISON)},
    ),
    'saturn': dict(
        key='firma-saturn-pyatigorsk-dairy-auction-2026-07-08',
        date='2026-07-08',
        title='«Фирма Сатурн» купила на торгах Пятигорский молочный комбинат',
        buyer_name='ООО «Фермерское хозяйство «Фирма Сатурн»',
        target='gba784476',
        seller='РФ в лице Росимущества',
        seller_id='g9fd82fee',
        ind='Пищепром и напитки', type='Продажа с торгов', status='Закрыта',
        src=[['Ведомости', V_SATURN], ['ЕГРЮЛ: история участников ООО «Пятигорский молочный комбинат»', DN_PMK]],
        evidence={**ev('buyer', 'ФХ «Фирма Сатурн»', 'buyer_name', V_SATURN),
                  **ev('target', 'Пятигорский молочный комбинат', 'target', V_SATURN)},
    ),
    'vsk': dict(
        key='vsk-ukaz-601-pushkarev-shares-2026-08-24',
        date='2026-08-24',
        title='Акции «Якутцемента», «Спасскцемента» и еще шести обществ передадут Военно-строительной компании',
        buyer_name='ППК «Военно-строительная компания»',
        asset='Акции АО «Бетоныч», АО «Восток АйТи», АО «Дальцемент», АО «Дробильно-сортировочный завод», АО ПО «Якутцемент», АО «Спасский комбинат асбестоцементных изделий», АО «Спасскцемент» и МКАО «ПБСД Холдинг»',
        seller='РФ в лице Росимущества',
        seller_id='g9fd82fee',
        ind='Строительство', type='M&A', status='Согласование получено',
        src=[['Указ Президента РФ от 24.08.2026 № 601', UKAZ_601]],
        evidence={**ev('buyer', 'публично-правовая компания «Военно-строительная компания»', 'buyer_name', UKAZ_601)},
    ),
    'praxair': dict(
        key='kuibyshevazot-praxair-rus-ruschemalliance-2026-08-10',
        date='2026-08-10',
        title='«Куйбышевазот» получил «Праксэа Рус» от «РусХимАльянса»',
        buyer_name='ПАО «Куйбышевазот»',
        target='ga1498ed1',
        seller='ООО «РусХимАльянс»',
        ind='Химия и удобрения', type='M&A', status='Закрыта',
        src=[['Интерфакс', IF_PRAXAIR], ['ЕГРЮЛ: история участников ООО «Праксэа Рус»', DN_PRAXAIR],
             ['Право.ру', 'https://pravo.ru/news/265232/']],
        evidence={**ev('buyer', 'ПАО «Куйбышевазот»', 'buyer_name', IF_PRAXAIR),
                  **ev('target', 'ООО «Праксэа Рус»', 'target', IF_PRAXAIR),
                  **ev('seller', 'ООО «РусХимАльянс»', 'seller', IF_PRAXAIR)},
    ),
    'softline': dict(
        key='aksioma-kapital-tetis-softline-borovikov-2023-04-20',
        date='2023-04-20',
        title='Фонд «Аксиома Капитал» купил Softline у основателя',
        buyer_name='ЗПИФ «Аксиома Капитал» под управлением ООО «Тэтис Кэпитал»',
        target='gda7d982b',
        seller='Игорь Боровиков',
        ind='ИТ и интернет', type='M&A', status='Закрыта',
        src=[['АК&М', AKM_SOFTLINE], ['ComNews', CN_SOFTLINE],
             ['Anti-Malware', 'https://www.anti-malware.ru/news/2023-04-07-118537/40902']],
        evidence={**ev('buyer', 'ЗПИФ «Аксиома Капитал» под управлением ООО «Тэтис Кэпитал»', 'buyer_name', AKM_SOFTLINE),
                  **ev('target', 'ПАО «Софтлайн»', 'target', AKM_SOFTLINE),
                  **ev('seller', 'Игорь Боровиков', 'seller', AKM_SOFTLINE)},
    ),
    'moex': dict(
        key='moex-city-4-sezar-group-30000-2025-11-01',
        date='2025-11-01',
        title='Мосбиржа купила у Sezar Group офисы в башне «Сити-4»',
        buyer='gbd9b5fa5',
        asset='Около 30 000 кв. м в башне «Сити-4» (бывшая «Империя II») в «Москва-Сити»',
        seller='Sezar Group',
        seller_id='g4cdff7b7',
        ind='Недвижимость', type='M&A', status='Закрыта',
        src=[['Ведомости', V_MOEX]],
        evidence={**ev('buyer', 'Мосбиржа', 'buyer', V_MOEX),
                  **ev('seller', 'Sezar Group', 'seller', V_MOEX)},
    ),
    'eurasia': dict(
        key='khalilov-kurdyumov-eurasia-trading-40-2025-04-08',
        date='2025-04-08',
        title='Рахман Халилов и Роман Курдюмов получили 40% «Евразия Трейдинг»',
        buyer_name='Рахман Халилов и Роман Курдюмов',
        asset='40% доли в ООО «Евразия Трейдинг»',
        seller='ООО «Евразия-Логистика»',
        seller_id='gbcf4a731',
        ind='Порты и инфраструктура', type='M&A', status='Закрыта',
        src=[['Коммерсантъ', K_EURASIA], ['ЕГРЮЛ: история участников ООО «Евразия Трейдинг»', DN_EURASIA]],
        evidence={**ev('buyer', 'Рахман Халилов', 'buyer_name', K_EURASIA),
                  **ev('seller', 'ООО «Евразия-Логистика»', 'seller', DN_EURASIA)},
    ),
    'radish': dict(
        key='forum-group-vozrozhdenie-radishcheva-21-2026-08',
        date='2026',
        title='«Форум-Групп» купил здание на Радищева, 21 в Екатеринбурге',
        buyer='g32edbd29',
        asset='Здание и участок на улице Радищева, 21 в Екатеринбурге',
        ind='Недвижимость', type='M&A', status='Закрыта',
        src=[['E1.RU', E1_RADISH]],
        evidence={**ev('buyer', 'ООО «Возрождение Екатеринбурга» (учредитель АО «Форум-Групп»)', 'buyer', E1_RADISH)},
    ),
}


def build(key):
    spec = dict(CARDS[key])
    card = {'id': gid(spec.pop('key')), 'date': spec.pop('date'), 'title': spec.pop('title')}
    for f in ('buyer', 'buyer_name', 'target', 'asset', 'seller', 'seller_id'):
        if spec.get(f):
            card[f] = spec[f]
    if card.get('seller'):
        card['seller_src'] = 'text'
    card.update({'ind': spec['ind'], 'type': spec['type'], 'status': spec['status'],
                 'sum': 'Не раскрыта',
                 'src': spec['src'], 'from_ingest': True,
                 'eco': dict(EMPTY_ECO), 'law': dict(EMPTY_LAW, adv=[]),
                 'party_evidence': spec['evidence'],
                 'pending_since': datetime.now(timezone.utc).isoformat(timespec='seconds')})
    if spec['type'] == 'M&A':
        card['kind'] = 'acquisition'
    return card


def main(argv):
    import tag_themes
    write = '--write' in argv
    only = argv[argv.index('--only') + 1] if '--only' in argv else None
    keys = [only] if only else list(CARDS)
    data = json.load(open(DATA, encoding='utf-8'))
    comp = data['companies']
    for key in keys:
        card = build(key)
        for f in ('buyer', 'target', 'seller_id'):
            if card.get(f):
                assert card[f] in comp, (key, f, card[f])
        themes = tag_themes.add_themes(card)
        print('%-8s %s | %s | %s | темы: %s' % (key, card['id'], card['date'], card['title'], themes))
    if not write:
        print('\nСухой прогон. Запись — --only <ключ> --write.')
        return 0
    assert only, 'запись — по одной карточке: --only <ключ>'
    data = json.load(open(DATA, encoding='utf-8'))
    pending = json.load(open(PENDING, encoding='utf-8'))      # перечитать прямо перед записью
    card = build(only)
    tag_themes.add_themes(card)
    assert card['id'] not in {d['id'] for d in data['deals']}, 'карточка уже в базе'
    assert card['id'] not in {c['id'] for c in pending['cards']}, 'карточка уже в pending.json'
    pending['cards'].append(card)
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО: %s в pending.json' % card['id'])
    return 0




# Описание нового профиля, заведенного приемкой этой же партии: первое
# предложение уходит в пост строкой «Покупатель», и описание с именем бренда
# внутри пост печатал вместо имени (check_post: «родовое описание вместо имени»).
DESC_FIXES = {
    'g5502d591': ('Холдинговая компания проекта районных торговых центров «Место встречи» в Москве. Юрлицо — ООО «Место встречи».',
                  'Владелец районных торговых центров на месте бывших московских кинотеатров. Юрлицо — ООО «Место встречи».'),
}


def fix_descs(write):
    data = json.load(open(DATA, encoding='utf-8'))      # перечитать прямо перед записью
    n = 0
    for cid, (old, new) in DESC_FIXES.items():
        cur = data['companies'][cid].get('desc')
        if cur == new:
            continue
        assert cur == old, (cid, cur)
        data['companies'][cid]['desc'] = new
        n += 1
    print('описаний профилей к правке: %d' % n)
    if write and n:
        with open(DATA, 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=1) + '\n')
        print('ЗАПИСАНО')


if __name__ == '__main__':
    if '--descs' in sys.argv:
        fix_descs('--write' in sys.argv)
        sys.exit(0)
    sys.exit(main(sys.argv[1:]))
