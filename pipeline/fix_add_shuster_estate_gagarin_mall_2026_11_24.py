# -*- coding: utf-8 -*-
"""Новая карточка по held-черновику d57328403 (приток, 24 ноября 2026):
механические ворота (`promote.py`) держали его с причиной «не названа ни
одна сторона» — заголовок АБН24 называет покупателя ролью («совладелец
«Маяковского»»), а не именем, и само юрлицо-покупатель в заголовке не
упомянуто вовсе.

СДЕЛКА. В Омске на торгах по банкротству ИП Эдуарда Турманидзе продана
часть бывшего ТК «Летур» (ныне «Гагарин Молл») на улице Гагарина —
нежилое помещение 212,3 кв. м и 1/50 доли земельного участка под
комплексом — за 19,35 млн рублей. Единственным участником и победителем
торгов стало ООО «УК «Центроград», действовавшее в интересах ООО «Шустер
Эстейт» (аренда и управление недвижимостью): конкурентов не было, и лот
ушел по стартовой цене.

КТО СТОРОНА. «Центроград» на торгах формально выступил представителем, а
не собственником: источник прямо пишет, что компания действовала «в
интересах» «Шустер Эстейт» (docs/card_parties.md, «Сторона — прямой
участник именно этого перехода»). Покупателем в карточку идет поэтому
«Шустер Эстейт», а роль «Центрограда» — в `law.struct`.

СВЯЗЬ С «МАЯКОВСКИМ». Заголовок АБН24 (со ссылкой на РБК Омск) называет
покупателя «совладельцем «Маяковского»» без расшифровки. По отдельной
статье «СуперОмск» (https://superomsk.ru/news/168723-..., прочитана целиком,
сохранена `save_source.py`), «Маяковский» — омский кинотеатр, а не
торговый центр: обеими структурами (и «Шустер Эстейт», и «Центроградом»)
управляет Илья Иванов, совладелец этого кинотеатра — единственный
учредитель и руководитель «Шустер Эстейт», в «Центрограде» делит доли с
Михаилом Немчиновым и Петром Варнавским (сын экс-председателя омского
Заксобрания Владимира Варнавского). Связь подтверждена независимо от
заголовка АБН24 — отдельным изданием со своей ссылкой на реестры.

ИНН НАЙДЕНЫ (list-org.com, 24 ноября 2026, см. `accepted_notes.searched`):
«Шустер Эстейт» — 5503199952, «УК «Центроград»» — 5503199938. Профиль
заведен только покупателю («Шустер Эстейт»): «Центроград» — представитель
на торгах, а не сторона сделки, профиль ему не нужен по аналогии с
организатором торгов, который не входит в каталог консультантов
(docs/card_parties.md, «Под вопросом»).

ПРОДАВЕЦ. ИП Эдуард Турманидзе — сын основателя группы «Летур» Левана
Турманидзе; его банкротство (несостоятельным признан Арбитражным судом
Омской области 24 апреля 2026 года, финансовый управляющий — Сергей
Кондаков) и есть основание торгов. Физическое лицо, профиль не заводится.

ИСТОЧНИКИ:
  АБН24 (цитирует РБК Омск) — https://abnews.ru/siberia/news/omsk/2026/11/24/
    v-omske-sovladelecz-mayakovskogo-priobrel-chast-byvshego-letura-za-19-mln-rublej
    (полный текст в кэше data/inbox/raw/2026-11-24-articles.jsonl)
  СуперОмск (итоги торгов, связь с Ивановым/«Маяковским») —
    https://superomsk.ru/news/168723-sovladelets_maiakovskogo_priobrel_chast_byvshego_letura_za_19_mln_rublei/
  СуперОмск (анонс торгов, дата банкротства, финансовый управляющий) —
    https://superomsk.ru/news/167010-chast_byvshego_tk_letur_na_gagarina_vystavili_na_torgi_za_19_35_mln_rublei/
  Оба текста «СуперОмска» сохранены `save_source.py` в
  data/inbox/triage/sources_2026-11-24.json — иначе `review.py` не видит их
  цитат при записи прозы (`written_shuster_estate_2026_11_24.py`).

Запуск:
    python3 pipeline/fix_add_shuster_estate_gagarin_mall_2026_11_24.py            # сухой прогон
    python3 pipeline/fix_add_shuster_estate_gagarin_mall_2026_11_24.py --write    # запись

После записи структурных полей — партия прозы (`eco.context`, `law.struct`)
в `pipeline/ingest/fixes/written_shuster_estate_2026_11_24.py` и
`python3 pipeline/ingest/review.py --write`.
"""
import json
import os
import random
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'ingest'))

DATA = os.path.join(ROOT, '..', 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, '..', 'static', 'data', 'pending.json')

ABNEWS_URL = ('https://abnews.ru/siberia/news/omsk/2026/11/24/'
              'v-omske-sovladelecz-mayakovskogo-priobrel-chast-byvshego-letura-za-19-mln-rublej')
SUPEROMSK_RESULT_URL = ('https://superomsk.ru/news/168723-sovladelets_maiakovskogo_priobrel_chast_'
                         'byvshego_letura_za_19_mln_rublei/')
SUPEROMSK_ANNOUNCE_URL = ('https://superomsk.ru/news/167010-chast_byvshego_tk_letur_na_gagarina_'
                           'vystavili_na_torgi_za_19_35_mln_rublei/')
FROM_RAW_ID = 'd57328403'


def new_id(existing):
    """id того же вида g + 8 hex-знаков, как у остальных карточек и профилей."""
    while True:
        candidate = 'g%08x' % random.getrandbits(32)
        if candidate not in existing:
            return candidate


def build_buyer():
    return {
        'name': 'Шустер Эстейт',
        'ind': 'Недвижимость',
        'desc': ('Омская компания, занимается арендой и управлением недвижимостью. Единственный '
                 'учредитель и руководитель — Илья Иванов, совладелец омского кинотеатра «Маяковский».'),
        'kpi': [],
        'inn': '5503199952',
        'legal_short': 'ООО «Шустер Эстейт»',
        'ownership': [{'name': 'Илья Иванов', 'id': None, 'as_of': '2026-11',
                       'source': ['СуперОмск', SUPEROMSK_RESULT_URL]}],
    }


def build_card(deal_id, buyer_id):
    return {
        'id': deal_id,
        'date': '2026-11-19',
        'date_basis': 'closing',
        'title': '«Шустер Эстейт» купил на торгах часть бывшего ТК «Летур» в Омске за 19,35 млн ₽',
        'ind': 'Недвижимость',
        'type': 'Продажа с торгов',
        'kind': 'acquisition',
        'status': 'Закрыта',
        'src': [['АБН24', ABNEWS_URL], ['СуперОмск', SUPEROMSK_RESULT_URL], ['СуперОмск', SUPEROMSK_ANNOUNCE_URL]],
        'from_ingest': True,
        'from_raw': {'draft_id': FROM_RAW_ID, 'title': 'В Омске совладелец «Маяковского» приобрел часть '
                     'бывшего «Летура» за 19 млн рублей'},
        # test_every_pending_card_has_pending_since: отметка, от которой
        # approve.py считает сутки молчания — карточка, заведенная мимо
        # promote.py, иначе остается без нее.
        'pending_since': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'sum': '19,35 млн ₽',
        'buyer': buyer_id,
        'asset': ('Нежилое помещение 212,3 кв. м и 1/50 доли земельного участка в бывшем ТК «Летур» '
                   '(ныне «Гагарин Молл») на улице Гагарина в Омске'),
        'seller': 'Эдуард Турманидзе (ИП, в банкротстве)',
        'seller_src': 'text',
        'eco': {'sum': '19,35 млн ₽', 'share': '—', 'val': '—', 'target_fin': '—', 'fin': '—',
                'rationale': '—', 'context': '—', 'finadv': '—'},
        'law': {'struct': '—', 'appr': '—', 'adv': [], 'terms': '—'},
        'party_evidence': {
            'buyer': [{'value': 'Шустер Эстейт', 'field': 'buyer',
                       'method': 'manual_source_review', 'url': SUPEROMSK_RESULT_URL}],
            'seller': [{'value': 'Эдуард Турманидзе', 'field': 'seller',
                        'method': 'manual_source_review', 'url': ABNEWS_URL}],
        },
        'accepted_notes': {
            'notes': ('Механические ворота (`promote.py`) держали черновик d57328403: заголовок АБН24 '
                      'называет покупателя ролью («совладелец «Маяковского»»), а не именем, и само '
                      'юрлицо-покупатель («Шустер Эстейт») в заголовке не упомянуто. «УК «Центроград»» '
                      'формально выиграла торги, но источник прямо пишет, что она действовала «в '
                      'интересах» «Шустер Эстейт» — стороной-покупателем в карточку идет поэтому '
                      '«Шустер Эстейт» (docs/card_parties.md, «Сторона — прямой участник именно этого '
                      'перехода»), а роль «Центрограда» на торгах описана в `law.struct`.'),
            'no_profile': {'seller': ('Эдуард Турманидзе — физическое лицо (ИП), профиль компании не '
                                       'заводится.')},
            'searched': ('Связь покупателя с «Маяковским» из заголовка АБН24 проверена отдельным '
                         'изданием: «СуперОмск» (https://superomsk.ru/news/168723-...) пишет, что '
                         '«Маяковский» — омский кинотеатр, а обеими структурами торгов управляет его '
                         'совладелец Илья Иванов — это подтверждение независимо от заголовка-источника, '
                         'со своей ссылкой на открытые реестры. ИНН искал по обеим компаниям в пяти '
                         'местах: WebSearch (несколько запросов, включая прямой поиск по названиям и '
                         'по ИНН) прямых карточек не дал; rusprofile.ru и zachestnyibiznes.ru не '
                         'отдали данные (защита от ботов, под поиском видна капча); checko.ru — 403; '
                         'companies.rbc.ru — 401 на прямой запрос; egrul.org (через egrul.itsoft.ru) — '
                         '403/404 по ИНН напрямую; list-org.com отдал обе карточки по текстовому поиску '
                         '(«Шустер Эстейт», «Центроград») с ИНН/КПП/адресом. Эдуард и Леван Турманидзе, '
                         'Илья Иванов, Михаил Немчинов, Петр Варнавский — физические лица, профили не '
                         'заводятся.'),
        },
    }


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    pending = json.load(open(PENDING, encoding='utf-8')) if os.path.exists(PENDING) else {'cards': []}

    assert not any('Шустер Эстейт' in (c.get('name') or '') for c in data['companies'].values()), \
        'профиль уже есть — скрипт не для повтора'
    assert not any(c.get('id') == FROM_RAW_ID or c.get('from_raw') == FROM_RAW_ID
                   or (isinstance(c.get('from_raw'), dict) and c['from_raw'].get('draft_id') == FROM_RAW_ID)
                   for c in pending['cards']), 'карточка по этому черновику уже заведена'

    all_ids = set(data['companies']) | {d['id'] for d in data['deals']} | {c['id'] for c in pending['cards']}
    buyer_id = new_id(all_ids)
    all_ids.add(buyer_id)
    buyer = build_buyer()
    deal_id = new_id(all_ids)

    card = build_card(deal_id, buyer_id)

    print('Новый профиль:')
    print('  buyer %s  %s  ИНН %s' % (buyer_id, buyer['name'], buyer['inn']))
    print('Новая карточка: %s' % deal_id)
    print('  title: %s' % card['title'])

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    data = json.load(open(DATA, encoding='utf-8'))
    assert buyer_id not in data['companies'], 'коллизия id при повторном чтении — перезапустите скрипт'
    data['companies'][buyer_id] = buyer
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    pending = json.load(open(PENDING, encoding='utf-8')) if os.path.exists(PENDING) else {'cards': []}
    assert not any(c['id'] == deal_id for c in pending['cards']), 'карточка уже есть в pending.json'
    pending['cards'].append(card)
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    print('\nЗАПИСАНО: 1 профиль в deals_promoted.json, 1 карточка в pending.json (id %s).' % deal_id)
    print('Теперь: python3 pipeline/ingest/raw_screen.py --drop %s --reason "..." --write' % FROM_RAW_ID)
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
