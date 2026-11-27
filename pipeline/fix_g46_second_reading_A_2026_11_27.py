# -*- coding: utf-8 -*-
"""Второе чтение трех новых карточек очереди (27 ноября 2026,
data/inbox/second_reading/2026-11-27-intake-g46-A.json): то, что не проходит
через таблицу правок и вычитку.

ЧТО ЧИНИТ.
1. g89b4c747 (ТЦ «Тройка»), pending.json: `date` «2026-04-01» -> «2026», `date_basis`
   снят. 1 апреля 2026 года — день публикации «Коммерсанта» («01.04.2026, 20:30»,
   «Об этом “Ъ” сообщили стороны сделки»); дня сделки нет ни там, ни в New Retail
   (2 апреля), а к вечеру 1 апреля часть помещений уже была переоформлена по ЕГРН —
   сделка могла пройти и в марте. docs/card_status_dates.md: «Нет дня — только год»,
   «Дата публикации не уточняет дату сделки». `review.py` дату годом не принимает
   (`date_is_supported` требует ГГГГ-ММ-ДД) и `date_basis` снять не умеет — поэтому
   разовый скрипт, как pipeline/fix_g13f5c85b_date_to_year_2026_11_24.py.
2. Профили сторон этих карточек, deals_promoted.json (`companies`):
   - ged60437e «Концерн «Энерготехнологии»»: описание называло концерн «сетью» —
     в «Коммерсанте» он «занимается развитием магазинов мебели и интерьера
     «Кубатура» в Санкт-Петербурге», издание зовет его ритейлером; первое
     предложение описания идет в строку «Покупатель» поста. У `legal_short` и в
     описании не хватало закрывающей елочки.
   - g5502d591 «Место встречи» -> «ООО «Место встречи»»: без формы имя читается как
     название сети торговых центров, а покупатель — общество (РИА, ЕГРЮЛ). Описание
     называло его владельцем торговых центров, но владельцем оно стало как раз в
     этой сделке; теперь — кто и когда создал общество («Коммерсантъ», 02.11.2023;
     РИА, 11.01.2024) и что с ним было дальше (ЕГРЮЛ), все с датами.
   - g58572d8a «ВТБ Индустриальная недвижимость» -> «ООО «ВТБ Индустриальная
     недвижимость»» (так в поле seller и в ЕГРЮЛ).
   - g8014ae3f «Фирма Сатурн» -> «ФХ «Фирма Сатурн»» («Ведомости»: «Фермерское
     хозяйство (ФХ) «Фирма Сатурн»»; ЕГРЮЛ: ООО «Фермерское хозяйство «Фирма
     Сатурн»»); у `legal_short` и в описании не хватало закрывающей елочки.
   - gba784476 ООО «Пятигорский молочный комбинат»: «перерабатывает около 350 т
     молока в сутки» — в «Ведомостях» это мощность («мощности позволяют
     перерабатывать»), а не фактический объем.
   Имена правятся на месте: id, привязки и match_keys те же (docs/company_profiles.md).
   Близнецов по новым именам в базе нет (проверено по именам всех профилей).

Запуск:
    python3 pipeline/fix_g46_second_reading_A_2026_11_27.py            # сухой прогон
    python3 pipeline/fix_g46_second_reading_A_2026_11_27.py --write    # запись
"""
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
if HERE not in sys.path:
    sys.path.insert(0, HERE)

CARD = 'g89b4c747'
OLD_DATE, NEW_DATE, OLD_BASIS = '2026-04-01', '2026', 'publication'
DATE_QUOTE = ('Ритейлер «Кубатура» выкупил торговый центр у «Кама Капитал» 01.04.2026, 20:30 … '
              'Об этом “Ъ” сообщили стороны сделки. Это подтверждается данными выписки ЕГРН, согласно '
              'которой часть помещения в торговом объекте уже перешла АО «Концерн "Энерготехнологии"».')
DATE_URL = 'https://www.kommersant.ru/doc/8553146'

# профиль -> поле -> (было, стало)
PROFILES = {
    'ged60437e': {
        'desc': ('Петербургская сеть мебельных и интерьерных центров «Кубатура». '
                 'Юрлицо — АО «Концерн «Энерготехнологии».',
                 'Петербургская торговая компания, развивает магазины мебели и интерьера «Кубатура». '
                 'Юрлицо — АО «Концерн «Энерготехнологии»».'),
        'legal_short': ('АО «Концерн «Энерготехнологии»', 'АО «Концерн «Энерготехнологии»»'),
    },
    'g5502d591': {
        'name': ('Место встречи', 'ООО «Место встречи»'),
        'desc': ('Владелец районных торговых центров на месте бывших московских кинотеатров. '
                 'Юрлицо — ООО «Место встречи».',
                 'Создано в июле 2023 года Константином Эрнстом, Григорием Печерским, Александром Тобаком '
                 'и ООО «СБК МБ». С декабря 2023 года владеет ООО «Эдисонэнерго», которое перестраивает '
                 'московские кинотеатры в районные торговые центры; в мае 2026 года перешло ЗПИФ '
                 '«Парус — Место встречи».'),
    },
    'g58572d8a': {
        'name': ('ВТБ Индустриальная недвижимость', 'ООО «ВТБ Индустриальная недвижимость»'),
    },
    'g8014ae3f': {
        'name': ('Фирма Сатурн', 'ФХ «Фирма Сатурн»'),
        'desc': ('Производитель молочных продуктов на юге России, бренды «Бабулины продукты» и «Миленка». '
                 'Юрлицо — ООО «ФХ «Фирма Сатурн», Карачаево-Черкесия; владелец — Али Хапсироков.',
                 'Производитель молочных продуктов на юге России, бренды «Бабулины продукты» и «Миленка». '
                 'Юрлицо — ООО «ФХ «Фирма Сатурн»», Карачаево-Черкесия; владелец — Али Хапсироков.'),
        'legal_short': ('ООО «ФХ «Фирма Сатурн»', 'ООО «ФХ «Фирма Сатурн»»'),
    },
    'gba784476': {
        'desc': ('Молочный завод в Пятигорске, перерабатывает около 350 т молока в сутки.',
                 'Молочный завод в Пятигорске, может перерабатывать около 350 т молока в сутки.'),
    },
}


def apply_card(pending, log):
    card = next((c for c in pending['cards'] if c['id'] == CARD), None)
    assert card is not None, 'карточки %s нет в очереди' % CARD
    if card.get('date') == NEW_DATE and 'date_basis' not in card:
        return 0
    assert card.get('date') == OLD_DATE, 'date уже другой: %r' % card.get('date')
    assert card.get('date_basis') == OLD_BASIS, 'date_basis уже другой: %r' % card.get('date_basis')
    assert card.get('status') == 'Закрыта', 'status изменился: %r' % card.get('status')
    assert not card.get('events'), 'у карточки появились этапы — их даты надо править вместе с date'
    card['date'] = NEW_DATE
    del card['date_basis']
    import fact_edit_guard
    fact_edit_guard.log(card, 'date', NEW_DATE, DATE_QUOTE, DATE_URL,
                        'второе чтение 27.11.2026: день публикации, дня сделки в источниках нет')
    log.append('%s: date %r -> %r, date_basis %r снят' % (CARD, OLD_DATE, NEW_DATE, OLD_BASIS))
    return 1


def apply_profiles(base, log):
    comps, n = base['companies'], 0
    taken = {c.get('name') for cid, c in comps.items() if cid not in PROFILES}
    for cid, fields in PROFILES.items():
        assert cid in comps, 'профиля %s нет в базе' % cid
        for field, (old, new) in fields.items():
            cur = comps[cid].get(field)
            if cur == new:
                continue
            assert cur == old, '%s.%s уже другой: %r' % (cid, field, cur)
            if field == 'name':
                assert new not in taken, 'профиль с именем %r уже есть' % new
            comps[cid][field] = new
            n += 1
            log.append('%s.%s: %r -> %r' % (cid, field, old, new))
    return n


def main(write):
    log = []
    apply_card(json.load(open(PENDING, encoding='utf-8')), log)
    apply_profiles(json.load(open(DATA, encoding='utf-8')), log)
    print('\n'.join(log) or 'Все уже применено.')
    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0
    # Перечитать оба файла прямо перед записью: рядом работают другие помощники.
    pending = json.load(open(PENDING, encoding='utf-8'))
    if apply_card(pending, []):
        json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    base = json.load(open(DATA, encoding='utf-8'))
    before = copy.deepcopy(base)
    if apply_profiles(base, []):
        import mass_edit_guard
        mass_edit_guard.check(before, base, os.environ.get('MASS_OK'))
        json.dump(base, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
