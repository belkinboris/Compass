# -*- coding: utf-8 -*-
"""Бэклог A21, вторая половина: стороной сделки записан её ПРЕДМЕТ (и наоборот).

КАК НАШЛИСЬ. Правило прогона 45: «название предмета текстом (`asset`) не должно
совпадать с названием стороны, а имя стороны текстом (`buyer_name`, `seller`) —
с названием профиля в `target`/`asset_id`». В отличие от «предметом стоит
покупатель», у этого класса замер работает: правило нашло 4 карточки и ни одного
ложного срабатывания.

ЧТО СЛОМАНО.
  * «Wildberries & Russ приобрела сеть «Рив Гош»» — продавцом стоял сам «Рив
    Гош», то есть проданная компания. Продавцами были её акционеры, и текст
    карточки это прямо говорит: «советником акционеров Рив Гош».
  * «Yadro купила 25% Mind Software» — продавцом стояла Mind Software, то есть
    снова предмет сделки. Кто продал долю, в карточке не сказано, и поле
    становится пустым: пустое честнее неверного.
  * «Инвестиции Softline Venture Partners в сервис Kickidler» и «TMT Investments
    возглавил раунд в стартап Postoplan» — предметом сделки числился ИНВЕСТОР,
    он же записан покупателем. Предмет — компания, в которую вложились.

ЧТО ПРОВЕРЯЕТСЯ ПЕРЕД ЗАПИСЬЮ. Поля обязаны содержать ровно те значения, ради
которых правка написана; новое имя продавца и название предмета обязаны
дословно лежать в тексте карточки; после правки ни одна компания не занимает в
сделке двух ролей, а правило, которым карточки найдены, больше не срабатывает
ни на одной записи базы (оно же закреплено тестом `test_asset_is_not_a_party`).

Запуск:
    python3 pipeline/fix_party_in_asset.py            # сухой прогон
    python3 pipeline/fix_party_in_asset.py --write    # записать
"""
import json
import re
import sys

PATH = 'static/data/deals_promoted.json'

PLAN = {
    # продавцом стояла сама проданная компания
    'g94683ed2': {'seller_id_to_asset': 'g842a7fd2', 'seller_text': 'Акционеры Рив Гош'},
    'gfef815a9': {'seller_id_to_asset': 'g51fbca0d', 'seller_text': None},
    # предметом сделки стоял инвестор (он же покупатель)
    'g4ff4b24c': {'drop_target': 'gdfb4c0d4', 'asset': 'Kickidler'},
    'g938e85ca': {'drop_target': 'g5f515899', 'asset': 'Postoplan'},
}

WORD = re.compile(r"[\w%,.]+", re.U)
ROLE_PAIRS = (('buyer', 'target'), ('buyer', 'seller_id'), ('target', 'seller_id'),
              ('buyer', 'asset_id'), ('seller_id', 'asset_id'), ('target', 'asset_id'))


def norm(s):
    return re.sub(r'\s+', ' ', str(s or '')).strip()


def bare(word):
    return word.strip('«»"\'(),.;:%').lower()


def flat(s):
    return re.sub(r'[«»"\'(),.\s]', '', str(s or '')).lower()


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


def collisions(deals, comps):
    """То самое правило, которым найдены карточки."""
    bad = []
    for d in deals:
        for field, other in (('asset', 'buyer'), ('asset', 'seller_id')):
            name = comps.get(d.get(other), {}).get('name')
            if d.get(field) and name and flat(name) == flat(d[field]):
                bad.append((d['id'], field, other))
        if d.get('asset') and d.get('seller') and flat(d['seller']) == flat(d['asset']):
            bad.append((d['id'], 'asset', 'seller'))
        for text_field in ('buyer_name', 'seller'):
            val = d.get(text_field)
            for ref in ('target', 'asset_id'):
                name = comps.get(d.get(ref), {}).get('name')
                if val and name and flat(name) == flat(val):
                    bad.append((d['id'], text_field, ref))
    return bad


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    comps = data['companies']

    if not collisions(data['deals'], comps):
        print('Уже применено: правило не срабатывает ни на одной карточке.')
        return

    planned = []
    for deal_id, plan in PLAN.items():
        deal = by_id.get(deal_id)
        assert deal is not None, 'нет сделки %s' % deal_id
        src = texts(deal)
        if 'seller_id_to_asset' in plan:
            cid = plan['seller_id_to_asset']
            assert deal.get('seller_id') == cid, '%s: в seller_id не %s' % (deal_id, cid)
            assert not deal.get('asset_id'), '%s: asset_id уже заполнен' % deal_id
            if plan['seller_text']:
                assert any(fits(plan['seller_text'], t) for t in src), \
                    '%s: имя продавца не ложится на текст карточки' % deal_id
        if 'drop_target' in plan:
            assert deal.get('target') == plan['drop_target'], \
                '%s: в target не %s, а %r' % (deal_id, plan['drop_target'], deal.get('target'))
            assert not deal.get('asset'), '%s: поле asset уже заполнено' % deal_id
            assert any(fits(plan['asset'], t) for t in src), \
                '%s: название предмета не ложится на текст карточки (%r)' % (deal_id, plan['asset'])
        planned.append((deal_id, plan, deal))

    print('Карточек к правке: %d' % len(planned))
    for deal_id, plan, _ in planned:
        print('  %s  %s' % (deal_id, plan))

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return

    for deal_id, plan, deal in planned:
        if 'seller_id_to_asset' in plan:
            deal['asset_id'] = plan['seller_id_to_asset']
            deal['seller_id'] = None
            if plan['seller_text']:
                deal['seller'] = plan['seller_text']
                deal['seller_src'] = 'text'
            else:
                deal['seller'] = None
                deal.pop('seller_src', None)
        if 'drop_target' in plan:
            deal['target'] = None
            deal['asset'] = plan['asset']

    left = collisions(data['deals'], comps)
    assert not left, 'правило всё ещё срабатывает: %s' % left[:3]
    bad = [(d['id'], a, b) for d in data['deals'] for a, b in ROLE_PAIRS
           if d.get(a) and d.get(a) == d.get(b)]
    assert not bad, 'одна компания в двух ролях: %s' % bad[:3]

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    filled = sum(1 for d in data['deals'] if d.get('seller_id') or norm(d.get('seller')))
    print('\nЗаписано. Исправлено карточек: %d. Продавец известен у %d из %d.'
          % (len(planned), filled, len(data['deals'])))


assert fits('Акционеры Рив Гош', 'выступила советником акционеров Рив Гош')
assert not fits('Акционеры Рив Гош', 'выступила советником акционеров Магнита')

if __name__ == '__main__':
    main('--write' in sys.argv)
