# -*- coding: utf-8 -*-
"""Явные поля карточки там, где разбор текста не может ответить сам:
`date_basis` (что за дата стоит в карточке) и `stake_acquired` (доля,
приобретаемая именно в этой сделке).

Разбор рецензента 6 сентября 2026 (вторая критика):

- Boxberry (`g46c6e23f`): карточка датирована 24 апреля 2025 — днём, когда
  Интерфакс СООБЩИЛ о закрытии; точный день закрытия стороны не называли.
  Без пометки ассистент и карточка превращали дату публикации в дату
  события («сделка закрыта 24 апреля»). `date_basis: 'publication'` —
  карточка и ответ ассистента говорят «дата сообщения о закрытии».
- «Ингосстрах Банк» (`g0201b97a`): заголовок называет проданный пакет
  (99,9% акций), а «Предмет / доля» описывает реструктуризацию самого
  покупателя («100% долей головной компании перешли к сейшельской…») —
  два разных процента о переходе долей, и правило контекста покупки честно
  отвечает «не установлено». Доля, купленная в ЭТОЙ сделке, — 99,9%, она
  стоит в заголовке; явное поле снимает неоднозначность, не переписывая
  текст. Значение обязано быть выводимо из заголовка карточки
  (`deal_multiples.acquired_percents`), иначе скрипт падает.

Оба значения — из закрытых списков/границ (`DATE_BASES`, 0 < доля ≤ 100);
держит `test_data.py::test_explicit_date_basis_and_stake_acquired_are_valid`.

Запуск:
    python3 pipeline/fix_explicit_field_overrides.py           # сухой прогон
    python3 pipeline/fix_explicit_field_overrides.py --write
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from deal_multiples import DATE_BASES, acquired_percents  # noqa: E402

DATA = 'static/data/deals_promoted.json'

DATE_OVERRIDES = {
    # id: (ожидаемая дата карточки, основание даты)
    'g46c6e23f': ('2025-04-24', 'publication'),
}
STAKE_OVERRIDES = {
    # id: (доля, приобретаемая в этой сделке; она обязана читаться в заголовке)
    'g0201b97a': 99.9,
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    deals = {d['id']: d for d in data['deals']}
    changed = 0
    for did, (date, basis) in DATE_OVERRIDES.items():
        assert basis in DATE_BASES, basis
        d = deals[did]
        assert d.get('date') == date, (did, d.get('date'))
        if d.get('date_basis') == basis:
            print(f'{did}: date_basis уже {basis}')
            continue
        assert not d.get('date_basis'), (did, d.get('date_basis'))
        print(f'{did}: date_basis -> {basis} ({d["title"][:60]})')
        changed += 1
        if write:
            d['date_basis'] = basis
    for did, stake in STAKE_OVERRIDES.items():
        d = deals[did]
        assert 0 < stake <= 100, stake
        assert stake in acquired_percents(d['title']), (did, d['title'], acquired_percents(d['title']))
        if d.get('stake_acquired') == stake:
            print(f'{did}: stake_acquired уже {stake}')
            continue
        assert d.get('stake_acquired') is None, (did, d.get('stake_acquired'))
        print(f'{did}: stake_acquired -> {stake} ({d["title"][:60]})')
        changed += 1
        if write:
            d['stake_acquired'] = stake
    if not write:
        print(f'Сухой прогон: правок {changed}. Запись — с ключом --write.')
        return 0
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print(f'Записано: {changed}.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
