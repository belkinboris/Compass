# -*- coding: utf-8 -*-
"""Новая карточка: Российская Федерация купила у Strabag Real Estate бизнес-центр
«Ленинский, 119» (через ООО «Ранита»), 23 ноября 2026.

ЗАЧЕМ. Два черновика притока (d13280516 — Ведомости, d95292829 — Telegram, ОДНА
сделка с двух источников) ушли в `data/inbox/hold/2026-11-23.json` механическим
фильтром: «не установлен предмет сделки» (заголовок Ведомостей не называет, что
продают) и «не видно связи с российским рынком — латиница» (Strabag/Ранита по
имени не дают кириллического признака). По смыслу это крупная, настоящая и
закрытая сделка на российском рынке недвижимости (объект в Москве, покупатель —
российское государство, цена 2,39 млрд ₽) — фильтр ошибся, решение по смыслу:
создаем карточку руками, минуя автоматические ворота `promote.py`, и кладем её
в `static/data/pending.json`, как обычно делают прошедшие ворота черновики (шаг 5
`routines/intake.md`). Дальше карточка идет по тому же пути: поиск источников,
чтение и запись (сделано этим скриптом + `write_card.py` для прозы), а приёмку
(`accept_card.py`) и второе чтение (`second_reading.py`) делают отдельные свежие
агенты — не сам сборщик карточки (правило «никогда не самосертифицировать»).

Тип сделки — «M&A», не «Временное управление»: оба источника пишут о прямой
купле-продаже за деньги («приобрела», «выкупила», сумма 2,39 млрд ₽, продавец
ООО «Ранита»), а не о передаче по указу президента без смены собственника.
Указа или решения о временном управлении в найденных источниках нет.

ИСТОЧНИКИ:
  Ведомости, https://www.vedomosti.ru/realty/articles/2026/11/23/1414126-shtab-kvartira-strabag-pereshla
  Telegram,  https://t.me/dealsma/7596 (сумма сделки)

ИНН/ОГРН продавца (ООО «Ранита») — проверены по datanewton.ru/search?query=Ранита
(обычный браузерный User-Agent): запись с генеральным директором «Ортенберг
Александр Вадимович» — то же имя, что в статье Ведомостей («генеральному
директору ООО «Ранита» Александру Ортенбергу»), ИНН 7706563424, ОГРН
1047797063687, адрес Москва, ОКВЭД 68.20.29 (аренда и управление недвижимым
имуществом) — совпадает с профилем деятельности из статьи. Других «Ранита» с
таким директором на странице поиска нет.

Запуск:
    python3 pipeline/fix_add_strabag_ranita_card_2026_11_23.py            # сухой прогон
    python3 pipeline/fix_add_strabag_ranita_card_2026_11_23.py --write    # запись
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

VEDOMOSTI_URL = 'https://www.vedomosti.ru/realty/articles/2026/11/23/1414126-shtab-kvartira-strabag-pereshla'
TELEGRAM_URL = 'https://t.me/dealsma/7596'


def gid(key):
    return 'g' + hashlib.sha1(key.encode('utf-8')).hexdigest()[:8]


DEAL_ID = gid('strabag-ranita-leninsky-119-2026-11-06')
SELLER_ID = gid('company-ranita-strabag-7706563424')
ASSET_ID = gid('asset-biznes-centr-leninsky-119-moscow')


def build_companies():
    seller = {
        'name': 'ООО «Ранита»',
        'ind': 'Недвижимость',
        'desc': ('Российская компания, управляющая коммерческой недвижимостью в Москве; '
                 'принадлежит австрийской Strabag Real Estate. До продажи владела '
                 'бизнес-центром «Ленинский, 119» на Ленинском проспекте.'),
        'kpi': [],
        'legal_short': 'ООО «Ранита»',
        'inn': '7706563424',
        'ogrn': '1047797063687',
    }
    asset = {
        'name': 'Бизнес-центр «Ленинский, 119»',
        'ind': 'Недвижимость',
        'desc': ('Бизнес-центр на юго-западе Москвы (около 25 100 кв. м), построен '
                  'австрийским девелопером Raiffeisen Evolution в 2013 году; до ноября '
                  '2026 года принадлежал ООО «Ранита» (Strabag Real Estate).'),
        'kpi': [],
        'asset': True,
    }
    return seller, asset


def build_card():
    card = {
        'id': DEAL_ID,
        'date': '2026-11-06',
        'title': 'Российская Федерация купила у Strabag Real Estate бизнес-центр «Ленинский, 119»',
        'ind': 'Недвижимость',
        'type': 'M&A',
        'kind': 'acquisition',
        'status': 'Закрыта',
        'src': [
            ['Ведомости', VEDOMOSTI_URL],
            ['@dealsma (Telegram)', TELEGRAM_URL],
        ],
        'from_ingest': True,
        # Текст eco/law пишется отдельно по фактам (`write_card.py`, WRITING_BRIEF.md),
        # не этим скриптом — здесь только структурные поля и заглушки.
        'eco': {
            'sum': '2,39 млрд ₽',
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
        'sum': '2,39 млрд ₽',
        'buyer_name': 'Российская Федерация',
        'seller': 'ООО «Ранита»',
        'seller_id': SELLER_ID,
        'seller_src': 'text',
        'asset': 'Бизнес-центр «Ленинский, 119»',
        'target': ASSET_ID,
        'party_evidence': {
            'buyer': [{
                'value': 'Российская Федерация', 'field': 'buyer_name',
                'method': 'manual_source_review', 'url': VEDOMOSTI_URL,
            }],
            'target': [{
                'value': 'Бизнес-центр «Ленинский, 119»', 'field': 'asset',
                'method': 'manual_source_review', 'url': VEDOMOSTI_URL,
            }],
            'seller': [{
                'value': 'ООО «Ранита»', 'field': 'seller',
                'method': 'manual_source_review', 'url': VEDOMOSTI_URL,
            }],
        },
        'pending_since': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'from_raw': {'draft_id': 'd13280516', 'title': 'Московская штаб-квартира австрийской Strabag '
                                                        'перешла в собственность государства'},
        'accepted_notes': {
            'no_profile': {
                'buyer': ('Покупатель — само государство (Российская Федерация), не юридическое лицо '
                          'в обычном смысле; орган, оформивший сделку (Росимущество?), в прочитанных '
                          'источниках не назван — запрос в Росимущество остался без ответа (Ведомости).'),
            },
            'searched': ('Ведомости 23.11.2026 (https://www.vedomosti.ru/realty/articles/2026/11/23/'
                          '1414126-shtab-kvartira-strabag-pereshla) и Telegram-канал @dealsma 23.11.2026 '
                          '(https://t.me/dealsma/7596) — один и тот же объект, два источника слиты в одну '
                          'карточку (черновики притока d13280516 и d95292829, оба в hold 23.11.2026: '
                          '«не установлен предмет сделки» и «не видно связи с российским рынком — '
                          'латиница» — решение по смыслу: это сделка на российском рынке недвижимости, '
                          'отвод снят вручную). ИНН/ОГРН продавца — datanewton.ru/search?query=Ранита, '
                          'запись с директором Ортенберг А.В., совпадающим с именем в статье Ведомостей. '
                          'WebSearch по указу о временном управлении/изъятии для Strabag/«Ранита» ничего '
                          'не нашел — оба источника описывают обычную купле-продажу за деньги, тип '
                          '«M&A» сохранен.'),
        },
    }
    return card


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    pending = json.load(open(PENDING, encoding='utf-8')) if os.path.exists(PENDING) else {'cards': []}

    assert DEAL_ID not in {c['id'] for c in pending['cards']}, 'карточка уже есть в pending.json'
    assert DEAL_ID not in {d['id'] for d in data['deals']}, 'карточка уже есть в базе'
    assert SELLER_ID not in data['companies'], 'профиль продавца уже существует'
    assert ASSET_ID not in data['companies'], 'профиль актива уже существует'

    seller, asset = build_companies()
    card = build_card()

    import tag_themes
    themes = tag_themes.add_themes(card)

    print('Карточка: %s' % card['id'])
    print('  title: %s' % card['title'])
    print('  seller profile: %s -> %s' % (SELLER_ID, seller['name']))
    print('  asset profile:  %s -> %s' % (ASSET_ID, asset['name']))
    print('  themes added: %s' % themes)

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    data = json.load(open(DATA, encoding='utf-8'))  # перечитать прямо перед записью
    pending = json.load(open(PENDING, encoding='utf-8')) if os.path.exists(PENDING) else {'cards': []}
    assert SELLER_ID not in data['companies']
    assert ASSET_ID not in data['companies']
    assert DEAL_ID not in {c['id'] for c in pending['cards']}
    data['companies'][SELLER_ID] = seller
    data['companies'][ASSET_ID] = asset
    pending['cards'].append(card)
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО: 2 профиля, 1 карточка в pending.json')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
