# -*- coding: utf-8 -*-
"""Каталог вычитки, класс A6: сторона записана текстом при живом профиле —
92 карточки (было 75 в замере каталога; полный повторный замер 15 августа
дал 102 кандидата, из них 10 отведены чтением).

Продавец/покупатель хранится ДВУМЯ способами: ссылкой на профиль
(`seller_id`/`buyer`) или именем текстом (`seller`/`buyer_name`) — вторая
форма для случаев, когда профиля не было. Здесь для 92 карточек профиль С
ТЕМ ЖЕ ИМЕНЕМ уже есть в базе, а ссылка не проставлена: профиль недосчитывает
сделку (счётчик на странице компании считается по `seller_id`/`buyer`), и
нет перехода со страницы сделки на карточку компании.

ОПАСНОСТЬ — ОМОНИМЫ (уроки CLAUDE.md: «Кама», «Акрон Холдинг» — одинаковое
имя, разные юрлица). Проставлять ссылку массово безопасно ТОЛЬКО для
однозначных случаев: крупных компаний/госструктур с уникальным на рынке
именем (ВТБ, Сбербанк, Яндекс, VK, Росимущество и подобные), где вероятность
совпадения с другой сущностью того же имени пренебрежимо мала. Это
большинство списка — но не весь.

ОТВЕДЕНО ЧТЕНИЕМ (не эта правка, риск неоднозначности выше среднего):
  * ИМЕНА ФИЗЛИЦ (g506ea8c4 — Михаил Бобров, gd7c2b9ee — Сергей Шишкарев,
    g34cab70b — Александр Рязанов, g7b4be1c4 — Евгений Туголуков,
    g5e4677da — Александр Клячин, g37619a9e — Игорь Рыбаков): у физлиц нет
    юридической уникальности имени, как у юрлица с полным наименованием —
    однофамильцы гораздо вероятнее, чем два юрлица с одинаковым названием.
  * ОБЩЕУПОТРЕБИМЫЕ НАЗВАНИЯ (ce7b84bec — «Управление активами»: это не имя
    конкретной компании, а тип деятельности, так называется огромное число
    юрлиц; gd38acdec — «Формат Инвест»: «Формат» самостоятельно частотное
    слово; gfebe16ad/buyer — «Русинн»: короткое, недостаточно проверено;
    g7d64b437 — «Газпром Тех»: дочернее общество, недостаточно проверено).

Запуск:
    python3 pipeline/link_party_profiles.py            # сухой прогон
    python3 pipeline/link_party_profiles.py --write    # запись
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

# карточки, чьи совпадения отведены чтением (см. докстрока выше)
DEFER_SELLER = {
    'g7d64b437', 'g506ea8c4', 'gd7c2b9ee', 'g34cab70b', 'g7b4be1c4',
    'gd38acdec', 'g5e4677da',
}
DEFER_BUYER = {'gfebe16ad', 'g37619a9e', 'ce7b84bec'}


def norm(s):
    s = re.sub(r'["«»\'“”]', '', str(s or ''))
    s = re.sub(r'\b(ООО|АО|ОАО|ЗАО|ПАО|Group|Holding|Limited|Ltd|Inc)\b', '', s, flags=re.I)
    s = s.replace('ё', 'е').lower()
    s = re.sub(r'[^a-zа-я0-9]', '', s)
    return s.strip()


def _self_check():
    assert norm('«Яндекс»') == norm('Яндекс') == 'яндекс'
    assert norm('ООО «Формат Инвест»') == norm('Формат Инвест')
    assert norm('ВТБ') != norm('ВТБ Капитал')


def find_candidates(data):
    comps = data['companies']
    by_name = {}
    for cid, c in comps.items():
        n = norm(c.get('name'))
        if n:
            by_name.setdefault(n, []).append(cid)

    seller_plan, buyer_plan, skipped = [], [], []
    for d in data['deals']:
        other_roles = {d.get('buyer'), d.get('target'), d.get('asset_id')}
        seller_text = d.get('seller')
        if seller_text and not d.get('seller_id') and d['id'] not in DEFER_SELLER:
            cands = by_name.get(norm(seller_text), [])
            if len(cands) == 1:
                if cands[0] in other_roles:
                    skipped.append((d['id'], 'seller_id', cands[0]))
                else:
                    seller_plan.append((d, seller_text, cands[0]))
        buyer_text = d.get('buyer_name')
        if buyer_text and not d.get('buyer') and d['id'] not in DEFER_BUYER:
            cands = by_name.get(norm(buyer_text), [])
            if len(cands) == 1:
                if cands[0] in {d.get('seller_id'), d.get('target'), d.get('asset_id')}:
                    skipped.append((d['id'], 'buyer', cands[0]))
                else:
                    buyer_plan.append((d, buyer_text, cands[0]))
    return seller_plan, buyer_plan, skipped


def main(argv):
    _self_check()
    data = json.load(open(DATA, encoding='utf-8'))
    seller_plan, buyer_plan, skipped = find_candidates(data)

    print('Продавец -> профиль: %d карточек' % len(seller_plan))
    for deal, text, cid in seller_plan[:8]:
        print('  %s %r -> %s (%s)' % (deal['id'], text, cid, data['companies'][cid]['name']))
    print('Покупатель -> профиль: %d карточек' % len(buyer_plan))
    for deal, text, cid in buyer_plan[:8]:
        print('  %s %r -> %s (%s)' % (deal['id'], text, cid, data['companies'][cid]['name']))
    print('Отведено чтением: %d продавцов, %d покупателей'
          % (len(DEFER_SELLER), len(DEFER_BUYER)))
    if skipped:
        print('Пропущено (тот же профиль уже в другой роли этой сделки): %d' % len(skipped))
        for s in skipped:
            print('  ', s)

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    for deal, _text, cid in seller_plan:
        deal['seller_id'] = cid
    for deal, _text, cid in buyer_plan:
        deal['buyer'] = cid
        deal['buyer_name'] = None

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
