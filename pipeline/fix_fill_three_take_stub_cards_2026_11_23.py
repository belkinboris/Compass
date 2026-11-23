# -*- coding: utf-8 -*-
"""Три карточки, родившиеся как пустые заглушки из решений владельца «это
сделка — в работу» (консоль, 23 ноября 2026; approve.py --write механически
создал заглушки в pending.json из сырья с verdict=take):

  g30404c73  d99277860  ГК «8 элемент» купила PWeM Invest (Mergers.ru, 13.11.2026)
  ga187c62e  d89690931  Игорь Кремнев получил 100% «Молочной столицы» от
                        Валентины Кремневой (Абирег, 23.11.2026)
  g7ad2f3e2  d62446775  ЧакVC купил 10% Chatix (Telegram @rusven, 23.11.2026)

Этот скрипт заменяет заглушки полными структурными полями (прозу —
`pipeline/ingest/fixes/written_2026_11_23_three_takes.py` через
`review.py --write`). Четвертое решение «в работу» (gc4d31e84, здание казино
XIX века в Калининграде, draft d26162939) здесь не трогается: TASS
(tass.ru/nedvizhimost/28343205) отдает 0 знаков текста этой сессии
(`fetch_article_texts.py` — «подозрительно короткий текст»), WebSearch по
заголовку и по номеру статьи не нашел зеркала — честно отложено до
следующего прогона с доступом к странице.

Профилей компаний не создаем ни для одной стороны: «ГК «8 элемент»» сама
статья называет «будущей» группой компаний (без единого юрлица), у PWeM
Invest нашелся только нечеткий лид (LEI-запись называет ОГРН 1215200023103,
не подтвержден вторым источником); у «Молочной столицы» просроченный адрес
в EMIS совпадает с текстом статьи (Липецк, до переезда в Лебедянь), но ИНН
в открытом доступе не нашелся; Chatix — ИП Демьянов К.С., как Semantica AI
утром того же дня. Везде — честная пустота в accepted_notes.no_profile.

Запуск:
    python3 pipeline/fix_fill_three_take_stub_cards_2026_11_23.py            # сухой прогон
    python3 pipeline/fix_fill_three_take_stub_cards_2026_11_23.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'ingest'))

PENDING = os.path.join(ROOT, '..', 'static', 'data', 'pending.json')

MERGERS_URL = 'https://mergers.ru/news/Investicionnaya-kompaniya-PWeM-Invest-voshla-v-sostav-GK-8-jelement-87785'
ABIREG_URL = ('https://abireg.ru/newsitem/119482-logistika-lebedyanmoloko-pereshla-k-'
              'upravlyayushchemu-aktsioneru-kholdinga-igoryu-kremnevu/')
RUSVEN_URL = 'https://t.me/rusven/7863'


def pwem_card(base):
    base.update({
        'title': 'ГК «8 элемент» купила PWeM Invest',
        'ind': 'Финансовые услуги',
        'type': 'M&A',
        'kind': 'acquisition',
        'status': 'Закрыта',
        'src': [['Mergers.ru', MERGERS_URL]],
        'eco': {'sum': '—', 'share': '—', 'val': '—', 'target_fin': '—', 'fin': '—',
                'rationale': '—', 'context': '—', 'finadv': '—'},
        'law': {'struct': '—', 'appr': '—', 'adv': [], 'terms': '—'},
        'buyer_name': 'ГК «8 элемент»',
        'asset': 'PWeM Invest',
        'party_evidence': {
            'buyer': [{'value': 'ГК «8 элемент»', 'field': 'buyer_name',
                       'method': 'explicit_news_title', 'url': MERGERS_URL}],
            'target': [{'value': 'PWeM Invest', 'field': 'asset',
                        'method': 'explicit_news_title', 'url': MERGERS_URL}],
        },
        'accepted_notes': {
            'no_profile': {
                'buyer': ('«ГК «8 элемент»» сама статья называет «будущей группой компаний» — '
                          'объединяет сеть «Ломбард 888» и ювелирную «Аналемму», но как единое '
                          'юрлицо в источнике не названа; профиль не заводим.'),
                'target': ('PWeM Invest (ООО ИК «Управление частным капиталом», Нижний Новгород) — '
                           'ИНН в открытом доступе не нашелся; найден только нечеткий лид: '
                           'запись LEI (leiscan.com) называет ОГРН 1215200023103 и юридический '
                           'адрес «Нижний Новгород, пл. Театральная, 3, офис 7», но LEI-статус '
                           'записи просрочен (LAPSED), и лид не подтвержден вторым источником — '
                           'профиль не заводим, оставляем для следующего прохода.'),
            },
            'searched': ('Mergers.ru, 13.11.2026 (первоисточник, прочитан целиком через '
                          'fetch_article_texts.py); WebSearch «ООО Управление частным капиталом '
                          'PWeM Invest Нижний Новгород ИНН» — нашел только запись LEI с ОГРН, без '
                          'подтверждения вторым источником.'),
        },
    })
    return base


def molstol_card(base):
    base.update({
        'title': 'Игорь Кремнев получил 100% «Молочной столицы» от Валентины Кремневой',
        'ind': 'Транспорт и логистика',
        'type': 'M&A',
        'status': 'Закрыта',
        'src': [['Абирег', ABIREG_URL]],
        'eco': {'sum': '—', 'share': '100% доли в ООО «Молочная столица»', 'val': '—',
                'target_fin': '—', 'fin': '—', 'rationale': '—', 'context': '—', 'finadv': '—'},
        'law': {'struct': '—', 'appr': '—', 'adv': [], 'terms': '—'},
        'buyer_name': 'Игорь Кремнев',
        'seller': 'Валентина Кремнева',
        'seller_src': 'text',
        'asset': 'Молочная столица',
        'party_evidence': {
            'buyer': [{'value': 'Игорь Кремнев', 'field': 'buyer_name',
                       'method': 'explicit_news_title', 'url': ABIREG_URL}],
            'seller': [{'value': 'Валентина Кремнева', 'field': 'seller',
                        'method': 'manual_source_review', 'url': ABIREG_URL}],
            'target': [{'value': 'Молочная столица', 'field': 'asset',
                        'method': 'explicit_news_title', 'url': ABIREG_URL}],
        },
        'accepted_notes': {
            'no_profile': {
                'target': ('ООО «Молочная столица» (Лебедянь, Липецкая обл., транспортный и '
                           'логистический оператор холдинга «Лебедяньмолоко») — ИНН в открытом '
                           'доступе не нашелся; запись EMIS (emis.cn) по старому адресу до '
                           'переезда (Липецк, Ангарская, 34) совпадает со статьей, но реквизиты '
                           'закрыты платным отчетом — профиль не заводим. Холдинг '
                           '«Лебедяньмолоко» (ИНН 4811005751) — ДРУГОЕ юрлицо (само молочное '
                           'производство), не путать с «Молочной столицей» (его логистическим '
                           'оператором).'),
                'buyer': 'Игорь Кремнев и Валентина Кремнева — физические лица, профиль не заводим.',
                'seller': 'см. buyer — то же физическое лицо по разные стороны сделки.',
            },
            'notes': ('Условия передачи доли статья прямо называет нераскрытыми («условия '
                      'передачи не раскрываются»), а сам Кремнев говорит, что доли перешли «в '
                      'рамках семьи» и «ни на что не влияют» — не подтверждено, были ли деньги; '
                      'заголовок и eco.val честно не называют сделку ни покупкой, ни '
                      'безвозмездной передачей там, где источник сам этого не говорит.'),
            'searched': ('Абирег, 23.11.2026 (первоисточник, прочитан целиком через '
                          'fetch_article_texts.py); WebSearch «ООО Молочная столица Лебедянь ИНН '
                          'ОГРН» — нашел только запись EMIS по старому адресу, без реквизитов в '
                          'открытом доступе, и не ту компанию («Лебедяньмолоко», другое юрлицо).'),
        },
    })
    return base


def chatix_card(base):
    base.update({
        'title': 'ЧакVC купил 10% Chatix',
        'ind': 'Искусственный интеллект',
        'type': 'Инвестиция',
        'kind': 'financing',
        'status': 'Закрыта',
        'src': [['Telegram: rusven', RUSVEN_URL]],
        'eco': {'sum': '6 млн ₽', 'share': '10% доли в Chatix', 'val': '—',
                'target_fin': '—', 'fin': '—', 'rationale': '—', 'context': '—', 'finadv': '—'},
        'law': {'struct': '—', 'appr': '—', 'adv': [], 'terms': '—'},
        'buyer_name': 'ЧакVC',
        'asset': 'Chatix',
        'sum': '6 млн ₽',
        'party_evidence': {
            'buyer': [{'value': 'ЧакVC', 'field': 'buyer_name',
                       'method': 'explicit_news_title', 'url': RUSVEN_URL}],
            'target': [{'value': 'Chatix', 'field': 'asset',
                        'method': 'explicit_news_title', 'url': RUSVEN_URL}],
        },
        'accepted_notes': {
            'no_profile': {
                'target': ('Chatix — по тексту объявления сам сервис зарегистрирован как ИП '
                           'Демьянов К.С., без юрлица; ИНН/ОГРНИП в открытом доступе не искали '
                           'дополнительно (тот же класс, что Semantica AI/ИП Коченевский тем же '
                           'утром) — профиль не заводим.'),
                'buyer': ('«ЧакVC» — венчурный фонд с evergreen-структурой капитала, управляющий '
                          'партнер Мартин Кольхаузер; юрлицо фонда в источнике не названо — '
                          'профиль не заводим.'),
            },
            'searched': 'Telegram-канал @rusven, 23.11.2026 (первоисточник, прочитан целиком).',
        },
    })
    return base


BUILDERS = {
    'g30404c73': pwem_card,
    'ga187c62e': molstol_card,
    'g7ad2f3e2': chatix_card,
}


def main(write):
    pending = json.load(open(PENDING, encoding='utf-8'))
    by_id = {c['id']: c for c in pending['cards']}
    missing = [cid for cid in BUILDERS if cid not in by_id]
    assert not missing, 'заглушек не нашлось: %s' % missing

    import tag_themes
    for cid, builder in BUILDERS.items():
        card = builder(dict(by_id[cid]))
        themes = tag_themes.add_themes(card)
        by_id[cid] = card
        print('Карточка: %s' % cid)
        print('  title: %s' % card['title'])
        print('  themes: %s' % themes)

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    pending = json.load(open(PENDING, encoding='utf-8'))  # перечитать прямо перед записью
    cur_by_id = {c['id']: c for c in pending['cards']}
    missing = [cid for cid in BUILDERS if cid not in cur_by_id]
    assert not missing, 'заглушек не нашлось при повторном чтении: %s' % missing
    pending['cards'] = [by_id.get(c['id'], c) for c in pending['cards']]
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО: 3 карточки заполнены в pending.json')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
