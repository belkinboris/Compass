# -*- coding: utf-8 -*-
"""Вычитка базы, партия m020 (марафон 12 ноября 2026): разовая часть — заголовки по стандарту, стороны, дата, сумма.

Каждый источник открыт заново (curl с обычным браузерным User-Agent) и сохранен save_source.save() в
data/inbox/triage/sources_2026-11-12_m020.json; история участников ЕГРЮЛ ООО «Центральное» — туда же текстом.

  g2369d101 — Ведомости 31.01.2023: из акционеров вышла «Биаксплен» из группы «Сибур» (продавец был пуст);
              заголовок — по стандарту закрытой покупки. ТАСС — защита от роботов, текст тот же у Ведомостей.
  g10053480 — Ъ 8655960: переговоры по словам источников — «может купить»; продавец в статье не назван
              (бенефициары АО «УК „Саратов-Птица“» не раскрываются).
  gd1b1a94e — Ъ 8604447: 1,25–1,4 млрд руб. — оценка Ивана Пешкова (BGP Capital), не цена сделки: сумма —
              «Не раскрыта», оценка остается в eco.val.
  g8a86fc9b — заголовок без юрлица в скобках.
  g34cab70b — дата годом → день записи в ЕГРЮЛ (26.02.2026, «Тамбовский бекон» 51%); заголовок без региона.
  gd2696c44 — Известия: переговоры по словам источников — «может купить».
  g5b8fa758 — Ъ 8692225: владелец «Островка» — Emerging Travel Group (ETG), продавец был пуст.

Без ключа — сухой прогон, запись по --write; база перечитывается прямо перед записью; повторный запуск
ничего не ломает (уже примененное пропускается).
"""
_BY = 'reread m020'
_J = ' … '
_REG = 'https://projectcompass.ru/api/companies/%s/fns'
_VED = 'https://www.vedomosti.ru/business/news/2023/01/31/961176-sibur-vishel-iz-manucor'
_MN_Q = ('Manucor указывает, что 16 января была завершена «сложная операция», в результате которой компания '
         '«Биаксплен», входящая в «Сибур», вышла из состава ее акционеров. Владельцем 5% Manucor стала компания '
         'L&M S.p.A.')
_MN_Q2 = 'Другой акционер – Loren SPV S.r.l. – увеличил свою долю до 95%.' + _J + '«Сибур» приобрел 50% Manucor'
_SP_Q = 'Агрохолдинг «Таврос» ведет переговоры о покупке поволжского производителя «Саратов-Птица»'
_KS_SP = 'https://www.kommersant.ru/doc/8655960'
_CX_Q = ('Руководитель департамента M&A BGP Capital Иван Пешков оценивает потенциальную стоимость сети в '
         '1,25–1,4 млрд руб.')
_CX_Q2 = 'Наиболее вероятным покупателем один из них называет фонд «Бумеранг Капитал».'
_KS_CX = 'https://www.kommersant.ru/doc/8604447'
_CD_Q = 'VK Tech купила CedrusData — независимого разработчика решений для больших данных и ИИ'
_RB_CD = 'https://rb.ru/news/vk-tech-kupila-cedrusdata-nezavisimogo-razrabotchika-reshenij-dlya-bolshih-dannyh-i-ii/'
_RA_REG = ('2026-02-26 share_changed: Рязанов Александр Николаевич (100.0 → 49.0); 2026-02-26 joined: ООО '
           '"ТАМБОВСКИЙ БЕКОН" (None → 51.0)')
_RA_Q = 'Агрохолдинг «Русагро» вошел в уставный капитал ООО «Центральное»' + _J + 'Доля компании составила 51%'
_KS_RA = 'https://www.kommersant.ru/doc/8443121'
_TT_Q = '«Туту» ведет переговоры о покупке платформы по организации командировок Trivio'
_IZ_TT = 'https://iz.ru/2027534/2026-01-20/tutu-vedet-peregovory-o-pokupke-servisa-delovykh-poezdok-trivio-za-8-mlrd-rublei'
_OS_Q = 'Владелец платформы — компания Emerging Travel Group (ETG) — готов отдать ее за 20 млрд руб.'
_KS_OS = 'https://www.kommersant.ru/doc/8692225'

ONE_OFF = [
 ('g2369d101', 'title', 'Дочка Сибура вышла из капитала итальянского производителя БОПП-пленки Manucor',
  'Loren SPV и L&M купили 50% Manucor у «Сибура»', _MN_Q + _J + _MN_Q2, _VED),
 ('g2369d101', 'seller', None, 'Сибур', _MN_Q, _VED),
 ('g2369d101', 'seller_id', None, 'g7f9a1e5e', _MN_Q, _VED),
 ('g10053480', 'title', 'ГК «Таврос» покупает «Саратов-Птицу»', '«Таврос» может купить «Саратов-Птицу»', _SP_Q, _KS_SP),
 ('gd1b1a94e', 'title', 'Фонд «Бумеранг Капитал» рассматривает приобретение сети кофеен Cofix',
  '«Бумеранг Капитал» может купить российский бизнес Cofix', _CX_Q2, _KS_CX),
 ('gd1b1a94e', 'sum', '1,25–1,4 млрд ₽ (по оценке)', 'Не раскрыта', _CX_Q, _KS_CX),
 ('gd1b1a94e', 'eco.sum', '1,25–1,4 млрд ₽ (по оценке)', 'Не раскрыта', _CX_Q, _KS_CX),
 ('g8a86fc9b', 'title', 'VK Tech приобрела CedrusData (ООО «Кверифай Лабс»)', 'VK Tech купила CedrusData', _CD_Q, _RB_CD),
 ('g34cab70b', 'title', '«Русагро» приобрела 51% ООО «Центральное» в Тамбовской области',
  '«Русагро» купила 51% ООО «Центральное»', _RA_Q, _KS_RA),
 ('g34cab70b', 'date', '2026', '2026-02-26', _RA_REG, _REG % 'g56e4248d'),
 ('gd2696c44', 'title', 'Tutu.ru покупает Trivio — платформу для организации корпоративных командировок',
  'Tutu.ru может купить Trivio', _TT_Q, _IZ_TT),
 ('g5b8fa758', 'seller', None, 'Emerging Travel Group', _OS_Q, _KS_OS),
]
_SET = [
 ('g34cab70b', 'date_basis', None, 'registry'),
]
_NOTES = [
 ('g5b8fa758', 'no_profile.seller',
  'Emerging Travel Group зарегистрирована в США, российские юрлица «Островка» контролирует Maletto Investments Ltd '
  '(ОАЭ) — профиль с ИНН не заводится (Ъ 8692225, ЕГРЮЛ ООО «Агентика Тревэл»; вычитка 12.11.2026, m020)'),
 ('g10053480', 'no_profile.seller',
  'продавец не назван: Ъ 8655960 — бенефициары АО «УК „Саратов-Птица“» не раскрываются, в 2024 году бизнес '
  'контролировали Елена Высоцкая (70%) и Дмитрий Иванов (30%); сделка не закрыта, кто продаст — неизвестно; '
  'искали: Ъ, поиск по «Таврос Саратов-Птица», реестр АО (недоступен) (вычитка 12.11.2026, m020)'),
 ('gd1b1a94e', 'no_profile.seller',
  'продавец не назван: сделка обсуждается; по ЕГРЮЛ 99,99% ООО «Урбан Кофикс Раша» у «Кофикс Глобал Лимитед», '
  'бенефициары по Ъ 8604447 — Cofix Group, Coffee Prime и Михаил и Григорий Печерские (в eco.context) '
  '(вычитка 12.11.2026, m020)'),
 ('gd2696c44', 'no_profile.seller',
  'продавец не назван: Известия, dp.ru и tourdom.ru пишут о переговорах «Туту» с Trivio, но владельцев Trivio '
  'не называют; реестр Trivio недоступен (вычитка 12.11.2026, m020)'),
]


def _get(obj, field):
    for p in field.split('.'):
        obj = obj.get(p) if isinstance(obj, dict) else None
    return obj


def _set(obj, field, value):
    parts = field.split('.')
    for p in parts[:-1]:
        obj = obj.setdefault(p, {})
    obj[parts[-1]] = value


def _apply(data):
    """Повторный запуск ничего не ломает: уже примененное пропускается."""
    import fact_edit_guard
    deals = {d['id']: d for d in data['deals']}
    for cid, field, old, new, quote, url in ONE_OFF:
        card = deals[cid]
        if _get(card, field) == new:
            continue
        assert _get(card, field) == old, (cid, field, _get(card, field))
        _set(card, field, new)
        fact_edit_guard.log(card, field, new, quote, url, _BY)
    for cid, field, old, new in _SET:
        if _get(deals[cid], field) == new:
            continue
        assert _get(deals[cid], field) == old, (cid, field, _get(deals[cid], field))
        _set(deals[cid], field, new)
    for cid, path, value in _NOTES:
        notes = deals[cid].setdefault('accepted_notes', {})
        if _get(notes, path) == value:
            continue
        assert _get(notes, path) is None, (cid, path, _get(notes, path))
        _set(notes, path, value)


if __name__ == '__main__':
    import copy
    import json
    import os
    import sys
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(os.path.dirname(os.path.dirname(here)))
    sys.path.insert(0, os.path.join(root, 'pipeline'))
    sys.path.insert(0, os.path.join(root, 'pipeline', 'ingest'))
    import mass_edit_guard  # noqa: E402
    path = os.path.join(root, 'static', 'data', 'deals_promoted.json')
    data = json.load(open(path, encoding='utf-8'))
    before = copy.deepcopy(data)
    _apply(data)
    mass_edit_guard.check(before, data, os.environ.get('MASS_OK'))
    print('Разовая часть m020: полей-фактов %d, заметок %d — проверки пройдены.' % (len(ONE_OFF), len(_NOTES)))
    if '--write' in sys.argv:
        fresh = json.load(open(path, encoding='utf-8'))      # перечитать прямо перед записью
        before = copy.deepcopy(fresh)
        _apply(fresh)
        mass_edit_guard.check(before, fresh, os.environ.get('MASS_OK'))
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(fresh, fh, ensure_ascii=False, indent=1)
        print('Записано.')
    else:
        print('Сухой прогон. Запись — с ключом --write.')
