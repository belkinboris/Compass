# -*- coding: utf-8 -*-
"""Пять жалоб владельца с телефона (16 августа 2026, скриншоты) — правки,
не укладывающиеся в модель review.py (одна дословная цитата на одно поле
целиком), по образцу pipeline/fix_deep_batch1_manual.py.

1. gfebe16ad (ВТБ/Courtyard by Marriott Kazan Kremlin, покупатель — Говор):
   на «Обзоре» стороны сделки читались абсурдно — «Предмет сделки: Русинн»
   между «Продавец: ВТБ» и «Покупатель: ООО «Русинн»» — предмет и
   покупатель оказались ОДНИМ И ТЕМ ЖЕ. Причина: `target` карточки
   ссылался на профиль g1c2d0229, чьё описание («Структура Александра
   Говора… в 2025 году купила у ВТБ отель…») — это описание ПОКУПАТЕЛЯ, а
   не отеля. Профиль при этом больше нигде не использован (ни в других
   карточках, ни в match_keys) — безопасно перелинковать: `buyer` ссылка
   на этот профиль (вместо текстового `buyer_name`, который дублировал то
   же самое), `target` снят (у отеля своего профиля-компании нет — как и у
   394 других карточек с активом, а не юрлицом-целью, `target=None` —
   обычное дело). Заодно снята вторая жалоба: цитата гендиректора отеля
   Александры Якушевой про сохранение стандартов и команды стояла в
   «Юристе» (`law.terms`) — это не юридический вопрос, а деловая
   непрерывность бизнеса; перенесена в `eco.context` (экономист).

2. g0fadc207 (Qiwi plc/АО «Киви» → Fusion Factor Fintech Limited): запись
   консультанта ALRUD на «Юристе» начиналась буквально с «на стороне
   продавца — Qiwi plc):» — оборванное начало фразы со стрелкой закрывающей
   скобки без открывающей. Роль стороны перенесена в тип консультанта (как
   у всех остальных записей этой сделки — «Юридический консультант ...
   (сторона продавца)»), описание начинается с заглавной буквы и без
   хвоста скобки.

3. g075e9738 (VK/АО «Р7»): запись консультанта ALUMNI Partners обрывалась
   на полуслове — «...Команда ALUMNI Partners сопровождала сделку по
   прод» (без источника для продолжения). Первое предложение того же
   абзаца уже содержит тот же факт целиком («ALUMNI Partners сопровождала
   Р7 в сделке по продаже доли Группе VK») — обрубленное второе
   предложение снято целиком, а не дописано на глаз (тот же принцип, что
   уже применялся к обрубленным полям карточек сделок).

Запуск:
    python3 pipeline/fix_owner_phone_20260816_manual.py            # сухой прогон
    python3 pipeline/fix_owner_phone_20260816_manual.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

HOTEL_ID = 'gfebe16ad'
HOTEL_BUYER_PROFILE = 'g1c2d0229'
HOTEL_OLD_LAW_TERMS = ('Генеральный директор отеля Александра Якушева '
                        'заверила, что стандарты обслуживания останутся '
                        'высокими, а команда сохранится')
HOTEL_OLD_ECO_CONTEXT = ('Для Говора это не первая инвестиция в '
                          'гостиничный бизнес и не первая сделка с ВТБ. В '
                          '2018 году его девелоперская компания '
                          '«Инрусинвест» уже приобрела у банка гостиницу '
                          'Courtyard by Marriott в Санкт-Петербурге за 2 '
                          'млрд рублей')
HOTEL_NEW_ECO_CONTEXT = (HOTEL_OLD_ECO_CONTEXT + '. ' + HOTEL_OLD_LAW_TERMS)

QIWI_ID = 'g0fadc207'
QIWI_OLD_ADV_0 = [
    'Юридический консультант',
    'ALRUD',
    'на стороне продавца — Qiwi plc): сопровождение сделки, составление '
    'обязывающих документов, консультирование по регуляторным и '
    'контрсанкционным вопросам; команду возглавил партнёр практики M&A '
    'Сергей Хананев',
]
QIWI_NEW_ADV_0 = [
    'Юридический консультант продавца (Qiwi plc)',
    'ALRUD',
    'Сопровождение сделки, составление обязывающих документов, '
    'консультирование по регуляторным и контрсанкционным вопросам; '
    'команду возглавил партнёр практики M&A Сергей Хананев',
]

VK_R7_ID = 'g075e9738'
VK_R7_OLD_ADV_0 = [
    'Юридический консультант',
    'ALUMNI Partners',
    'по данным телеграм-канала фирмы — ALUMNI Partners сопровождала Р7 в '
    'сделке по продаже доли Группе VK 💼 Команда ALUMNI Partners '
    'сопровождала сделку по прод',
]
VK_R7_NEW_ADV_0 = [
    'Юридический консультант',
    'ALUMNI Partners',
    'По данным телеграм-канала фирмы, ALUMNI Partners сопровождала Р7 в '
    'сделке по продаже доли Группе VK.',
]


def by_id(data):
    return {d['id']: d for d in data['deals']}


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    ids = by_id(data)
    comps = data['companies']

    hotel = ids[HOTEL_ID]
    assert hotel.get('buyer') is None, 'у gfebe16ad уже стоит buyer — правка неактуальна'
    assert hotel.get('buyer_name') == 'ООО «Русинн»'
    assert hotel.get('target') == HOTEL_BUYER_PROFILE
    assert hotel['law']['terms'] == HOTEL_OLD_LAW_TERMS
    assert hotel['eco']['context'] == HOTEL_OLD_ECO_CONTEXT
    assert comps.get(HOTEL_BUYER_PROFILE, {}).get('name') == 'Русинн'
    other_refs = [d['id'] for d in data['deals']
                  if d['id'] != HOTEL_ID and HOTEL_BUYER_PROFILE in
                  (d.get('buyer'), d.get('target'), d.get('seller_id'))]
    assert not other_refs, 'профиль %s используется ещё где-то: %s' % (HOTEL_BUYER_PROFILE, other_refs)

    qiwi = ids[QIWI_ID]
    assert qiwi['law']['adv'][0] == QIWI_OLD_ADV_0, 'law.adv[0] у g0fadc207 уже другой'

    vk = ids[VK_R7_ID]
    assert vk['law']['adv'][0] == VK_R7_OLD_ADV_0, 'law.adv[0] у g075e9738 уже другой'

    print('gfebe16ad: buyer -> %s, buyer_name снят, target снят, '
          'цитата Якушевой перенесена в eco.context' % HOTEL_BUYER_PROFILE)
    print('g0fadc207: law.adv[0] переформатирован (роль стороны -> тип)')
    print('g075e9738: law.adv[0] обрубленное предложение снято')

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    hotel['buyer'] = HOTEL_BUYER_PROFILE
    hotel.pop('buyer_name', None)
    hotel['target'] = None
    hotel['law']['terms'] = None
    hotel['eco']['context'] = HOTEL_NEW_ECO_CONTEXT

    qiwi['law']['adv'][0] = QIWI_NEW_ADV_0
    vk['law']['adv'][0] = VK_R7_NEW_ADV_0

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
