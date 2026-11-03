# -*- coding: utf-8 -*-
"""Вычитка 3 ноября 2026 (партия ne): то, что review.py не умеет.

1. RETRACTED: g6206d0f7 (IPO GloraX) — сумма «16 млрд ₽» не стоит ни в одной статье: размер IPO —
   2,1 млрд ₽ (пресс-релиз GloraX 31.10.2025: «Размер IPO составил 2,1 млрд рублей»), капитализация
   с допэмиссией — 18,1 млрд ₽. Сумма меняется записью FIXES партии ne; здесь — защита от возврата
   (docs/card_money.md, «После правки или снятия суммы»).
2. LEGAL_SHORT (находка приемки party_legal_form:target у g711eb87e): party_legal_names.py не
   разбирает реестровые имена ПАО НК "РУССНЕФТЬ" и БАНК "ТРАСТ" (ПАО) — ставим вручную по полному
   наименованию из /api/companies/<id>/fns.
3. LAW.ADV g6206d0f7: «Nextons — юридический консультант эмитента» с пометкой «Источник:
   обогащение/веб-поиск» не подтверждает ни одна статья, пресс-релизы GloraX и поиск (3 ноября 2026;
   сайт nextons.ru отдает 503). VERBA LEGAL (консультант банков-организаторов) подтвержден постом
   в @LawFirms/9767 — остается. Пустое поле честнее неподтвержденного консультанта.
4. SRC g6206d0f7: t.me/LKPconsult/3527 — пост о сервисе Роспатента по ставкам роялти, не об этой
   сделке (про IPO GloraX — соседний пост 3528, комментарий юриста ЛКП, а не консультанта сделки).
   Источник доказанно чужой — снимается (docs/card_editing.md, «Источники»).
5. THEMES g6206d0f7: «Продажа с торгов» у IPO — тема только для продажи с молотка, не для
   биржевых торгов (docs/card_parties.md, «Темы сделки»).
6. NO_PARTIES geb18dcad: выкуп ТМК собственных акций у несогласных акционеров — продавцов-миноритариев
   не называет ни одна статья; как у «Полюса» (g06b7ba6e), отсутствие пары объясняется словами,
   а не «Продавец: не раскрыт».
7. DESC профиля «Платежный сервис А3» (g5a8d6013): «Платежный сервис (ООО «А3»)» — неверное юрлицо
   (в реестре ООО «Платежный сервис А3», ИНН 7702726396), а пост брал из него «Предмет: … —
   платежный сервис (» (находка приемки post). Первая фраза — кто это, по Forbes/Интерфаксу.

После записи — python3 pipeline/facts_derive.py --write.

    python3 <этот файл>            # сухой прогон
    python3 <этот файл> --write    # записать (из корня репозитория, после review.py --write)
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

RETRACT = [('g6206d0f7', 'sum', '16 млрд ₽')]
LEGAL = [  # профиль, имя (для сверки), legal_short
    ('g839c87d5', 'РуссНефть', 'ПАО НК «РуссНефть»'),
    ('gdc4235da', 'Траст', 'ПАО Банк «Траст»'),
]
ADV_DROP = [('g6206d0f7', 'Nextons')]
SRC_DROP = [('g6206d0f7', 'https://t.me/LKPconsult/3527')]
THEME_DROP = [('g6206d0f7', 'Продажа с торгов')]
NO_PARTIES = [('geb18dcad',
               'Выкуп компанией собственных акций у акционеров, несогласных с реорганизацией: продавцы — '
               'миноритарии, их имена не раскрываются.')]
DESC = [('g5a8d6013',
         'Платежный сервис (ООО «А3»); в 2025 году 80% купил фонд Brio Capital у прежнего единственного '
         'владельца Артура Хримяна.',
         'Инфраструктура регулярных онлайн-платежей для банков: ЖКУ, связь, штрафы, налоги. ООО «Платежный '
         'сервис А3» основано в 2010 году; в 2025 году 80% купил фонд Brio Capital у Артура Хримяна.')]


def main(write=False):
    raw = open(DATA, encoding='utf-8').read()          # перечитать прямо перед записью
    data = json.loads(raw)
    deals = {d['id']: d for d in data['deals']}
    comps = data['companies']
    for did, field, val in RETRACT:
        d = deals[did]
        cur = d.get(field)
        if cur == val:
            assert not write, '%s: %s все еще %r — сначала review.py --write' % (did, field, cur)
            print('%s: %s все еще %r (сухой прогон до review.py --write)' % (did, field, cur))
        lst = d.setdefault('retracted', {}).setdefault(field, [])
        if val not in lst:
            lst.append(val)
            print('%s: retracted.%s += %r' % (did, field, val))
    for cid, name, legal in LEGAL:
        p = comps[cid]
        assert p.get('name') == name, '%s: имя %r' % (cid, p.get('name'))
        assert p.get('legal_short') in (None, legal), '%s: legal_short уже %r' % (cid, p.get('legal_short'))
        if p.get('legal_short') != legal:
            print('%s: legal_short -> %s' % (cid, legal))
            p['legal_short'] = legal
    for did, firm in ADV_DROP:
        adv = deals[did]['law']['adv']
        keep = [a for a in adv if a[1] != firm]
        if len(keep) != len(adv):
            assert len(adv) - len(keep) == 1, adv
            print('%s: law.adv без %s' % (did, firm))
            deals[did]['law']['adv'] = keep
    for did, url in SRC_DROP:
        src = deals[did]['src']
        keep = [s for s in src if s[1] != url]
        if len(keep) != len(src):
            assert keep, '%s: не остается ни одного источника' % did
            print('%s: src без %s' % (did, url))
            deals[did]['src'] = keep
    for did, theme in THEME_DROP:
        th = deals[did].get('themes') or []
        if theme in th:
            print('%s: themes без %s' % (did, theme))
            deals[did]['themes'] = [t for t in th if t != theme]
    for did, text in NO_PARTIES:
        d = deals[did]
        assert d.get('no_parties') in (None, text), '%s: no_parties %r' % (did, d.get('no_parties'))
        assert not d.get('seller') and not d.get('seller_id'), did
        if d.get('no_parties') != text:
            print('%s: no_parties -> %s' % (did, text))
            d['no_parties'] = text
    for cid, old, new in DESC:
        p = comps[cid]
        assert p.get('desc') in (old, new), '%s: desc %r' % (cid, p.get('desc'))
        if p['desc'] != new:
            print('%s: desc -> %s' % (cid, new))
            p['desc'] = new
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    out = json.dumps(data, ensure_ascii=False, indent=1)
    if raw.endswith('\n'):
        out += '\n'
    open(DATA, 'w', encoding='utf-8').write(out)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
