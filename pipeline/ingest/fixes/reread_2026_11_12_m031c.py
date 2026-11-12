# -*- coding: utf-8 -*-
"""Вычитка базы, партия m031 (марафон 12 ноября 2026), часть C: две старые карточки, полная вычитка.

gd71753e0 (Яндекс / eLama), g2c2e274b (группа «Холдинг Аква» / «Архыз Оригинал»).

Источники открыты заново и сохранены save_source.save() в data/inbox/triage/sources_2026-11-12_m031.json.

Поиск источников и сверка с реестром:
  gd71753e0 — сообщение Яндекса 13.06.2024, ADPASS, СПИБА (Maxima Legal и Nextons — консультанты продавцов, один из
              продавцов — сооснователь Максим Горбачев); Nextons — сброс соединения, Marketscreener — доступ закрыт.
              Реестр сайта: ООО «АДВ-Сервис» (основное юрлицо eLama по ADPASS) Яндексу не переходило — в 2026 году его
              участники Андрей Липатов и ЛФ Капитал; Яндекс купил технологическую платформу сервиса, поэтому
              правовая форма предмету не ставится.
  g2c2e274b — РБК 10.06.2024 (сделка закрыта 10 июня, согласования ФАС получены); РБК Компании — 401. Покупатель —
              ООО «Аква Инвестиции» (владелец 100% ООО «Холдинг Аква»): профиль группы получил это юрлицо.
"""

_BY = 'reread m031c'

FIXES = [{'id': 'gd71753e0',
  'field': 'eco.val',
  'old': 'Аналитики оценивают сумму сделки в 10−15 млрд ₽. Более низкие оценки называли основатель MediaSniper '
         'Дмитрий Туркевич — 6–7,5 млрд ₽ за всю компанию, старший аналитик Газпромбанка Сергей Либин, придерживаясь '
         'консервативной оценки, — 10 млрд ₽, старший партнер VDI Group Илья Хоффман — 6–8,5 млрд ₽. Общая оценка '
         'компании — 6–10 млрд ₽.',
  'new': 'Опрошенные эксперты оценили весь бизнес eLama в 6–10 млрд ₽: основатель MediaSniper Дмитрий Туркевич — в '
         '6–7,5 млрд ₽, старший партнер VDI Group Илья Хоффман — в 6–8,5 млрд ₽, старший аналитик Газпромбанка '
         'Сергей Либин при консервативном подходе — в 10 млрд ₽.',
  'quote': 'Опрошенные ADPASS эксперты оценили весь бизнес eLama в коридоре в 6-10 млрд рублей. … основатель '
           'платформы алгоритмических закупок MediaSniper Дмитрий Туркевич … что дало бы стоимость всей компании в '
           '6-7,5 млрд рублей … Старший партнер консалтинговой группы VDI Group Илья Хоффман … текущая оценка '
           'компании, вероятно, находится в интервале 3-4,5 EBITDA или в денежном выражении в диапазоне 6-8,5 млрд '
           'рублей … старший аналитик Газпромбанка Сергей Либин … –— Придерживаясь консервативной оценки, получим 10 '
           'млрд рублей».',
  'why': 'вычитка 12 ноября 2026 (партия m031) по статье, сохраненной save_source.py; оценки «10–15 млрд ₽» нет ни в '
         'одном источнике'},
 {'id': 'gd71753e0',
  'field': 'eco.context',
  'old': 'Стороны не раскрыли ключевые параметры сделки. Неясно, кто именно продавал и какую часть — фонд Impulse VC '
         'Романа Абрамовича или основатель Алексей Довжиков.',
  'new': 'О покупке eLama Яндекс впервые объявил в январе 2022 года и рассчитывал закрыть сделку к середине того же '
         'года, но она затянулась на два с лишним года. Кто из владельцев и какую долю продал, стороны не раскрыли; '
         'один из продавцов — сооснователь платформы Максим Горбачев. В 2014 году фонд Impulse VC Романа Абрамовича '
         'вложил в eLama $800 тыс. за миноритарную долю.',
  'quote': 'Впервые «Яндекс» объявил о приобретении eLama в январе 2022. Тогда компания рассчитывала закрыть сделку '
           'уже к середине года. … Яндекс завершил сделку по покупке технологической платформы сервиса eLama. … Но '
           'покупатель и продавец скрыли ее ключевые параметры: кто и в каком объеме продал свои доли — инвестфонд '
           'Романа Абрамовича Impulse VC или основатель компании Алексей Довжиков, а также во сколько была оценена '
           'компания. … Максим Горбачев, один из основателей и продавцов платформы eLama … Известно, что в 2014 году '
           'венчурный фонд Impulse VC Романа Абрамовича вложил в eLama $800 тыс., получив миноритарную долю.',
  'why': 'вычитка 12 ноября 2026 (партия m031) по статье, сохраненной save_source.py; продавец частично известен '
         '(сооснователь Максим Горбачев, СПИБА)'},
 {'id': 'g2c2e274b',
  'field': 'title',
  'old': 'АФК «Система» передала 100% «Архыз VITA» группе «Холдинг Аква»',
  'new': 'Группа «Холдинг Аква» купила 100% «Архыз Оригинал» у АФК «Система»',
  'quote': 'По итогам сделки ООО «Аква Инвестиции», владеющее 100% ООО «Холдинг Аква», получило полный контроль над '
           'производителем воды «Архыз VITA» (ООО «Архыз Оригинал»). … Компания передала 100% производителя «Архыз '
           'VITA» группе «Холдинг Аква», выпускающей «Ессентуки» и «Нарзан».',
  'why': 'вычитка 12 ноября 2026 (партия m031) по статье, сохраненной save_source.py; стандарт закрытой покупки «X '
         'купил N% Y у Z» (pipeline/title_standard.py)'},
 {'id': 'g2c2e274b',
  'field': 'eco.share',
  'old': '—',
  'new': '100% долей ООО «Архыз Оригинал»',
  'quote': 'По итогам сделки ООО «Аква Инвестиции», владеющее 100% ООО «Холдинг Аква», получило полный контроль над '
           'производителем воды «Архыз VITA» (ООО «Архыз Оригинал»).',
  'why': 'вычитка 12 ноября 2026 (партия m031) по статье, сохраненной save_source.py; доля не была заполнена'},
 {'id': 'g2c2e274b',
  'field': 'law.struct',
  'old': 'Доля АФК «Система» в уставном капитале «Аква Инвестиций» выросла до 37,5%.',
  'new': 'АФК «Система» передала 100% ООО «Архыз Оригинал» в ООО «Аква Инвестиции», которому принадлежит 100% ООО '
         '«Холдинг Аква». В обмен доля «Системы» в «Аква Инвестициях» выросла до 37,5%, и она стала крупнейшим '
         'акционером.',
  'quote': 'По итогам сделки ООО «Аква Инвестиции», владеющее 100% ООО «Холдинг Аква», получило полный контроль над '
           'производителем воды «Архыз VITA» (ООО «Архыз Оригинал»). … «Таким образом, доля АФК «Система» в уставном '
           'капитале «Аква Инвестиций» увеличилась до 37,5%, что сделало ее крупнейшим акционером компании», — '
           'уточнили в «Холдинг Аква».',
  'why': 'вычитка 12 ноября 2026 (партия m031) по статье, сохраненной save_source.py; добавлено, кто получил '
         'компанию и как «Система» стала акционером'},
 {'id': 'g2c2e274b',
  'field': 'law.appr',
  'old': 'Публично не сообщалось',
  'new': 'По словам «Холдинг Аква», сделку согласовала ФАС.',
  'quote': 'Сделка была закрыта 10 июня, уточнили в «Холдинг Аква». Условия сделки в компании не раскрыли, добавив '
           'лишь, что она получила все необходимые согласования от ФАС.',
  'why': 'вычитка 12 ноября 2026 (партия m031) по статье, сохраненной save_source.py; стояло «Публично не '
         'сообщалось», хотя холдинг сообщил о согласованиях ФАС'},
 {'id': 'g2c2e274b',
  'field': 'eco.context',
  'old': 'ООО «Аква Инвестиции», которому принадлежит 100% ООО «Холдинг Аква», получило полный контроль над ООО '
         '«Архыз Оригинал» — производителем воды «Архыз VITA», купленным «дочкой» «Системы» в 2022 году за 450 млн '
         '₽. По итогам 2025 года прибыль компании составила 439 938 000 ₽ при выручке 12 214 350 000 ₽.',
  'new': 'В июне 2022 года «Архыз Оригинал» за 450 млн ₽ купила «дочка» АФК «Система»; еще до этого «Система» как '
         'кредитор фактически руководила компанией.',
  'quote': 'Эту компанию «дочка» АФК «Система» купила в июне 2022 года за 450 млн руб. … До сделки АФК «Система» '
           'была кредитором компании и фактически управляла ее бизнесом, сообщал «Коммерсантъ».',
  'why': 'вычитка 12 ноября 2026 (партия m031) по статье, сохраненной save_source.py; прибыль и выручка «за 2025 '
         'год» без названия компании не подтвердились ни в одном открытом источнике (РБК Компании — 401)'},
 {'id': 'g2c2e274b',
  'field': 'extra',
  'old': 'АФК «Система» передала 100% производителя минеральной воды «Архыз VITA» группе «Холдинг Аква», которая '
         'выпускает «Ессентуки» и «Нарзан». После объединения АФК «Система» стала крупнейшим акционером холдинга.',
  'new': 'До сделки в портфеле «Холдинг Аква» были «Ессентуки» № 4 и № 17, «Нарзан» и Gorji. Холдинг считает себя '
         'вторым производителем упакованной минеральной воды в России: 5,5% рынка в деньгах. За 2023 год его выручка '
         'выросла до 6,5 млрд ₽ с 4,3 млрд ₽, а чистая прибыль упала почти на 22%, до 300,3 млн ₽.',
  'quote': 'До сих пор «Холдинг Аква» был известен как единственный производитель минеральной воды «Ессентуки» № 4 и '
           '№ 17 и «Нарзан», а также бренда Gorji. … «Холдинг Аква», по собственным данным, занимает второе место на '
           'рынке упакованной минеральной воды в России с долей 5,5% в денежном выражении. … В 2023 году ее выручка '
           'составила 6,5 млрд руб. против 4,3 млрд руб. в 2022-м. Впрочем, чистая прибыль за год сократилась почти '
           'на 22%, до 300,3 млн руб.',
  'why': 'вычитка 12 ноября 2026 (партия m031) по статье, сохраненной save_source.py; прежний текст повторял '
         'заголовок и устройство сделки'}]

ONE_OFF = [('gd71753e0',
  'eco.rationale',
  None,
  'Яндекс объяснил покупку тем, что сможет лучше приспособить свои рекламные сервисы к малому и среднему бизнесу: на '
  'опыте eLama и с нейросетями Яндекса для таких компаний появятся новые инструменты управления рекламой. Платформа '
  'сохранит свой бренд.',
  'Сделка позволит лучше адаптировать рекламные сервисы Яндекса под потребности малого и среднего бизнеса. Такой '
  'бизнес со временем получит новые инструменты для управления рекламой — они будут созданы на базе опыта eLama и с '
  'использованием нейросетевых технологий Яндекса. Яндекс продолжит развивать платформу под тем же брендом.',
  'https://yandex.ru/company/news/01-13-06-2024'),
 ('gd71753e0',
  'seller',
  None,
  'Максим Горбачев и другие основатели eLama',
  'Максим Горбачев, один из основателей и продавцов платформы eLama … Юридическими консультантами со стороны '
  'продавцов выступают Maxima Legal и Nextons.',
  'https://spiba.ru/news/maxima-legal-i-nextons-predstavili-interesy-prodavczov-v-ramkah-sdelki-po-pokupke-yandeksom-tehnologicheskoj-platformy-elama/')]

_SET = [('gd71753e0', 'seller_src', None, 'text'), ('g2c2e274b', 'date_basis', None, 'closing')]

_RETRACT = []

_NOTES = []

_COMPANY = [('g0dd2333b', 'legal_short', None, 'ООО «Аква Инвестиции»'),
 ('gf5f447de', 'legal_short', None, 'ООО «Архыз Оригинал»')]

GOLD = []

BASELINE_GONE = []



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
    import review
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
    for comp, field, old, new in _COMPANY:
        c = data['companies'][comp]
        if c.get(field) == new:
            continue
        assert c.get(field) == old, (comp, field, c.get(field))
        c[field] = new
    # Прежние записи таблицы на те же поля (архив партий) учтены отпечатком: новая запись этой партии — последняя.
    mine = {(f['id'], f['field']) for f in FIXES}
    for f in review.FIXES:
        key = (f['id'], f['field'])
        if key in mine and f not in FIXES and f.get('field') != 'src':
            marks = deals[key[0]].setdefault('proofread_absorbed', {}).setdefault(key[1], [])
            fp = review.fix_fingerprint(f['new'])
            if fp not in marks:
                marks.append(fp)


def _baseline(write):
    import json
    import os
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
                        'pipeline', 'text_rules_baseline.json')
    raw = open(path, encoding='utf-8').read()
    b = json.loads(raw)
    left = [k for k in b['known'] if k not in BASELINE_GONE]
    if len(left) == len(b['known']) or not write:
        return
    b['known'] = left
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(b, fh, ensure_ascii=False, indent=1)
        if raw.endswith('\n'):
            fh.write('\n')


def _gold(write):
    """Строки золотой выборки, которые вычитка сделала неверными: правятся тем же коммитом."""
    import json
    import os
    if not GOLD:
        return
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
                        'pipeline', 'gold', 'analytics_gold.json')
    raw = open(path, encoding='utf-8').read()
    g = json.loads(raw)
    rows = {r['id']: r for r in g['deals']}
    changed = False
    for cid, field, old, new in GOLD:
        if rows[cid].get(field) == new:
            continue
        assert rows[cid].get(field) == old, (cid, field, rows[cid].get(field))
        rows[cid][field] = new
        changed = True
    if changed and write:
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(g, fh, ensure_ascii=False, indent=1)
            if raw.endswith('\n'):
                fh.write('\n')


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
    _gold(False)
    print('Разовая часть: полей-фактов %d, снятых значений %d, заметок %d, профилей %d — проверки пройдены.'
          % (len(ONE_OFF), len(_RETRACT), len(_NOTES), len(_COMPANY)))
    if '--write' in sys.argv:
        fresh = json.load(open(path, encoding='utf-8'))      # перечитать прямо перед записью
        before = copy.deepcopy(fresh)
        _apply(fresh)
        mass_edit_guard.check(before, fresh, os.environ.get('MASS_OK'))
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(fresh, fh, ensure_ascii=False, indent=1)
        _baseline(True)
        _gold(True)
        print('Записано. Дальше: python3 pipeline/ingest/review.py --write')
    else:
        print('Сухой прогон. Запись — с ключом --write.')
