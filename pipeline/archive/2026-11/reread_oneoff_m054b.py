# -*- coding: utf-8 -*-
"""Вычитка 12 ноября 2026 (марафон, партия m054, вторая часть): правки, которые не ложатся в FIXES.

Что чинит: суммы-оценки с границей («до N млн ₽ (по оценке)» — review.py такой формат
не разбирает), пустое поле вместо фактов не по адресу, покупатель по реестру (новый профиль
формального покупателя) и описания профилей сторон, где стояли неподтвержденные факты
(цена-оценка как цена, число точек и состав группы, которых нет в источниках). Каждая правка
факта — с цитатой источника через fact_edit_guard.log.

    python3 pipeline/archive/2026-11/reread_oneoff_m054b.py            # сухой прогон
    python3 pipeline/archive/2026-11/reread_oneoff_m054b.py --write

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

Q_DEERE = 'В «Инсайте» отказались раскрыть параметры сделки.'
U_DEERE = 'https://www.kommersant.ru/doc/5863484'

# (id карточки, поле, было, стало, цитата, адрес)
DEALS = [
    # g585f0c61: 11 млрд ₽ — объем облигаций «Инсайта», размещенных 28 февраля, а не цена
    # (Frank Media, «Коммерсантъ»); покупатель параметры сделки не раскрыл.
    ('g585f0c61', 'sum', '11 млрд ₽', 'Не раскрыта', Q_DEERE, U_DEERE),
    ('g585f0c61', 'eco.sum', '11 млрд ₽', 'Не раскрыта', Q_DEERE, U_DEERE),
    # g5607637d: 25 августа 2023 — день публикации «Коммерсанта» (02:02) о уже закрытой сделке, а не
    # день события; у АО реестр акционеров не открыт, точного дня нет ни в одном источнике —
    # остается год (docs/card_status_dates.md, «Нет дня — только год»).
    ('g5607637d', 'date', '2023-08-25', '2023',
     'Структура инвестфонда «Сигнет Инвестиции» закрыла сделку по покупке крупного в Забайкалье '
     'агрохолдинга «Комсомолец», управляющего почти 190 тыс. га.', 'https://www.kommersant.ru/doc/6174781'),
    # g2d075f03: «1 марта» — выдуманный день (первое число месяца); о продаже пакета впервые
    # сообщили РБК и Frank Media 15 марта 2023 года.
    ('g2d075f03', 'date', '2023-03-01', '2023-03-15',
     '15.03.2023, 08:04 Рынки Поделиться Инвестфонд Russia Partners выставил на продажу свою долю в «Банки.ру»',
     'https://frankmedia.ru/116199'),
    # День — первое сообщение о выставлении пакета (РБК и Frank Media, 15 марта 2023 года).
    ('g2d075f03', 'date_basis', None, 'announcement', '', ''),
]

# (id профиля, поле, было, стало)
PROFILES = [
    ('g96702273', 'desc',
     'Лизинговая компания John Deere Financial; в 2023 году ее купила инвестиционная группа «Инсайт» '
     'Авета Миракяна, сумму сделки не раскрыли (фигурирующие «~11 млрд ₽» — отдельный облигационный '
     'выпуск «Инсайта», размещенный накануне покупки, а не цена актива).',
     'Бывшая кэптивная лизинговая компания John Deere в России. С марта 2023 года принадлежит группе '
     '«Инсайт», с апреля работает под брендом Fleet Finance.'),
    # Лизинг — финансовая услуга, не перевозки (отрасль карточки исправлена тем же прогоном).
    ('g96702273', 'ind', 'Транспорт и логистика', 'Финансовые услуги'),
    # Покупатель g5607637d: «в 2023 году продан фонду Глеба Фетисова» — неверно: ООО «АПК» само
    # покупатель, а связь с Фетисовым Павел Полухин опроверг («Коммерсантъ»).
    ('ge9ceb16e', 'desc',
     'Владелец АО «Племенной Завод «Комсомолец»» (188 тыс. га сельхозземель в Забайкалье); в 2023 году '
     'продан фонду Глеба Фетисова.',
     'Холдинговая компания ГК «Иррико», которой владеет ЗПИФ «Сигнет — инвестиции 1» под управлением '
     '«Сигнет Капитала». В 2023 году купила АО «Племенной завод «Комсомолец»».'),
    ('gc4b5b9a8', 'legal_short', None, 'АО «Племенной завод «Комсомолец»»'),
    # Предмет g2d075f03: юрлицо — ООО «Информационное агентство «Банки.ру»» (vc.ru, «Контур.Фокус»).
    ('gdaa028e0', 'legal_short', None, 'ООО «Информационное агентство «Банки.ру»»'),
]

NEW = {}
NEW_REG = []


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
