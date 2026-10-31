# -*- coding: utf-8 -*-
"""Имена владельцев не пишутся в заголовок и строку стороны (17 октября 2026).

Владелец и партнер: «вообще без имен, если не физик сторона» — «компании
Артема Молчанова» в посте выглядит желтушно. Снимаем имя из заголовка и
строки покупателя у трех карточек; проза карточки не трогается.

    python3 pipeline/fix_no_person_names_in_titles_2026_10_17.py          # сухой прогон
    python3 pipeline/fix_no_person_names_in_titles_2026_10_17.py --write
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

TITLES = {
    'g38bdff94': ('«РусГазДобыча» передала 49% ООО «Гидроиндустрия» (группа ГМС) компании Артема Молчанова',
                  '«РусГазДобыча» передала 49% ООО «Гидроиндустрия» (группа ГМС) компании «Гидромаш МСК»'),
    'g0dea398b': ('БКХ «Коломенский» Алексея Тулупова, владельца Sminex, купил российский бизнес финской Fazer',
                  'БКХ «Коломенский» купил российский бизнес финской Fazer'),
    'ga13c3ea7': ('Viterra продала 50% Зернового терминального комплекса «Тамань» компании «Доставка морем» Ильи Косых',
                  'Viterra продала 50% Зернового терминального комплекса «Тамань» компании «Доставка морем»'),
}
OLD_BUYER, NEW_BUYER = '«Гидромаш МСК» (Артем Молчанов)', '«Гидромаш МСК»'


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))      # перечитано прямо перед записью
    by_id = {d['id']: d for d in data['deals']}
    for did, (old, new) in TITLES.items():
        d = by_id[did]
        assert d['title'] == old, (did, d['title'])
        d['title'] = new
        print('%s: %s\n        → %s' % (did, old, new))
    g = by_id['g38bdff94']
    assert g['buyer_name'] == OLD_BUYER
    g['buyer_name'] = NEW_BUYER
    for ev in g['party_evidence']['buyer']:
        if ev['value'] == OLD_BUYER:
            ev['value'] = NEW_BUYER
    if g.get('post_preview'):
        g['post_preview'] = (g['post_preview']
                             .replace(TITLES['g38bdff94'][0], TITLES['g38bdff94'][1])
                             .replace(OLD_BUYER, NEW_BUYER))
        assert 'Молчанов' not in g['post_preview']
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
