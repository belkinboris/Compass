# -*- coding: utf-8 -*-
"""Вычитка, марафон 12 ноября 2026, партия m045: правки, которые не ложатся в таблицу
FIXES review.py (сумма «Не раскрыта», дата со сменой года, очистка поля, тексты
профилей, ИНН профиля).

Что чиним и почему:
  g5405b876 «Агама» / Royal Greenland — в сумме стояла оценка инвестбанкира Ильи Шумова
    стоимости ВСЕЙ компании (капитал и резервы, ~300 млн ₽), а не цена 50%: сумма —
    «Не раскрыта», оценка остается в eco.val. Та же «цена» — в описаниях трех профилей.
  gc92ba4cb «Логистика и точка» / Havi — датой стоял день одобрения ФАС (26.12.2022);
    ООО «Рулог» перешло к АО «ЛИТ» по ЕГРЮЛ 4 мая 2023 года. В «Показателях компании»
    лежало описание HAVI без чисел (перенесено в контекст пересказом). Профиль покупателя —
    АО «ЛИТ», ИНН 4253053233 (ЕГРЮЛ ООО «Рулог» + «Коммерсантъ»: «АО «Логистика и точка»
    (АО «ЛИТ»)»).
  gca3a8810 «Герофарм» / АЗТ — 200–450 млн ₽ — оценка аналитика RNC Pharma, Vademecum:
    «Детали и стоимость сделки не раскрываются»; «Форма расчетов» описывала покупателя.
  gf9bd12d5 «Газпром-медиа» / Insight People — 5,5–7,5 млрд ₽ — оценка INFOLine
    (Sostav: «Сумма сделки не раскрывается»); дата — запись ЕГРЮЛ 15 ноября 2023 года.

    python3 pipeline/archive/2026-11/reread_m045.py            # сухой прогон
    python3 pipeline/archive/2026-11/reread_m045.py --write
Повторный запуск ничего не ломает: примененные правки пропускаются («уже применено»).
"""
import copy
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
REGISTRY_PY = os.path.join(ROOT, 'pipeline', 'fns_registry.py')
BY = 'вычитка m045, 12.11.2026'
U = '(уже применено)'

AGAMA_Q = ('По его мнению, стоимость «Агама Роял Гринланд», скорее всего, не превышает сумму капитала и '
           'резервов компании — около 300 млн руб. на конец 2022 года.')
K_AGAMA = 'https://www.kommersant.ru/doc/6444981'
AZT_Q = 'Детали и стоимость сделки не раскрываются.'
VAD = 'https://vademec.ru/news/2023/12/07/gerofarm-priobrel-49-doley-v-gruppe-azt/'
GPM_Q = 'Сумма сделки не раскрывается. Гендиректор агентства «INFOLine-Аналитика» Михаил Бурмистров оценил её в 5−7 млрд руб.'
SOS = 'https://www.sostav.ru/publication/gazprom-media-kupil-dolyu-v-insight-people-64409.html'
RULOG_Q = 'Соответствующая информация внесена в ЕГРЮЛ 4 мая.'
K_RULOG = 'https://www.kommersant.ru/doc/5968492'
INS_Q = 'Запись от 2023-11-15: вошел в участники — ООО "ГПМ ПРОЕКТЫ" (ИНН 7701736754), доля была None%, стала 51.0%.'
INS_URL = 'https://projectcompass.ru/api/companies/gca04c4fb/fns'

# (id карточки, поле, старое значение, новое, цитата, адрес) — поле с точкой: eco.*
CARD_EDITS = [
    ('g5405b876', 'sum', '≈300 млн ₽ (по оценке)', 'Не раскрыта', AGAMA_Q, K_AGAMA),
    ('g5405b876', 'eco.sum', '≈300 млн ₽ (по оценке)', 'Не раскрыта', AGAMA_Q, K_AGAMA),
    ('gc92ba4cb', 'date', '2022-12-26', '2023-05-04', RULOG_Q, K_RULOG),
    ('gc92ba4cb', 'date_basis', None, 'registry', RULOG_Q, K_RULOG),
    ('gc92ba4cb', 'eco.target_fin',
     "Партнер McDonald's по логистике, присутствовавший на российском рынке с 2003 г. Помимо перевозок и "
     "управления цепочками поставок, HAVI занимается упаковкой и переработкой отходов.", '—', None, None),
    ('gca3a8810', 'sum', '200–450 млн ₽ (по оценке)', 'Не раскрыта', AZT_Q, VAD),
    ('gca3a8810', 'eco.sum', '200–450 млн ₽ (по оценке)', 'Не раскрыта', AZT_Q, VAD),
    ('gca3a8810', 'eco.fin',
     'Покупатель — производитель инсулинов, генно-инженерных человеческих и аналоговых. Кроме них, «Герофарм» '
     'выпускает препараты для эндокринологии, психоневрологии, гинекологии и офтальмологии. Компанией руководит '
     'Петр Родионов, владеют ею он и его семья.', '—', None, None),
    ('gf9bd12d5', 'sum', '5,5–7,5 млрд ₽', 'Не раскрыта', GPM_Q, SOS),
    ('gf9bd12d5', 'eco.sum', '5,5–7,5 млрд ₽', 'Не раскрыта', GPM_Q, SOS),
    ('gf9bd12d5', 'date', '2023-11-16', '2023-11-15', INS_Q, INS_URL),
    ('gf9bd12d5', 'date_basis', None, 'registry', INS_Q, INS_URL),
]
# Снятые суммы — в retracted, чтобы обогащение не вернуло их с той же статьей.
RETRACT = [('g5405b876', 'sum', '≈300 млн ₽ (по оценке)'), ('gca3a8810', 'sum', '200–450 млн ₽ (по оценке)'),
           ('gf9bd12d5', 'sum', '5,5–7,5 млрд ₽')]

# (id профиля, поле, старое, новое)
PROFILE_EDITS = [
    ('gb98f4c3d', 'desc',
     'В 2023 году выкупила у Royal Greenland ее 50% долей в СП «Агама Роял Гринланд», доведя владение до 100%, за ≈300 млн ₽ (по оценке).',
     'Производитель рыбы и морепродуктов, бренды Agama и «Бухта изобилия». В 2023 году выкупила у Royal Greenland '
     'ее 50% в СП «Агама Роял Гринланд» и стала его единственным владельцем.'),
    ('ge6e44c7d', 'desc',
     'Датская рыбопромышленная компания; прекратила поставки в РФ после начала военных действий на Украине, в 2023 году продала свои 50% в ООО «Агама Роял Гринланд» ГК «Агама» за ≈300 млн ₽ (по оценке).',
     'Рыбопромышленная группа, принадлежит правительству Гренландии; 49 фабрик в Гренландии, Европе и Канаде. '
     'После начала военных действий на Украине остановила поставки в Россию, в 2023 году продала свои 50% '
     'в ООО «Агама Роял Гринланд» ГК «Агама».'),
    ('g04532c52', 'desc',
     'Совместное предприятие ГК «Агама» и Royal Greenland; в 2023 году «Агама» выкупила 50% датского партнера (прекратившего поставки в РФ после 2022 года) за ~300 млн ₽ (по оценке), доведя владение до 100%.',
     'Переработчик рыбы и морепродуктов в Подмосковье, бренды Agama и «Бухта изобилия»; бывшее СП ГК «Агама» '
     'и Royal Greenland. В 2023 году «Агама» выкупила 50% Royal Greenland и стала единственным владельцем.'),
    ('ge7bf8dc5', 'legal_short', None, 'АО «ЛИТ»'),
    # Правовая форма сторон по ЕГРЮЛ (сайт /api/companies/<id>/fns): party_legal_names.py
    # из контейнера ходит в сеть нестабильно — ставим здесь то же, что он предлагает.
    ('gca04c4fb', 'legal_short', None, 'ООО «Инсайт Люди»'),
    ('g41e65d78', 'legal_short', None, 'АО «Газпром-медиа Холдинг»'),
    ('gb98f4c3d', 'legal_short', None, 'ООО «ГК Агама»'),
    ('g84204bcd', 'legal_short', None, 'ООО «Герофарм»'),
]

REGISTRY_ENTRY = {
    "company_id": 'ge7bf8dc5', "decision": "confirmed", "inn": '4253053233',
    "reason": 'Покупатель сделки gc92ba4cb (вычитка m045, 12.11.2026). «Логистика и точка» — АО «ЛИТ», ИНН 4253053233: (1) ЕГРЮЛ ООО «Рулог» (ИНН 7732121398) на нашем сайте — 04.05.2023 вошел участник АО "ЛИТ", ИНН 4253053233, 100%, вместо Havi Global Logistics GmbH; (2) «Коммерсантъ» 05.05.2023 (kommersant.ru/doc/5968492): «АО «Логистика и точка» (АО «ЛИТ») стало единственным владельцем компании ООО «Рулог»», принадлежит Александру Говору. Код региона 42 (Кемеровская обл.) сходится с кузбасским происхождением Говора. Прежнее решение (no_match, 23.10.2026) перебирало три ООО «Логистика и точка», а покупатель — АО.',
    "date": '2026-11-12'}


def get(card, field):
    if '.' in field:
        a, b = field.split('.', 1)
        return (card.get(a) or {}).get(b)
    return card.get(field)


def put(card, field, value):
    if '.' in field:
        a, b = field.split('.', 1)
        card.setdefault(a, {})[b] = value
    else:
        card[field] = value


MY_IDS = ('g5405b876', 'gdc4ff4ab', 'g8e7eee71', 'gc92ba4cb', 'gca3a8810', 'gf9bd12d5', 'gaa0f4fb7', 'geda130b6',
          'g9016d7ac', 'g1e2b16c3', 'g19186bb9', 'g3db7d882')


def drop_fixed_baseline(data):
    """Исправленное старое нарушение правил текста уходит из text_rules_baseline.json
    (test_card_text_follows_the_house_rules требует: исправил — убери из списка).
    Трогаем только отпечатки карточек этой партии."""
    import text_rules
    path = text_rules.BASELINE
    base = json.load(open(path, encoding='utf-8'))
    now = {fp for fp, did, *_ in text_rules.all_findings({'deals': [d for d in data['deals'] if d['id'] in MY_IDS]})}
    keep = [fp for fp in base['known'] if not (fp.split('|')[0] in MY_IDS and fp not in now)]
    if len(keep) != len(base['known']):
        print('  снято из списка старых нарушений: %d' % (len(base['known']) - len(keep)))
        base['known'] = keep
        json.dump(base, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))          # перечитываем прямо перед записью
    old = copy.deepcopy(data)
    deals = {d['id']: d for d in data['deals']}
    comps = data['companies']
    changed = 0
    for cid, field, was, new, quote, url in CARD_EDITS:
        card = deals[cid]
        cur = get(card, field)
        if cur == new:
            print('  %s %s %s' % (cid, field, U))
            continue
        assert cur == was, '%s %s: ожидали %r, стоит %r' % (cid, field, was, cur)
        put(card, field, new)
        if quote and field in fact_edit_guard.FACT_FIELDS:
            fact_edit_guard.log(card, field, new, quote, url, BY)
        print('  ПРАВИМ %s %s: %r -> %r' % (cid, field, str(was)[:50], new))
        changed += 1
    for cid, field, value in RETRACT:
        r = deals[cid].setdefault('retracted', {}).setdefault(field, [])
        if value not in r:
            r.append(value)
            changed += 1
    for pid, field, was, new in PROFILE_EDITS:
        cur = comps[pid].get(field)
        if cur == new:
            print('  профиль %s %s %s' % (pid, field, U))
            continue
        assert cur == was, 'профиль %s %s: ожидали %r, стоит %r' % (pid, field, was, cur)
        comps[pid][field] = new
        print('  ПРАВИМ профиль %s %s' % (pid, field))
        changed += 1
    import fns_registry
    need_reg = (fns_registry.by_company_id().get('ge7bf8dc5') or {}).get('inn') != '4253053233'
    print('  реестр ИНН: %s' % ('добавить АО «ЛИТ»' if need_reg else U))
    if not write:
        print('Сухой прогон: правок %d. Запись — --write.' % changed)
        return 0
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK') or None)
    if changed:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    if need_reg:
        import fns_notes_to_registry
        assert fns_notes_to_registry.edit_registry_entry('ge7bf8dc5', REGISTRY_ENTRY)
    drop_fixed_baseline(data)
    print('Записано правок: %d' % changed)
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
