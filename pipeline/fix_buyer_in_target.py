# -*- coding: utf-8 -*-
"""Бэклог A21: предметом сделки стоит ПОКУПАТЕЛЬ (или вовсе чужая компания).

ЧТО СЛОМАНО. У шести карточек в поле «предмет» стоит не то, что продали:
  * «Arconic продала 100% российского бизнеса ООО «Промышленные инвестиции»» —
    предметом числился покупатель;
  * «Банк «ФК Открытие» продал пакет акций ВТБ банку «Траст»» — предметом «Траст»;
  * «Raven Russia ведёт переговоры о приобретении логопарка у Smart Development» —
    предметом сам Raven Russia;
  * «Приобретение «М.Видео» 100% ООО «Эльдорадо» у группы «Сафмар»» — предметом
    «М.Видео»;
  * «Эксойл» продал завод «Масленица» компании ЭФКО» — перепутаны все три роли:
    предметом стоял продавец, покупателем — проданный завод;
  * «ЛабКвест приобрела 90% долей ФораЛаб» — предметом стоял банк
    «Санкт-Петербург», не имеющий к сделке отношения.
На экране это плашка «Продавец → Предмет сделки → Покупатель», в которой предмет
и покупатель — одна и та же компания. Хуже пустого поля: пустое честно.

ПОЧЕМУ ЭТО НЕ ПАРТИЯ, А ШЕСТЬ КАРТОЧЕК. Механического замера у класса нет, и
это проверено двумя правилами:
  * «имя профиля из `target` стоит в заголовке ПЕРЕД глаголом покупки» — 6
    кандидатов, из них верен 1 (g12115ab1). Остальные пять — правильные записи:
    «Продажа акций АО «Разрез «Степановский» на торгах», «Pre-IPO раунд АО
    «Х-Скаут» для приобретения…», «Топ-менеджер АТОЛ выкупил 100% акций»;
  * «в тексте карточки покупателем назван тот же профиль, что стоит предметом» —
    5 кандидатов, все ложные: правило захватывает хвост фразы («Покупатель —
    банк приобрел 73% долей в ООО «РБТОЧКАРУ»»), а два оставшихся — честные
    buyback («Магнит» выкупил свои акции, «ЛУКОЙЛ» — у нерезидентов).
Вывод записан в бэклог: класс находится чтением, а не правилом. Все шесть
карточек этого скрипта найдены при чтении 540 карточек в прогонах 40–44.

ЧТО ПРОВЕРЯЕТСЯ ПЕРЕД ЗАПИСЬЮ. Поле должно содержать ровно тот профиль, который
мы собираемся переставить (иначе скрипт падает), название предмета обязано
дословно лежать в тексте карточки, а после правки ни одна компания не занимает
в сделке двух ролей.

Запуск:
    python3 pipeline/fix_buyer_in_target.py            # сухой прогон
    python3 pipeline/fix_buyer_in_target.py --write    # записать
"""
import json
import re
import sys

PATH = 'static/data/deals_promoted.json'

# id -> что сделать. `move` — из какого поля в какое переезжает профиль,
# `asset` — название предмета текстом (профиля у него в базе нет).
PLAN = {
    'g5b337455': {'target_to_buyer': 'g389d0bbb', 'asset': 'Самарский завод'},
    'g05ca1a94': {'target_to_buyer': 'gdc4235da', 'asset': 'пакет акций ВТБ (9,08%)'},
    'g12115ab1': {'target_to_buyer': 'g21d61789', 'asset': 'логопарк в Красногорске'},
    'g937ef5d4': {'target_to_buyer': 'g444cac01', 'asset': 'ООО «Эльдорадо»'},
    # у этой карточки перепутаны все три роли сразу
    'g549ddd5a': {'target_to_seller': 'gecb9dad0', 'buyer_to_target': 'gc30a99a3',
                  'new_buyer': 'g5db3de73', 'seller_text': '«Эксойл»'},
    # профиль в `target` не имеет отношения к сделке — снимаем, предмет текстом
    'g68297df0': {'drop_target': 'gf881a88f', 'asset': 'ФораЛаб'},
}

WORD = re.compile(r"[\w%,.]+", re.U)


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


def texts(deal):
    eco = deal.get('eco') or {}
    return [t for t in [norm(deal.get('title')), norm(deal.get('extra')),
                        norm(eco.get('share')), norm(eco.get('rationale'))] if t]


ROLE_PAIRS = (('buyer', 'target'), ('buyer', 'seller_id'), ('target', 'seller_id'),
              ('buyer', 'asset_id'), ('seller_id', 'asset_id'), ('target', 'asset_id'))


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    comps = data['companies']

    done = sum(1 for i, p in PLAN.items()
               if 'target_to_buyer' in p and by_id[i].get('buyer') == p['target_to_buyer'])
    if done == sum(1 for p in PLAN.values() if 'target_to_buyer' in p):
        print('Уже применено.')
        return
    assert done == 0, 'скрипт применён частично'

    planned = []
    for deal_id, plan in PLAN.items():
        deal = by_id.get(deal_id)
        assert deal is not None, 'нет сделки %s' % deal_id
        src = texts(deal)
        if 'target_to_buyer' in plan:
            cid = plan['target_to_buyer']
            assert deal.get('target') == cid, \
                '%s: в target не %s, а %r' % (deal_id, cid, deal.get('target'))
            assert not deal.get('buyer') and not deal.get('buyer_name'), \
                '%s: покупатель уже заполнен' % deal_id
        if 'drop_target' in plan:
            assert deal.get('target') == plan['drop_target'], '%s: в target не тот профиль' % deal_id
        if 'target_to_seller' in plan:
            assert deal.get('target') == plan['target_to_seller'], '%s: в target не тот профиль' % deal_id
            assert deal.get('buyer') == plan['buyer_to_target'], '%s: в buyer не тот профиль' % deal_id
            assert not deal.get('seller') and not deal.get('seller_id'), \
                '%s: продавец уже заполнен' % deal_id
            assert any(fits(plan['seller_text'], t) for t in src), \
                '%s: имя продавца не ложится на текст карточки' % deal_id
            assert comps.get(plan['new_buyer']), '%s: нет профиля покупателя' % deal_id
            assert any(fits(comps[plan['new_buyer']]['name'], t) for t in src), \
                '%s: покупатель не назван в тексте карточки' % deal_id
        if 'asset' in plan:
            assert any(fits(plan['asset'], t) for t in src), \
                '%s: название предмета не ложится на текст карточки (%r)' % (deal_id, plan['asset'])
            assert not deal.get('asset'), '%s: поле asset уже заполнено' % deal_id
        planned.append((deal_id, plan, deal))

    print('Карточек к правке: %d' % len(planned))
    for deal_id, plan, deal in planned:
        print('  %s  %s' % (deal_id, ', '.join(
            ('%s=%s' % (k, comps[v]['name'] if v in comps else v)) for k, v in plan.items())))

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    for deal_id, plan, deal in planned:
        if 'target_to_buyer' in plan:
            deal['buyer'] = plan['target_to_buyer']
            deal['target'] = None
        if 'drop_target' in plan:
            deal['target'] = None
        if 'target_to_seller' in plan:
            deal['seller_id'] = plan['target_to_seller']
            deal['seller'] = plan['seller_text']
            deal['seller_src'] = 'text'
            deal['target'] = plan['buyer_to_target']
            deal['buyer'] = plan['new_buyer']
        if 'asset' in plan:
            deal['asset'] = plan['asset']

    # После правки ни одна компания не занимает в сделке двух ролей.
    bad = [(d['id'], a, b) for d in data['deals'] for a, b in ROLE_PAIRS
           if d.get(a) and d.get(a) == d.get(b)]
    assert not bad, 'одна компания в двух ролях: %s' % bad[:3]

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано. Исправлено карточек: %d.' % len(planned))


assert fits('Самарский завод', 'Arconic продала 100% российского алюминиевого бизнеса (Самарский завод)')
assert not fits('Казанский завод', 'Arconic продала 100% российского алюминиевого бизнеса (Самарский завод)')

if __name__ == '__main__':
    main('--write' in sys.argv)
