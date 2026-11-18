# -*- coding: utf-8 -*-
"""g74dbc4b1 (Wylsacom/«Иммортал») — два поля, которые `review.py` не может
принять через FIXES, хотя решение обосновано текстом источника:

1. ТИП. Черновик притока поставил `type: "M&A"` по словам «стал владельцем»
   (они в словаре M&A), но по тексту доли таковы: Меркулов — 40%, Агневский —
   30%, Петухов (Wylsacom) — 30%. Ни у кого нет контроля, Петухов получил
   МИНОРИТАРНЫЙ пакет — по правилу CLAUDE.md/docs/card_status_dates.md
   («Раунд и миноритарная доля — «Инвестиция»»; «100% долей или контрольный
   пакет — M&A») это «Инвестиция», а не M&A. `review.check` не пропустит эту
   правку через FIXES механически: словарь `TYPE_WORDS['Инвестиция']`
   («инвестиц», «раунд», «вложил», «миноритарн», «профинансир», «вошел в
   капитал») не встречается в тексте источника буквально — заметка Ведомостей
   сухо цитирует ЕГРЮЛ, не называя сделку ни тем, ни другим словом. Решение —
   по смыслу (доля без контроля), тот же случай, что `fix_psb_atom_investment_card.py`
   18 августа 2026 (ПСБ/«Атом»: тоже допэмиссия/вход в капитал без слова
   «инвестиция» в тексте).

2. ДАТА. Поле несло день забора/публикации статьи (2026-11-18) — ровно тот
   случай, который `docs/card_status_dates.md` («Дата публикации не уточняет
   дату сделки») просит не делать: Ведомости лишь СЕГОДНЯ сослались на
   данные ЕГРЮЛ о текущем составе участников, но день, когда доля
   фактически перешла Петухову, в тексте не назван и не найден (искали ОГРН
   «Иммортала» для истории участников — не нашли, см. accepted_notes).
   `review.date_is_supported` требует день и месяц словами в цитате — их
   нет, и записать точный день через FIXES нельзя, не выдумав его. Честный
   вид — `date: "unknown"` (тот же формат, что `draft.py` ставит по
   умолчанию при отсутствии даты).

Статус на «Закрыта» и предмет на «ООО «Иммортал»» меняются ОБЫЧНЫМИ FIXES
review.py (слово «стал владельцем» подтверждает оба механически) —
отдельным файлом `pipeline/ingest/fixes/g74dbc4b1_card_2026_11_18.py`.

Запуск: python3 pipeline/fix_g74dbc4b1_immortal_type_date_2026_11_18.py           # проверка
        python3 pipeline/fix_g74dbc4b1_immortal_type_date_2026_11_18.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

CARD_ID = 'g74dbc4b1'
OLD_TYPE, NEW_TYPE = 'M&A', 'Инвестиция'
OLD_DATE, NEW_DATE = '2026-11-18', 'unknown'


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    cards = {c['id']: c for c in data['cards']}
    card = cards.get(CARD_ID)
    if card is None:
        raise SystemExit('карточки %s нет в очереди — состояние изменилось' % CARD_ID)

    assert card.get('type') == OLD_TYPE, (
        'ожидался type=%r, сейчас %r — состояние изменилось' % (OLD_TYPE, card.get('type')))
    assert card.get('date') == OLD_DATE, (
        'ожидался date=%r, сейчас %r — состояние изменилось' % (OLD_DATE, card.get('date')))

    print('ПРАВИМ %s:' % CARD_ID)
    print('  type: %r -> %r (миноритарная доля без контроля — «Инвестиция»)' % (OLD_TYPE, NEW_TYPE))
    print('  date: %r -> %r (день перехода доли в источниках не назван)' % (OLD_DATE, NEW_DATE))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0

    card['type'] = NEW_TYPE
    card['date'] = NEW_DATE

    json.dump(data, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
