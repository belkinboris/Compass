# -*- coding: utf-8 -*-
"""Вычитка, марафон 12–13 ноября 2026, партия m206 (часть 1): то, что таблица правок не умеет.

- ge361bfa8 (Харитонин/Reckitt): 30–40 млрд ₽ — оценка инвестбанкира Пешкова всех активов, а не цена
  сделки: сумма «Не раскрыта», оценка с автором — в eco.val (docs/card_money.md, решение 13 ноября 2026);
  продавец — британская Reckitt Benckiser (профиль g5ba54588): российские юрлица принадлежат ей.
- ge0f7b957 (Газпромбанк/ГК «Эксперт»): профиль ГК «Эксперт» (gc4b2178f) в реестре ФНС был сопоставлен с
  ООО «МЦ Эксперт» (ИНН 4823075464) — это сеть клиник, которую в мае 2025 года купила «Мать и дитя»
  (в реестре сейчас ООО «Хавен» 99% и ООО «Клиника Мать и дитя» 1%), а не группа «Эксперт»: решение
  снято в brand_needs_inn. Покупатели — «мажоритарные акционеры», по имени не названы: заметка приемки.
- g0b081bb7 («Брусника»/ФСК): 1,8–2 млрд ₽ — оценка Дубейковского (Ricci), сумма «Не раскрыта»; стороны
  договорились, день договоренности не назван — дата годом; описание профиля участков без «продал».
- g352523e0 (IPO 1С): «1С не раскрывает свою отчетность» нет в источниках — снято.
- g27543cdc (ВСК): продавец текстом без долей и оговорки; «Условия сделки» — общее мнение юриста о таких
  сделках, а не условие этой — снято.
- gc7e0b5c9 (Tutu.ru/Travel.ru): опечатка в имени продавца («Технологий туризма»).

Без ключа — сухой прогон; --write пишет, перечитав базу прямо перед записью. Повторный запуск
ничего не ломает («уже применено»).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import fact_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY = 'вычитка m206, 13.11.2026'
IZ = 'https://iz.ru/2101186/denis-kuznetcov/na-proizvoditelya-durex-i-vanish-v-rossii-nashelsya-pretendent'
KOM_BR = 'https://www.kommersant.ru/doc/8499768'
KOM_VSK = 'https://www.kommersant.ru/doc/8209968'
SOSTAV = 'https://www.sostav.ru/publication/tutu-ru-kupil-domen-travel-ru-79706.html'
NONE = 'Не раскрыта'


def fingerprint(value):
    import review
    return review.fix_fingerprint(value)


def absorb(card, field, value):
    fp = fingerprint(value)
    lst = card.setdefault('proofread_absorbed', {}).setdefault(field, [])
    if fp not in lst:
        lst.append(fp)


def retract_sum(card, old, quote, url, out):
    if card.get('sum') == NONE and (card.get('eco') or {}).get('sum') == NONE:
        return
    assert card.get('sum') == old and card['eco'].get('sum') == old, (card.get('sum'), card['eco'].get('sum'))
    card['sum'] = NONE
    card['eco']['sum'] = NONE
    r = card.setdefault('retracted', {}).setdefault('sum', [])
    if old not in r:
        r.append(old)
    fact_edit_guard.log(card, 'sum', NONE, quote, url, BY)
    fact_edit_guard.log(card, 'eco.sum', NONE, quote, url, BY)
    out.append('%s sum -> Не раскрыта' % card['id'])


def apply(data):
    deals = {d['id']: d for d in data['deals']}
    comps = data['companies']
    out = []

    c = deals['ge361bfa8']
    retract_sum(c, '30–40 млрд ₽ (рыночная оценка)',
                'Все российские активы Reckitt инвестиционный банкир Иван Пешков оценивает в 30–40 млрд с учетом долга.',
                IZ, out)
    if c.get('seller_id') != 'g5ba54588':
        assert c.get('seller_id') is None and c.get('seller') is None, (c.get('seller_id'), c.get('seller'))
        assert comps['g5ba54588']['name'] == 'Reckitt Benckiser'
        c['seller_id'] = 'g5ba54588'
        fact_edit_guard.log(c, 'seller_id', 'g5ba54588',
                            'В нашей стране у Reckitt два юрлица — ООО «Рекитт Бенкизер Хэлскэр» (90% принадлежит '
                            'британской материнской структуре, оставшиеся 10% у немецкого подразделения) и ООО '
                            '«Рекитт Бенкизер» (на 100% контролируется головной британской организацией).', IZ, BY)
        out.append('ge361bfa8 seller_id -> g5ba54588')

    c = deals['ge0f7b957']
    notes = c.setdefault('accepted_notes', {}).setdefault('no_profile', {})
    why = ('покупатели — «мажоритарные акционеры» группы, по имени не названы ни в пресс-релизе Газпромбанка, '
           'ни в «Коммерсанте», ни в Vademecum; искали также поиском по сделке и по ООО «Барель» (ЕГРЮЛ из '
           'контейнера не открылся) — кто именно выкупил долю, не нашлось')
    if notes.get('buyer') != why:
        notes['buyer'] = why
        out.append('ge0f7b957 accepted_notes.no_profile.buyer')

    c = deals['g0b081bb7']
    retract_sum(c, '1,8–2 млрд ₽',
                'По его оценке, совокупная стоимость обоих проектов, проданных ГК ФСК «Бруснике», могла составить '
                'около 1,8–2 млрд руб.', KOM_BR, out)
    if c.get('date') != '2026':
        assert c.get('date') == '2026-03-13', c.get('date')
        c['date'] = '2026'
        for e in c.get('events') or []:
            if e.get('date') == '2026-03-13':
                e['date'] = '2026'
        fact_edit_guard.log(c, 'date', '2026',
                            'ГК ФСК Владимира Воронина договорилась о продаже двух площадок в Санкт-Петербурге '
                            'суммарной площадью 2,2 га оценочно за 1,8–2 млрд руб.', KOM_BR, BY)
        out.append('g0b081bb7 date -> 2026')
    p = comps['g8d88e734']
    desc = 'Два участка под жилую застройку в Санкт-Петербурге: на проспекте Обуховской Обороны и улице Ольги Берггольц.'
    if p.get('desc') != desc:
        assert p['desc'].startswith('Два участка под жилую застройку в Санкт-Петербурге (2,2 га'), p['desc']
        p['desc'] = desc
        out.append('g8d88e734 desc')

    c = deals['g352523e0']
    if c['eco'].get('target_fin') != '—':
        assert c['eco']['target_fin'] == '1С не раскрывает свою отчетность', c['eco']['target_fin']
        absorb(c, 'eco.target_fin', '1С не раскрывает свою отчётность')
        c['eco']['target_fin'] = '—'
        out.append('g352523e0 eco.target_fin -> —')

    c = deals['g27543cdc']
    seller = 'Сергей Цикалюк и ПАО «ЭсЭфАй»'
    if c.get('seller') != seller:
        assert c.get('seller') == 'Сергей Цикалюк (51%) и инвестхолдинг SFI (49%) — по неофициальным данным', c.get('seller')
        c['seller'] = seller
        fact_edit_guard.log(c, 'seller', seller,
                            'О том, что собственники страхового дома ВСК (51% у Сергея Цикалюка, 49% у '
                            'инвестиционного холдинга SFI, принадлежащего семье Гуцериевых) рассматривают продажу '
                            'компании целиком или частично, рассказали “Ъ” три собеседника на финансовом рынке.',
                            KOM_VSK, BY)
        out.append('g27543cdc seller')
    if c['law'].get('terms') != '—':
        old = c['law']['terms']
        assert old.startswith('По словам руководителя страховой практики МЭФ LEGAL Ивана Рыбакова'), old
        import review
        for f in review.FIXES:
            if f['id'] == 'g27543cdc' and f['field'] == 'law.terms':
                absorb(c, 'law.terms', f['new'])
        c['law']['terms'] = '—'
        out.append('g27543cdc law.terms -> —')

    c = deals['gc7e0b5c9']
    seller = 'ООО «Технологии туризма» и Rus Travel Group Ltd'
    if c.get('seller') != seller:
        assert c.get('seller') == 'ООО «Технологий туризма» и Rus Travel Group Ltd', c.get('seller')
        c['seller'] = seller
        fact_edit_guard.log(c, 'seller', seller,
                            'Ранее товарный знак принадлежал ООО «Технологии туризма», а домен — американской Rus '
                            'Travel Group Ltd.', SOSTAV, BY)
        out.append('gc7e0b5c9 seller')
    return out


def registry(write):
    """gc4b2178f: ООО «МЦ Эксперт» — купленная «Матерью и дитя» сеть клиник, а не группа «Эксперт»."""
    rows = json.load(open(os.path.join(ROOT, 'pipeline', 'fns_registry.json'), encoding='utf-8'))
    cur = [r for r in rows if r.get('company_id') == 'gc4b2178f']
    if cur and cur[0]['decision'] == 'brand_needs_inn':
        return []
    assert cur and cur[0]['inn'] == '4823075464', cur
    if write:
        import fns_notes_to_registry
        ok = fns_notes_to_registry.edit_registry_entry('gc4b2178f', {
            'company_id': 'gc4b2178f', 'decision': 'brand_needs_inn', 'inn': None,
            'reason': ('Вычитка m206, 13.11.2026: профиль — группа «Эксперт» (сеть «МРТ-Эксперт», основатель Елена '
                       'Латышева), а прежнее решение ставило ему ООО «МЦ Эксперт», ИНН 4823075464. Это купленная '
                       '«Матерью и дитя» в мае 2025 года сеть клиник: по истории участников ЕГРЮЛ с 22.05.2025 у нее '
                       'ООО «Хавен» 99% и ООО «Клиника Мать и дитя» 1%, до того — ООО «Барель» 99%. Юрлицо группы '
                       '(вероятно, ООО «Барель», где по «Коммерсанту» были доли структур Газпромбанка) — ИНН не найден. '
                       'Прежняя причина: ' + cur[0]['reason']),
            'date': '2026-11-13'})
        assert ok
    return ['fns_registry gc4b2178f -> brand_needs_inn']


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    out = apply(data) + registry(False)
    print('\n'.join(out) or 'уже применено')
    if '--write' in argv and out:
        data = json.load(open(DATA, encoding='utf-8'))      # перечитать прямо перед записью
        if apply(data):
            with open(DATA, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=1)
        registry(True)
        print('записано')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
