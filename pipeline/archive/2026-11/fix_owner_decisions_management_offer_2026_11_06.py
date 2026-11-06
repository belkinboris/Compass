# -*- coding: utf-8 -*-
"""Решения владельца 6 ноября 2026 — применение к двум карточкам очереди.

Владелец (Борис) ответил на открытые вопросы второго чтения двух карточек
очереди (`static/data/pending.json`) и сделал из ответов правила:

1. Тип «Передача в управление» — собственник сам (не указом президента)
   передает управление компанией управляющей компании, например по итогам
   конкурса; собственность не переходит. «Временное управление» — только по
   указу. Птицефабрика «Островная» (g8317fa58): правительство Сахалинской
   области по итогам конкурсного отбора передало управление ООО «Новая
   инвестиционно-финансовая компания» — тип «Передача в управление».
2. Управляющая компания — сторона карточки с ролью «Управляющая компания»
   (`buyer`). Профиля у ООО «Новая инвестиционно-финансовая компания» в базе
   не было — заводится здесь (docs/company_profiles.md). ИНН надежно не
   найден: ЕГРЮЛ из этой среды не отвечает (egrul.nalog.ru — обрыв
   соединения, api-fns — 403), веб-поиск по точному названию нашел только
   другие компании с похожими именами; записано в accepted_notes.no_inn.
   Без указа поле `no_parties` («покупателя и продавца нет») больше не
   верно — снимается; `kind` — «management».
3. Добровольное предложение всем акционерам: продавец — «Акционеры
   «<компания>»» (как «Миноритарные акционеры «Квадры»» у опубликованной
   g552abe79). «Т-Технологии»/«Циан» (g9b4c2e71): seller — «Акционеры
   «Циана»». Профиль не заводится, причина уже в accepted_notes.no_profile.
4. Цена за акцию в посте — строкой «Цена: 993,05 ₽ за акцию», без премии.
   Цена лежала только в прозе (`eco.fin`: «Покупатель предлагает 993,05 ₽ за
   акцию»; `law.struct`: «по 993,05 ₽ за штуку») — переносится в явное поле
   `eco.price_per_share` (docs/card_money.md). Число — подстрока `eco.fin`.

`post_preview` обеих карточек собирается заново (format_post.render): старый
снимок нес «#временное_управление» и «Продавец: не раскрыт», а publication
берет первым именно снимок — без пересборки в канал ушел бы старый текст.
Штампы приемки и второго чтения не трогаются: отпечаток содержимого
разошелся, карточки надо перепринять и показать в консоли заново.

Обе карточки к моменту записи уже в базе (решения из консоли применены 6 ноября,
«Циан» опубликован постом владельца) — скрипт правит карточки базы; пост
«Циана» не пересобирается (текст владельца, post_override), «Островной» —
собирается (пост еще не вышел, post_not_before).

Запуск: python3 pipeline/archive/2026-11/fix_owner_decisions_management_offer_2026_11_06.py [--write]
Без ключа — сухой прогон. Файлы перечитываются прямо перед записью.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'publish'))

import accept_card  # noqa: E402
import format_post  # noqa: E402

DAY = '2026-11-06'

MGMT_CARD = 'g8317fa58'
MGMT_NAME = 'Новая инвестиционно-финансовая компания'
MGMT_PROFILE = {
    'name': MGMT_NAME,
    'ind': 'Агро',
    # Факт — из law.struct этой карточки (слова Антона Зайцева, 1prime.ru и
    # Life.ru): «у нее есть опыт управления птицефабриками в России».
    'desc': ('Компания с опытом управления птицефабриками в России. '
             'Юрлицо — ООО «Новая инвестиционно-финансовая компания».'),
    'kpi': [],
    'legal_short': 'ООО «Новая инвестиционно-финансовая компания»',
}
MGMT_NO_INN = ('ИНН не найден надежно: ЕГРЮЛ из среды приемки не отвечает (egrul.nalog.ru — обрыв '
               'соединения, api-fns — 403), веб-поиск по точному названию «Новая инвестиционно-финансовая '
               'компания» нашел только другие юрлица с похожими именами; в статьях (1prime.ru, Life.ru, '
               'ТАСС) ИНН и город регистрации не названы. Искать по ЕГРЮЛ/rusprofile с регионом Сахалин.')
MGMT_NOTE = (' Решение владельца 6 ноября 2026: передача управления самим собственником (по конкурсу, не '
             'по указу) — тип «Передача в управление», не «Временное управление»; управляющая компания '
             '— сторона карточки с ролью «Управляющая компания». Тип сменен, профиль ООО «Новая '
             'инвестиционно-финансовая компания» заведен и стоит в buyer, no_parties снято '
             '(pipeline/archive/2026-11/fix_owner_decisions_management_offer_2026_11_06.py).')
NO_PARTIES_OLD = ('Управление передано по итогам конкурсного отбора, собственность не переходила — акции '
                  'остаются у правительства Сахалинской области; покупателя и продавца нет.')

OFFER_CARD = 'g9b4c2e71'
OFFER_SELLER = 'Акционеры «Циана»'
PRICE = '993,05 ₽ за акцию'
OFFER_NOTE = (' Решение владельца 6 ноября 2026: при добровольном предложении всем акционерам продавец — '
              '«Акционеры «Циана»» (как «Миноритарные акционеры «Квадры»» у g552abe79); цена за акцию '
              'в посте — строкой «Цена: 993,05 ₽ за акцию», без премии (поле eco.price_per_share) '
              '(pipeline/archive/2026-11/fix_owner_decisions_management_offer_2026_11_06.py).')


def apply(base, pending):
    comps = base['companies']
    cards = {c['id']: c for c in base['deals']}
    log = []

    # --- 1–2. «Островная»: тип и управляющая компания ---------------------
    card = cards[MGMT_CARD]
    twins = [k for k, v in comps.items() if v.get('name') == MGMT_NAME]
    if card.get('type') == 'Передача в управление':
        log.append('%s: уже «Передача в управление»' % MGMT_CARD)
    else:
        assert card.get('type') == 'Временное управление', card.get('type')
        assert card.get('kind') == 'custody', card.get('kind')
        assert not any(card.get(f) for f in ('buyer', 'buyer_name', 'seller', 'seller_id')), card
        assert card.get('no_parties') == NO_PARTIES_OLD, card.get('no_parties')
        assert card.get('target') == 'g0a8a70c9', card.get('target')
        assert not twins, twins
        cid = accept_card._new_profile_id(base, MGMT_NAME)
        comps[cid] = dict(MGMT_PROFILE)
        log.append('профиль %s: %s' % (cid, MGMT_NAME))
        card['type'] = 'Передача в управление'
        card['kind'] = 'management'
        card['buyer'] = cid
        card.pop('no_parties')
        notes = card.setdefault('accepted_notes', {})
        notes.setdefault('no_inn', {})['buyer'] = MGMT_NO_INN
        notes['notes'] = str(notes.get('notes') or '') + MGMT_NOTE
        log.append('%s: тип «Передача в управление», buyer=%s, no_parties снято' % (MGMT_CARD, cid))

    # --- 3–4. «Циан»: продавец и цена за акцию ----------------------------
    card = cards[OFFER_CARD]
    eco = card.setdefault('eco', {})
    if card.get('seller') == OFFER_SELLER:
        log.append('%s: продавец уже «%s»' % (OFFER_CARD, OFFER_SELLER))
    else:
        assert not card.get('seller') and not card.get('seller_id'), (card.get('seller'), card.get('seller_id'))
        assert (card.get('accepted_notes') or {}).get('no_profile', {}).get('seller'), 'нет no_profile.seller'
        card['seller'] = OFFER_SELLER
        log.append('%s: seller = %s' % (OFFER_CARD, OFFER_SELLER))
    if eco.get('price_per_share') == PRICE:
        log.append('%s: цена уже стоит' % OFFER_CARD)
    else:
        assert not eco.get('price_per_share'), eco.get('price_per_share')
        # Перенос факта — подстрока поля-источника (docs/card_editing.md).
        assert '993,05 ₽ за акцию' in str(eco.get('fin') or ''), eco.get('fin')
        eco['price_per_share'] = PRICE
        log.append('%s: eco.price_per_share = %s' % (OFFER_CARD, PRICE))
    notes = card.setdefault('accepted_notes', {})
    if OFFER_NOTE.strip() not in str(notes.get('notes') or ''):
        notes['notes'] = str(notes.get('notes') or '') + OFFER_NOTE

    # --- снимки постов -------------------------------------------------------
    for cid in (MGMT_CARD,):
        card = cards[cid]
        text = format_post.render(card, comps)   # строка «Подробнее в карточке» — внутри
        if card.get('post_preview') != text:
            card['post_preview'] = text
            log.append('%s: post_preview собран заново' % cid)
    return log


def main(write=False):
    base = json.load(open(BASE, encoding='utf-8'))
    pending = json.load(open(PENDING, encoding='utf-8'))
    for line in apply(base, pending):
        print(line)
    print('\n--- пост %s ---\n%s' % (MGMT_CARD, next(c for c in base['deals'] if c['id'] == MGMT_CARD)['post_preview']))
    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0
    # Перечитать прямо перед записью: чужой пуш между чтением и записью не
    # должен стереться старым снимком (docs/card_editing.md).
    base = json.load(open(BASE, encoding='utf-8'))
    pending = json.load(open(PENDING, encoding='utf-8'))
    apply(base, pending)
    json.dump(base, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    open(BASE, 'a', encoding='utf-8').write('\n')
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
