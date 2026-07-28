# -*- coding: utf-8 -*-
"""Бэклог A20, третья партия: «Продавец — X» в именительном падеже.

ГЛАВНОЕ — ЭТО ОШИБКА ЗАМЕРА, А НЕ НОВАЯ ПАРТИЯ. Прогоны 32, 34, 40 и 41 искали
сторону сделки шаблоном `продавц\\w*`. Основа «продавц» есть у всех падежей,
КРОМЕ именительного: «продавца», «продавцы», «продавцом» — совпадают, а
«Продавец» — нет. Именно так поле чаще всего и подписано: «Продавец — Андрей
Комаров», «Продавец: Александр Москаленко», «Продавец — Минимущество
Ингушетии». Из-за одной буквы мимо всех прошлых прогонов прошли 99 карточек,
и в бэклоге стояло «осталось ~50 кандидатов, самый частый признак — шумный».

ЗАМЕР. Карточек без продавца — 867. Со словом «Продавец» в именительном
падеже — 99; ещё 74 нашлись по признакам перехода собственности («принадлежал»,
«передал», «сменил собственника», «перешло к», «вышел из капитала»), которые
раньше тоже не проверялись. Прочитано и то и другое, заполнено 96, отклонено 5.

ЧТО ПРОВЕРЯЕТСЯ ПЕРЕД ЗАПИСЬЮ — то же, что в прогонах 40 и 41: имя ложится на
текст карточки слово в слово с точностью до окончаний (для перечислений — по
частям), продавец не совпадает с покупателем, а совпадение с предметом сделки
не пропускается молча: такие карточки обязаны лежать в ROLE_FIX.

ЧТО ОТКЛОНЕНО. «Продавец — физические лица», «Продавец — бенефициары не
раскрыты» — это пустота, а не имя. Отдельно отклонены две карточки, где
продавцом назван сам предмет сделки и что именно продано, из текста не следует.

ОТДЕЛЬНЫЙ СЛУЧАЙ — SAME_NAME_OK. Продавец и предмет называются похоже, но это
разные стороны: «Продавец — Decathlon, предмет — Decathlon Russia», «продавец —
Schaeffler, предмет — завод Schaeffler в Ульяновске». Проверка обязана таких
случаев не пропускать молча, поэтому каждый записан явно, с причиной.

ДВЕ ПРАВКИ НАЗВАНИЙ. Профили, которые становятся продавцами и попадают в плашку
сторон: «НАО «Интерсфера» (структура семьи Якова Панченко» — обрыв с незакрытой
скобкой, и «группа «Аллтек»» — со строчной буквы.

Запуск:
    python3 pipeline/extract_sellers_nominative.py            # сухой прогон
    python3 pipeline/extract_sellers_nominative.py --write    # записать
"""
import json
import re
import sys

PATH = 'static/data/deals_promoted.json'

# id сделки -> имя продавца. Значение — кусок текста карточки, у длинных
# оставлено само имя (без «который сохранил 49%» и прочих продолжений).
TABLE = {
    # --- «Продавец — X» в именительном падеже
    'g2a6d5d16': 'НАО «Интерсфера»',
    'g014c51ff': 'Группа «Аллтек»',
    'gd88cbe9a': 'Андрей Комаров',
    'gadd238c3': 'Ижевский электромеханический завод «Купол»',
    'g69437311': 'Дарья Ермакова',
    'gf7e349aa': 'Лев Гориловский через ООО «СИГП»',
    'g7cab373d': 'ПАО «Банк ПСБ»',
    'gef02a680': 'Виталий Анатольевич Богданов',
    'g948e18e1': 'Nordgold',
    'gd66af0f7': 'Илья Рагозин',
    'ge4cded31': 'Сергей Бачин',
    'g1b5e8ab8': 'Raiffeisen Bank International',
    'g38e5718e': 'Владимир Мехришвили',
    'g97d0d2a2': 'Минимущество Ингушетии',
    'g081ac83c': 'Елена Кудакова',
    'g506ea8c4': 'Михаил Бобров',
    'gdf93c62d': 'Суховерхов Андрей Владимирович',
    'g016f1b13': 'Абрамян Рузанна Рудиковна',
    'gf019cd92': 'АО «Ю-Крафт» под управлением Владислава Цыгана',
    'g0748e794': 'Правительство Республики Башкортостан',
    'gf3a811bd': 'Алексей Сучков',
    'g926d097b': 'Геннадий Бобрицкий',
    'g7ce0250d': 'Галина Юрьевна Бочкова',
    'gf8dfe9c4': 'Аболмасов Александр Геннадьевич',
    'g2d90c4d5': 'ING Group',
    'g334b5760': 'Дмитрий Валерьевич Васильев',
    'g14443784': 'Купцов Алексей Владимирович',
    'gc567457f': 'Ирина Доброхотова',
    'g6bf4b33c': 'Ваган Арутюнян',
    'g707633b2': 'Олег Петрович Зеваков',
    'ge292671d': 'Эдуард Лукин',
    'gc0ba024d': 'Холдинг Mirafox',
    'gb43c8bcb': 'Свердловская область',
    'g4b78d957': 'РТ-Инвест',
    'g282be68a': 'Faurecia',
    'g981d090f': 'Шишкина Олеся Андреевна',
    'g809f9155': 'Руслан Вдовин',
    'gd75ae46f': 'Hines',
    'g087764ec': 'Валентин Викторович Микляев',
    'ga28b511a': 'Семья Михаила Николаева',
    'geb236ba2': 'ICT Holding Limited',
    'gd2d13f3b': 'Amtel Properties',
    'ga5b0724c': 'ООО «Форум»',
    'g685e38f9': 'РСХБ Управление Активами',
    'gedc0eb10': 'Егор Егерев',
    'gec687f97': 'Binance',
    'gb31c796f': 'Елена Полетаева',
    'g60fedbfd': 'Татьяна Григорьевна Коваленко',
    'g037385e2': 'Алексей Николаевич Ананьин',
    'g3a25a36c': 'Управляющая компания «Контрдата Капитал»',
    'g60280ac0': 'Decathlon',
    'g9ec93147': 'Олег Романович Рыбалов и Сбербанк',
    'ga3376e53': 'Mall Management Group',
    'g85b8634d': '«Огмент инвестментс лимитед»',
    'g2d075f03': 'Russia Partners',
    'g2f572b66': 'АО «Кавказ.РФ»',
    'g3b976e82': 'Goldman Sachs',
    'g94c9a39d': 'Plaza Development',
    'g6ad6fe69': 'Максим Ефименко',
    'g1c5d636d': 'Владимир Лисин',
    'g7fac547e': 'Братишко Олег Владимирович',
    'gc6322659': 'My.Games',
    'g6007df5d': 'Level Group',
    'g0885d151': 'Алексей Зуев',
    'gc4c76129': 'Егор Егерев',
    'g1d73eef1': 'Александр Москаленко',
    # --- признаки перехода собственности, которых прежние прогоны не искали
    'gd8b851c3': 'Сбербанк',
    'gc6448a17': 'ЦБ РФ',
    'gcc2b3aef': 'Фонд «Нейронные сети»',
    'gc3d735fc': 'Банк России',
    'gaf184ebb': 'Владимир Евтушенков',
    'gabc867f3': 'AVG Capital Partners',
    'g4aa98650': 'Банк «Траст»',
    'g5dc9e216': 'Sberbank Europe AG',
    'gcdf0e196': 'Fieldwood Energy',
    'g3cc2009d': 'Petropavlovsk PLC',
    'g51cff34c': 'Артур Хримян',
    'gd5671442': 'Банк «ФК Открытие»',
    'ge6f1e0ae': 'Globaltrans',
    'g7cb5d8f8': '«Альфа-Групп»',
    'g5c0f70c6': 'Mondi Group',
    'g2ab512d7': 'Polymetal International',
    'ge56325d9': 'SIIC',
    'gc88ca79d': 'АФК «Система»',
    'g2c2e274b': 'АФК «Система»',
    'g54843952': 'ТЭН',
    'g889e051d': 'АФК «Система»',
    'g5405b876': 'Royal Greenland',
    'g4ce32808': 'Алина Зиннатуллина',
    'g5fb64cd9': 'Schaeffler',
    'g446bbeee': 'Вадим Швецов',
    'ge5782922': 'НИИ «Масштаб»',
    'g3c56d235': 'ООО «Кисс Коала»',
    'g1f43265d': 'ЕБРР',
    'gc9461b5c': 'Сбербанк Инвестиции',
    'g8cf8098f': 'Татарстан',
}

# Профиль продавца стоял в `target`: предметом сделки числился сам продавец.
ROLE_FIX = {
    'g2a6d5d16': 'gc9f213a2',   # продан: логопарк «Шоссейная»
    'g014c51ff': 'gdd2bc1fc',   # проданы: акции Sibanthracite PLC
    'g1b5e8ab8': 'g05efe03b',   # продавалась: доля в российской «дочке»
    'g4b78d957': 'g1c4e37e4',   # переданы: активы восьми компаний
    'gcc2b3aef': 'g02a00875',   # продана: доля в ООО «Ред Софт»
    'g4aa98650': 'gdc4235da',   # проданы: привилегированные акции «Русснефти»
    'g5dc9e216': 'g847db8e9',   # проданы: пять дочерних банков
    'g3cc2009d': 'g74eaf526',   # проданы: российские золотодобывающие активы
    'gd5671442': 'g7ac0b3cc',   # проданы: два объекта недвижимости в Москве
    'ge6f1e0ae': 'g9d236ace',   # проданы: железнодорожные активы
    'g7cb5d8f8': 'g361eb484',   # переданы: 7,73% акций IDS Borjomi
    'g3c56d235': 'g63a953b7',   # продан: российский каталог Sony Music
    'g8cf8098f': 'ga481b0bf',   # продан: «Татспиртпром»
}

# Профили, которые становятся продавцами и попадают в плашку сторон.
NAME_FIX = {
    'gc9f213a2': ('НАО «Интерсфера» (структура семьи Якова Панченко', 'НАО «Интерсфера»'),
    'gdd2bc1fc': ('группа «Аллтек»', 'Группа «Аллтек»'),
}

# Продавец и предмет называются похоже, но это РАЗНЫЕ стороны: продаётся
# российский актив материнской компании. Роль менять не нужно — нужно явное
# решение, иначе проверка «продавец не равен предмету» просто промолчит.
SAME_NAME_OK = {
    'gec687f97': 'продавец — Binance, предмет — «Binance (российский бизнес)»',
    'g60280ac0': 'продавец — Decathlon, предмет — Decathlon Russia',
    'g5fb64cd9': 'продавец — Schaeffler, предмет — завод Schaeffler в Ульяновске',
    'g3b976e82': 'продавец — Goldman Sachs, предмет — «Российский бизнес Goldman Sachs»',
    'g948e18e1': 'продавец — Nordgold, предмет — рудники Bissa и Bouly',
    'gc6322659': 'продавец — My.Games, предмет — платформа Boosty',
    'g2d075f03': 'продавец — Russia Partners, предмет — доля в Банки.ру',
    'g6007df5d': 'продавец — Level Group, предмет — жилой проект Level Group на Перовском шоссе',
}

# Прочитано и отвергнуто.
SKIP = {
    'ged395e90': '«Продавец — физические лица» — имени нет',
    'g623cf943': '«Продавец — бенефициары не раскрыты» — это пустота',
    'g2369d101': 'продавец назван описательно — «дочка Сибура», юрлицо не названо',
    'g9d9e7ab6': 'компания привлекает инвестора в свой капитал: продавцом подписана она '
                 'сама, а кто именно продаёт долю — из текста не следует',
    'g57a44f07': 'продавцом названо само приобретаемое ООО «Эйдос Робототехника» — '
                 'что именно продано и кем, из текста не следует',
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
    """Одно и то же имя с точностью до окончаний, обрезки или регистра."""
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
    assert set(SAME_NAME_OK) <= set(TABLE), 'разрешение на совпадение без имени продавца'
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
            if other and close_names(other, name) and deal_id not in SAME_NAME_OK:
                assert ROLE_FIX.get(deal_id) == deal.get(field) and field == 'target', \
                    '%s: продавец стоит в поле %s (%r) — решение не записано' % (deal_id, field, other)
        if deal_id in ROLE_FIX:
            cid = ROLE_FIX[deal_id]
            assert comps.get(cid), '%s: нет профиля %s' % (deal_id, cid)
            assert deal.get('target') == cid, '%s: ожидали профиль продавца в target' % deal_id
            assert close_names(comps[cid]['name'], name), \
                '%s: профиль %r не похож на имя продавца' % (deal_id, comps[cid]['name'])
        planned.append((deal_id, name, deal))

    for cid, (was, now) in NAME_FIX.items():
        assert norm(comps[cid]['name']) == was, 'профиль %s уже не %r' % (cid, was)
        assert fits(now, was), 'новое имя профиля не выводится из старого'

    print('Карточек к заполнению: %d (из них роль исправляется: %d; отклонено при чтении: %d)'
          % (len(planned), len(ROLE_FIX), len(SKIP)))
    for deal_id, name, _ in planned:
        print('  %s%s  %s' % (deal_id, ' [роль]' if deal_id in ROLE_FIX else '      ', name))
    for was, now in NAME_FIX.values():
        print('  правка названия профиля: %s -> %s' % (was, now))

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
    for cid, (_, now) in NAME_FIX.items():
        comps[cid]['name'] = now
    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    filled = sum(1 for d in data['deals'] if d.get('seller_id') or norm(d.get('seller')))
    print('\nЗаписано. Продавец известен у %d карточек из %d.' % (filled, len(data['deals'])))
    print('Связано с профилем компании: %d.'
          % sum(1 for d in data['deals'] if d.get('seller_id')))


# Правило проверяется на себе.
assert not fits('Иван Петров', 'Продавец — Андрей Комаров (экс-владелец ЧТПЗ)')
assert fits('Андрей Комаров', 'Продавец — Андрей Комаров (экс-владелец ЧТПЗ)')
assert fits_parts('Олег Романович Рыбалов и Сбербанк',
                  ['Продавец — Олег Романович Рыбалов и Сбербанк (владеют 90,01% и 9,99%)'])
assert not fits_parts('Олег Романович Рыбалов и ВТБ',
                      ['Продавец — Олег Романович Рыбалов и Сбербанк (владеют 90,01% и 9,99%)'])

if __name__ == '__main__':
    main('--write' in sys.argv)
