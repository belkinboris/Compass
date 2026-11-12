# -*- coding: utf-8 -*-
"""Вычитка 12 ноября 2026, марафон, партия m063: правки, которые review.py не умеет.

Доказательства и поиск — в докстроке pipeline/ingest/fixes/reread_2026_11_12_m063.py, тексты статей —
data/inbox/triage/sources_2026-11-12_m063.json. Здесь: суммы «Не раскрыта» и «(по оценке)» (review.py их не
принимает), даты годом, доли в «Предмет / доля» с числами из нескольких цитат, описания и имена профилей,
снятые значения (retracted), заметки приемки и отпечатки прежних записей таблицы правок на переписанных полях
(иначе test_no_duplicate_fix_for_one_field и test_review_table_is_applied_and_not_pending).

Каждая правка проверяет старое значение (assert); повторный запуск — «уже применено».
Запуск — внутри pipeline/reread_apply.py (после review.py --write):
    python3 pipeline/archive/2026-11/reread_oneoff_m063.py            # сухой прогон
    python3 pipeline/archive/2026-11/reread_oneoff_m063.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, ROOT)

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

BY = 'вычитка 12 ноября 2026, партия m063'

SET = [('g547ff4b8',
  'eco.share',
  'ЛУКОЙЛ купил завод в 2008 году, ему принадлежит 49% предприятия.',
  '100% ISAB S.r.l.',
  'has successfully completed the acquisition of the entire share capital of ISAB S.r.l. (“ISAB”), previously held '
  'by LITASCO S.A.',
  'https://goi.energy/?page_id=944'),
 ('g547ff4b8',
  'sum',
  '€1,5 млрд',
  '€1,5 млрд (по оценке)',
  'Сделка оценивается примерно в €1,5 млрд, сообщало агентство Reuters в декабре.',
  'https://www.kommersant.ru/doc/5759356'),
 ('g547ff4b8',
  'eco.sum',
  '€1,5 млрд',
  '€1,5 млрд (по оценке)',
  'Сделка оценивается примерно в €1,5 млрд, сообщало агентство Reuters в декабре.',
  'https://www.kommersant.ru/doc/5759356'),
 ('g96b1cdaf',
  'date',
  '2022-12-01',
  '2022',
  '« Лукойл » в декабре 2022 г. консолидировал 56,43% акций энергетической компании « ЭЛ5-Энерго » (ранее «Энел '
  'Россия»), сообщила энергокомпания 9 января 2023 г. В октябре 2022 г. « Лукойл » купил 26,9% акций энергокомпании. '
  '… получив в результате продажи своей доли итальянским Enel 26,9%, еще 29,5% отошло к "ААА Управление капиталом". '
  'В январе 2023 года "ЛУКОЙЛ" увеличил прямую долю в компании до 56,43% ("ААА Управление капиталом" вышло из '
  'состава акционеров)',
  'https://www.vedomosti.ru/business/news/2023/01/09/958384-lukoil-poluchil-el5-energo'),
 ('g96b1cdaf',
  'sum',
  '137 млн € (за пакет Enel)',
  'Не раскрыта',
  'В результате « Лукойл » и «Газпромбанк-Фрезия» (структура Газпромбанка) получили 26,9% и 29,5% акций «Энел '
  'Россия» соответственно. Сумма сделки составила около 137 млн евро. … В сообщениях «ЭЛ5-Энерго» и «Лукойла» от 9 '
  'января не раскрывается, чьи акции были выкуплены нефтяной компанией. Но процент выкупленных акций в точности '
  'соответствует доле, которую получила в результате сделки «Газпромбанк-Фрезия» (29,5%).',
  'https://www.vedomosti.ru/business/news/2023/01/09/958384-lukoil-poluchil-el5-energo'),
 ('g96b1cdaf',
  'eco.sum',
  '€137 млн',
  'Не раскрыта',
  'В результате « Лукойл » и «Газпромбанк-Фрезия» (структура Газпромбанка) получили 26,9% и 29,5% акций «Энел '
  'Россия» соответственно. Сумма сделки составила около 137 млн евро. … В сообщениях «ЭЛ5-Энерго» и «Лукойла» от 9 '
  'января не раскрывается, чьи акции были выкуплены нефтяной компанией. Но процент выкупленных акций в точности '
  'соответствует доле, которую получила в результате сделки «Газпромбанк-Фрезия» (29,5%).',
  'https://www.vedomosti.ru/business/news/2023/01/09/958384-lukoil-poluchil-el5-energo'),
 ('g96b1cdaf',
  'eco.share',
  'В декабре 2022 года Лукойл довел долю в ЭЛ5-Энерго до 56,43%: выкупил 29,5% акций у Газпромбанк-Фрезии, а в '
  'октябре — 26,9% у Enel примерно за 137 млн евро.',
  '56,43% акций ПАО «ЭЛ5-Энерго»: 26,9% у Enel (октябрь 2022 года) и 29,5% у ЗПИФ «Газпромбанк-Фрезия»',
  '« Лукойл » в декабре 2022 г. консолидировал 56,43% акций энергетической компании « ЭЛ5-Энерго » (ранее «Энел '
  'Россия»), сообщила энергокомпания 9 января 2023 г. В октябре 2022 г. « Лукойл » купил 26,9% акций энергокомпании. '
  '… В результате « Лукойл » и «Газпромбанк-Фрезия» (структура Газпромбанка) получили 26,9% и 29,5% акций «Энел '
  'Россия» соответственно. Сумма сделки составила около 137 млн евро. … получив в результате продажи своей доли '
  'итальянским Enel 26,9%, еще 29,5% отошло к "ААА Управление капиталом". В январе 2023 года "ЛУКОЙЛ" увеличил '
  'прямую долю в компании до 56,43% ("ААА Управление капиталом" вышло из состава акционеров)',
  'https://www.vedomosti.ru/business/news/2023/01/09/958384-lukoil-poluchil-el5-energo'),
 ('gac36eece',
  'sum',
  '19–20 млрд ₽',
  'Не раскрыта',
  'Сумму сделки стороны не раскрывают. Гендиректор «Infoline-аналитики» Михаил Бурмистров оценивает стоимость KDL в '
  '15 млрд руб. Источник, близкий к одной из сторон сделки, уверяет, что она выше – 19–20 млрд руб.',
  'https://www.vedomosti.ru/business/articles/2022/12/28/957441-gruppa-medskan'),
 ('gac36eece',
  'eco.sum',
  '19–20 млрд ₽',
  'Не раскрыта',
  'Сумму сделки стороны не раскрывают. Гендиректор «Infoline-аналитики» Михаил Бурмистров оценивает стоимость KDL в '
  '15 млрд руб. Источник, близкий к одной из сторон сделки, уверяет, что она выше – 19–20 млрд руб.',
  'https://www.vedomosti.ru/business/articles/2022/12/28/957441-gruppa-medskan'),
 ('ge29c8b25',
  'date',
  '2022-12-01',
  '2022',
  'закрыл инвестиционный раунд на 325 млн рублей, инвестором выступил Венчурный фонд Национальной технологической '
  'инициативы под управлением инвестиционной компании Kama Flow. Приобретенная доля не раскрывается. В Kama Flow '
  'рассчитывают, что к 2026 году компания займет более 50% российского рынка и покажет пятикратный рост выручки.',
  'http://kamaflow.com/ru/post/developer-smart-operating-systems-mvs-attracted-325-million-rubles-kama-flow/'),
 ('gabc53206',
  'eco.share',
  '—',
  'Доля в ООО «КонтролХак»; по ЕГРЮЛ сейчас у ООО «ИнноХаб» 4%',
  'сейчас: Куприн Сергей Валерьевич — 40.5%\n'
  'сейчас: Пятаков Максим Игоревич — 40.5%\n'
  'сейчас: Сердюк Виктор Александрович — 15.0%\n'
  'сейчас: ООО "ИННОХАБ" — 4.0%',
  'https://projectcompass.ru/api/companies/gfe3416fc/fns'),
 ('gabc53206',
  'date_basis',
  None,
  'registry',
  '03.07.2023 Новый учредитель – ООО "ИННОХАБ".',
  'https://www.audit-it.ru/contragent/1205000049627_ooo-kontrolkhak'),
 ('g2dc1ba74',
  'seller',
  None,
  'Ball Corporation',
  'Группа "Арнест", купившая в сентябре прошлого года активы по производству алюминиевых банок для напитков у '
  'американской Ball Corporation',
  'https://www.interfax.ru/business/886448'),
 ('g2dc1ba74',
  'date',
  '2022-10-01',
  '2022',
  'Группа "Арнест", купившая в сентябре прошлого года активы по производству алюминиевых банок для напитков у '
  'американской Ball Corporation',
  'https://www.interfax.ru/business/886448'),
 ('g0e8b9617',
  'eco.share',
  '—',
  '100% акций АО «Иль де Ботэ»',
  'The deal, which includes the sale of 100 percent of its shares for the Russian business, has been made with the '
  'country’s local general manager, with the goal of favouring continuity for its employees.',
  'https://fashionunited.com/news/business/lvmh-owned-sephora-sells-russian-subsidiary/2022071248584')]

RETRACT = [('g96b1cdaf', 'sum', '137 млн € (за пакет Enel)'), ('gac36eece', 'sum', '19–20 млрд ₽')]

COMP = [('gaf3029ec',
  'desc',
  'В 2022 году договорилась о покупке у ЛУКОЙЛа 49% НПЗ ISAB на Сицилии, сформировав партнерство с Trafigura для '
  'поставок нефти.',
  'Энергетическое подразделение фонда ARGUS New Energy Fund; в 2023 году купило у ЛУКОЙЛа нефтеперерабатывающий '
  'комплекс ISAB на Сицилии.'),
 ('g85fa7898',
  'desc',
  'Нефтеперерабатывающий завод на Сицилии; в 2022 году ЛУКОЙЛ договорился продать 49% его доли группе G.O.I. ENERGY '
  'из-за санкций ЕС на морские поставки российской нефти.',
  'Нефтеперерабатывающий комплекс в Приоло-Гарджало на Сицилии (НПЗ, установка газификации и электростанция), '
  'принадлежит ISAB S.r.l.; в 2023 году ЛУКОЙЛ продал компанию G.O.I. Energy.'),
 ('gfe3416fc',
  'desc',
  'Разработчик платформы для симуляции кибератак (клиентские договоренности на 125 млн ₽); в 2022 году долю в '
  'компании купил «Росатом».',
  'Разработчик платформы, которая имитирует кибератаки (Breach and Attack Simulation); резидент «Сколково». В 2023 '
  'году долю в компании купил Инновационный хаб Росатома.'),
 ('g7bc50710', 'name', 'заводы по производству клея и сухих смесей', 'Киилто-Клей'),
 ('g7bc50710', 'legal_short', None, 'АО «Киилто-Клей»'),
 ('g7bc50710',
  'desc',
  'Заводы финской Kiilto по производству клея и сухих строительных смесей — АО «Киилто-Клей», ООО «Киилто Фэмили» и '
  'ООО «Киилто-Клей Раменское»; в 2022 году их купила ГК Bergauf.',
  'Бывшая российская «дочка» финской Kiilto (после продажи — «Кесто»): заводы клеев в Раменском и сухих строительных '
  'смесей в Малоярославце; вместе с ООО «Киилто Фэмили» и ООО «Киилто-Клей Раменское» в 2022 году перешла к Bergauf '
  'Group.'),
 ('gdbbfc5d2',
  'desc',
  'Сеть медицинских лабораторий; в 2022 году ее купил «Медскан» у UFG Private Equity.',
  'Сеть медицинских лабораторий (основное юрлицо — «Диагностика»): 13 региональных лабораторий и более 350 '
  'медицинских офисов в 40 с лишним городах; с 2022 года принадлежит группе «Медскан».'),
 ('gb7239f07', 'name', 'российский менеджмент во главе с Евгением Дроздовым', 'Евгений Дроздов'),
 ('gb7239f07',
  'desc',
  'В 2022 году купил у LVMH 100% сети магазинов Sephora в России («Иль де Ботэ»).',
  'Гендиректор российской Sephora; в 2022 году купил у LVMH сеть, которая вернулась к имени «Иль де Ботэ».'),
 ('g9144b447',
  'desc',
  'Сеть магазинов Sephora в России, ранее принадлежавшая LVMH, переименована в «Иль де Ботэ».',
  'Российская сеть парфюмерии и косметики, основана в 2001 году; в 2013–2022 годах принадлежала Sephora (LVMH) и '
  'работала под ее брендом.'),
 ('g30a195ea', 'ind', 'Пищепром и напитки', 'Производство тары'),
 ('ge2a1dca0', 'legal_short', None, 'ПАО «ЭЛ5-Энерго»'),
 ('g446ef7c3', 'legal_short', None, 'ООО «ИнноХаб»'),
 ('g9144b447', 'legal_short', None, 'АО «Иль де Ботэ»'),
 ('gfe3416fc', 'legal_short', None, 'ООО «КонтролХак»')]

NOTES = {}

TOUCHED = {'g547ff4b8': ['title',
               'law.struct',
               'law.terms',
               'eco.rationale',
               'eco.val',
               'eco.context',
               'extra',
               'eco.share',
               'sum',
               'eco.sum'],
 'g96b1cdaf': ['title', 'law.struct', 'eco.val', 'extra', 'date', 'sum', 'eco.sum', 'eco.share'],
 'gac36eece': ['title',
               'date_basis',
               'eco.val',
               'eco.target_fin',
               'eco.rationale',
               'eco.context',
               'eco.share',
               'sum',
               'eco.sum'],
 'ge29c8b25': ['title', 'law.struct', 'extra', 'date'],
 'gabc53206': ['title', 'law.struct', 'extra', 'eco.share', 'date_basis'],
 'g383b170f': ['date', 'date_basis', 'eco.target_fin', 'eco.context'],
 'g0e8b9617': ['title', 'eco.val', 'eco.target_fin', 'law.appr', 'eco.context', 'extra', 'eco.share'],
 'g2dc1ba74': ['title', 'law.appr', 'law.terms', 'eco.share', 'law.struct', 'seller', 'date']}



def get(card, field):
    obj = card
    for p in field.split('.'):
        obj = obj.get(p) if isinstance(obj, dict) else None
    return obj


def put(card, field, value):
    parts = field.split('.')
    obj = card
    for p in parts[:-1]:
        obj = obj.setdefault(p, {})
    if value is None:
        obj.pop(parts[-1], None)
    else:
        obj[parts[-1]] = value


def main(argv):
    write = '--write' in argv
    import fact_edit_guard
    import mass_edit_guard
    import review
    raw = open(DATA, encoding='utf-8').read()          # перечитать прямо перед записью
    data = json.loads(raw)
    old = json.loads(raw)
    by = {d['id']: d for d in data['deals']}
    done = 0
    for cid, field, was, new, quote, url in SET:
        card = by[cid]
        cur = get(card, field)
        if cur == new:
            print('уже применено: %s.%s' % (cid, field))
            continue
        assert cur == was, '%s.%s: в базе %r, ожидали %r' % (cid, field, cur, was)
        put(card, field, new)
        fact_edit_guard.log(card, field, new, quote, url, BY)
        print('%s.%s: %r → %r' % (cid, field, was, new))
        done += 1
    for cid, field, value in RETRACT:
        lst = by[cid].setdefault('retracted', {}).setdefault(field, [])
        if value not in lst:
            lst.append(value)
            done += 1
    for cid, notes in NOTES.items():
        acc = by[cid].setdefault('accepted_notes', {})
        for key, text in notes.items():
            if '.' in key:
                a, b = key.split('.')
                if acc.setdefault(a, {}).get(b) != text:
                    acc[a][b] = text
                    done += 1
            elif acc.get(key) != text:
                acc[key] = text
                done += 1
    for comp, field, was, new in COMP:
        cur = data['companies'][comp].get(field)
        if field == 'legal_short' and cur:      # party_legal_names.py уже поставил форму из реестра
            continue
        if cur != new:
            assert cur == was, '%s.%s: %r' % (comp, field, cur)
            data['companies'][comp][field] = new
            print('%s.%s → %r' % (comp, field, new))
            done += 1
    # Отпечатки прежних записей таблицы на переписанных полях.
    for cid, fields in TOUCHED.items():
        card = by[cid]
        absorbed = card.setdefault('proofread_absorbed', {})
        for field in fields:
            recs = [f for f in review.FIXES if (f['id'], f['field']) == (cid, field)
                    and BY.split()[-1] not in str(f.get('why', ''))]
            for f in recs:
                if f['new'] == get(card, field):
                    continue
                fp = review.fix_fingerprint(f['new'])
                marks = absorbed.setdefault(field, [])
                if fp not in marks:
                    marks.append(fp)
                    done += 1
        if not absorbed:
            card.pop('proofread_absorbed', None)
    print('изменений: %d' % done)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    if not done:
        return 0
    mass_edit_guard.check(old, data, key='reread')
    out = json.dumps(data, ensure_ascii=False, indent=1)
    if raw.endswith('\n'):
        out += '\n'
    open(DATA, 'w', encoding='utf-8').write(out)
    print('записано')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
