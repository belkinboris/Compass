# -*- coding: utf-8 -*-
"""Вычитка базы, партия m101 (марафон 12 ноября 2026), часть 1: gb89d3a84 (АО «Медприбор» / ООО «ВТС»).

Источники открыты заново и сохранены save_source.save() в data/inbox/triage/sources_2026-11-12_m101.json:
Коммерсантъ 9092327 (текст статьи из страницы), Vademecum 09.11.2026, выписка ЕГРЮЛ по ООО «ВТС» (api-fns.ru, метод egr).

  gb89d3a84 — Ъ: «Медприбор» «стало владельцем ООО «ВТС», ранее принадлежавшего» Александре Губе, «сделка прошла
              осенью»; Vademecum по СПАРК: «переход 100% доли». ЕГРЮЛ: ООО «ВТС» (ИНН 7841001703) — 100% у Губы
              Александры Сергеевны с 05.09.2013 по 18.10.2026, с 19.10.2026 — 100% у АО «МЕДПРИБОР» (ИНН 7801148650,
              в процессе реорганизации присоединением — как в Ъ). Дата — день записи в реестре (19.10.2026), а не день
              публикации. «1,2–1,3 млрд ₽» — оценка гендиректора Infoline-Аналитики Михаила Бурмистрова стоимости 100% долей,
              не цена: сумма — «Не раскрыта», оценка уже в eco.val. Предмет — именем общества, доля — в eco.share.

Порядок записи (reread_apply.py): review.py --write (FIXES), затем разовая часть этого файла с --write
(ONE_OFF/_SET/_RETRACT/_SRC_ADD). Поля разовой части и FIXES не пересекаются.
"""

O = {}
O[('gb89d3a84', 'title')] = 'АО «Медприбор» купило долю в ООО «ВТС»'
O[('gb89d3a84', 'asset')] = ('ООО «ВТС» — поставщик медицинского оборудования, официальный партнер Siemens Healthineers '
                             'по поставке и обслуживанию томографов и УЗИ-аппаратов')
O[('gb89d3a84', 'eco.share')] = '—'

WHY = 'вычитка 12 ноября 2026 (партия m101) по статье, сохраненной save_source.py; '
_J = ' … '
_BY = 'reread m101'

_KM = 'https://www.kommersant.ru/doc/9092327'
_VAD = ('https://vademec.ru/news/2026/11/09/svyazannaya-s-iclinic-kompaniya-priobrela-rossiyskogo-partnera-'
        'siemens-healthineers/')
_EGR = 'https://api-fns.ru/api/egr?req=7841001703'

_K_OWN = ('Петербургское АО «Медприбор», связанное с ГК «Центральная медицинская база» Эдуарда Иванова, стало владельцем '
          'ООО «ВТС», ранее принадлежавшего малоизвестной в медийном поле предпринимательнице Александре Губе')
_K_EST = ('Гендиректор «Infoline-Аналитики» Михаил Бурмистров оценивает стоимость 100% долей ВТС в 1,2–1,3 млрд рублей '
          'с учетом средств на счетах')
_V_100 = 'Данные о переходе 100% доли в «ВТС» компании «Медприбор» отражены в СПАРК-Интерфакс'
_R_NEW = 'Участник с 19 октября 2026 года: АО "МЕДПРИБОР" (ИНН 7801148650'
_R_OLD = 'Прежний участник: Губа Александра Сергеевна, доля 100%, с 5 сентября 2013 года по 18 октября 2026 года'


def _f(cid, field, new, quote, why):
    return {'id': cid, 'field': field, 'old': O[(cid, field)], 'new': new, 'quote': quote, 'why': WHY + why}


FIXES = [
    _f('gb89d3a84', 'asset', 'ООО «ВТС»', _K_OWN,
       'предмет — именем общества; чем занимается ВТС, уже сказано в контексте'),
    _f('gb89d3a84', 'eco.share', '100% доли в ООО «ВТС»', _V_100 + _J + _K_OWN,
       'доля не была записана: перешли 100% долей (Vademecum по СПАРК, ЕГРЮЛ)'),
    _f('gb89d3a84', 'title', 'АО «Медприбор» купило ООО «ВТС»', _K_OWN + _J + _V_100,
       'куплены 100% долей — «купило долю» не согласуется с предметом'),
]

ONE_OFF = [
    ('gb89d3a84', 'sum', '1,2-1,3 млрд ₽ (по оценке)', 'Не раскрыта', _K_EST, _KM),
    ('gb89d3a84', 'eco.sum', '1,2-1,3 млрд ₽ (по оценке)', 'Не раскрыта', _K_EST, _KM),
    ('gb89d3a84', 'date', '2026-11-09', '2026-10-19', _R_NEW + _J + _R_OLD, _EGR),
]
_SET = [
    ('gb89d3a84', 'accepted_notes.no_profile.target',
     'ООО «ВТС» (vtsmedical.ru, адрес Санкт-Петербург, ул. Володи Ермака 17) — найден сайт и партнерская страница '
     'Siemens Healthineers, но ОГРН/ИНН не нашли ни там, ни на rusprofile/2ГИС/list-org по названию — профиль без ИНН не заводим',
     'ООО «ВТС», ИНН 7841001703, ОГРН 1037867002810 (СПАРК: ул. Володи Ермака, 17, гендиректор Сергей Пинчук; ЕГРЮЛ по '
     'api-fns.ru) — найдено вычиткой 12.11.2026; профиль компании не заведен, ИНН записан здесь'),
    ('gb89d3a84', 'accepted_notes.no_profile.buyer',
     'АО «Медприбор» — WebSearch нашел кандидата (ИНН 7801148650, в процессе реорганизации — совпадает со статьей), но '
     'руководитель по данным агрегатора (Иванова Надежда) не совпадает с названным в статье владельцем (Эдуард Иванов) — '
     'совпадение не подтверждено, профиль с неточным ИНН не заводим',
     'АО «Медприбор», ИНН 7801148650, ОГРН 1027800539557 — подтверждено вычиткой 12.11.2026: именно это общество с '
     '19.10.2026 записано в ЕГРЮЛ единственным участником ООО «ВТС» (100%), и оно в реорганизации присоединением, как '
     'пишет Коммерсантъ; Эдуард Иванов — учредитель, а не гендиректор, расхождения нет. Профиль компании не заведен, ИНН записан здесь'),
    ('gb89d3a84', 'accepted_notes.no_inn.buyer',
     'АО «Медприбор» — см. no_profile.buyer: кандидат по ИНН нашелся, но расходится по руководителю, не подтвержден',
     'АО «Медприбор» — ИНН 7801148650 подтвержден реестром (см. no_profile.buyer)'),
    ('gb89d3a84', 'accepted_notes.no_profile.seller',
     'Александра Губа — физлицо, продавец доли, профиль компании не нужен; первоисточник (Коммерсантъ через Mergers.ru) '
     'сам называет ее как прежнюю владелицу, история участников ЕГРЮЛ через datanewton не проверялась (нет ключа) — '
     'имя продавца уже известно из статьи, а не из реестра',
     'Александра Губа — физлицо, продавец: по ЕГРЮЛ (api-fns.ru) владела 100% ООО «ВТС» с 05.09.2013 по 18.10.2026, '
     'как и пишет Коммерсантъ; профиль компании не нужен'),
    ('gb89d3a84', 'date_basis', None, 'registry'),
]
_RETRACT = [
    ('gb89d3a84', 'sum', '1,2-1,3 млрд ₽ (по оценке)'),
]
_NOTES = []
_SRC_ADD = [
    ('gb89d3a84', None, ['ЕГРЮЛ: участники ООО «ВТС»', _EGR]),
]
_COMPANY = []


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
    for cid, field, value in _RETRACT:
        lst = deals[cid].setdefault('retracted', {}).setdefault(field, [])
        if value not in lst:
            lst.append(value)
    for cid, path, value in _NOTES:
        notes = deals[cid].setdefault('accepted_notes', {})
        if _get(notes, path) == value:
            continue
        assert _get(notes, path) is None, (cid, path, _get(notes, path))
        _set(notes, path, value)
    for cid, pos, pair in _SRC_ADD:
        src = deals[cid].setdefault('src', [])
        if any(s[1] == pair[1] for s in src):
            continue
        if pos is None:
            src.append(list(pair))
        else:
            src.insert(pos, list(pair))
    for comp, field, old, new in _COMPANY:
        c = data['companies'][comp]
        if c.get(field) == new:
            continue
        assert c.get(field) == old, (comp, field, c.get(field))
        c[field] = new


if __name__ == '__main__':
    import copy
    import json
    import os
    import sys
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(os.path.dirname(here)))       # pipeline/
    sys.path.insert(0, os.path.dirname(here))                         # pipeline/ingest/
    import mass_edit_guard  # noqa: E402
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(here))), 'static', 'data', 'deals_promoted.json')
    data = json.load(open(path, encoding='utf-8'))
    before = copy.deepcopy(data)
    _apply(data)
    mass_edit_guard.check(before, data, os.environ.get('MASS_OK'))
    print('Разовая часть: полей-фактов %d, полей %d, снятых значений %d — проверки пройдены.'
          % (len(ONE_OFF), len(_SET), len(_RETRACT)))
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
