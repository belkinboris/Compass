# -*- coding: utf-8 -*-
"""Вычитка 13 ноября 2026, партия m109c, вторая часть: еще четыре карточки с находкой
`sum_is_expert_estimate`, сторона «Местный менеджмент» у Kerry и испорченный legal_short ТОКК.

Сумма — по правилу docs/card_money.md, «Что идет в сумму» (13 ноября 2026): оценка эксперта или
аналитика — не цена; sum и eco.sum «Не раскрыта», цифра с автором — в eco.val, старое — в retracted.sum.

g25a6766d (Baggins Coffee): Коммерсантъ — «Сумму сделки по покупке Baggins Coffee в компаниях не
  раскрыли. Гендиректор «Infoline-Аналитики» Михаил Бурмистров считает, что стоимость сети не
  превышает 350 млн руб.» — оценка аналитика всей сети.
g8e6dcf0b («Артмуза»): РИА Недвижимость — «Эксперты, опрошенные изданием [«Деловым Петербургом»],
  оценили сделку в 1,6 миллиарда рублей»; eco.val называет, чьи это эксперты.
gb42bc45e (Rostic's, Калуга): Коммерсантъ 9078223 — «Только ООО ТК, по оценке гендиректора
  «Infoline-Аналитики» Михаила Бурмистрова, стоит 50 млн руб.» — оценка компании, не цена.
g8b57089b (здание DDX): Коммерсантъ 9008489 — «По оценке старшего директора департамента оценки и
  консалтинга CMWP Антона Калистратова, рыночная стоимость проданного здания может составлять
  1,2–1,8 млрд руб.» — оценка консультанта.

g88dcf73e (Kerry): покупатель «Местный менеджмент» — описание, а не сторона. Российская «дочка» —
  ООО «Керри», ИНН 7707597514, ОГРН 5067746073115 (зарегистрировано 11 августа 2006 года; Kerry
  открыла ООО «Керри» в 2006 году — DairyNews). Datanewton, история участников по ОГРН: 16 июня
  2022 года 100% перешли от Kerry Group B.V. к нидерландской Apollo Ingredients Holding B.V.;
  15 июля 2022 года 0,1% — у Picard Investments B.V.; 18 января 2023 года общество переименовано
  в ООО «Олвин»; 2 декабря 2024 года участники записаны как «Аполло Ингредиентс Холдинг СПВ Лтд» и
  «Пикард Инвестментс Холдинг СПВ Лтд». Kerry (RTÉ/Reuters) называет покупателя местным
  менеджментом; кто владеет Apollo Ingredients Holding, открытые источники не говорят (искали:
  WebSearch по-русски и по-английски, datanewton, rusprofile/checko закрыты). Покупатель — юрлицо
  из реестра, версия Kerry — в «Как устроена сделка».

ТОКК (профиль tokk): реестр api-fns отдает short_name «ООО "ЗАВОД УПАКОВОЧНЫХ ИЗДЕЛИЙ ТОКК" И
  ООО "ЗУИ ТОКК"» — это полное и сокращенное имя ОДНОГО общества (ИНН 5040045543, ОГРН
  1025005119699, legal_name «ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "ЗАВОД УПАКОВОЧНЫХ ИЗДЕЛИЙ
  ТОКК"»), а legal_short собрал из них два юрлица. legal_short — по полному имени.

    python3 pipeline/archive/2026-11/reread_oneoff_m109cb.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY, DAY = 'reread_oneoff_m109cb', '2026-11-13'
NO = 'Не раскрыта'

SUMS = {
    'g25a6766d': ('350 млн ₽ (по оценке)',
                  'Сумму сделки по покупке Baggins Coffee в компаниях не раскрыли. Гендиректор «Infoline-Аналитики» '
                  'Михаил Бурмистров считает, что стоимость сети не превышает 350 млн руб. — оценка аналитика.',
                  'https://www.kommersant.ru/doc/9062977'),
    'g8e6dcf0b': ('1,6 млрд ₽ (по оценке)',
                  'Эксперты, опрошенные изданием, оценили сделку в 1,6 миллиарда рублей. — оценка экспертов, не цена.',
                  'https://realty.ria.ru/20261028/artmuza-2127458071.html'),
    'gb42bc45e': ('50 млн ₽ (по оценке)',
                  'Только ООО ТК, по оценке гендиректора «Infoline-Аналитики» Михаила Бурмистрова, стоит 50 млн руб. '
                  '— оценка компании аналитиком, не цена; условия всей сделки не раскрыты.',
                  'https://www.kommersant.ru/doc/9078223'),
    'g8b57089b': ('1,2–1,8 млрд ₽ (по оценке)',
                  'По оценке старшего директора департамента оценки и консалтинга CMWP Антона Калистратова, рыночная '
                  'стоимость проданного здания может составлять 1,2–1,8 млрд руб. — оценка консультанта, не цена.',
                  'https://www.kommersant.ru/doc/9008489'),
}
ESTIMATE_BASIS = ('g25a6766d',)

RIA = 'https://realty.ria.ru/20261028/artmuza-2127458071.html'
DN = 'https://datanewton.ru/api/v2/history?ogrn=5067746073115&startDate=2000-01-01&attributes=OWNERS'
RTE = 'https://www.rte.ie/news/business/2023/0216/1356949-kerry-group-full-year-results'
EGRUL_KERRY = ('Datanewton, ООО «Керри» (ИНН 7707597514, ОГРН 5067746073115), участники: 2022-06-16 было — ЧАСТНАЯ '
               'КОМПАНИЯ С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "КЕРРИ ГРУПП Б.В." 100.0%; стало — ЧАСТНАЯ КОМПАНИЯ С '
               'ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "АПОЛЛО ИНГРИДИЕНТС ХОЛДИНГ Б.В." 100.0%; 2022-07-15 — "АПОЛЛО '
               'ИНГРИДИЕНТС ХОЛДИНГ Б.В." 99.9%, "ПИКАРД ИНВЕСТМЕНТС Б.В." 0.1%; наименование 2023-01-18: ООО '
               '"КЕРРИ" → ООО "ОЛВИН"; 2024-12-02 — "АПОЛЛО ИНГРЕДИЕНТС ХОЛДИНГ СПВ ЛТД" 99.9%, "ПИКАРД '
               'ИНВЕСТМЕНТС ХОЛДИНГ СПВ ЛТД" 0.1%')
_KERRY_STRUCT = ('По ЕГРЮЛ, 16 июня 2022 года 100% ООО «Керри» (ИНН 7707597514) перешли от нидерландской Kerry Group '
                 'B.V. к нидерландской Apollo Ingredients Holding B.V.; в июле 2022 года 0,1% получила Picard '
                 'Investments B.V. В январе 2023 года общество переименовано в ООО «Олвин». Kerry называет '
                 'покупателя местным менеджментом российской компании; кто владеет Apollo Ingredients Holding, '
                 'открытые источники не сообщают.')
_KERRY_Q = (EGRUL_KERRY + ' || It also agreed a deal to divest 100% of the share capital of Kerry Limited Liability '
            'Company, its subsidiary in Russia, to local management.')
KERRY_BUYER_NOTE = ('Покупатель по ЕГРЮЛ (история участников ООО «Керри», ОГРН 5067746073115, datanewton) — '
                    'нидерландская Apollo Ingredients Holding B.V. (с декабря 2024 года — «Аполло Ингредиентс Холдинг '
                    'СПВ Лтд»); иностранное юрлицо, профиль не заводили. Kerry называет покупателя местным '
                    'менеджментом; владельцев Apollo искали 13 ноября 2026 (WebSearch по-русски и по-английски, '
                    'datanewton, отчет Kerry в пересказе RTÉ/Reuters) — не названы.')
KERRY_TARGET_NOTE = ('ООО «Керри» (ныне ООО «Олвин»), ИНН 7707597514, ОГРН 5067746073115 — найдено по истории '
                     'участников (datanewton) 13 ноября 2026; профиль предмета в этой партии не заводили.')

SETS = [
    ('g8e6dcf0b', 'eco.val',
     'Эксперты оценивают сделку в 1,6 млрд ₽. Партнер Rusland SP Дмитрий Лехмус считает, что после '
     'градостроительной подготовки площадка может подорожать до 2,6 млрд ₽ — это около 130 тыс. ₽ за квадратный '
     'метр будущих продаваемых площадей.',
     'Эксперты, опрошенные «Деловым Петербургом», оценили сделку в 1,6 млрд ₽. Партнер Rusland SP Дмитрий Лехмус '
     'считает, что после градостроительной подготовки площадка может подорожать до 2,6 млрд ₽ — это около 130 тыс. ₽ '
     'за квадратный метр будущих продаваемых площадей.',
     'стал миллиардер Андрей Гомон, сообщил "Деловой Петербург" . Эксперты, опрошенные изданием, оценили сделку в '
     '1,6 миллиарда рублей.', RIA),
    ('g88dcf73e', 'buyer_name', 'Местный менеджмент', 'Apollo Ingredients Holding B.V.', EGRUL_KERRY, DN),
    ('g88dcf73e', 'title', 'Местный менеджмент купил российскую дочернюю компанию Kerry Group',
     'Apollo Ingredients Holding купил российскую дочернюю компанию Kerry Group', EGRUL_KERRY, DN),
    ('g88dcf73e', 'law.struct', '—', _KERRY_STRUCT, _KERRY_Q, DN),
]
RETRACT = {('g88dcf73e', 'buyer_name')}

TOKK = ('tokk', 'ООО «Завод Упаковочных Изделий Токк" И ООО "зуи ТОКК»', 'ООО «Завод упаковочных изделий ТОКК»')


def _absorb(card, field, final, fixes):
    import review
    for r in fixes:
        if r.get('id') == card['id'] and r.get('field') == field and r.get('new') not in (None, final) \
                and isinstance(r.get('new'), str):
            box = card.setdefault('proofread_absorbed', {}).setdefault(field, [])
            fp = review.fix_fingerprint(r['new'])
            if fp not in box:
                box.append(fp)


def _get(c, path):
    if '.' in path:
        top, sub = path.split('.')
        return c[top], sub
    return c, path


def apply(data, fixes):
    by = {d['id']: d for d in data['deals']}
    n = 0
    for cid, (old, quote, url) in SUMS.items():
        c = by[cid]
        eco = c['eco']
        if c.get('sum') != NO:
            assert c.get('sum') == old, (cid, c.get('sum'))
            c['sum'] = NO
            box = c.setdefault('retracted', {}).setdefault('sum', [])
            if old not in box:
                box.append(old)
            fact_edit_guard.log(c, 'sum', NO, quote, url, BY, DAY)
            n += 1
        if eco.get('sum') != NO:
            assert eco.get('sum') == old, (cid, eco.get('sum'))
            eco['sum'] = NO
            fact_edit_guard.log(c, 'eco.sum', NO, quote, url, BY, DAY)
            n += 1
        if cid in ESTIMATE_BASIS and c.get('sum_basis') == 'estimate':
            del c['sum_basis']
            n += 1
        _absorb(c, 'sum', NO, fixes)
        _absorb(c, 'eco.sum', NO, fixes)
    for cid, path, old, new, quote, url in SETS:
        c = by[cid]
        o, k = _get(c, path)
        cur = o.get(k)
        if cur == new:
            continue
        assert cur == old, (cid, path, cur)
        o[k] = new
        if (cid, path) in RETRACT:
            box = c.setdefault('retracted', {}).setdefault(path, [])
            if old not in box:
                box.append(old)
        fact_edit_guard.log(c, path, new, quote, url, BY, DAY)
        _absorb(c, path, new, fixes)
        n += 1
    c = by['g88dcf73e']
    np_ = c.setdefault('accepted_notes', {}).setdefault('no_profile', {})
    if np_.get('buyer') != KERRY_BUYER_NOTE:
        np_['buyer'] = KERRY_BUYER_NOTE
        np_['target'] = KERRY_TARGET_NOTE
        n += 1
    comps = data['companies']
    p = comps[TOKK[0]]
    if p.get('legal_short') != TOKK[2]:
        assert p.get('legal_short') == TOKK[1], p.get('legal_short')
        p['legal_short'] = TOKK[2]
        n += 1
    return n


def main(write):
    import review
    fixes = review.load_fixes()
    raw = open(DATA, encoding='utf-8').read()
    old, data = json.loads(raw), json.loads(raw)
    n = apply(data, fixes)
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
    apply(fresh, fixes)
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
    print('ЗАПИСАНО: %d правок.' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
