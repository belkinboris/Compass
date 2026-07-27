# -*- coding: utf-8 -*-
"""Бэклог A15: продавец назван в тексте в родительном падеже.

ЗАЧЕМ. Продолжение прогона 32: там заполнены 22 продавца из формулировок вида
«продавцом выступил X» — имя уже стоит в именительном падеже и переносится
дословно. Осталась вторая формула — «купил Y У X»: «у Светланы Рыбальченко»,
«у Александра Рязанова». Имя есть, но в родительном падеже.

ПОЧЕМУ ЭТО ОТДЕЛЬНЫЙ СКРИПТ. Главный инвариант прошлых прогонов —
«результат обязан быть дословным куском текста карточки» — здесь не работает:
«Светлана Рыбальченко» в тексте не встречается ни разу. Прямо записать
родительный падеж нельзя: на экране получится «Продавец: Светланы
Рыбальченко».

ЧЕМ ЗАМЕНЁН ИНВАРИАНТ. Проверкой падежа: результат обязан слово в слово
ложиться на кусок исходного текста, отличаясь ТОЛЬКО окончаниями. Совпадением
двух слов считаем общее начало не короче 3 знаков и не меньше 60% длины
короткого слова — это разрешает «Светланы» → «Светлана» и «Козиной» →
«Козина», но запрещает подставить другое имя. Правило проверяется на себе:
в конце скрипта стоит assert, что «Иван Петров» на «у Александра Рязанова» не
ложится.

ЗАМЕР (прогон 34). Кандидатов с формулой «купил … у <Имя>» — 13, прочитаны все.
Годными признаны 9. Отклонены 4 — причины в SKIP: в двух случаях предложение
описывает ДРУГУЮ сделку (предыдущую смену собственника, более позднюю
консолидацию), в одном речь про опцион, в одном продавец и предмет — одно и то
же лицо, и что именно продано, из текста не следует.

Запуск:
    python3 pipeline/extract_sellers_genitive.py            # сухой прогон
    python3 pipeline/extract_sellers_genitive.py --write    # записать
"""
import json
import re
import sys

PATH = 'static/data/deals_promoted.json'

# id сделки -> имя продавца в именительном падеже
TABLE = {
    # 2019-04 · «Севергрупп» купила долю в «Ленте» — продавцы названы в заголовке
    'ge3195449': 'TPG и ЕБРР',
    # 2021-03 · Capital Group купила 16,6% «ТВК «Тишинка»
    'g4444b396': 'Козина Елена Александровна (8,3%) и Травин Сергей Олегович (8,3%)',
    # 2022-08 · структуры Потанина купили «Меридиан-Сервис»
    'g724e85ed': 'Александр Рязанов',
    # 2025-02 · ГАП «Ресурс» купила агрофирму «Рубеж»
    'ga95b1d54': 'Павел Артемов',
    # 2023-06 · Александр Орехов консолидировал ГК «Азот»
    'gb2d5da8c': 'Светлана Рыбальченко',
    # 2021-12 · Сбербанк выкупил «Союзмультфильм» — приватизация
    'gb8717464': 'Российская Федерация',
    # 2024-09 · «Русагро» получила контроль над «Агро-Белогорьем»
    'g97d9fa60': 'Лариса Ковалева (5%) и другие владельцы',
    # 2024-07 · СХП «Колос» купила «Колос Кубани»
    'g8e7eee71': 'Владислав Пономаренко',
    # 2023-11 · МТС купила 15% «Проектной среды»
    'g38129341': 'Мария и Юрий Висневские',
}

# Связь с профилем компании — только при точном совпадении названия.
LINK = {
    'g724e85ed': 'ga09351d2',   # профиль «Александр Рязанов» уже есть в базе
}

# Просмотрено и отвергнуто.
SKIP = {
    'g40d9cd2e': 'предложение описывает предыдущую смену собственника (апрель 2022), '
                 'а не эту сделку',
    'gb2ab7521': 'предложение про более позднюю консолидацию (октябрь 2020), продавец '
                 'этой сделки из него не следует',
    'g221e9139': 'речь про опцион на покупку, а не про состоявшуюся продажу',
    'g40477661': '«ФораЛаб» в этой карточке и продавец, и предмет — что именно продано, '
                 'из текста не следует',
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
    rw = WORD.findall(result)
    sw = WORD.findall(source)
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
            '%s: продавец уже заполнен' % deal_id
        # Главная проверка: имя отличается от текста карточки только окончаниями.
        assert any(fits(name, t) for t in texts(deal) if t), \
            '%s: имя не ложится на текст карточки' % deal_id
        buyer = comps.get(deal.get('buyer'), {}).get('name') if deal.get('buyer') else None
        assert not buyer or bare(buyer) != bare(name), \
            '%s: продавец совпал с покупателем' % deal_id
        cid = LINK.get(deal_id)
        if cid:
            profile = comps.get(cid)
            assert profile and bare(profile['name']) == bare(name), \
                '%s: профиль не совпадает с именем продавца' % deal_id
            assert cid not in (deal.get('buyer'), deal.get('target'), deal.get('asset_id')), \
                '%s: профиль уже занят другой ролью' % deal_id
        planned.append((deal_id, name, deal))

    print('Карточек к заполнению: %d (связано с профилем: %d; отклонено при чтении: %d)'
          % (len(planned), len(LINK), len(SKIP)))
    for deal_id, name, _ in planned:
        print('  %s  %s' % (deal_id, name))

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    for deal_id, name, deal in planned:
        deal['seller'] = name
        deal['seller_src'] = 'text'
        if deal_id in LINK:
            deal['seller_id'] = LINK[deal_id]
    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    filled = sum(1 for d in data['deals'] if d.get('seller_id') or norm(d.get('seller')))
    print('\nЗаписано. Продавец известен у %d карточек из %d.' % (filled, len(data['deals'])))


# Правило проверяется на себе: чужое имя ложиться не должно.
assert not fits('Иван Петров', 'приобрели 100% долей у Александра Рязанова')
assert fits('Александр Рязанов', 'приобрели 100% долей у Александра Рязанова')

if __name__ == '__main__':
    main('--write' in sys.argv)
