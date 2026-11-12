# -*- coding: utf-8 -*-
"""Вычитка базы, марафон 12 ноября 2026, партия m028 (вторая часть: «Алгоритмика», LeClick, «Миллеровский элеватор», завод EcoPartners): правки, которые не ложатся в таблицу FIXES.

ЧТО ЧИНИТ. Поля-факты, подтвержденные реестром (дата перехода доли, продавец по истории
участников ЕГРЮЛ), снятие неподтвержденных значений (оценки без автора и источника),
доля, заголовок по стандарту (`pipeline/title_standard.py`) и тексты профилей. Каждая
правка факта несет цитату источника (`fact_edit_guard.log`), перед записью стоит `assert`
на старое значение; повторный запуск пропускает уже примененное.

ПОЧЕМУ НЕ review.py. Дата из реестра не названа в статье прописью (review.py такую дату не
принимает), заглушки и снятие значений таблица не переносит, профили она не правит.

    python3 pipeline/archive/2026-11/reread_m028_b.py            # сухой прогон
    python3 pipeline/archive/2026-11/reread_m028_b.py --write    # запись (делает reread_apply.py)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
DAY, BY = '2026-11-12', 'reread_m028_b'
FACT = set(fact_edit_guard.FACT_FIELDS)

# Правки карточек: id, поле (через точку: eco.val), старое, новое, цитата, адрес.
EDITS = []
# Правки профилей: id профиля, ключ, старое, новое.
COMPANY = []
# Снятые значения — в retracted, чтобы обогащение их не вернуло: id, поле, значение.
RETRACT = []
# Ключи сопоставления профилей (match_keys): id профиля, ключ.
MATCH = []

# --- данные партии (вторая часть) ---
RB_ALG = 'https://rb.ru/news/algoritmika-lobanov/'
CN_ALG = 'https://www.cnews.ru/news/top/2024-10-22_sberbank_kupil_onlajn-shkolu'
REG_ALG = 'https://datanewton.ru/api/v2/history?ogrn=5167746505273&startDate=2024-01-01&attributes=OWNERS'
Q_KF_ALG = 'По данным «Контур.Фокус», 100% ООО «Алгоритмики» получило «Управление и Развитие» в октябре.'
Q_REG_ALG = ('ЕГРЮЛ, участники ООО «Алгоритмика» (ОГРН 5167746505273), запись от 2024-10-02: вышли ЛОБАНОВ АНДРЕЙ СЕРГЕЕВИЧ '
             '23,9976% и АО "ЦИФРОВОЕ ОБРАЗОВАНИЕ" 61,7094%; новый участник — «доступ к сведениям ограничен».')
EDITS += [
 # gfecb608d «Алгоритмика»: Сбербанк в покупателях — версия источников Forbes, продавец назвал «частного инвестора»;
 # по «Контур.Фокусу» 100% получило ООО «Управление и Развитие» (владельцы скрыты). Дата 1 сентября — выдуманная.
 dict(id='gfecb608d', field='title', old='Сбер купил онлайн-школу программирования «Алгоритмика»',
      new='«Управление и Развитие» купило «Алгоритмику»', quote=Q_KF_ALG, url=RB_ALG),
 dict(id='gfecb608d', field='buyer', old='g28ff15bb', new=None, quote=Q_KF_ALG, url=RB_ALG),
 dict(id='gfecb608d', field='buyer_name', old=None, new='ООО «Управление и Развитие»', quote=Q_KF_ALG, url=RB_ALG),
 dict(id='gfecb608d', field='seller', old=None, new='Андрей Лобанов и АО «Цифровое образование»', quote=Q_REG_ALG, url=REG_ALG),
 dict(id='gfecb608d', field='date', old='2024-09-01', new='2024-10-02', quote=Q_REG_ALG, url=REG_ALG),
 dict(id='gfecb608d', field='date_basis', old=None, new='registry', quote='', url=''),
 dict(id='gfecb608d', field='sum', old='≈1 млрд ₽ (по оценке)', new='1–1,5 млрд ₽ (по оценке)',
      quote='Собеседники издания оценили сделку в от 1 до 1,5 млрд руб.', url=CN_ALG),
 dict(id='gfecb608d', field='eco.sum', old='≈1 млрд ₽ (по оценке)', new='1–1,5 млрд ₽ (по оценке)',
      quote='Собеседники издания оценили сделку в от 1 до 1,5 млрд руб.', url=CN_ALG),
 dict(id='gfecb608d', field='eco.share', old='—', new='100% доли в ООО «Алгоритмика»', quote=Q_KF_ALG, url=RB_ALG),
 dict(id='gfecb608d', field='ind', old='ИТ и интернет', new='Образование', quote='', url=''),
]
COMPANY += [
 ('g19cfffaf', 'legal_short', None, 'ООО «Алгоритмика»'),
 ('g19cfffaf', 'ind', 'ИТ и интернет', 'Образование'),
 ('g19cfffaf', 'desc', 'Сеть школ программирования для детей.',
  'Онлайн-школа программирования и математики для детей и подростков, основана Андреем Лобановым в 2016 году; российская часть бизнеса (ООО «Алгоритмика») продана в 2024 году.'),
]


HB_LC = 'https://habr.com/ru/news/848184/'
API_LC = 'https://projectcompass.ru/api/companies/g43e8e08b/fns'
Q_REG_LC = ('ЕГРЮЛ по данным API-ФНС, АО «ЛЕКЛИК» (ИНН 7703475522): запись от 2024-10-28 — единственный акционер '
            'ООО "ЯНДЕКС.ЕДА" (ИНН 9705114405).')
Q_SELL_LC = ('Основной акционер, основатель и генеральный директор LeClick Анастасия Люстина подтвердила эту информацию. … '
             'Вопрос, кто ещё выступил продавцом, как и то, какова сумма сделки, стороны не раскрывают.')
EDITS += [
 # ge7072ad5 «Яндекс» / LeClick: 1 сентября — выдуманный день (новость вышла 3–4 октября, закрытие — после нее)
 dict(id='ge7072ad5', field='date', old='2024-09-01', new='2024-10-28', quote=Q_REG_LC, url=API_LC),
 dict(id='ge7072ad5', field='date_basis', old=None, new='registry', quote='', url=''),
 dict(id='ge7072ad5', field='seller', old=None, new='Анастасия Люстина', quote=Q_SELL_LC, url=HB_LC),
 dict(id='ge7072ad5', field='eco.share', old='—', new='100% акций АО «Леклик»',
      quote='«Яндекс» купил 100% долей в сервисе LeClick и специализированное ПО для хостес SmartReserve, рассказали в компании.', url=HB_LC),
]
COMPANY += [
 ('g43e8e08b', 'name', 'АО «ЛЕКЛИК»', 'LeClick'),
 ('g43e8e08b', 'legal_short', None, 'АО «Леклик»'),
 ('g43e8e08b', 'desc', 'Сервис бронирования ресторанов LeClick и ПО SmartReserve, работает в 25 городах с 2500 договорами; в 2024 году его 100% купил Яндекс для запуска онлайн-бронирования в Яндекс Еде.',
  'Сервис бронирования столиков в ресторанах и программа для хостес SmartReserve; основан Анастасией Люстиной в 2012 году. Работал в 25 городах России. С осени 2024 года принадлежит «Яндексу» (ООО «Яндекс.Еда»).'),
]
MATCH += [('g43e8e08b', 'leclick'), ('g43e8e08b', 'леклик')]


OL_ME = 'https://oleoscope.com/news/rostovskaya-zernovaya-kompaniya-vykupit-akcii/'
RBC_ME = 'https://rostov.rbc.ru/rostov/freenews/66eda9a29a794770794a7159'
Q_ME = 'РЗК «Ресурс» стал основным собственником элеватора в сентябре этого года, выкупив 90,09% акций у агропромышленного холдинга «Грейнрус».'
EDITS += [
 # g5f4bbb4f «Миллеровский элеватор»: продавец — «Грейнрус» (через ООО «Грейнрус Трейд»), 1 сентября — выдуманный день
 dict(id='g5f4bbb4f', field='title', old='ГАП «Ресурс» приобрела 90% акций ПАО «Миллеровский элеватор»',
      new='ГАП «Ресурс» купила 90,09% «Миллеровского элеватора» у «Грейнруса»', quote=Q_ME, url=OL_ME),
 dict(id='g5f4bbb4f', field='seller', old=None, new='ООО «Грейнрус Трейд»',
      quote='С 2021 года элеватор принадлежал Агропромышленному холдингу «Грейнрус» через ООО «Грейнрус Трейд». … ' + Q_ME, url=RBC_ME),
 dict(id='g5f4bbb4f', field='date', old='2024-09-01', new='2024',
      quote='РЗК «Ресурс» стал основным собственником элеватора в сентябре этого года — день в источниках не назван (Oleoscope, РБК Ростов 20.09.2024).', url=OL_ME),
 dict(id='g5f4bbb4f', field='eco.share', old='—', new='90,09% акций ПАО «Миллеровский элеватор»', quote=Q_ME, url=OL_ME),
]
COMPANY += [
 ('g6e222d1f', 'name', 'ПАО «Миллеровский элеватор»', 'Миллеровский элеватор'),
 ('g6e222d1f', 'legal_short', None, 'ПАО «Миллеровский элеватор»'),
 ('g6e222d1f', 'desc', 'Элеватор в Ростовской области мощностью хранения до 150 тыс. тонн зерновых и масличных культур; в 2024 году свыше 90% акций купила ГАП «Ресурс».',
  'Элеватор в Миллерово (Ростовская область): в 2023 году принял 79,5 тыс. т сельхозпродукции. С 2021 года принадлежал агрохолдингу «Грейнрус», в сентябре 2024 года 90,09% акций купила РЗК «Ресурс» (ГАП «Ресурс»).'),
]



K_TN = 'https://www.kommersant.ru/doc/7180836'
Q_TN = ('Объем инвестиций в проект составил 1,45 млрд руб., а сумма сделки может быть не менее 1,5–1,6 млрд руб., оценивает '
        'гендиректор «Infoline-Аналитики» Михаил Бурм… Корпорация «Технониколь» приобрела промышленный комплекс группы '
        'EcoPartners, который был запущен в Твери год назад. Сумма сделки не раскрывается.')
EDITS += [
 # g97a4c417 «Технониколь» / завод EcoPartners: 1,5–1,6 млрд ₽ — оценка аналитика, стороны цену не раскрыли;
 # 1 сентября — выдуманный день (статья Ъ 24.09.2024, дня сделки нет)
 dict(id='g97a4c417', field='title', old='Технониколь приобрела завод по переработке пластика в Твери',
      new='«Технониколь» купила у EcoPartners завод по переработке пластика в Твери',
      quote='«Технониколь» Сергея Колесникова и Игоря Рыбакова приобрела промышленный комплекс по переработке отходов ПЭТ (полиэтилентерефталат) и ПНД-упаковки (полиэтилен низкого давления) в Твери у ГК EcoPartners, рассказали “Ъ” стороны сделки.', url=K_TN),
 dict(id='g97a4c417', field='sum', old='1,5–1,6 млрд ₽ (по оценке)', new='Не раскрыта', quote=Q_TN, url=K_TN),
 dict(id='g97a4c417', field='eco.sum', old='1,5–1,6 млрд ₽ (по оценке)', new='Не раскрыта', quote=Q_TN, url=K_TN),
 dict(id='g97a4c417', field='date', old='2024-09-01', new='2024',
      quote='Коммерсантъ, 24.09.2024: «Технониколь» приобрела завод по переработке пластика в Твери — день сделки в статье не назван.', url=K_TN),
]
COMPANY += [
 ('g321e8b05', 'name', 'завод по переработке ПЭТ/ПНД в Твери', 'Завод по переработке ПЭТ и ПНД в Твери'),
 ('g321e8b05', 'desc', 'Завод переработки ПЭТ и ПНД-упаковки (хлопья, регранулят, ПЭТ-лента); в 2024 году его купила «Технониколь» за 1,5–1,6 млрд ₽ (по оценке).',
  'Завод в Твери, перерабатывающий отходы ПЭТ- и ПНД-упаковки: хлопья, регранулят, упаковочная ПЭТ-лента. Построен ГК EcoPartners, запущен в сентябре 2023 года; в 2024 году куплен «Технониколь».'),
]
MATCH += [('g321e8b05', 'завод по переработке пэт и пнд в твери')]
RETRACT += [('g97a4c417', 'sum', '1,5–1,6 млрд ₽ (по оценке)')]




def get(card, field):
    if '.' in field:
        head, tail = field.split('.', 1)
        return (card.get(head) or {}).get(tail)
    return card.get(field)


def put(card, field, value):
    if '.' in field:
        head, tail = field.split('.', 1)
        card.setdefault(head, {})[tail] = value
    elif value is None:
        card.pop(field, None)
    else:
        card[field] = value


def apply(data, verbose=False):
    by = {d['id']: d for d in data['deals']}
    done = skipped = 0
    for e in EDITS:
        card = by[e['id']]
        cur = get(card, e['field'])
        if cur == e['new']:
            skipped += 1
            continue
        assert cur == e['old'], '%s %s: в базе %r, ожидали %r' % (e['id'], e['field'], cur, e['old'])
        put(card, e['field'], e['new'])
        if e['field'] in FACT:
            fact_edit_guard.log(card, e['field'], e['new'], e['quote'], e['url'], BY, DAY)
        done += 1
        if verbose:
            print('%s %s: %r → %r' % (e['id'], e['field'], str(cur)[:80], str(e['new'])[:80]))
    for cid, key, old, new in COMPANY:
        comp = data['companies'].setdefault(cid, {}) if old is None else data['companies'][cid]
        if comp.get(key) == new:
            skipped += 1
            continue
        assert comp.get(key) == old, '%s.%s: %r' % (cid, key, comp.get(key))
        if new is None:
            comp.pop(key, None)
        else:
            comp[key] = new
        done += 1
        if verbose:
            print('профиль %s.%s: %r → %r' % (cid, key, str(old)[:80], str(new)[:80]))
    for cid, key in MATCH:
        keys = data.setdefault('match_keys', {}).setdefault(cid, [])
        if key not in keys:
            keys.append(key)
            done += 1
    for did, field, value in RETRACT:
        lst = by[did].setdefault('retracted', {}).setdefault(field, [])
        if value not in lst:
            lst.append(value)
    return done, skipped


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    old, data = json.loads(raw), json.loads(raw)
    done, skipped = apply(data, verbose=True)
    print('правок: %d, уже применено: %d' % (done, skipped))
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    if not done:
        print('Все уже применено.')
        rebaseline(json.loads(raw))
        return 0
    fresh_raw = open(DATA, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    apply(fresh)
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
    print('ЗАПИСАНО.')
    rebaseline(fresh)
    return 0


def rebaseline(data):
    """Исправленные вычиткой старые нарушения правил текста уходят из text_rules_baseline.json
    (test_card_text_follows_the_house_rules требует убрать «исправленные»). Только для карточек
    партии и только сокращение списка."""
    import text_rules
    ids = {e['id'] for e in EDITS}
    known = json.load(open(text_rules.BASELINE, encoding='utf-8'))
    now = {f[0] for f in text_rules.all_findings({'deals': [d for d in data['deals'] if d['id'] in ids]})}
    left = [fp for fp in known['known'] if fp.split('|')[0] not in ids or fp in now]
    if len(left) != len(known['known']):
        print('из списка старых нарушений убрано: %d' % (len(known['known']) - len(left)))
        known['known'] = left
        with open(text_rules.BASELINE, 'w', encoding='utf-8') as fh:
            json.dump(known, fh, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
