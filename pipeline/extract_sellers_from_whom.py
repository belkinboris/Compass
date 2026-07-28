# -*- coding: utf-8 -*-
"""Бэклог A20: «купил Y у <кого именно> X» — предлог с пояснением перед именем.

ЧТО ПРОПУСКАЛОСЬ. Прогон 43 закрыл вариант «у основателя / владельца X», но
пояснение между предлогом и именем бывает любым: «у банка «Траст»», «у группы
«Сафмар»», «у аэропорта Домодедово», «у девелопера Stone Hedge», «у кипрских
компаний Arfay Enterprises Limited и TGOK Investment Limited», «у структуры
Дерипаски». Ни один прошлый шаблон этого не ловил: они требовали либо заглавную
букву сразу после «у», либо конкретное слово-пояснение.

ЗАМЕР. Признак «глагол покупки … у <строчные слова> <Имя>» есть у 43 карточек
без продавца; ещё 34 нашлись по признаку «доля X» (пулы пересекаются на 4, всего
73 карточки). Прочитаны все: заполнено 42, отклонено 18 с записанными причинами,
остальные 13 были разобраны и отклонены ещё в прогонах 34–43.

ГЛАВНАЯ ЛОВУШКА ЭТОГО ПРИЗНАКА — «магазины У ДОМА». В карточке «Лента купила
сеть Монетка» стоит «приобретение сетью Лента магазинов у дома под брендом
Монетка»: механическая выемка записала бы продавцом «дом под брендом Монетка».
Отсюда правило: признак сужает выборку для чтения, но сам по себе именем не
является.

ЧТО ЕЩЁ ОТКЛОНЕНО. «Выкуп собственных акций у нерезидентов» и «выкуп у
миноритариев» — сторона не названа; «у основателей» и «у саудовского холдинга»
— тоже; предложения о ДРУГИХ сделках («ранее выкупил у группы «Онэксим»»).

ЧТО ПРОВЕРЯЕТСЯ ПЕРЕД ЗАПИСЬЮ — то же, что в прогонах 40–43: имя ложится на
текст карточки слово в слово с точностью до окончаний (перечисления — по
частям), продавец не равен покупателю, а совпадение с предметом сделки требует
явного решения (ROLE_FIX или SAME_NAME_OK).

Запуск:
    python3 pipeline/extract_sellers_from_whom.py            # сухой прогон
    python3 pipeline/extract_sellers_from_whom.py --write    # записать
"""
import json
import re
import sys

PATH = 'static/data/deals_promoted.json'

TABLE = {
    # --- «у <пояснение> X»
    'gf5c8e14e': 'Структуры Александра Клячина',
    'g5d6c6428': 'Аэропорт Домодедово',
    'g703d5597': 'Банк непрофильных активов «Траст»',
    'g420cae8d': 'Prosus N.V.',
    'g22000f22': 'Павел Грачёв и Михаил Стискин',
    'gbb672c86': 'Дочка «ВСМПО-Ависма» («Авитранс»)',
    'gc5f9c1d9': 'Kingfisher plc',
    'gca198c27': 'Сергей Шилов и Евгений Жуланов',
    'g79f683bc': 'Stone Hedge',
    'ge1fbcfb8': 'Наталья Болдина',
    'g3875e8f5': 'Владимир Земцов',
    'g5dc6cb47': 'Семья Даниленко',
    'g9995eb50': 'Компания «Центр фанерной торговли»',
    'g8ff9bdf8': 'Девелопер «Галс-девелопмент»',
    'g42e42759': 'Trüffel 2 GmbH',
    'g573b8819': 'Группа Accent',
    'gdc72cc35': 'Группа PPF',
    'gafc21bdd': 'Структура Дерипаски',
    'g2653122b': 'Группа ВТБ',
    'g7d5f252d': 'Банк «Траст»',
    'g1d76aeb5': 'Stone',
    'gc96f0c6b': 'Структура ГК ПИК',
    'g5013525f': 'Владимир Хлебников и Денис Павлюк',
    'g2dfef7a3': 'Hong Kong Wangsu Science & Technology Company Limited',
    'g4feb488a': 'Группа Аплана',
    'ged4a85ae': 'Алексей и Ирина Макаровы',
    'g256dd345': 'Банк «Траст»',
    'g3fdf0220': 'Компания Ener1',
    'g0e8d79c1': 'Arfay Enterprises Limited и TGOK Investment Limited',
    'g92f41a2d': 'Холдинг «Синдика»',
    'g383b170f': 'Kiilto',
    'g0c19cd78': 'Холдинг Продо',
    'g2a27e6b5': 'Альянс Renault-Nissan и UniCredit',
    # --- признак «доля X»
    'g6d74bc39': 'Shell',
    'g7b4be1c4': 'Евгений Туголуков',
    'g4764cf2b': 'Uber',
    'g551049ec': 'Uber',
    'g8ea21d1b': 'Solvay',
    'g93f7b5d8': 'ЕБРР',
    'g8a8ae3f7': 'Marathon Group',
    'g937ef5d4': 'Группа «Сафмар»',
    'gd1130c05': 'Volkswagen Group',
}

# Профиль продавца стоял в `target`: предметом сделки числился сам продавец.
ROLE_FIX = {
    'gc5f9c1d9': 'ga577cb9a',   # продано: 100% ООО «Касторама Рус»
    'g79f683bc': 'gace55b64',   # продан: бизнес-центр Stone Курская
    'g1d76aeb5': 'gace55b64',   # обсуждается: тот же бизнес-центр
    'gbb672c86': 'gff44d7b7',   # проданы: 4,35% акций «РусГидро»
}

SKIP = {
    'g91c0cb1e': '«магазинов У ДОМА под брендом Монетка» — это тип магазина, а не продавец',
    'g75837e8b': '«выкуп собственных акций у нерезидентов» — сторона не названа',
    'g552abe79': 'обязательная оферта миноритариям; продавцы не названы, а «у группы '
                 '«Онэксим»» — про предыдущую сделку',
    'g5ccd2edb': '«выкупил у основателей» — имена не названы',
    'g507c9a35': '«у саудовского холдинга в ОАЭ» — имя не названо',
    'g4bd9caea': 'соглашение об урегулировании споров трёх сторон; кто у кого покупает, '
                 'из текста не следует',
    'g67b98f28': 'предложение о другой сделке того же покупателя («Аггреко Евразия» у Aggreko)',
    'gb2ab7521': 'более поздняя консолидация — отклонено ещё в прогоне 34',
    'g07fffba3': '«у супруги своего основателя Петра Белого, Натальи» — фамилия продавца '
                 'в карточке не названа',
    'g2777a4b6': 'доли участников сократились из-за размытия при допэмиссии, а не продажи',
    'g18fd392a': 'то же: доли основателей снизились, продажа из текста не следует',
    'g1f2895c0': 'то же: доля «Смарт сервис ЛТД» снизилась после допэмиссии',
    'g51fbc8c8': 'то же: доли владельцев сократились при входе новых инвесторов',
    'ga3afca6c': 'то же: доли основного владельца и партнёра сократились',
    'ged59a2eb': 'допэмиссия: доля покупателя выросла, продавца нет',
    'gad6ed1b8': 'фамилия продавца («доли Гольдорта») в карточке не раскрыта полностью',
    'g7e7b60ca': 'выход «Медси» из проекта — более позднее событие, а не эта инвестиция',
    'ga1935680': '«продажа контрольной доли OBI» — продавец не назван',
}

WORD = re.compile(r"[\w%,.]+", re.U)
SPLIT = re.compile(r'\s+и\s+|,\s*')


def norm(s):
    return re.sub(r'\s+', ' ', str(s or '')).strip()


def bare(word):
    return word.strip('«»"\'(),.;:%').lower()


def same_word(a, b):
    a, b = bare(a), bare(b)
    if not a or not b:
        return False
    if a == b:
        return True
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i >= max(3, int(0.6 * n))


def words(s):
    return [w for w in WORD.findall(s) if bare(w)]


def fits(result, source):
    rw, sw = words(result), words(source)
    if not rw:
        return False
    return any(all(same_word(a, b) for a, b in zip(rw, sw[i:i + len(rw)]))
               for i in range(len(sw) - len(rw) + 1))


def fits_parts(result, sources):
    parts = [p for p in (x.strip() for x in SPLIT.split(result)) if words(p)]
    return all(any(fits(p, t) for t in sources if t) for p in parts)


def close_names(a, b):
    x, y = bare(a), bare(b)
    if x in y or y in x:
        return True
    wa, wb = words(a), words(b)
    n = min(len(wa), len(wb))
    return bool(n) and all(same_word(p, q) for p, q in zip(wa[:n], wb[:n]))


def texts(deal):
    eco = deal.get('eco') or {}
    law = deal.get('law') or {}
    return [t for t in [norm(deal.get('title')), norm(deal.get('extra')),
                        norm(eco.get('share')), norm(eco.get('rationale')),
                        norm(eco.get('context')), norm(law.get('struct')),
                        norm(law.get('terms'))] if t]


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    comps = data['companies']
    assert not (set(TABLE) & set(SKIP)), 'карточка одновременно в таблице и в отказах'
    assert set(ROLE_FIX) <= set(TABLE), 'ROLE_FIX без имени продавца'

    done = sum(1 for i, name in TABLE.items() if norm(by_id[i].get('seller')) == norm(name))
    if done == len(TABLE):
        print('Уже применено: у всех %d карточек продавец записан.' % done)
        return
    assert done == 0, 'скрипт применён частично (%d из %d)' % (done, len(TABLE))

    planned = []
    for deal_id, name in TABLE.items():
        deal = by_id.get(deal_id)
        assert deal is not None, 'нет сделки %s' % deal_id
        assert not deal.get('seller_id') and not norm(deal.get('seller')), \
            '%s: продавец уже заполнен — %r' % (deal_id, norm(deal.get('seller')))
        src = texts(deal)
        assert any(fits(name, t) for t in src) or fits_parts(name, src), \
            '%s: имя не ложится на текст карточки (%r)' % (deal_id, name)
        buyer = comps.get(deal.get('buyer'), {}).get('name') if deal.get('buyer') else None
        assert not buyer or bare(buyer) != bare(name), \
            '%s: продавец совпал с покупателем' % deal_id
        for field in ('target', 'asset_id'):
            other = comps.get(deal.get(field), {}).get('name') if deal.get(field) else None
            if other and close_names(other, name):
                assert ROLE_FIX.get(deal_id) == deal.get(field) and field == 'target', \
                    '%s: продавец совпал с полем %s (%r) — решение не записано' % (deal_id, field, other)
        if deal_id in ROLE_FIX:
            cid = ROLE_FIX[deal_id]
            assert comps.get(cid), '%s: нет профиля %s' % (deal_id, cid)
            assert deal.get('target') == cid, '%s: ожидали профиль продавца в target' % deal_id
            assert close_names(comps[cid]['name'], name), \
                '%s: профиль %r не похож на имя продавца' % (deal_id, comps[cid]['name'])
        planned.append((deal_id, name, deal))

    print('Карточек к заполнению: %d (из них роль исправляется: %d; отклонено при чтении: %d)'
          % (len(planned), len(ROLE_FIX), len(SKIP)))
    for deal_id, name, _ in planned:
        print('  %s%s  %s' % (deal_id, ' [роль]' if deal_id in ROLE_FIX else '      ', name))

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    for deal_id, name, deal in planned:
        deal['seller'] = name
        deal['seller_src'] = 'text'
        if deal_id in ROLE_FIX:
            deal['seller_id'] = ROLE_FIX[deal_id]
            deal['target'] = None
            deal['target_was_seller'] = True
    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    filled = sum(1 for d in data['deals'] if d.get('seller_id') or norm(d.get('seller')))
    print('\nЗаписано. Продавец известен у %d карточек из %d.' % (filled, len(data['deals'])))
    print('Связано с профилем компании: %d.'
          % sum(1 for d in data['deals'] if d.get('seller_id')))


# Правило проверяется на себе: пояснение между «у» и именем не мешает, чужое имя
# не проходит, перечисление проверяется по частям.
assert fits('Группа PPF', 'покупает ООО «ППФ Страхование жизни» у группы PPF')
assert not fits('Группа ВТБ', 'покупает ООО «ППФ Страхование жизни» у группы PPF')
assert fits_parts('Павел Грачёв и Михаил Стискин',
                  ['выкупил акций у бывшего гендиректора «Полюса» Павла Грачёва и его '
                   'экс-финдиректора Михаила Стискина'])
assert not fits_parts('Павел Грачёв и Иван Петров',
                      ['выкупил акций у бывшего гендиректора «Полюса» Павла Грачёва и его '
                       'экс-финдиректора Михаила Стискина'])

if __name__ == '__main__':
    main('--write' in sys.argv)
