# -*- coding: utf-8 -*-
"""Вычитка-марафон 13 ноября 2026, партия m236 (часть 3): правки, которые review.py не принимает.

Статьи открыты заново (curl) и сохранены save_source.py (day 2026-11-12_m236).

gacc757b6 (Selectel): по сущфакту сделка с 10% «состоялась 30 апреля» 2025 года (Интерфакс, 05.05.2025),
  19 мая — день сообщения White Square; 10% купила ИК «Солнечный ветер» (а не «инвестиционные структуры»),
  4,852% — Андрей Голухов «ранее в апреле», обе доли — у Servertech; заголовок по стандарту, eco.share —
  долей в АО.
Профили «Группа «Синара»» и «ТД «Библио-Глобус»» — правовая форма по ЕГРЮЛ (legal_short).
g9f6fe860 («Единая сеть»): заголовок по стандарту; eco.share и law.struct — пустое «приобретение
  компании», Selectel сообщает о покупке 100% ООО «Единая сеть»; eco.val — мнение без автора
  («Если озвученная цена верна, Selectel переплатил… Вероятно…») — снято; дня 25 декабря нет ни в одном
  источнике (Selectel, Habr — без даты сделки) — дата годом.
geb221705 (X5 / MAY24): «около 1 млрд ₽» — предположение Михаила Бурмистрова («Infoline-аналитика»),
  а не цена; в sum «Не раскрыта», оценка остается в eco.val.
gb5d8a18a («М.Видео»): заголовок по стандарту «X купил акции Y»; в law.struct «сама компания» —
  разговорно, и акции компания у себя не покупала (покупатели — структуры собственников).

    python3 pipeline/archive/2026-11/reread_oneoff_m236c.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY, DAY = 'reread_oneoff_m236c', '2026-11-13'
IFX = 'https://www.interfax.ru/amp/1024079'
SEL = 'https://selectel.ru/about/newsroom/news/selectel-soobshchaet-o-priobretenii-oblachnogo-provajdera-servers-ru/'
OB = 'https://www.oborot.ru/news/zachem-x5-group-optovyj-marketplejs-may24-i-skolko-za-nego-uplacheno-i225021.html'.replace('www.', '')
VM = 'https://www.vedomosti.ru/investments/news/2026/11/12/1244817-mvideo-zavershila'
PR = 'https://1prime.ru/20261112/dopemissija-875162299.html'

EDITS = [
    ('gacc757b6', 'date', '2025-05-19', '2025-04-30',
     'Как говорится в сообщении о сущфакте "Селектела", сделка состоялась 30 апреля.', IFX, None),
    ('gacc757b6', 'buyer_name', 'Инвестиционные структуры Геворка Вермишяна и Андрей Голухов',
     'ИК «Солнечный ветер» и Андрей Голухов',
     'Инвестиционная компания "Солнечный ветер", основанная экс-главой "Мегафона" Геворком Вермишяном, приобрела '
     '10% АО "Селектел"; ранее в апреле член совета директоров АО "Селектел" Андрей Голухов приобрел 4,852% компании у Servertech',
     IFX, 'buyer_name'),
    ('gacc757b6', 'title', 'Selectel: проданы 10% акций структурам Геворка Вермишяна и 4,852% — Андрею Голухову',
     '«Солнечный ветер» и Андрей Голухов купили 10% и 4,852% Selectel у Servertech',
     'Инвестиционная компания "Солнечный ветер"… приобрела 10% АО "Селектел"; Андрей Голухов приобрел 4,852% компании у Servertech',
     IFX, None),
    ('gacc757b6', 'eco.share',
     'Андрей Голухов из совета директоров получил 4,852%, а 10% купила инвесткомпания, которую основал Геворк '
     'Вермишян, в прошлом глава «Мегафона».',
     'Акции АО «Селектел»: 10% и 4,852%',
     'приобрела 10% АО "Селектел"… Андрей Голухов приобрел 4,852% компании у Servertech', IFX, None),
    ('g9f6fe860', 'title', 'Selectel приобрел облачного провайдера «Единая сеть» (Servers.ru)',
     'Selectel купил облачного провайдера «Единая сеть»',
     'сообщает о приобретении 100% компании ООО «Единая сеть», работающей под брендами Servers.ru, Exepto.ru и Fozzy.ru',
     SEL, None),
    ('g9f6fe860', 'eco.share',
     'Приобретение компании «Единая сеть», работающей под брендами Servers.ru, Exepto.ru и Fozzy.ru.',
     '100% долей в ООО «Единая сеть»',
     'сообщает о приобретении 100% компании ООО «Единая сеть»', SEL, None),
    ('g9f6fe860', 'law.struct', 'Приобретение компании «Единая сеть».', '—',
     'поле повторяло предмет и ничего не сообщало о механике сделки', SEL, None),
    ('g9f6fe860', 'eco.val',
     'Если озвученная цена верна, Selectel переплатил: она равна двум годовым выручкам компании. Вероятно, '
     'покупателю нужна доля «Единой сети» на рынке выделенных серверов — в 2023 году это третий оператор рынка с долей 10%.',
     '—', 'мнение без автора в источниках карточки не найдено (Selectel, Habr) — снято', SEL, None),
    ('g9f6fe860', 'date', '2024-12-25', '2024',
     'Selectel сообщает о приобретении 100% компании ООО «Единая сеть» — день сделки в источниках не назван',
     SEL, None),
    ('geb221705', 'sum', '1 млрд ₽ (по оценке)', 'Не раскрыта',
     'Гендиректор "Infoline-аналитики" Михаил Бурмистров предполагает, что сумма сделки могла составить 1 млрд рублей — оценка аналитика, не цена',
     OB, 'sum'),
    ('geb221705', 'eco.sum', '1 млрд ₽ (по оценке)', 'Не раскрыта',
     'Гендиректор "Infoline-аналитики" Михаил Бурмистров предполагает, что сумма сделки могла составить 1 млрд рублей — оценка аналитика, не цена',
     OB, None),
    ('geb221705', 'sum_basis', 'estimate', None,
     'Михаил Бурмистров предполагает, что сумма сделки могла составить 1 млрд рублей', OB, None),
    ('gb5d8a18a', 'title', '«М.видео» закрыла допэмиссию: акционеры выкупили весь выпуск за 24,95 млрд рублей',
     'Акционеры «М.Видео» купили акции допэмиссии на 24,95 млрд ₽',
     '«М.Видео» завершило допэмиссию акций на 24,95 млрд рублей', VM, None),
    ('gb5d8a18a', 'law.struct',
     'Акции покупают не новые инвесторы с открытого рынка, а сама компания и структуры, связанные с ее нынешними собственниками.',
     'Акции покупают не новые инвесторы с открытого рынка, а структуры, связанные с нынешними собственниками компании.',
     'Все 500 миллионов обыкновенных акций дополнительного выпуска выкуплены по цене 49,9 рубля за акцию', PR, 'SUB'),
]
DATE_BASIS = {'gacc757b6': 'closing'}
# Правовая форма профилей сторон — по ЕГРЮЛ (party_legal_names.py не собрал имя: у АО «Группа Синара»
# в выписке нет кавычек, у «Библио-Глобуса» реестр не ответил; ИНН — из досье партии).
LEGAL = {'g0ecbc0fb': ('Группа «Синара»', 'АО «Группа Синара»'),        # АО ГРУППА СИНАРА, ИНН 6658252583
         'g4ff12e16': ('ТД «Библио-Глобус»', 'ООО «Торговый дом «Библио-Глобус»»')}  # ИНН 7701023055


def get(c, path):
    cur = c
    for k in path.split('.'):
        cur = (cur or {}).get(k)
    return cur


def put(c, path, val):
    ks = path.split('.')
    cur = c
    for k in ks[:-1]:
        cur = cur.setdefault(k, {})
    cur[ks[-1]] = val


def apply(data):
    by = {d['id']: d for d in data['deals']}
    n = 0
    for cid, path, old, new, quote, url, retract in EDITS:
        c = by[cid]
        if retract == 'SUB':
            cur = get(c, path)
            if new in cur and old not in cur:
                continue
            assert cur.count(old) == 1, (cid, path)
            new_full = cur.replace(old, new)
            put(c, path, new_full)
            fact_edit_guard.log(c, path, new_full, quote, url, BY, DAY)
            n += 1
            continue
        if get(c, path) == new:
            continue
        assert get(c, path) == old, (cid, path, get(c, path))
        if new is None and path in ('buyer', 'sum_basis'):
            c.pop(path, None)
        else:
            put(c, path, new)
        if retract:
            lst = c.setdefault('retracted', {}).setdefault(retract, [])
            if old not in lst:
                lst.append(old)
        fact_edit_guard.log(c, path, new, quote, url, BY, DAY)
        n += 1
    for pid, (name, short) in LEGAL.items():
        prof = data['companies'][pid]
        if prof.get('legal_short') == short:
            continue
        assert prof.get('name') == name and not prof.get('legal_short'), (pid, prof.get('name'))
        prof['legal_short'] = short
        n += 1
    for cid, basis in DATE_BASIS.items():
        if by[cid].get('date_basis') != basis:
            by[cid]['date_basis'] = basis
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
