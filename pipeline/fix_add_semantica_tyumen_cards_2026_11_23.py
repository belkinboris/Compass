# -*- coding: utf-8 -*-
"""Две новые карточки по решению владельца «это сделка — в работу» (консоль,
23 ноября 2026, draft_id d86170319 и d37090047 — `approve.fetch_decisions()`
подтвердил verdict="take" у обоих).

ФРИИ проинвестировал в проект Semantica AI (CNews, 23 ноября 2026): сумма и
доля не раскрыты, профиля компании-цели нет — по открытым каталогам
(workspace.ru, startpack.ru) Semantica AI ведется как ИП Антона Коченевского,
без юрлица; ИНН/ОГРНИП через веб-поиск не нашелся (ЕГРИП egrul.nalog.ru
отсюда не открывается).

Завод по производству скотча в Тюменской области выставлен на продажу за
13 млн рублей (URA.RU, 23 ноября 2026): объявление на площадке бесплатных
объявлений, имя продавца и юрлицо не названы, покупателя еще нет — честная
пустота с обеих сторон, как у `gc13b1fc9` (участок бывшего мясокомбината
«Красноармейский», 21 ноября 2026).

Структурные поля — этим скриптом (минуя `promote.py`, как шаг 5
`routines/intake.md` для черновиков, отклоненных воротами по формальным
причинам: заголовок d86170319 — без глагола-предиката, d37090047 —
«не установлен предмет сделки»); прозу (`eco.*`) дописывает FIXES-партия
`pipeline/ingest/fixes/written_2026_11_23_semantica_tyumen.py` через
`review.py --write`. Приемку и второе чтение делают отдельные свежие агенты
(правило «никогда не самосертифицировать»).

ИСТОЧНИКИ:
  CNews, https://www.cnews.ru/news/line/2026-11-23_semantica_ai_privlekla_investitsii
  URA.RU, https://ura.news/news/1053146518

Запуск:
    python3 pipeline/fix_add_semantica_tyumen_cards_2026_11_23.py            # сухой прогон
    python3 pipeline/fix_add_semantica_tyumen_cards_2026_11_23.py --write    # запись
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

CNEWS_URL = 'https://www.cnews.ru/news/line/2026-11-23_semantica_ai_privlekla_investitsii'
URA_URL = 'https://ura.news/news/1053146518'


def gid(key):
    return 'g' + hashlib.sha1(key.encode('utf-8')).hexdigest()[:8]


SEMANTICA_ID = gid('frii-semantica-ai-investment-2026-11-23')
TYUMEN_ID = gid('tyumen-scotch-tape-factory-sale-2026-11-23')

FRII_ID = 'g1ea0e717'  # уже есть в data['companies']


def build_semantica_card():
    return {
        'id': SEMANTICA_ID,
        'date': '2026-11-23',
        'title': 'ФРИИ проинвестировал в проект Semantica AI',
        'ind': 'ИТ и интернет',
        'type': 'Инвестиция',
        'kind': 'financing',
        'status': 'Закрыта',
        'src': [['CNews', CNEWS_URL]],
        'from_ingest': True,
        'eco': {
            'sum': '—',
            'share': '—',
            'val': '—',
            'target_fin': '—',
            'fin': '—',
            'rationale': '—',
            'context': '—',
            'finadv': '—',
        },
        'law': {
            'struct': '—',
            'appr': '—',
            'adv': [],
            'terms': '—',
        },
        'buyer': FRII_ID,
        'asset': 'Semantica AI',
        'party_evidence': {
            'buyer': [{
                'value': 'ФРИИ', 'field': 'buyer',
                'method': 'manual_source_review', 'url': CNEWS_URL,
            }],
            'target': [{
                'value': 'Semantica AI', 'field': 'asset',
                'method': 'manual_source_review', 'url': CNEWS_URL,
            }],
        },
        'pending_since': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'from_raw': {'draft_id': 'd86170319', 'title': 'Semantica AI привлекла инвестиции ФРИИ'},
        'accepted_notes': {
            'no_profile': {
                'target': ('Semantica AI (ai-semantica.com) по открытым каталогам (workspace.ru, '
                            'startpack.ru) ведется как ИП Антона Коченевского, без юридического '
                            'лица; ИНН/ОГРНИП веб-поиском не нашелся (ЕГРИП egrul.nalog.ru отсюда '
                            'не открывается напрямую) — профиль компании не заводим, предмет '
                            'обозначен текстом в asset.'),
            },
            'searched': ('CNews, 23.11.2026 (первоисточник, прочитан целиком через fetch_article_texts.py); '
                          'WebSearch «Семантика АИ ИНН ОГРН ai-semantica.com» и «ИП Коченевский Антон '
                          'Владимирович ОГРНИП ИНН» — без результата по реестрам; workspace.ru/contractors/'
                          'semantica-ai/ и startpack.ru/application/semantica-ai прочитаны (WebFetch) — '
                          'последний прямо называет вендора «ИП Коченевский А.В.», без ИНН/ОГРНИП; '
                          'ai-semantica.com/offer отдает только заголовок (страница на JS), требований '
                          'реквизитов не нашлось.'),
        },
    }


def build_tyumen_card():
    return {
        'id': TYUMEN_ID,
        'date': '2026-11-23',
        'title': 'Завод по производству скотча в Тюменской области выставлен на продажу за 13 млн рублей',
        'ind': 'Потребительские товары',
        'type': 'M&A',
        'status': 'Обсуждается',
        'src': [['URA.RU', URA_URL]],
        'from_ingest': True,
        'eco': {
            'sum': '13 млн ₽',
            'share': '—',
            'val': '—',
            'target_fin': '—',
            'fin': '—',
            'rationale': '—',
            'context': '—',
            'finadv': '—',
        },
        'law': {
            'struct': '—',
            'appr': '—',
            'adv': [],
            'terms': '—',
        },
        'sum': '13 млн ₽',
        'asset': 'Завод по производству скотча в Тюменской области',
        'seller_src': 'text',
        'party_evidence': {
            'target': [{
                'value': 'Завод по производству скотча в Тюменской области', 'field': 'asset',
                'method': 'manual_source_review', 'url': URA_URL,
            }],
        },
        'pending_since': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'from_raw': {'draft_id': 'd37090047',
                     'title': 'В Тюменской области продают крупный завод по производству скотча'},
        'accepted_notes': {
            'no_profile': {
                'seller': ('Продавец — автор объявления на площадке бесплатных объявлений; имя '
                           'человека и название юридического лица в источнике не называются, завод '
                           'не выступает как отдельное юрлицо с публичным именем — честная пустота, '
                           'профиль не заводим.'),
                'buyer': 'объявление о продаже — покупателя еще нет, профиль не заводим.',
            },
            'searched': ('URA.RU, 23.11.2026 (первоисточник, прочитан целиком через '
                          'fetch_article_texts.py) — единственная найденная публикация об этом '
                          'объявлении; второй независимой публикации не искали отдельно, так как сама '
                          'статья описывает анонимное объявление на доске, а не стороны сделки, '
                          'которых можно было бы подтвердить вторым источником.'),
        },
    }


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    pending = json.load(open(PENDING, encoding='utf-8')) if os.path.exists(PENDING) else {'cards': []}

    assert SEMANTICA_ID not in {c['id'] for c in pending['cards']}, 'карточка Semantica AI уже есть в pending.json'
    assert TYUMEN_ID not in {c['id'] for c in pending['cards']}, 'карточка Тюмень уже есть в pending.json'
    assert SEMANTICA_ID not in {d['id'] for d in data['deals']}, 'карточка Semantica AI уже есть в базе'
    assert TYUMEN_ID not in {d['id'] for d in data['deals']}, 'карточка Тюмень уже есть в базе'
    assert FRII_ID in data['companies'], 'профиль ФРИИ должен уже существовать'

    semantica = build_semantica_card()
    tyumen = build_tyumen_card()

    import tag_themes
    themes1 = tag_themes.add_themes(semantica)
    themes2 = tag_themes.add_themes(tyumen)

    print('Карточка: %s' % semantica['id'])
    print('  title: %s' % semantica['title'])
    print('  themes: %s' % themes1)
    print('Карточка: %s' % tyumen['id'])
    print('  title: %s' % tyumen['title'])
    print('  themes: %s' % themes2)

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    data = json.load(open(DATA, encoding='utf-8'))  # перечитать прямо перед записью
    pending = json.load(open(PENDING, encoding='utf-8')) if os.path.exists(PENDING) else {'cards': []}
    assert SEMANTICA_ID not in {c['id'] for c in pending['cards']}
    assert TYUMEN_ID not in {c['id'] for c in pending['cards']}
    pending['cards'].append(semantica)
    pending['cards'].append(tyumen)
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО: 2 карточки в pending.json')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
