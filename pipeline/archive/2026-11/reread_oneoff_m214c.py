# -*- coding: utf-8 -*-
"""Вычитка 12 ноября 2026, партия m214 (третья часть): то, чего не умеет review.py.

g1a626d5b (RuStore): Коммерсантъ, 16 июля 2026 года: «По данным ЕГРЮЛ, с 15 июля новым владельцем
  компании—разработчика RuStore (ООО «Много приложений») стал ее гендиректор Дмитрий Панкрушев. До этого
  компания полностью принадлежала дочерней организации МКПАО ВК — ООО «Компания ВК»». Дата — 15 июля 2026
  года по реестру; продавец — ООО «Компания ВК» (профиль g2ed1a259), а не МКПАО «ВК»; профиль RuStore —
  без «договорилась о продаже».
gc8fac4fb («Ниармедик»): 5 февраля 2026 года — день поста юристов Delcredere; «Медвестник» написал о
  покупке 29 декабря 2025 года («Владельцем сети клиник «Ниармедик» стала столичная «АВС-медицина»»),
  день перехода не назван, ЕГРЮЛ сети (ООО «ОК Ниармедик - Доктор рядом») не открылся — дата годом 2025.
  Профиль сети — без устаревшего «АФК ищет покупателя».
gd3769bb9 (Е-ПРОМ): продавец не назван — где искали записано в accepted_notes; из профиля снят
  неподтвержденный «единственный учредитель Булат Валиев».

    python3 pipeline/archive/2026-11/reread_oneoff_m214c.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY, DAY = 'reread_oneoff_m214c', '2026-11-12'
KOM = 'https://www.kommersant.ru/doc/8816553'
KOM_Q = ('По данным ЕГРЮЛ, с 15 июля новым владельцем компании—разработчика RuStore (ООО «Много приложений») стал ее '
         'гендиректор Дмитрий Панкрушев. До этого компания полностью принадлежала дочерней организации МКПАО ВК — '
         'ООО «Компания ВК».')
MV = 'https://medvestnik.ru/content/news/avs-medicina-vykupila-kliniki-niarmedik.html'
MV_Q = ('29.12.2025 … Владельцем сети клиник «Ниармедик» стала столичная «АВС-медицина». — день перехода не назван, '
        '5 февраля 2026 года — день поста юристов; дата годом.')
PROFILES = {
    'gb233260a': ('Российский магазин приложений', 'Российский магазин приложений для Android и «Авроры»; его разрабатывает '
                  'ООО «Много приложений». В июле 2026 года VK продал 100% этой компании ее гендиректору Дмитрию Панкрушеву.'),
    'gd0791726': ('Объединенная сеть медицинских клиник', 'Сеть многопрофильных клиник в Москве и Обнинске, созданная '
                  'объединением «Ниармедика» и «Доктор рядом»; управляет ею ООО «ОК Ниармедик - Доктор рядом».'),
    'g876ac66c': ('Производитель зарядных станций', 'Производитель зарядных станций для электромобилей; поставил больше '
                  '1400 быстрых станций в 42 региона России.'),
}
NO_SELLER = ('Продавец 49,99% долей Е-ПРОМ не назван: Advance Capital называет себя консультантом самой Е-ПРОМ. Где '
             'искали: пресс-релиз Advance Capital, «Ведомости» (23.09.2025), пост BIRCH (@LawFirms), поиск ИНН и '
             'истории участников ООО «Е-ПРОМ» (Зеленодольск) — ФНС, companies.rbc.ru, audit-it.ru — не открылись '
             'или не нашли юрлицо.')


def apply(data):
    by = {d['id']: d for d in data['deals']}
    comps = data['companies']
    n = 0
    c = by['g1a626d5b']
    if c['date'] != '2026-07-15':
        assert c['date'] == '2026-07-16', c['date']
        c['date'] = '2026-07-15'
        c['date_basis'] = 'registry'
        fact_edit_guard.log(c, 'date', '2026-07-15', KOM_Q, KOM, BY, DAY)
        n += 1
    if c.get('seller_id') != 'g2ed1a259':
        assert c.get('seller_id') == 'g4e694234' and c.get('seller') == 'VK', (c.get('seller_id'), c.get('seller'))
        c['seller_id'] = 'g2ed1a259'
        c['seller'] = 'ООО «Компания ВК»'
        fact_edit_guard.log(c, 'seller_id', 'g2ed1a259', KOM_Q, KOM, BY, DAY)
        fact_edit_guard.log(c, 'seller', 'ООО «Компания ВК»', KOM_Q, KOM, BY, DAY)
        n += 1
    if comps['gb233260a'].get('legal_short') != 'ООО «Много приложений»':
        comps['gb233260a']['legal_short'] = 'ООО «Много приложений»'
        n += 1
    c = by['gc8fac4fb']
    if c['date'] != '2025':
        assert c['date'] == '2026-02-05', c['date']
        c['date'] = '2025'
        fact_edit_guard.log(c, 'date', '2025', MV_Q, MV, BY, DAY)
        n += 1
    c = by['gd3769bb9']
    notes = c.setdefault('accepted_notes', {}).setdefault('no_profile', {})
    if notes.get('seller') != NO_SELLER:
        notes['seller'] = NO_SELLER
        n += 1
    for pid, (start, new) in PROFILES.items():
        if comps[pid].get('desc') != new:
            assert comps[pid].get('desc', '').startswith(start), pid
            comps[pid]['desc'] = new
            n += 1
    return n


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    old, data = json.loads(raw), json.loads(raw)
    n = apply(data)
    if not n:
        print('Уже применено.')
        return 0
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    bad = fact_edit_guard.unbacked(old, data)
    assert not bad, bad
    if not write:
        print('Сухой прогон: %d правок. Запись — с ключом --write.' % n)
        return 0
    fresh_raw = open(DATA, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    apply(fresh)
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
    print('ЗАПИСАНО: %d правок.' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
