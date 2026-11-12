# -*- coding: utf-8 -*-
"""Вычитка 12 ноября 2026, партия m062 (часть 2): правки, которые не ложатся в таблицу FIXES.

Что чинит: даты и стороны по истории участников ЕГРЮЛ (party_legal_names.py), суммы, которых нет ни в одном
источнике (снимаются в «Не раскрыта», снятое — в retracted), продавца, которого источник не называет,
описания профилей с действием стороны. Каждая правка факта — с цитатой источника (fact_edit_guard.log).

    python3 pipeline/archive/2026-11/reread_oneoff_m062b.py           # сухой прогон
    python3 pipeline/archive/2026-11/reread_oneoff_m062b.py --write   # запись

База перечитывается прямо перед записью; у каждой правки assert на старое значение; повторный
запуск — «уже применено».
"""
import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY = 'reread m062'
_MISSING = object()
_API = 'https://projectcompass.ru/api/companies/%s/fns'

_BZ_REG = ('ЕГРЮЛ, ООО «Базелевс», ИНН 7723575123: 21.03.2022 вышел Бекмамбетов Тимур Нуруахитович (100%), вошла '
           'Рустамова Лала Илгаровна (100%); 10.01.2023 доля Рустамовой 100% → 50%, вошел Асадов Тимур Арифджанович (50%)')
_BZ_LEGAL = ('Сделка затронула только российское юрлицо Bazelevs — ООО «Базелевс» — за ним останутся права на русскоязычный '
             'контент. Бекмамбетов из российского бизнеса полностью вышел, у него остаётся только американское производство. '
             '… Сделка не коснулась рекламного бизнеса — ООО «Базелевс Реклама». … Сделка пока еще находится в процессе, ее '
             'собираются завершить через несколько месяцев')
_BZ_URL = 'https://www.sostav.ru/publication/timur-bekmambetov-prodal-kinostudiyu-bazelevs-e-prodyuseram-58276.html'
_PM_OWN = ('В 2021 г. основным владельцем компании стал Воротынцев, его доля составила 56%. По 8% получили Сергей Куликовский … '
           'и Сергей Германович . 20% отошли к Ольге Беловой … В конце 2022 г. 51% доля в «Полиматика Рус» стала принадлежать '
           'ОФД «Сотфлайн» , одной из связанных с группой Softline компаний. У Воротынцева осталось 29%, у Беловой – 16%, у '
           'Куликовского – 4%. Германович вышел из капитала компании.')
_PM_URL = 'https://www.cnews.ru/news/top/2026-04-06_softline_za_230_millionov_pereprodal'
_PM_REG = ('ЕГРЮЛ, ООО «Полиматика Рус», ИНН 7721721509: 22.12.2022 вошло ООО «Софтлайн Безопасность» (51%), доля Воротынцева '
           '64% → 29%, Беловой — 16%, Куликовского — 4%')
_AZ_DEAL = ('Подконтрольное инвестиционной группе «Русские фонды» ООО «Олимп Инвест» стало владельцем 19,9% ООО «Твинс Групп», '
            'которому принадлежит отель «Азимут Олимпик» на Олимпийском проспекте Москвы. Изменения в ЕГРЮЛ внесены 21 декабря. '
            'Остальными 80,1% владеет МКООО «Азимут Групп»')
_AZ_URL = 'https://www.kommersant.ru/doc/5747145'
_LC_REG = ('ЕГРЮЛ, ООО «Глобал МК», ИНН 7708401299: 28.12.2022 доля Краснолуцкого Игоря Геннадьевича 100% → 58,1197%, вошло '
           'АО «ААА Управление капиталом» (Д.У. ЗПИФ «Яшма») с 41,8803%')
_LC_SUM = ('Vademecum и «Новый проспект» о цене не пишут; «3 млрд ₽» нет ни в одном источнике карточки и ни в одной выдаче '
           'поиска («Глобал МК», «Яшма», Газпромбанк, Lahta Clinic)')
_LC_URL = 'https://vademec.ru/news/2023/02/13/dochka-gazprombanka-stala-sovladeltsem-peterburgskoy-seti-lahta-clinic/'
_CN_GUESS = ('Исходя из текущих котировок ценных бумаг ЦИАН на Московской бирже - 412 руб. за одну акцию, стоимость '
             'проданного Goldman Sachs пакета акций можно оценить в 2,92 млрд руб.')
_CN_URL = 'https://www.cnews.ru/news/top/2023-02-14_goldman_sachs_prodal_aktsii_tsian'
_CN_DATE = 'В декабре та же компания приобрела 9,4% в «Циан».'
_CN_PRAVO = 'https://pravo.ru/news/245035/'
_OC_DEAL = ('Композитный дивизион госкорпорации "Росатом", компания "Юматекс", завершил покупку активов американской группы '
            'Owens Corning в России и Беларуси')
_OC_URL = 'https://sputnik.by/20221212/aktivy-amerikanskoy-owens-corning-v-belarusi-pereshli-k-rosatomu-1070018605.html'
_GG_REG = ('ЕГРЮЛ, ООО «Сколково Парадайз», ИНН 9709065540: 18.11.2022 доля ООО «РЮЗ» 100% → 55%, вошло ООО «Рота-полка» (45%)')
_GG_SIND = ('Остальные 55% принадлежат структуре созданного сенатором Арсеном Каноковым холдинга «Синдика» … Президент '
            '«Синдики» Олег Эскиндаров отметил, что «Рота» — «давний партнер» холдинга, не став раскрывать условия сделки.')
_GG_URL = 'https://www.kommersant.ru/doc/5796344'

OPS = [
    # ge8f111a2: Бекмамбетов вышел из ООО 21.03.2022 (100% — Рустамовой); 50/50 сложилось 10.01.2023 — день закрытия.
    ('deal', 'ge8f111a2', 'date', '2022-12-22', '2023-01-10', _BZ_REG, _API % 'gdbf41437'),
    ('deal', 'ge8f111a2', 'date_basis', _MISSING, 'registry', _BZ_REG, _API % 'gdbf41437'),
    ('deal', 'ge8f111a2', 'eco.share', '—', '100% доли в ООО «Базелевс»', _BZ_REG, _API % 'gdbf41437'),
    ('deal', 'ge8f111a2', 'law.struct',
     'Рекламный бизнес «Базелевса» в сделку не вошел: им, как и раньше, руководит Екатерина Ткаченко, она же владеет им вместе с другими совладельцами. Когда о сделке сообщили, ее еще структурировали, а завершить рассчитывали за несколько месяцев.',
     'Продано только российское ООО «Базелевс» с правами на русскоязычный контент; американское производство осталось у Бекмамбетова, рекламное ООО «Базелевс Реклама» в сделку не вошло. Рустамова и Асадов получили по 50%.\n\nПо ЕГРЮЛ, Бекмамбетов вышел из участников 21 марта 2022 года, передав 100% Рустамовой, а Асадов вошел с долей 50% 10 января 2023 года. В декабре 2022 года, когда о сделке сообщили, ее еще собирались завершить через несколько месяцев.',
     _BZ_LEGAL + ' … ' + _BZ_REG, _BZ_URL),
    # g91ef0733: продавцы — те, чьи доли уменьшились 22.12.2022 (ЕГРЮЛ, CNews по Контур.Фокусу).
    ('deal', 'g91ef0733', 'seller', _MISSING, 'Григорий Воротынцев, Ольга Белова, Сергей Куликовский и Сергей Германович', _PM_OWN, _PM_URL),
    ('deal', 'g91ef0733', 'seller_src', _MISSING, 'registry', None, None),
    ('deal', 'g91ef0733', 'date_basis', 'signing', 'registry', _PM_REG, _API % 'g04181f17'),
    # g46445373: долю 19,9% «Твинс Групп» отдало МКООО «Азимут Групп» (ЕГРЮЛ 21.12.2022: 100% → 80,1%), а не сеть Azimut Hotels.
    ('deal', 'g46445373', 'seller', 'Azimut Hotels', 'МКООО «Азимут Групп»', _AZ_DEAL, _AZ_URL),
    ('deal', 'g46445373', 'seller_id', 'g05c33d81', _MISSING, _AZ_DEAL, _AZ_URL),
    ('deal', 'g46445373', 'retracted.seller', _MISSING, ['Azimut Hotels'], None, None),
    ('deal', 'g46445373', 'date_basis', _MISSING, 'registry', _AZ_DEAL, _AZ_URL),
    # g054eba01: суммы нет ни в одном источнике; дата — вход ЗПИФ «Яшма» в «Глобал МК» по ЕГРЮЛ.
    ('deal', 'g054eba01', 'sum', '3 млрд ₽', 'Не раскрыта', _LC_SUM, _LC_URL),
    ('deal', 'g054eba01', 'eco.sum', '3 млрд ₽', 'Не раскрыта', _LC_SUM, _LC_URL),
    ('deal', 'g054eba01', 'retracted.sum', _MISSING, ['3 млрд ₽'], None, None),
    ('deal', 'g054eba01', 'date', '2022-12-03', '2022-12-28', _LC_REG, _API % 'gdf730902'),
    ('deal', 'g054eba01', 'date_basis', _MISSING, 'registry', _LC_REG, _API % 'gdf730902'),
    ('deal', 'g054eba01', 'accepted_notes.no_profile.seller', _MISSING,
     'Продавец не установлен: по ЕГРЮЛ 28.12.2022 доля Игоря Краснолуцкого в ООО «Глобал МК» уменьшилась со 100% до 58,12%, '
     'вошло АО «ААА Управление капиталом» (ЗПИФ «Яшма»); Vademecum и «Новый проспект» не пишут, кому ушли деньги — '
     'Краснолуцкому или в капитал общества; поиск по «Глобал МК», «Яшма», Газпромбанк, Lahta Clinic условий не дал.', None, None),
    # g0dedddbd: 2,92 млрд ₽ — расчет CNews по котировке февраля 2023 года, не цена; «1 декабря» — заглушка (в источнике «в декабре»).
    ('deal', 'g0dedddbd', 'sum', '2,92 млрд ₽ (по оценке)', 'Не раскрыта', _CN_GUESS, _CN_URL),
    ('deal', 'g0dedddbd', 'eco.sum', '2,92 млрд ₽ (по оценке)', 'Не раскрыта', _CN_GUESS, _CN_URL),
    ('deal', 'g0dedddbd', 'retracted.sum', _MISSING, ['2,92 млрд ₽ (по оценке)'], None, None),
    ('deal', 'g0dedddbd', 'date', '2022-12-01', '2022', _CN_DATE, _CN_PRAVO),
    # gf5101b05: продавец назван во всех источниках.
    ('deal', 'gf5101b05', 'seller', _MISSING, 'Owens Corning', _OC_DEAL, _OC_URL),
    ('deal', 'gf5101b05', 'seller_src', _MISSING, 'text', None, None),
    # g92f41a2d: ЕГРЮЛ показывает только форму (доля «РЮЗ» 100 → 55%, «Рота-полка» — 45%); кто получил деньги — продажа
    # доли или вклад в капитал — не сказано ни в одном источнике, «Синдика» условия не раскрыла. Продавца не утверждаем.
    ('deal', 'g92f41a2d', 'date', '2022-12-01', '2022-11-18', _GG_REG, _API % 'gf51e23a8'),
    ('deal', 'g92f41a2d', 'date_basis', _MISSING, 'registry', _GG_REG, _API % 'gf51e23a8'),
    ('deal', 'g92f41a2d', 'seller', 'Холдинг «Синдика»', _MISSING, _GG_SIND + ' … ' + _GG_REG, _GG_URL),
    ('deal', 'g92f41a2d', 'seller_id', 'g47fde1f7', _MISSING, _GG_SIND, _GG_URL),
    ('deal', 'g92f41a2d', 'retracted.seller', _MISSING, ['Холдинг «Синдика»'], None, None),
    ('deal', 'g92f41a2d', 'accepted_notes.no_profile.seller', _MISSING,
     'Продавец не установлен: по ЕГРЮЛ 18.11.2022 доля ООО «РЮЗ» (структура «Синдики») в ООО «Сколково Парадайз» '
     'уменьшилась со 100% до 55%, вошло ООО «Рота-полка» с 45%; Ъ 5796344, Ъ 6122580 и New Retail не пишут, кому ушли '
     'деньги, президент «Синдики» условия не раскрыл — продажа доли или вклад в капитал, неизвестно.', None, None),
    ('deal', 'g92f41a2d', 'extra',
     'ГК «Рота», бенефициар которой — депутат Госдумы Дмитрий Саблин, купила 45% в головной компании сети «Глобус Гурмэ» — ООО «Сколково Парадайз». Продал долю холдинг «Синдика», у которого остались 55%. Сделка закрыта в декабре 2022 года.',
     'По ЕГРЮЛ, 18 ноября 2022 года доля ООО «РЮЗ», структуры «Синдики», в «Сколково Парадайз» уменьшилась до 55%, а 45% получило ООО «Рота-полка». Продала ли «Синдика» долю или «Рота» внесла деньги в капитал, стороны не раскрыли.',
     _GG_REG + ' … ' + _GG_SIND, _GG_URL),
    ('company', 'gf51e23a8', 'desc',
     'Головная компания сети премиальных супермаркетов «Глобус Гурмэ» в Москве; в 2022 году холдинг «Синдика» продал 45% ГК «Рота».',
     'Головная компания сети премиальных супермаркетов «Глобус Гурмэ» в Москве.'),
    ('company', 'g18853272', 'desc',
     'Компания депутата Госдумы Дмитрия Саблина; в 2022 году купила 45% в головной компании сети «Глобус Гурмэ» у холдинга «Синдика», оставившего себе 55%.',
     'Группа, основанная депутатом Госдумы Дмитрием Саблиным: недвижимость, гостиницы, производство продуктов питания.'),
]


def get(obj, path):
    for k in path.split('.'):
        if not isinstance(obj, dict) or k not in obj:
            return _MISSING
        obj = obj[k]
    return obj


def put(obj, path, value):
    ks = path.split('.')
    for k in ks[:-1]:
        obj = obj.setdefault(k, {})
    if value is _MISSING:
        obj.pop(ks[-1], None)
    else:
        obj[ks[-1]] = value


def apply(data):
    import fact_edit_guard
    by = {d['id']: d for d in data['deals']}
    done = 0
    for op in OPS:
        if op[0] == 'deal':
            _k, cid, path, old, new, quote, url = op
            card = by[cid]
            cur = get(card, path)
            if cur == new:
                print('уже применено: %s %s' % (cid, path))
                continue
            assert cur == old, '%s %s: в базе %r, ожидали %r' % (cid, path, cur, old)
            put(card, path, new)
            if quote:
                fact_edit_guard.log(card, path, None if new is _MISSING else new, quote, url, BY)
            print('%s %s: %r → %r' % (cid, path, str(old)[:60], str(new)[:60]))
        else:
            _k, pid, key, old, new = op
            comp = data['companies'][pid]
            cur = comp.get(key, _MISSING)
            if cur == new:
                print('уже применено: профиль %s %s' % (pid, key))
                continue
            if key == 'legal_short' and old is _MISSING and cur not in (_MISSING, None, ''):
                # Правовую форму успел поставить party_legal_names.py другой партии — не спорим.
                print('правовая форма уже стоит: профиль %s %r' % (pid, cur))
                continue
            assert cur == old, 'профиль %s %s: %r, ожидали %r' % (pid, key, cur, old)
            if new is _MISSING:
                comp.pop(key, None)
            else:
                comp[key] = new
            print('профиль %s %s: %r → %r' % (pid, key, str(old)[:60], str(new)[:60]))
        done += 1
    return done


def drop_fixed_baseline(data):
    """Старые нарушения правил текста, исправленные этой партией, уходят из
    text_rules_baseline.json (иначе test_card_text_follows_the_house_rules: «исправлено
    старых нарушений — уберите их»). Трогаются только записи карточек этой партии."""
    import text_rules
    ids = {op[1] for op in OPS if op[0] == 'deal'}
    found = {fp for fp, did, *_ in text_rules.all_findings({'deals': [d for d in data['deals'] if d['id'] in ids]})}
    store = json.load(open(text_rules.BASELINE, encoding='utf-8'))
    keep = [fp for fp in store['known'] if fp.split('|')[0] not in ids or fp in found]
    if len(keep) != len(store['known']):
        print('из базовой линии правил текста убрано исправленных: %d' % (len(store['known']) - len(keep)))
        store['known'] = keep
        json.dump(store, open(text_rules.BASELINE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def main(argv):
    write = '--write' in argv
    data = json.load(open(DATA, encoding='utf-8'))
    before = copy.deepcopy(data)
    n = apply(data)
    if not write:
        print('Сухой прогон: %d правок. Запись — --write.' % n)
        return 0
    if not n:
        return 0
    data = json.load(open(DATA, encoding='utf-8'))          # перечитать прямо перед записью
    before = copy.deepcopy(data)
    apply(data)
    import mass_edit_guard
    mass_edit_guard.check(before, data, os.environ.get('MASS_OK'))
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    drop_fixed_baseline(data)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
