# -*- coding: utf-8 -*-
"""Карточка `ga5198c41` (Сергей Семак / «Юхата») — правки по второму чтению
(SECOND_READING_BRIEF.md, 25 ноября 2026, отдельная сессия): пять полей, не
через `review.py`.

ПОЧЕМУ НЕ ЧЕРЕЗ review.py.
- `date` / `events[0].date`: карточка несла день публикации заметки ТАСС
  (2026-11-25), а не день события. Запись о новом составе участников в
  ЕГРЮЛ (datanewton.ru, ОГРН 1265000045485) — от 24.11.2026 (см.
  accepted_notes.checked.registry_owners этой же карточки); по правилу
  «день записи о новых участниках — дата закрытой сделки» (docs/intake_run.md,
  шаг 8) и «дата — день события… а не дата публикации статьи»
  (docs/card_status_dates.md) верный день — 2026-11-24. В тексте источника
  этот день не назван словами, поэтому `review.date_is_supported` его не
  примет — решение по регистру, тот же класс, что у `fix_pilot_owner_comments_2026_11_02.py`
  (Аэрофлот/«Директ Стар»: `put(ae, 'date', ...)` напрямую).
- `law.struct`: поле было пустым, хотя механика сделки нестандартная (вход
  новым взносом при увеличении уставного капитала, без выкупа доли у
  Михайлова). Обоснование — та же история участников ЕГРЮЛ, которой нет в
  кэше статьи на диске, поэтому `review.py`/`write_card.py` не подтвердят
  текст цитатой из `data/inbox/raw`: тот же случай, что `law.struct` у
  gc9ea6b08 («Аэрофлот» не покупал долю у прежних участников, а вошел в
  капитал через увеличение) — записано тем же способом, прямым `assert`.
- `asset`: поле несло не имя предмета, а предложение-дубль `eco.share`
  («33,34% доли в ООО «Юхата»»). У сделки есть профиль компании (g85035f89,
  имя «Юхата») — по образцу других карточек типа «Инвестиция» (Tams,
  Kickidler, «Директ Стар») в `asset` идет короткое имя, а доля и
  юридическая форма — в `eco.share`. Структурное поле, не прозаическое.
- `eco.context`: второй абзац — не про эту сделку, а про соседние активы
  Семака (пищевое производство, рестораны, совокупная выручка и прибыль его
  компаний, оценка Rusprofile) — запрещенный приёмом второго чтения пример
  («контекст про соседние активы тех же людей»): цифры стоят прямо под
  «33,34% доли в ООО «Юхата»», читатель может принять их за показатели
  самой «Юхаты». Правка — убрать абзац, а не переписать прозу по цитате,
  поэтому `review.py` (он сверяет цитату поля целиком, а не удаление куска
  уже стоящего текста) не подходит; `docs/card_editing_scripts.md`,
  «Дописывание и правка… — одноразовым скриптом с assert на старое
  значение».
- профиль компании (`companies['g85035f89'].desc`, в `deals_promoted.json`):
  снята фраза «участник проекта «Сколково»» — ни ТАСС, ни Рамблер ее не
  называют, а собственный поиск сборщика (accepted_notes.searched) её не
  подтвердил («профиля проекта не нашлось»); второе чтение не нашло ее ни в
  одном источнике тоже (WebSearch) — непроверенный факт в профиле компании,
  снят по правилу CLAUDE.md «не подменять отсутствующие данные
  правдоподобными».

Запуск:
    python3 pipeline/fix_ga5198c41_second_reading_2026_11_25.py            # сухой прогон
    python3 pipeline/fix_ga5198c41_second_reading_2026_11_25.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PENDING = os.path.join(ROOT, '..', 'static', 'data', 'pending.json')

CARD_ID = 'ga5198c41'

OLD_DATE, NEW_DATE = '2026-11-25', '2026-11-24'
OLD_ASSET = '33,34% доли в ООО «Юхата»'
NEW_ASSET = 'Юхата'
OLD_STRUCT = '—'
NEW_STRUCT = ('Семак не выкупал долю у Ивана Михайлова, а вошел в капитал «Юхаты» через '
              'увеличение уставного капитала и получил 33,34%. По данным ЕГРЮЛ, номинал доли '
              'Михайлова не изменился, а его доля снизилась с 100% до 66,66%.')
OLD_CONTEXT = ('«Юхата» — исследовательская компания в сфере естественных и технических наук; '
               'Семак получил в ней 33,34%.\n'
               '\n'
               'У Семака есть и другие активы — в пищевом производстве и ресторанном бизнесе. '
               'Совокупная выручка его компаний по итогам 2025 года составила 646 млн ₽ — на 12% '
               'меньше, чем годом раньше; чистая прибыль — 20 млн ₽, на 17% больше. По оценке '
               'Rusprofile, стоимость всех его долей на конец 2025 года — 44 млн ₽.')
NEW_CONTEXT = '«Юхата» — исследовательская компания в сфере естественных и технических наук; Семак получил в ней 33,34%.'


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    cards = {c['id']: c for c in data['cards']}
    card = cards.get(CARD_ID)
    if card is None:
        raise SystemExit('карточки %s нет в очереди — состояние изменилось' % CARD_ID)

    assert card.get('date') == OLD_DATE, 'date изменилось: %r' % card.get('date')
    assert card.get('events') and card['events'][0].get('date') == OLD_DATE, (
        'events[0].date изменилось: %r' % (card.get('events') or [{}])[0].get('date'))
    assert card.get('asset') == OLD_ASSET, 'asset изменилось: %r' % card.get('asset')
    assert (card.get('law') or {}).get('struct') == OLD_STRUCT, (
        'law.struct изменилось: %r' % (card.get('law') or {}).get('struct'))
    assert (card.get('eco') or {}).get('context') == OLD_CONTEXT, (
        'eco.context изменилось: %r' % (card.get('eco') or {}).get('context'))

    print('ПРАВИМ %s:' % CARD_ID)
    print('  date: %r -> %r (день записи в ЕГРЮЛ, не день публикации)' % (OLD_DATE, NEW_DATE))
    print('  events[0].date: %r -> %r' % (OLD_DATE, NEW_DATE))
    print('  asset: %r -> %r (имя предмета, не дубль eco.share)' % (OLD_ASSET, NEW_ASSET))
    print('  law.struct: пусто -> механика (допэмиссия/вход в капитал, без выкупа у Михайлова)')
    print('  eco.context: убран абзац про соседние активы Семака (не об этой сделке)')
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0

    card['date'] = NEW_DATE
    card['date_basis'] = 'registry'
    card['events'][0]['date'] = NEW_DATE
    card['asset'] = NEW_ASSET
    card.setdefault('law', {})['struct'] = NEW_STRUCT
    card.setdefault('eco', {})['context'] = NEW_CONTEXT

    json.dump(data, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
