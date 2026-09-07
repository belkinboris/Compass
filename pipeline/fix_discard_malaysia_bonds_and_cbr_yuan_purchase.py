# -*- coding: utf-8 -*-
"""Приток 7 сентября 2026 (11:20) — две карточки прошли ворота ошибочно,
тот же класс дефекта, что g4246335d (обзор покупок туристов) с прогона
10:20: разбор заголовка формально нашёл «покупателя» и «предмет» там,
где сделки M&A вообще нет.

- gd431b049: «За август инвесторы вложили рекордные $3,9 млрд в облигации
  Малайзии из-за ИИ» (Ведомости) — макроэкономическая новость о рынке
  облигаций Малайзии, без единой российской стороны; разбор вычленил
  «buyer_name: За август инвесторы» и «asset: облигации Малайзии из-за
  ИИ» — бессмысленная пара, формально прошедшая проверку ворот.
- g8ccc9185: «Банк России купил на внутреннем рынке юани на 5,9 миллиарда
  рублей» (ПРАЙМ) — рутинная валютная операция ЦБ на открытом рынке, не
  сделка M&A (нет смены контроля над компанией); разбор дал
  «buyer_name: России», «asset: на внутреннем рынке юани на 5,9
  миллиарда рублей».

Обе карточки удаляются из pending.json тем же приёмом (discarded_urls),
что и g4246335d, до отправки в консоль.

Запуск: python3 pipeline/fix_discard_malaysia_bonds_and_cbr_yuan_purchase.py [--write]
"""
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE_PATH = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

TARGETS = {
    'gd431b049': 'https://www.vedomosti.ru/investments/news/2026/09/07/1226819-investori-vlozhili',
    'g8ccc9185': 'https://1prime.ru/20260907/tsentrobank-873068181.html',
}


def main(write=False):
    with open(PENDING_PATH, encoding='utf-8') as f:
        pending = json.load(f)
    with open(STATE_PATH, encoding='utf-8') as f:
        state = json.load(f)

    discarded = state.setdefault('discarded_urls', {})
    kept = []
    removed = []
    for c in pending['cards']:
        if c['id'] in TARGETS:
            url = TARGETS[c['id']]
            assert any(len(s) > 1 and s[1] == url for s in (c.get('src') or [])), c['id']
            assert url not in discarded, url
            discarded[url] = {
                'id': c['id'], 'title': c.get('title'),
                'at': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
            }
            removed.append(c['id'])
        else:
            kept.append(c)

    assert set(removed) == set(TARGETS), (removed, TARGETS)
    pending['cards'] = kept

    print('Сняты карточки (ложный разбор заголовка, ворота пропустили ошибочно):', ', '.join(removed))

    if write:
        with open(PENDING_PATH, 'w', encoding='utf-8') as f:
            json.dump(pending, f, ensure_ascii=False, indent=1)
            f.write('\n')
        with open(STATE_PATH, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('(сухой прогон, для записи — --write)')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
