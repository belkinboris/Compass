# -*- coding: utf-8 -*-
"""Бэклог A20: продавец назван в заголовке карточки, но поле «Продавец» пусто.

ЧТО СЛОМАНО. У 1044 сделок из 1333 сторона «продавец» пуста, хотя в 91 случае
имя стоит прямо в заголовке: «Henkel продала российский бизнес…», «Покупка сети
Real у Metro AG…», «Банк «Траст» продал ТРК «Аквилон»». Юрист открывает карточку
и видит «Продавец — не раскрыт» там, где продавец назван первым словом.

ЗАМЕР. Кандидатов с признаком продавца в тексте — 215; из них в ЗАГОЛОВКЕ — 91,
это и есть партия скрипта. Прочитаны все 91: заполнено 88 (у 7 из них продавец
уже лежал в базе, но в поле «предмет» — см. ROLE_FIX), 3 отклонены (см. SKIP).
Оставшиеся 124 кандидата, где признак только в тексте, — следующая партия.

ЧТО ПРОВЕРЯЕТСЯ ПЕРЕД ЗАПИСЬЮ.
  * Имя ложится на текст этой же карточки слово в слово с точностью до
    окончаний (правило прогона 34: общее начало ≥ 3 знаков и ≥ 60% длины
    короткого слова). Это разрешает «у «Росатома»» → «Росатом» и запрещает
    подставить другое имя; правило проверяется на себе assert-ом внизу файла.
  * Продавец не совпадает с покупателем и с предметом сделки. Совпадение с
    предметом — не повод пропустить карточку молча: такие 7 карточек вынесены
    в ROLE_FIX, где профиль продавца переезжает из `target` в `seller_id`
    (механика прогона 32: `target_was_seller`).

ЧЕГО НЕ ДЕЛАЕМ. Не выводим продавца из смысла: «Дочка Сибура вышла из капитала
Manucor» — юрлицо не названо, и «Сибур» продавцом не был, продавала его дочка.
Не чиним заодно чужие роли: у g549ddd5a покупателем стоит проданный завод —
это отдельная правка, записанная в бэклог.

Запуск:
    python3 pipeline/extract_sellers_titles.py            # сухой прогон
    python3 pipeline/extract_sellers_titles.py --write    # записать
"""
import json
import re
import sys

PATH = 'static/data/deals_promoted.json'

# id сделки -> имя продавца. Порядок — как в выборке для чтения.
TABLE = {
    'g2b1fe015': 'VK',                                  # «Интеррос» выкупил 25% Точка Банка у VK
    'g1e331a43': 'International Paper',
    'g0fadc207': 'Qiwi plc',
    'g3c46e216': 'Mondi',
    'gf6232eec': 'Башкирия',
    'g5b337455': 'Arconic',
    'gef7d4e54': 'БНА «Траст»',
    'g7dcbe19d': 'Metro AG',
    'ge13d1b5c': 'SDVentures Дмитрия Волкова',
    'g2b9c2d45': 'VK',
    'g6f4a071a': 'Henkel',
    'g71aec6a5': 'Росимущество',
    'gbaf3c565': 'СФИ (Сафмар финансовые инвестиции)',
    'g711eb87e': 'Банк «Траст»',
    'g0591604d': '«Интеррос капитал»',
    'g22b470f6': 'Segezha Group',
    'g9ff9761f': 'ОНЭКСИМ Михаила Прохорова',
    'g05ca1a94': 'Банк «ФК Открытие»',
    'ge6f261a7': 'Давид Давидович',
    'ga845fb01': 'Becar Asset Management',
    'g392ccc1e': 'Роман Абрамович, Александр Абрамов и партнёры',   # в тексте — родительный падеж
    'g8bd5e457': 'Stockmann',
    'g12115ab1': 'Smart Development',
    'g5030d3e8': 'Zurich Insurance',
    'g55f1c662': 'Valio',
    'g7d64b437': '«Газпром Тех»',
    'gcb309b35': 'Игорь Семёнов',
    'g9876feaa': 'Банк «Траст»',
    'gda61c5b8': 'РЖД',
    'g15b9d8e2': 'Александр Конов',
    'g755cbf86': 'АФК «Система»',
    'gd4645195': '«Севергрупп»',
    'gd3ba954d': '«Сбер»',
    'g1eb1565c': 'Группа «Самолет»',
    'g09cee885': 'ВТБ',
    'gd6b3c796': 'ОСК',
    'ge0f7b957': 'Газпромбанк',
    'g6a4b0a2a': '«Росатом»',
    'g31136d69': "O'Key Group S.A.",
    'g405236c9': 'Всеинструменты.ру',
    'g17fc21d6': 'Auchan',
    'gc9bc132c': '«Киевская площадь»',
    'gf6be51a1': 'Ростелеком',
    'gfe21a083': 'Акционеры «Валента Фарм»',
    'g073bf58b': 'BASF',
    'g766a4daf': 'Ipackchem',
    'g4cac8db4': 'Knauf',
    'gd297770d': 'Daimler Truck',
    'g97679d43': 'ВТБ',
    'g31546fef': '«КР Плюс»',
    'ga1828730': 'Glencore',
    'g401b169a': 'СДС-Холдинг',
    'g23827051': 'PPF Real Estate',
    'g87d0201c': 'Роман Троценко',
    'g0b733c0f': 'AB InBev',
    'g8430c9d9': '«Роснефть»',
    'g577cd599': 'Morgan Stanley',
    'ge578141f': 'Takeda Pharmaceutical Company',
    'g5301e77e': 'Hempel',
    'g66bb0d00': 'Банк «Открытие»',
    'g81163284': '3M',
    'gfca749be': 'Kraft Heinz',
    'g221e4969': 'Bonum Capital',
    'gef104d00': 'МТС',
    'g37066bfe': 'Reima',
    'g091016a1': 'Decathlon',
    'g6b737511': 'Александр Салаев',
    'g2800e337': 'Группа «Уралсиб»',
    'gdfe2f116': '«Траст»',
    'g6fc4d4ac': 'FM Logistic',
    'g8ac1b593': 'Amber Beverage Group',
    'ga7232033': 'ВТБ',
    'g327686f7': 'Continental',
    'g6168731b': 'Heineken',
    'g1a58d740': 'Группа «Талтэк»',
    'g76159e00': 'Дмитрий Кленов',
    'g81670f73': 'Банк «Траст»',
    'gf0b712ef': 'Олег Дерипаска',
    'g5fd0e682': 'Леонид Блаватник',                     # в заголовке «Л.Блаватник», в тексте полностью
    'g560e3f93': '«Абрау-Дюрсо»',
    'gecf3eca5': 'ALD Automotive',
    # Продавец уже был в базе, но лежал в поле «предмет сделки» — см. ROLE_FIX.
    'ga69530bc': 'ООО «Технологии и моторы» (S7)',
    'gbc0b68bd': '«Фаберлик»',
    'g4fc7af86': 'Ipsos SA',
    'g5a22a31a': 'Агрохолдинг «Степь»',
    'g5a1ee21e': 'НЛМК',
    'g88d5e740': 'НЛМК',
    'g8ce554c5': '«Рамо-М»',
}

# Профиль продавца стоял в `target`: предметом сделки числился сам продавец.
# Механика прогона 32 — профиль переезжает в `seller_id`, `target` очищается,
# а флаг `target_was_seller` объясняет на экране, почему у сделки нет карточки
# предмета (продан актив, у которого своего профиля в базе нет).
ROLE_FIX = {
    'ga69530bc': 'g985f25da',   # продано: акции БЭМЗ
    'gbc0b68bd': 'g2e17f275',   # продано: фабрика по пошиву одежды
    'g4fc7af86': 'g47ea94cf',   # продано: 80% российского бизнеса
    'g5a22a31a': 'g63ba8735',   # продаются: портовые активы в Азове и Волгодонске
    'g5a1ee21e': 'gaf725105',   # продаются: американские заводы
    'g88d5e740': 'gaf725105',   # продаётся: сортовой дивизион
    'g8ce554c5': 'g91552e84',   # продан: участок земли
}

# Прочитано и отвергнуто.
SKIP = {
    'g2369d101': 'продавец назван описательно — «дочка Сибура»; юрлицо не названо, '
                 'а сам «Сибур» продавцом не выступал',
    'gea8ea954': 'продавец и предмет — одно имя: Flowwow продаёт собственное российское '
                 'юрлицо, строка «Продавец: Flowwow → Предмет: Flowwow» ничего не добавляет',
    'g549ddd5a': 'у карточки перепутаны все три роли: покупателем стоит проданный завод '
                 '«Масленица», а покупатель (ЭФКО) не записан вовсе — это правка ролей, '
                 'а не заполнение продавца',
}
# Продавец записан, но у карточки остаётся ДРУГОЙ дефект ролей: предметом сделки
# стоит покупатель. Это не мешает заполнить продавца и чинится отдельно (бэклог
# A21), поэтому карточки остаются в TABLE, а не уходят в SKIP.
KNOWN_ROLE_DEFECT = {
    'g5b337455': 'предметом сделки стоит покупатель — ООО «Промышленные инвестиции»',
    'g05ca1a94': 'предметом сделки стоит покупатель — банк «Траст»',
    'g12115ab1': 'предметом сделки стоит покупатель — Raven Russia',
}

WORD = re.compile(r"[\w%,.]+", re.U)


def norm(s):
    return re.sub(r'\s+', ' ', str(s or '')).strip()


def bare(word):
    return word.strip('«»"(),.;:%').lower()


def same_word(a, b):
    """Одно и то же слово с точностью до окончания."""
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


def fits(result, source):
    """Ложится ли результат на кусок источника слово в слово."""
    rw = [w for w in WORD.findall(result) if bare(w)]
    sw = [w for w in WORD.findall(source) if bare(w)]
    return any(all(same_word(a, b) for a, b in zip(rw, sw[i:i + len(rw)]))
               for i in range(len(sw) - len(rw) + 1))


def texts(deal):
    eco = deal.get('eco') or {}
    return [norm(deal.get('title')), norm(deal.get('extra')), norm(eco.get('share')),
            norm(eco.get('rationale')), norm(eco.get('context'))]


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
        # Главная проверка: имя взято из текста этой же карточки, а не сочинено.
        assert any(fits(name, t) for t in texts(deal) if t), \
            '%s: имя не ложится на текст карточки (%r)' % (deal_id, name)
        buyer = comps.get(deal.get('buyer'), {}).get('name') if deal.get('buyer') else None
        assert not buyer or bare(buyer) != bare(name), \
            '%s: продавец совпал с покупателем' % deal_id
        # Совпадение с предметом молча не пропускаем: либо это разные стороны,
        # либо карточка обязана лежать в ROLE_FIX с профилем.
        for field in ('target', 'asset_id'):
            other = comps.get(deal.get(field), {}).get('name') if deal.get(field) else None
            if other and bare(other) == bare(name):
                assert ROLE_FIX.get(deal_id) == deal.get(field) and field == 'target', \
                    '%s: продавец стоит в поле %s — решение не записано' % (deal_id, field)
        if deal_id in ROLE_FIX:
            cid = ROLE_FIX[deal_id]
            profile = comps.get(cid)
            assert profile, '%s: нет профиля %s' % (deal_id, cid)
            assert deal.get('target') == cid, '%s: ожидали профиль продавца в target' % deal_id
            assert bare(profile['name']) == bare(name) or bare(profile['name']) in bare(name), \
                '%s: профиль %r не совпадает с именем продавца' % (deal_id, profile['name'])
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


# Правило проверяется на себе: чужое имя ложиться не должно, а падежная форма — должна.
assert not fits('Иван Петров', 'приобрела Баимский проект у Романа Абрамовича')
assert fits('Роман Абрамович', 'приобрела Баимский проект у Романа Абрамовича')
assert fits('«Росатом»', 'выкупит 49% УК «Дело» у «Росатома»')

if __name__ == '__main__':
    main('--write' in sys.argv)
