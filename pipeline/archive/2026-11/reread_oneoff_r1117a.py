# -*- coding: utf-8 -*-
"""Вычитка 17 ноября 2026, партия r1117a: правки, которые review.py не умеет или чье поле
уже занято записью FIXES в другом файле (тогда отпечаток той записи — в proofread_absorbed).

Тексты статей — data/inbox/triage/sources_2026-11-17_r1117a.json; история участников —
сайт /api/companies/<id>/fns (party_legal_names.py).

Очередь расхождений с реестром (pipeline/party_registry_queue.json):
  g00421dd1 (ТилТех / Poison Drop) — карточка верна: по ЕГРЮЛ 25% до 23.11.2023 принадлежали
    самому ООО «Пойзон Дроп» (доля общества, с 12.09.2023), предмет продавцом не бывает;
    25% — миноритарная доля, тип «Инвестиция», продавца нет. Правится только заголовок:
    название фонда без кавычек.
  g3a25a36c (ГК «Максима» / GMCS) — продавец верен: в ЕГРЮЛ 65% с 14.09.2022 значатся за
    ООО «Контрада Капитал» (ИНН 7702513045, ОГРН 1047796009128, тип владельца «ПИФ» — доверительный
    управляющий ЗПИКФ «Контрада-Спутник»); ComNews: фонд продал 65% «МТ-Интеграции» 7 июля 2023 года.
    Запись реестра «вышел 31.01.2023» — запаздывание выписок, сделка была в июле; поэтому аудит
    окна сделки его не видит. ИНН профиля «Контрада Капитал» подтверждается (ЕГРЮЛ GMCS + ComNews/CNews).
    Ошибки: «1–1,5 млрд ₽» — оценка «участников рынка» и Максима Кутузова (платформа «Сфера»),
    стороны цену не раскрыли (ComNews) — в sum «Не раскрыта», оценка остается в eco.val;
    заголовок «60%» спорил с долей 65%, которую группа получила у фонда; law.struct — цепочка
    из 8+ слов ComNews, переписан; в контексте — опровержение входа группы в «Аквариус»
    (другая сделка, 2025 год) — снято.
  g2d653619 (АО «ЦК» / «АЛД Автомотив») — карточка верна: «АО АЛД» в ЕГРЮЛ — французская
    ALD S.A., то есть сама ALD Automotive (Frank Media: «приобрела у входящей в группу Societe
    Generale ALD Automotive»). Правок нет.

Остальные карточки:
  c51d0bb64 (ВТБ / WB Банк) — 5% с правом увеличить долю, «доля останется миноритарной»
    (Sostav со слов Пьянова) — тип «Инвестиция», а не M&A; доля по форме; «больше 547 млрд ₽» —
    при полном размещении допэмиссия дала бы 547,46 млрд ₽ (Ведомости), то есть «до»;
    пометка агентства «— ИФ» в цитате и оценочное «наконец» в контексте.
  gbde15bde (ДОМ.РФ / «39 Арсенал») — 427,26 млн ₽ — начальная цена аукциона, не цена сделки:
    в sum «Не раскрыта», начальная цена и ожидание рынка — в eco.val; цена убрана из заголовка.
  g9018f8c8 («Лента» / «Улыбка радуги») — в eco.share было описание компании.

Запуск: python3 pipeline/archive/2026-11/reread_oneoff_r1117a.py [--write]
Без ключа — сухой прогон. База перечитывается прямо перед записью, у каждой правки
assert на старое значение; повторный запуск — «уже применено».
"""
import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, ROOT)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY = 'вычитка r1117a, 17.11.2026'
TODAY = '2026-11-17'
NONE = 'Не раскрыта'

KOM_PD = 'https://www.kommersant.ru/doc/6321483'
Q_PD = ('Венчурный фонд «ТилТех Капитал» стал владельцем 25% сети магазинов ювелирных украшений '
        'Poison Drop.')

COMN = ('https://www.comnews.ru/content/229281/2023-10-06/2023-w40/1007/'
        'gk-maksima-kupila-byvshiy-oskolok-maykor')
Q_GM_65 = ('7 июля 2023 г. ЗПИКФ "Контрада-Спутник" продал 65% долей в ООО "Джи-Эм-Си-Эс Верэкс" компании '
           '"МТ-Интеграция", входящей в ГК "Максима".')
Q_GM_SUM = 'Стоимость 60%-ного и 5%-ного пакетов в GMCS ни покупатель, ни продавцы не раскрыли.'
OLD_GM_SUM = '1–1,5 млрд ₽ (по оценке)'
OLD_GM_STRUCT = ('7 июля 2023 года ЗПИКФ «Контрада-Спутник» продал 65% долей в ООО «Джи-Эм-Си-Эс Верэкс» '
                 'компании «МТ-Интеграция», входящей в группу компаний «Максима». Уже 31 июля 2023 года '
                 '«МТ-Интеграция» перепродала 60% уставного капитала GMCS АО «Инвестмир» — структуре Сергея '
                 'Асланяна, председателя совета директоров ГК «Максима»: доля пробыла у нее 24 дня. Оставшиеся '
                 'доли распределены так: 29% у президента GMCS Екатерины Воропаевой, 11% — у исполнительного '
                 'директора Ильи Дрозмана.')
NEW_GM_STRUCT = ('Фонд «Контрада-Спутник» под управлением «Контрада Капитал» 7 июля 2023 года передал 65% GMCS '
                 'компании «МТ-Интеграция» из группы «Максима». 31 июля «МТ-Интеграция» перепродала 60% '
                 'АО «Инвестмир» — головной структуре группы, которой владеет председатель совета директоров '
                 '«Максимы» Сергей Асланян, а 5% — президенту GMCS Екатерине Воропаевой; ее доля выросла до 29%. '
                 'Еще 11% остались у исполнительного директора GMCS Ильи Дрозмана.')
FNS_GM = 'https://projectcompass.ru/api/companies/g93a65e59/fns'

VED_VTB = 'https://www.vedomosti.ru/investments/news/2026/11/12/1244904-vtb-otkril-podpisku'
SOST_VTB = 'https://www.sostav.ru/publication/v-vtb-raskryli-podrobnosti-sdelki-s-rvb-84163.html'
PRIME_VTB = 'https://1prime.ru/20261112/vtb-875174455.html'
Q_VTB_TYPE = 'ВТБ сможет увеличить долю в указанных активах, но она останется миноритарной.'
Q_VTB_SHARE = ('ВТБ с 13 по 30 ноября проведет сбор заявок на реализацию преимущественного права приобретения '
               'акций в рамках допэмиссии для сделки по приобретению 5% в "WB Банке"')

URA = 'https://ura.news/news/1053143896'
Q_URA = 'Начальная стоимость комплекса 427,26 млн рублей.'
OLD_URA_SUM = '427,26 млн ₽'

KOM_UR = 'https://www.kommersant.ru/doc/7344356'
Q_UR = ('Ритейлер «Лента» объявил о приобретении 100% акций АО «Торговый дом Эра», которое владеет сетью '
        'магазинов косметики и товаров для дома «Улыбка радуги».')

# (карточка, путь поля, старое, новое, цитата, адрес); цитата None — поле не факт (проза).
# старое: значение или ('REPL', a, b) — замена фрагмента.
DEAL_OPS = [
    ('g00421dd1', 'title', 'Фонд ТилТех Капитал купил 25% сети ювелирных магазинов Poison Drop',
     'Фонд «ТилТех Капитал» купил 25% сети ювелирных магазинов Poison Drop', Q_PD, KOM_PD),

    ('g3a25a36c', 'title', 'ГК «Максима» купила 60% интегратора GMCS',
     'ГК «Максима» купила 65% интегратора GMCS', Q_GM_65, COMN),
    ('g3a25a36c', 'sum', OLD_GM_SUM, NONE, Q_GM_SUM, COMN),
    ('g3a25a36c', 'eco.sum', OLD_GM_SUM, NONE, Q_GM_SUM, COMN),
    ('g3a25a36c', 'retracted.sum', None, [OLD_GM_SUM], None, None),
    ('g3a25a36c', 'law.struct', OLD_GM_STRUCT, NEW_GM_STRUCT, None, None),
    ('g3a25a36c', 'eco.context',
     ('REPL', 'Позднее ГК «Максима» стала называться ГК «МТ-Интеграция»; позже группа опровергла, что входит '
              'в число акционеров ГК «Аквариус».',
      'Позднее ГК «Максима» стала называться ГК «МТ-Интеграция».'), None, None),
    ('g3a25a36c', 'accepted_notes.checked.registry', None,
     'Продавец по ЕГРЮЛ — ООО «Контрада Капитал» (ИНН 7702513045), доверительный управляющий ЗПИКФ '
     '«Контрада-Спутник»: 65% записаны за ним с 14 сентября 2022 года. В выписках сайта он «выходит» '
     '31 января 2023 года, но ComNews называет день продажи фондом — 7 июля 2023 года, когда 65% получила '
     '«МТ-Интеграция»; запись реестра запаздывает. 31 июля 2023 года 60% перешли к АО «Инвестмир» (головная '
     'структура группы «Максима»), 5% — к Екатерине Воропаевой.', None, None),

    ('c51d0bb64', 'type', 'M&A', 'Инвестиция', Q_VTB_TYPE, SOST_VTB),
    ('c51d0bb64', 'eco.share', '—', '5% доли в ООО «ВБ Банк»', Q_VTB_SHARE, PRIME_VTB),
    ('c51d0bb64', 'law.struct',
     ('REPL', 'которая может дать больше 547 млрд ₽.', 'при полном размещении она дала бы до 547 млрд ₽.'),
     None, None),
    ('c51d0bb64', 'eco.context',
     ('REPL', '«Да, она (допэмиссия — ИФ) перенеслась, но она будет», — сказал он, отвечая',
      '«Да, она перенеслась, но она будет», — сказал он о допэмиссии, отвечая'), None, None),
    ('c51d0bb64', 'eco.context',
     ('REPL', '12 ноября 2026 года банк наконец раскрыл окно для действующих акционеров',
      '12 ноября 2026 года банк открыл подписку для действующих акционеров'), None, None),
    ('c51d0bb64', 'src', None, ['Sostav', SOST_VTB], None, None),

    ('gbde15bde', 'title',
     'ДОМ.РФ выставил на торги территорию бывшего завода «39 Арсенал» в Перми за 427,26 млн рублей',
     'ДОМ.РФ выставил на торги территорию бывшего завода «39 Арсенал» в Перми',
     'Аукцион организует корпорация «Дом.РФ».', URA),
    ('gbde15bde', 'sum', OLD_URA_SUM, NONE, Q_URA, URA),
    ('gbde15bde', 'eco.sum', OLD_URA_SUM, NONE, Q_URA, URA),
    ('gbde15bde', 'retracted.sum', None, [OLD_URA_SUM], None, None),
    ('gbde15bde', 'eco.val', '—',
     'Начальная цена аукциона — 427,26 млн ₽. Участники рынка не исключают, что на торгах цена превысит '
     '1 млрд ₽.', None, None),

    ('g9018f8c8', 'eco.share', '100% акций АО «Торговый дом „Эра“», владельца сети «Улыбка радуги»',
     '100% акций АО «Торговый дом «Эра»»', Q_UR, KOM_UR),
]

DEAL_OPS = [op if len(op) == 6 else op[:3] + (None,) + op[3:] for op in DEAL_OPS]

KONTRADA = {
    'company_id': 'g13992bb8', 'decision': 'confirmed', 'inn': '7702513045', 'date': TODAY,
    'reason': ('Вычитка r1117a (2026-11-17): ООО «Контрада Капитал», ИНН 7702513045, ОГРН 1047796009128. '
               'В истории участников ООО «Джи-Эм-Си-Эс Верэкс» (ИНН 7716593315, сайт /api/companies/g93a65e59/fns) '
               'оно с 14.09.2022 записано владельцем 65% с типом «ПИФ» — доверительный управляющий ЗПИКФ '
               '«Контрада-Спутник»; ComNews (06.10.2023): фонд «Контрада-Спутник» купил долю у Вячеслава '
               'Кузьмичева в сентябре 2022 года и продал 65% «МТ-Интеграции» 7 июля 2023 года; CNews: управляющая '
               'компания «Контрдата [так] Капитал», прежде «Управляющая компания «КапиталЪ Паевые инвестиционные '
               'фонды»». Прежняя запись (no_match, 2026-10-23) не находила связи со сделкой — теперь она есть в ЕГРЮЛ.'),
}


def get(obj, path):
    for k in path.split('.'):
        if not isinstance(obj, dict):
            return None
        obj = obj.get(k)
    return obj


def put(obj, path, value):
    keys = path.split('.')
    for k in keys[:-1]:
        obj = obj.setdefault(k, {})
    if value is None:
        obj.pop(keys[-1], None)
    else:
        obj[keys[-1]] = value


def absorb_fixes(card, path):
    """Поле переписано, а в таблице правок есть запись на него — ее отпечаток в proofread_absorbed."""
    import review
    for f in review.FIXES:
        if f['id'] == card['id'] and f['field'] == path and f.get('new') is not None:
            fp = review.fix_fingerprint(f['new'])
            lst = card.setdefault('proofread_absorbed', {}).setdefault(path, [])
            if fp not in lst:
                lst.append(fp)


def apply(data):
    import fact_edit_guard
    deals = {d['id']: d for d in data['deals']}
    done = todo = 0
    for cid, path, was, new, quote, url in DEAL_OPS:
        card = deals[cid]
        if path == 'src':
            srcs = card.setdefault('src', [])
            if any(s[1] == new[1] for s in srcs):
                done += 1
                continue
            srcs.append(new)
            print('  ИСТОЧНИК %s: %s' % (cid, new[1]))
            todo += 1
            continue
        cur = get(card, path)
        if isinstance(was, tuple) and was[0] == 'REPL':
            _, a, b = was
            if b in cur and a not in cur:
                done += 1
                continue
            assert cur.count(a) == 1, '%s %s: нет фрагмента %r' % (cid, path, a)
            put(card, path, cur.replace(a, b))
            absorb_fixes(card, path)
            print('  ПРАВИМ %s %s: …%s… -> …%s…' % (cid, path, a[:40], b[:50]))
            todo += 1
            continue
        if path == 'retracted.sum':
            lst = card.setdefault('retracted', {}).setdefault('sum', [])
            add = [v for v in new if v not in lst]
            if not add:
                done += 1
                continue
            lst.extend(add)
            print('  СНЯТО %s sum: %r' % (cid, add))
            todo += 1
            continue
        if cur == new:
            done += 1
            continue
        assert cur == was, '%s %s: в базе %r, ожидали %r' % (cid, path, cur, was)
        put(card, path, new)
        absorb_fixes(card, path)
        if quote:
            fact_edit_guard.log(card, path, new, quote, url, BY, TODAY)
        print('  ПРАВИМ %s %s: %r -> %r' % (cid, path, str(was)[:50], str(new)[:60]))
        todo += 1
    return done, todo


def registry(write):
    import fns_registry
    import fns_notes_to_registry
    row = fns_registry.by_company_id().get(KONTRADA['company_id']) or {}
    if row.get('decision') == 'confirmed' and row.get('inn') == KONTRADA['inn']:
        return 0
    assert row.get('decision') == 'no_match', row
    print('  РЕЕСТР g13992bb8 «Контрада Капитал»: no_match -> confirmed, ИНН 7702513045')
    if write:
        assert fns_notes_to_registry.edit_registry_entry(KONTRADA['company_id'], KONTRADA)
    return 1


def main(argv):
    write = '--write' in argv
    import fact_edit_guard
    import mass_edit_guard
    data = json.load(open(DATA, encoding='utf-8'))      # перечитываем прямо перед записью
    old = copy.deepcopy(data)
    done, todo = apply(data)
    reg = registry(write)
    print('уже применено: %d, к записи: %d (реестр ИНН: %d)' % (done, todo, reg))
    bad = fact_edit_guard.unbacked(old, data)
    assert not bad, bad
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    if not todo:
        print('Уже применено.')
        return 0
    mass_edit_guard.check(old, data, key=os.environ.get('MASS_OK'))
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('записано')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
