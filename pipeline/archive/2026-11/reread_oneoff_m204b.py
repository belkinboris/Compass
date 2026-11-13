# -*- coding: utf-8 -*-
"""Вычитка, марафон 12 ноября 2026, партия m204 (часть 3): продавцы, которых нельзя назвать, и правовая форма.

ЧТО ЧИНИТ И ПОЧЕМУ.
- g93724e30 («Займер» / МКК «Содействие XXI»): продавец в статьях не назван. История участников ЕГРЮЛ
  (Датаньютон, ОГРН 1146685039599) показывает запись 19.03.2025: «Займер» вошел с 51%, один участник
  вышел, доля другого уменьшилась, но имена в выдаче скрыты; уставный капитал не менялся (1 млн ₽, у
  «Займера» 510 000 ₽ номинала) — значит, доли куплены у участников. Где искали — в заметке приемки;
  смысл даты — запись в реестре; правовая форма предмета — ООО МКК «Содействие XXI».
- gdd4bb811 (ОСК / «Звезда»): сделка не состоялась; продавца как стороны нет. Владельцы АО «СТС» по
  ЕГРЮЛ — АО «РН-Транс» и ООО «ГПБ - Промышленные инвестиции»; смысл суммы — оценка затрат.

    python3 pipeline/archive/2026-11/reread_oneoff_m204b.py [--write]

Повторный запуск ничего не меняет («уже применено»).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import fact_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

NOTE_ZAYMER = ('Продавец не назван ни «Займером», ни Интерфаксом, ни «Ведомостями» (20.03.2025). История участников '
               'ЕГРЮЛ (Датаньютон, ОГРН 1146685039599): 19.03.2025 вошло ПАО МФК «Займер» с 51% (510 000 ₽ номинала), '
               'один участник вышел, доля другого уменьшилась, имена в выдаче скрыты; уставный капитал 1 млн ₽ не '
               'менялся — доли куплены у участников. После сделки: Андрей Афанасьев 44%, Андрей Богер 4%, Андрей '
               'Татарченков 1%. Искали еще: сообщение «Займера» для инвесторов, веб-поиск ИНН и учредителей МКК '
               '(Банкирос — ИНН 6685079610), реестр сайта (предмет не сопоставлен).')
NOTE_ZVEZDA = ('Сделка не состоялась, продавца как стороны нет. Владельцы АО «Современные технологии судостроения» по '
               'ЕГРЮЛ — АО «РН-Транс» (структура «Роснефти») и ООО «ГПБ - Промышленные инвестиции»; передачу «Звезды» в '
               'ОСК предлагала «Роснефть» (Коммерсантъ 08.11.2024, Фонтанка 18.03.2025).')


def card_of(data, cid):
    return next(x for x in data['deals'] if x['id'] == cid)


def apply(data):
    comps = data['companies']
    done = []
    c = card_of(data, 'g93724e30')
    notes = c.setdefault('accepted_notes', {}).setdefault('no_profile', {})
    if notes.get('seller') != NOTE_ZAYMER:
        assert not c.get('seller') and not c.get('seller_id')
        notes['seller'] = NOTE_ZAYMER
        c['date_basis'] = 'registry'
        t = comps['gafde93cd']
        assert t['name'] == 'МКК «Содействие XXI»' and 'купил МФК «Займер»' in t['desc']
        t['legal_short'] = 'ООО МКК «Содействие XXI»'
        t['desc'] = ('Микрокредитная компания (зарегистрирована в 2014 году), владеет ООО «Селлер Капитал» — сервисом '
                     'Seller Capital, который кредитует продавцов на маркетплейсах (линии 1–50 млн ₽). С марта 2025 '
                     'года 51% принадлежит «Займеру».')
        done.append('g93724e30')
    c = card_of(data, 'gdd4bb811')
    notes = c.setdefault('accepted_notes', {}).setdefault('no_profile', {})
    if notes.get('seller') != NOTE_ZVEZDA:
        assert not c.get('seller') and not c.get('seller_id')
        notes['seller'] = NOTE_ZVEZDA
        c['sum_basis'] = 'estimate'
        done.append('gdd4bb811')
    return done


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    old, data = json.loads(raw), json.loads(raw)
    done = apply(data)
    print('применяется к:', ', '.join(done) if done else 'ничего — уже применено')
    bad = fact_edit_guard.unbacked(old, data)
    assert not bad, bad
    if not write or not done:
        print('Сухой прогон. Запись — с ключом --write.' if not write else 'ЗАПИСАНО: нечего.')
        return 0
    fresh_raw = open(DATA, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    apply(fresh)
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
