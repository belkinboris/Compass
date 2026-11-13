# -*- coding: utf-8 -*-
"""Вычитка, партия m106a (13 ноября 2026), часть 4: закрыть два вопроса консоли по
карточкам, которые снимает pipeline/archive/2026-11/reread_deferred_m235.py.

Решение проверено заново 13 ноября 2026:
  * g4cd1fa52 (Wintershall Dea вывела российские СП из отчетности) — бухгалтерское событие,
    продажа самих долей — карточка g3bb1fadb («Согаз» и «Газовые технологии»,
    распоряжения № 873-р и № 865-р от 16.04.2026). Вопрос wintershall-one-or-two: «одна
    карточка на обоих покупателей» остается как есть (g3bb1fadb вычитана m235), карточка об
    уходе Wintershall снимается в обоих вариантах ответа — так и сказано в самом вопросе.
  * g4f4dc9b5 (Philip Morris переоценила долю 23% в «Мегаполисе», 10-Q за 3 квартал 2023 года,
    Интерфакс) — продажи не было; поиск 13 ноября 2026 (Интерфакс, 2firsts, Ведомости,
    отчеты PMI за 2025 год) продажи доли тоже не нашел. Вопрос pmi-megapolis-not-deal —
    ответ «убрать карточку».

Вопросы уходят из pipeline/open_questions.json, только когда карточки уже нет в базе
(скрипт m235 идет в плане первым).

    python3 pipeline/archive/2026-11/reread_deferred_m106ad.py           # сухой прогон
    python3 pipeline/archive/2026-11/reread_deferred_m106ad.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
QUESTIONS = os.path.join(ROOT, 'pipeline', 'open_questions.json')
CLOSE = {'g4cd1fa52': 'wintershall-one-or-two', 'g4f4dc9b5': 'pmi-megapolis-not-deal'}


def main(argv):
    write = '--write' in argv
    raw = open(QUESTIONS, encoding='utf-8').read()
    rows = json.loads(raw)
    drop = [r for r in rows if r.get('id') in CLOSE and str(r.get('key') or '').startswith(CLOSE[r['id']])]
    if not drop:
        print('Уже применено.')
        return 0
    ids = {d['id'] for d in json.load(open(DATA, encoding='utf-8'))['deals']}
    still = [r['id'] for r in drop if r['id'] in ids]
    if still and write:
        raise SystemExit('ОТКАЗ: карточки %s еще в базе — сначала reread_deferred_m235.py --write' % still)
    for r in drop:
        print('  закрыть вопрос %s (%s)' % (r['key'], r['id']))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    kept = [r for r in rows if r not in drop]
    with open(QUESTIONS, 'w', encoding='utf-8') as f:
        f.write(json.dumps(kept, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))
    print('ЗАПИСАНО: закрыто вопросов %d' % len(drop))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
