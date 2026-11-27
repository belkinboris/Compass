# -*- coding: utf-8 -*-
"""Приток 27 ноября 2026, второе чтение карточек g6138adf7 (Мосбиржа / «Сити-4») и
g0d9b4792 (Softline / ЗПИФ «Аксиома Капитал»): две правки, которые не ложатся в FIXES.
Остальное по тому же чтению — записи таблицы (fixes/written_2026_11_27_vm.py,
g46new_2026_11_27_softline.py) через `review.py --write`.

1. g6138adf7, дата. Стояло 2025-11-01 с `date_basis: publication` — это день публикации
   «Ведомостей» (он же в адресе статьи). Дня сделки не называют ни «Ведомости» («Мосбиржа
   закрыла одну из крупнейших сделок на рынке офисной недвижимости этого года»), ни ПРАЙМ
   от 2 ноября 2025 года; в реестре сделка не видна (помещения, а не доля в обществе).
   Дата — годом, «2025»; основание дня (`date_basis`) у даты-года не пишется
   (docs/card_status_dates.md, «Дата публикации не уточняет дату сделки»; тот же случай —
   fix_g13f5c85b_date_to_year_2026_11_24.py). `review.py` день до года не снимает
   (`date_is_supported` принимает только ГГГГ-ММ-ДД), запись date_basis из
   fixes/g46new_2026_11_27_moex.py убрана.

2. Профиль покупателя g4aa10564 (ЗПИФ «Аксиома Капитал»), описание. Профиль заведен
   приемкой этой карточки, других сделок у него нет. Управляющая компания была записана
   «Тэтис Кэпитал» — так у АК&M; в ЕГРЮЛ (история участников ООО «Алварус Капитал»,
   datanewton, ОГРН 1227700514370, запись 27.04.2023) — ООО «ТЕТИС КЭПИТАЛ», ИНН
   7709853192; так же пишут ComNews и Anti-Malware. По тому же реестру 22.08.2024 фонд
   перешел под управление ООО «Баланс Эссет Менеджмент» (в отчетности группы — 6 августа
   2024 года), 22.10.2026 — ООО «Управляющая компания «Инвестум». Строка «Покупатель»
   поста берет первое предложение описания, которого нет в заголовке: теперь это
   «паевой фонд, которым в 2023 году управляло ООО «Тетис Кэпитал»» — без двух тире подряд.

Запуск: python3 pipeline/fix_g46_second_reading_B_2026_11_27.py [--write]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'ingest'))
DATA = os.path.join(HERE, '..', 'static', 'data', 'deals_promoted.json')

MOEX = 'g6138adf7'
FUND = 'g4aa10564'
OLD_DESC = ('Закрытый паевой инвестиционный фонд, владелец группы Softline. Под управлением ООО «Тэтис '
            'Кэпитал», с 2024 года — ООО «Баланс Эссет Менеджмент».')
NEW_DESC = ('Закрытый паевой фонд, которым в 2023 году управляло ООО «Тетис Кэпитал». С августа 2024 года '
            'управляющая компания — ООО «Баланс Эссет Менеджмент», с октября 2026 года — ООО «Управляющая '
            'компания „Инвестум“». Фонду принадлежит группа Softline.')


def fix_card(pending):
    card = next(c for c in pending['cards'] if c['id'] == MOEX)
    assert card.get('date') in ('2025-11-01', '2025'), 'date изменился: %r' % card.get('date')
    assert card.get('date_basis') in ('publication', None), 'date_basis изменился: %r' % card.get('date_basis')
    assert card.get('status') == 'Закрыта', 'status изменился: %r' % card.get('status')
    assert not card.get('events'), 'у карточки появились этапы — их дату тоже надо сверить'
    changed = card.get('date') != '2025' or 'date_basis' in card
    card['date'] = '2025'
    card.pop('date_basis', None)
    return changed


def fix_profile(base):
    comp = base['companies'][FUND]
    assert comp.get('desc') in (OLD_DESC, NEW_DESC), 'описание профиля изменилось: %r' % comp.get('desc')
    used = [d['id'] for d in base['deals'] if FUND in (d.get('buyer'), d.get('seller_id'), d.get('target'))]
    assert not used, 'профиль уже стоит в опубликованных сделках %s — описание править отдельно' % used
    changed = comp['desc'] != NEW_DESC
    comp['desc'] = NEW_DESC
    return changed


def main(write):
    import promote
    pending = promote.load_pending()
    base = json.load(open(DATA, encoding='utf-8'))
    print('%s: дата -> 2025, date_basis снят: %s' % (MOEX, 'да' if fix_card(pending) else 'уже сделано'))
    print('%s: описание профиля: %s' % (FUND, 'меняем' if fix_profile(base) else 'уже сделано'))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    # Оба файла перечитываются прямо перед записью: их пишут и другие прогоны.
    pending = promote.load_pending()
    raw = open(DATA, encoding='utf-8').read()
    base = json.loads(raw)
    card_changed, profile_changed = fix_card(pending), fix_profile(base)
    if card_changed:
        promote.save_pending(pending)
    if profile_changed:
        with open(DATA, 'w', encoding='utf-8') as f:
            json.dump(base, f, indent=1, ensure_ascii=False)
            f.write('\n' if raw.endswith('\n') else '')
    print('Записано.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main('--write' in sys.argv))
