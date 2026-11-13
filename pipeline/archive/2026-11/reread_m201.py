# -*- coding: utf-8 -*-
"""Вычитка базы, марафон 12 ноября 2026, партия m201, часть первая: ge4cded31, g43b0394d, g741672ac.

ge4cded31 (Тымлатский рыбокомбинат / «Алаид») — источники: АиФ-Приморье (пересказ Konkurent.ru, сам
            konkurent.ru — 502), Интерфакс 1052288, Ведомости Юг; реестр участников по ОГРН 1146504000477
            (datanewton.ru) и реестр лицензий МЧС (ИНН 6515003317, Северо-Курильск). Профиль предмета был
            сопоставлен с однофамильцем по названию — ООО «Компания Алаид» из Владивостока (ИНН 2536284622,
            единственный участник Тищенко с 2015 года); исправлен ИНН. По реестру 9 октября 2025 года из участников
            вышли ООО «Органик проект» (70%) и Сергей Бачин (30%) — продавец дополнен юрлицом. Отрасль по
            предмету (рыболовство) — «Агро», как у профилей и других рыбных сделок базы. Заголовок — по стандарту.
g43b0394d (RWB / «Инфо-Ю») — Коммерсантъ 8096717 (данные Rusprofile), Sostav, реестр участников (Плахотникова
            вышла 3 октября 2025 года, РВБ — 100%). Заголовок — по стандарту; проза — write_card.
g741672ac (Kama Flow / Platformeco) — Ведомости, Инк. (2 октября 2025), сообщение KAMA FLOW (опубликовано
            2 октября 2025: «We announced the closing of the deal at the Moscow Startup Summit»), datanewton:
            ООО «Платформеко» ИНН 9728110573 (ОГРН 1237700734590, руководитель Шелухин С. В.), доли участников
            совпадают с данными СПАРК в «Ведомостях» (65,04/18,4/11,04/5,52%) — профилю поставлен ИНН. Дата — день
            объявления о закрытии (date_basis closing). Заголовок — по стандарту («купил долю»).

gcfae418d («Севергрупп» / ЮМГ) — Коммерсантъ 8335691 (объявление 29 декабря 2025 года) и 8781323 (закрытие
            1 июля 2026 года: 23,85 млн акций, 20,9%). Дата 2025-10-01 не была днем никакого события сделки — исправлена
            на день закрытия. «Ее выручка… почти 13 млрд» в финансах предмета — выручка «Скандинавии», а не ЮМГ:
            переписано (write_card). Заголовок — по стандарту.

Запуск: без ключа — сухой прогон; --write — запись (база перечитывается прямо перед записью, assert на старые
значения, повторный запуск ничего не ломает). Правка факта — с fact_edit_guard.log.
"""
import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BY = 'вычитка 12 ноября 2026, партия m201'
DN_ALAID = 'https://datanewton.ru/api/v2/history?ogrn=1146504000477&startDate=2000-01-01&attributes=OWNERS'
IFX_ALAID = 'https://www.interfax.ru/business/1052288'
KOM_INFO = 'https://www.kommersant.ru/doc/8096717'
SOSTAV_INFO = 'https://www.sostav.ru/publication/russ-priobrel-tambovskogo-operatora-naruzhnoj-reklamy-info-yu-78638.html'
VED_KAMA = 'https://www.vedomosti.ru/technology/articles/2025/10/02/1143710-kama-flow-vlozhila'
INC_KAMA = 'https://incrussia.ru/news/kama-flow-investirovala-100-mln-rub-v-razrabotchika-produkta-dlya-vnedreniya-ii-agentov-platformeco/'
KF_KAMA = 'https://kamaflow.com/en/post/kama-flow-has-invested-100-million-rubles-in-platformeco/'
KOM_EMC2 = 'https://www.kommersant.ru/doc/8781323'
DN_PLAT = 'https://datanewton.ru/api/v2/history?ogrn=1237700734590&startDate=2000-01-01&attributes=OWNERS'

# (карточка, поле, новое значение, цитата, адрес)
SET = [
    ('ge4cded31', 'seller', 'ООО «Органик проект» и Сергей Бачин',
     '09.10.2025: Бачин Сергей Викторович (30%) и ООО «ОРГАНИК ПРОЕКТ» (70%) вышли из участников; вошло '
     'ООО «ТЫМЛАТСКИЙ РЫБОКОМБИНАТ» (ОГРН 1024101415546) — 100%.', DN_ALAID),
    ('ge4cded31', 'title', 'Тымлатский рыбокомбинат купил ООО «Алаид»',
     'ООО "Тымлатский рыбокомбинат" (ТРК, входит в группу Salmonica) стало владельцем рыбодобытчика ООО "Алаид" '
     '(Сахалин)', IFX_ALAID),
    ('ge4cded31', 'ind', 'Агро', '', ''),
    ('g43b0394d', 'title', 'RWB купил ООО «Инфо-Ю»',
     'Группа Russ, входящая в RWB, завершила сделку по приобретению тамбовского рекламного агентства «Инфо-Ю».',
     SOSTAV_INFO),
    ('g741672ac', 'title', 'Kama Flow купил долю в Platformeco',
     'Инвесткомпания получила миноритарный пакет в Platformeco, но его размер не раскрывается.', VED_KAMA),
    ('g741672ac', 'date_basis', 'closing', '', ''),
    ('gcfae418d', 'date', '2026-07-01',
     'EMC завершила объединение с сетью клиник «Скандинавия» «Севергрупп» получил 20,9% консолидированной компании '
     '01.07.2026, 18:13 Группа компаний «Европейский медицинский центр» (EMC) подписала сделку по объединению с сетью '
     'клиник «Скандинавия»', KOM_EMC2),
    ('gcfae418d', 'date_basis', 'closing', '', ''),
    ('gcfae418d', 'title', '«Севергрупп» купил 20,9% ЮМГ',
     'В результате «Севергрупп» получило 20,9% ЮМГ, сообщили в EMC.', KOM_EMC2),
]

OLD = {
    'ge4cded31|seller': 'Сергей Бачин',
    'ge4cded31|title': 'Тымлатский рыбокомбинат (Salmonica) приобрел ООО «Алаид» с квотами на добычу гребешка и рыбы',
    'ge4cded31|ind': 'ГМК и добыча',
    'g43b0394d|title': 'Wildberries и Russ приобрели регионального оператора наружной рекламы «Инфо-Ю»',
    'g741672ac|title': 'Kama Flow инвестировала 100 млн руб. в Platformeco',
    'g741672ac|date_basis': None,
    'gcfae418d|date': '2025-10-01',
    'gcfae418d|date_basis': None,
    'gcfae418d|title': 'Холдинг ЮМГ (EMC) привлек инвестицию «Севергрупп» в обмен на акции и клиники «Скандинавия»',
}

SRC_ADD = [
    ('g741672ac', 'KAMA FLOW', KF_KAMA),
    ('g741672ac', 'Инк.', INC_KAMA),
    ('ge4cded31', 'ЕГРЮЛ', DN_ALAID),
    ('g741672ac', 'ЕГРЮЛ', DN_PLAT),
]

# (профиль, поле, новое значение)
COMPANY = [
    ('gd60107d2', 'legal_short', 'ООО «Тымлатский рыбокомбинат»'),
    ('gb241fb3e', 'legal_short', 'ООО «Алаид»'),
    ('g3c6d4b91', 'legal_short', 'ООО «Платформеко»'),
    ('g7b8acf13', 'legal_short', 'МКПАО «ЮМГ»'),
    ('g7b8acf13', 'desc', 'Холдинг медицинских клиник (ЕМС, «Семейный доктор»); в 2026 году провел допэмиссию в пользу '
                          '«Севергрупп» Алексея Мордашова в обмен на клиники «Скандинавия», сделка одобрена ФАС.'),
]
COMPANY_OLD = {
    'gd60107d2|legal_short': None,
    'gb241fb3e|legal_short': None,
    'g3c6d4b91|legal_short': None,
    'g7b8acf13|legal_short': None,
    'g7b8acf13|desc': 'Холдинг медицинских клиник (ЕМС, «Семейный доктор»); в 2025 году провел допэмиссию в пользу '
                      '«Севергрупп» Алексея Мордашова в обмен на клиники «Скандинавия», сделка одобрена ФАС.',
}

# (профиль, прежний ИНН, новый ИНН, почему)
REGISTRY = [
    ('gb241fb3e', '2536284622', '6515003317',
     'ООО «Алаид», ОГРН 1146504000477, ИНН 6515003317, Северо-Курильск (реестр лицензий МЧС России); тот же ОГРН — '
     'история участников ЕГРЮЛ (datanewton.ru): 16.05.2024 вошли Сергей Бачин (30%) и ООО «Органик проект» (70%), '
     '09.10.2025 вошел ООО «Тымлатский рыбокомбинат» (100%) — ровно как в Интерфаксе и АиФ. Прежний ИНН 2536284622 — '
     'владивостокская ООО «Компания Алаид» (единственный участник Тищенко с 2015 года), другая компания.'),
    ('g3c6d4b91', None, '9728110573',
     'ООО «Платформеко», ОГРН 1237700734590, ИНН 9728110573, руководитель Шелухин С. В. (datanewton.ru); доли '
     'участников в истории ЕГРЮЛ (Шелухин 65,04%, Бондарик 18,4%, Юсупов 11,04%, «Портофино Кэпитал» 5,52%) '
     'совпадают с данными СПАРК в «Ведомостях» 2 октября 2025 года.'),
]


def _get(card, field):
    o = card
    for p in field.split('.'):
        o = o.get(p) if isinstance(o, dict) else None
    return o


def _set(card, field, value):
    parts = field.split('.')
    o = card
    for p in parts[:-1]:
        o = o.setdefault(p, {})
    o[parts[-1]] = value


def _apply(data):
    sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
    sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
    import fact_edit_guard
    import review
    deals = {d['id']: d for d in data['deals']}
    comps = data['companies']
    changed = 0
    for cid, field, new, quote, url in SET:
        card = deals[cid]
        cur = _get(card, field)
        if cur == new:
            continue                                   # уже применено
        assert cur == OLD['%s|%s' % (cid, field)], (cid, field, cur)
        _set(card, field, new)
        changed += 1
        if field in fact_edit_guard.FACT_FIELDS:
            assert quote and url, (cid, field)
            fact_edit_guard.log(card, field, new, quote, url, BY)
        marks = card.setdefault('proofread_absorbed', {}).setdefault(field, [])
        for f in review.FIXES:
            if (f.get('id'), f.get('field')) == (cid, field) and f.get('new') != new:
                fp = review.fix_fingerprint(f['new'])
                if fp not in marks:
                    marks.append(fp)
        if not marks:
            card['proofread_absorbed'].pop(field, None)
    for cid, label, url in SRC_ADD:
        src = deals[cid].setdefault('src', [])
        if not any(u == url for _l, u in src):
            src.append([label, url])
    for comp, field, new in COMPANY:
        cur = comps[comp].get(field)
        if cur == new:
            continue
        assert cur == COMPANY_OLD['%s|%s' % (comp, field)], (comp, field, cur)
        comps[comp][field] = new
    return changed


def _apply_registry(write):
    path = os.path.join(ROOT, 'pipeline', 'fns_registry.json')
    rows = json.load(open(path, encoding='utf-8'))
    for comp, old, new, reason in REGISTRY:
        row = [r for r in rows if r.get('company_id') == comp]
        assert len(row) == 1 and row[0].get('inn') in (old, new), (comp, row)
        row[0].update({'inn': new, 'decision': 'confirmed', 'reason': reason, 'date': '2026-11-12'})
    if write:
        json.dump(rows, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        open(path, 'a', encoding='utf-8').write('\n')


if __name__ == '__main__':
    sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
    path = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
    base = json.load(open(path, encoding='utf-8'))
    new = copy.deepcopy(base)
    n = _apply(new)
    _apply_registry(False)
    import fact_edit_guard
    print('fact_edit_guard:', fact_edit_guard.problem(base, new) or 'чисто')
    print('Полей к записи: %d (из %d в списке).' % (n, len(SET)))
    if '--write' in sys.argv:
        import mass_edit_guard
        fresh = json.load(open(path, encoding='utf-8'))      # перечитать прямо перед записью
        before = copy.deepcopy(fresh)
        _apply(fresh)
        mass_edit_guard.check(before, fresh, key=os.environ.get('MASS_OK'))
        json.dump(fresh, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        _apply_registry(True)
        print('Записано.')
    else:
        print('Сухой прогон. Запись — с ключом --write.')
