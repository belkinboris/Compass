# -*- coding: utf-8 -*-
"""Качество 27 ноября 2026, недельная проверка gb82efd9f («Медскан», 49% «Медскан Лаб»).

По истории участников ЕГРЮЛ ООО «Медскан Лаб» (datanewton, ОГРН 1227700484076) 25.11.2026
49% перешли комбинированному ЗПИФ «ПроектИнвест Плюс» (ИНН управляющей компании 9731111231),
у АО «Медскан» осталось 51%. Дата, покупатель, law.struct и eco.context записаны через
review.py (fixes/reading_2026_11_27_week_1.py). Здесь — то, что review.py не правит:
событие «Сделка завершена» (дата годом и слова «имя не раскрыл») и пояснения приемки,
которые говорили, что покупатель не назван и записи в реестре нет.

    python3 pipeline/archive/2026-11/quality_oneoff_gb82efd9f_2026_11_27.py           # сухо
    python3 pipeline/archive/2026-11/quality_oneoff_gb82efd9f_2026_11_27.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
CID = 'gb82efd9f'

NOTE_OLD = ('Покупатель — стратегический партнер, имя которого «Медскан» не раскрыл; проданы 49% лабораторного '
            'направления KDL, группа из контура «Росатома» сохранила 51%.')
NOTE_NEW = ('«Медскан» назвал покупателя стратегическим партнером без имени; по ЕГРЮЛ 49% ООО «Медскан Лаб» '
            '25 ноября 2026 года перешли комбинированному ЗПИФ «ПроектИнвест Плюс», у группы из контура '
            '«Росатома» остался 51%.')
BUYER_NOTE_NEW = ('Покупатель по ЕГРЮЛ — комбинированный ЗПИФ «ПроектИнвест Плюс» (запись об участниках '
                  'ООО «Медскан Лаб» от 25.11.2026, datanewton, ОГРН 1227700484076; ИНН управляющей компании '
                  '9731111231 — ООО «УК «Капитал Инвест Менеджмент»). Пресс-релиз называет покупателя '
                  '«стратегическим партнером» без имени; кто владеет паями фонда, не раскрыто. Профиль фонду '
                  'не заведен: у паевого фонда нет своего юрлица и ИНН, а других сделок фонда в базе нет.')
REG_ADD = (' Дополнено 27.11.2026: в истории участников появилась запись от 25.11.2026 — АО «Медскан» 100% → 51%, '
           'вошел комбинированный ЗПИФ «ПроектИнвест Плюс» (ИНН управляющей компании 9731111231) с 49%.')


def apply(data):
    c = next(d for d in data['deals'] if d['id'] == CID)
    n = 0
    ev = c['events'][0]
    if ev['date'] != '2026-11-25':
        assert ev['date'] == '2026' and c['date'] == '2026-11-25', (ev['date'], c['date'])
        ev['date'] = '2026-11-25'
        n += 1
    if ev['note'] != NOTE_NEW:
        assert ev['note'] == NOTE_OLD, ev['note']
        ev['note'] = NOTE_NEW
        n += 1
    notes = c['accepted_notes']
    if notes['no_profile']['buyer'] != BUYER_NOTE_NEW:
        assert notes['no_profile']['buyer'].startswith('Имя покупателя не раскрыто'), notes['no_profile']['buyer'][:60]
        notes['no_profile']['buyer'] = BUYER_NOTE_NEW
        n += 1
    if not notes['checked']['registry_owners'].endswith(REG_ADD):
        assert 'Новых записей после 2025-10-24 нет' in notes['checked']['registry_owners']
        notes['checked']['registry_owners'] += REG_ADD
        n += 1
    return n


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    old, data = json.loads(raw), json.loads(raw)
    n = apply(data)
    if not n:
        print('Уже применено.')
        return 0
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    bad = fact_edit_guard.unbacked(old, data)
    assert not bad, bad
    if not write:
        print('Сухой прогон: %d правок. Запись — с ключом --write.' % n)
        return 0
    fresh_raw = open(DATA, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    apply(fresh)
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
    print('ЗАПИСАНО: %d правок.' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
