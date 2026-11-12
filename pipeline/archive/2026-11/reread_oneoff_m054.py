# -*- coding: utf-8 -*-
"""Вычитка 12 ноября 2026 (марафон, партия m054): правки, которые не ложатся в FIXES.

Что чинит: суммы-оценки с границей («до N млн ₽ (по оценке)» — review.py такой формат
не разбирает), пустое поле вместо фактов не по адресу, покупатель по реестру (новый профиль
формального покупателя) и описания профилей сторон, где стояли неподтвержденные факты
(цена-оценка как цена, число точек и состав группы, которых нет в источниках). Каждая правка
факта — с цитатой источника через fact_edit_guard.log.

    python3 pipeline/archive/2026-11/reread_oneoff_m054.py            # сухой прогон
    python3 pipeline/archive/2026-11/reread_oneoff_m054.py --write

База перечитывается прямо перед записью; на каждое поле — assert на старое значение;
повторный запуск ничего не меняет («уже применено»).
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
REG = os.path.join(ROOT, 'pipeline', 'fns_registry.json')
BY = 'вычитка m054, 12 ноября 2026'

Q_KARAV = 'Гендиректор компании «INFOLine-Аналитика» Михаил Бурмистров оценил сделку не более чем в 100 млн руб.'
U_KARAV = 'https://incrussia.ru/news/neftmagistral-bratya-karavaevy/'
Q_SVET = ('2023-03-14: было — нет; стало — АКЦИОНЕРНОЕ ОБЩЕСТВО "ВЕСТЕЛКОМ" (ОГРН: 1027739488105) '
          '99.99%; (299 970 руб.)')
U_SVET = 'https://datanewton.ru/api/v2/history?ogrn=1025007115253&startDate=2000-01-01&attributes=OWNERS'

# (id карточки, поле, было, стало, цитата, адрес)
DEALS = [
    # g595aca8d: 100 млн — верхняя граница оценки аналитика, стороны цену не называли.
    ('g595aca8d', 'sum', '100 млн ₽', 'До 100 млн ₽ (по оценке)', Q_KARAV, U_KARAV),
    ('g595aca8d', 'eco.sum', '100 млн ₽', 'До 100 млн ₽ (по оценке)', Q_KARAV, U_KARAV),
    # gbdec3442: в «Оценке» стояли аудитория и состав раунда — это не оценка; оба факта
    # перенесены в «Контекст» и «Структуру» (write_card), поле — пустое.
    ('gbdec3442', 'eco.val',
     'Аудитория сервисов «Здоровье.ру» — около 600 тыс. человек. Кроме ведущего инвестора Kama Flow, '
     'в раунде участвовали инвесторы венчурного клуба «Синдикат».', '—', '', ''),
    # gfc7d8f5f: по ЕГРЮЛ 99,99% ООО «Фирма «Светец»» получило АО «Вестелком» («дочка» «Ростелекома»
    # по «Коммерсанту»), 0,01% — АО «АМТ». Формальный покупатель не подменяется профилем группы
    # (docs/card_parties.md: «Покупатель — ровно в раскрытой части и формально», «Покупатель и
    # продавец в схеме — те, кто в реестре»). «Ростелеком» остается в заголовке и прозе.
    ('gfc7d8f5f', 'buyer', 'g00f14033', 'gvestelkom', Q_SVET, U_SVET),
]

# (id профиля, поле, было, стало)
PROFILES = [
    # Покупатель g595aca8d: в описании стояли «42 заведения» (в источниках — «больше 40») и
    # «за 100 млн ₽» (это оценка аналитика, а не цена). Retail.ru, Inc. Russia.
    ('g66f786bb', 'desc',
     'В 2023 году купил сеть кафе «Кулинарная лавка братьев Караваевых» (42 заведения в Москве, '
     'ООО «Селена») за 100 млн ₽.',
     'Топливная компания: сеть АЗС «Нефтьмагистраль» в Москве и Подмосковье. Юрлицо — ООО «ТД НМ»; '
     'в равных долях принадлежит Александру и Наталии Ерастовым. В 2023 году купила сеть кафе '
     '«Кулинарная лавка братьев Караваевых».'),
    ('gcc7851ad', 'desc',
     'Управляет сетью кафе «Кулинарная лавка братьев Караваевых» (42 заведения в Москве); в 2023 году '
     'ее 100% купил торговый дом «Нефтьмагистраль».',
     'Юрлицо, на которое зарегистрирован домен московской сети кафе «Кулинарная лавка братьев '
     'Караваевых» (основана в 2008 году). С марта 2023 года принадлежит торговому дому «Нефтьмагистраль».'),
    # Предмет gfc7d8f5f: «группа включает «Новион» и «Светец Интегро»» — ни в одном источнике нет.
    ('gdd692aa7', 'desc',
     'Разработчик ПО для телекоммуникационных сетей (группа включает «Новион» и «Светец Интегро»); '
     'в 2023 году ее 100% купил «Ростелеком».',
     'Разработчик и интегратор программного обеспечения для телекоммуникационных и информационных '
     'сетей, работает с 1991 года. С 2023 года принадлежит «дочкам» «Ростелекома» — АО «Вестелком» '
     'и АО «АМТ».'),
    # Покупатель g595aca8d: правовая форма по реестру (ООО «ТД НМ», ИНН 7722582752 — fns_registry.json);
    # party_legal_names.py в репетиции ее не поставил (реестр сайта не ответил).
    ('g66f786bb', 'legal_short', None, 'ООО «ТД НМ»'),
    # Покупатель g739d9094: ООО «Центр искусственного интеллекта МВС» (ООО «МВС ИИ», ИНН 9725021438).
    ('g28add31b', 'legal_short', None, 'ООО «МВС ИИ»'),
    # Предмет g739d9094: «Инфомат» не «владеет разработчиком» — это сам разработчик под брендом
    # «Инфоматика» (Интерфакс); с декабря 2024 года у МТС ИИ 55% (ЕГРЮЛ).
    ('g82b438e2', 'desc',
     'Владеет разработчиком умных турникетов и билетных систем «Инфоматика»; в 2023 году 49% купила '
     'МТС AI, основатель Давид Тартаковский сохранил 51%.',
     'Казанский разработчик билетно-пропускных систем, турникетов и оборудования для платежных '
     'терминалов, бренд «Инфоматика». С декабря 2024 года 55% принадлежит МТС AI.'),
]

# Новые профили (id → профиль) и строки реестра ФНС к ним (ИНН — по истории участников ЕГРЮЛ).
NEW = {
    'gvestelkom': {'name': 'Вестелком', 'legal_short': 'АО «Вестелком»', 'ind': 'Телеком',
                   'desc': 'Дочерняя компания «Ростелекома»; в 2023 году получила 99,99% ООО «Фирма «Светец»».',
                   'kpi': ['Профиль', 'Автоматический']},
}
NEW_REG = [
    {'company_id': 'gvestelkom', 'decision': 'confirmed', 'inn': '7703081503', 'date': '2026-11-12',
     'reason': 'АО «Вестелком», ИНН 7703081503, ОГРН 1027739488105 — участник ООО «Фирма «Светец»» с 99,99% '
               'с 14.03.2023 (история участников ЕГРЮЛ, datanewton.ru); «дочка» «Ростелекома» по '
               '«Коммерсанту» (kommersant.ru/doc/5875450).'},
]


def _get(card, field):
    if '.' in field:
        a, b = field.split('.', 1)
        return (card.get(a) or {}).get(b)
    return card.get(field)


def _set(card, field, value):
    if '.' in field:
        a, b = field.split('.', 1)
        card.setdefault(a, {})[b] = value
    else:
        card[field] = value


def apply_reg(rows):
    have = {r.get('company_id') for r in rows}
    n = 0
    for row in NEW_REG:
        if row['company_id'] not in have:
            rows.append(dict(row))
            n += 1
    return n


def apply(data):
    by = {d['id']: d for d in data['deals']}
    comps = data['companies']
    done = 0
    for pid, prof in NEW.items():
        if pid in comps:
            print('уже применено: профиль %s' % pid)
            continue
        comps[pid] = dict(prof)
        done += 1
        print('новый профиль %s %s' % (pid, prof['name']))
    for cid, field, old, new, quote, url in DEALS:
        card = by[cid]
        cur = _get(card, field)
        if cur == new:
            print('уже применено: %s %s' % (cid, field))
            continue
        assert cur == old, (cid, field, cur)
        _set(card, field, new)
        if field in fact_edit_guard.FACT_FIELDS:
            fact_edit_guard.log(card, field, new, quote, url, BY)
        done += 1
        print('%s %s: %r → %r' % (cid, field, str(old)[:50], new))
    for pid, field, old, new in PROFILES:
        cur = comps[pid].get(field)
        if field == 'legal_short' and cur:
            print('уже есть legal_short: профиль %s — %s' % (pid, cur))
            continue
        if cur == new:
            print('уже применено: профиль %s %s' % (pid, field))
            continue
        assert cur == old, (pid, field, cur)
        comps[pid][field] = new
        done += 1
        print('профиль %s %s: %r → %r' % (pid, field, (old or '')[:50], new[:50]))
    return done


def main(argv):
    n = apply(json.load(open(BASE, encoding='utf-8')))
    n += apply_reg(json.load(open(REG, encoding='utf-8')))
    if '--write' not in argv:
        print('Сухой прогон: правок %d. Запись — --write.' % n)
        return 0
    data = json.load(open(BASE, encoding='utf-8'))
    apply(data)
    with open(BASE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    rows = json.load(open(REG, encoding='utf-8'))
    if apply_reg(rows):
        with open(REG, 'w', encoding='utf-8') as f:
            json.dump(rows, f, ensure_ascii=False, indent=1)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
