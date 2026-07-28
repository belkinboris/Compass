# -*- coding: utf-8 -*-
"""Бэклог A16: значение обрывается посреди названия компании.

ЧТО СЛОМАНО. На экране стоит «ВТБ Капитал приобрёл около 15% в Delimobil
Holding S.» — название разрезано пополам на «S.A.». Так же обрезаны «Shell
Salym Development B.» (B.V.), «Prosus N.» (N.V.), «Reg.» (Reg.ru), «ВЭБ.»
(ВЭБ.РФ), «Mail.» (Mail.ru), «etprf.» (etprf.ru).

ОТКУДА. Тот же разрез «точка + пробел = конец предложения», что чинил A6, но с
другой стороны: в A6 обрывок начинался с закрывающей скобки, в A12 — кончался
висящим «;», а здесь текст режется ВНУТРИ слова, на точке сокращения. Правило
`LATIN_ABBR_END` в `fix_truncated_fields.py` ловило такой обрыв только в
середине значения, а не в самом его конце.

ЗАМЕР (прогон 36). Прогнаны все строковые поля `eco.*` и `law.*` по 1333
карточкам: обрыв внутри слова — 8 значений в 7 карточках (7 в «Предмете / доле»,
1 в «Показателях таргета»). Все восстановимы: продолжение лежит в
«Дополнительной информации» той же карточки.

КАК ЧИНИМ. Значение дотягивается до конца предложения в тексте карточки.
Ничего не сочиняем: восстановленный текст обязан НАЧИНАТЬСЯ с того, что уже
стоит в поле, и дословно совпадать с куском источника — скрипт падает, если
это не так. Ни одно поле, кроме перечисленных, не трогается.

Запуск:
    python3 pipeline/fix_truncated_names.py            # сухой прогон
    python3 pipeline/fix_truncated_names.py --write    # записать
"""
import json
import re
import sys

PATH = 'static/data/deals_promoted.json'
SENT = re.compile(r"(?<=[.!?])\s+(?=(?-i:[А-ЯЁA-Z«\"]))")

# (id сделки, группа, поле) — прочитаны все восемь
CASES = [
    ('g0f9ca0a0', 'eco', 'share'),        # Shell Salym Development B.V.
    ('g420cae8d', 'eco', 'share'),        # Prosus N.V.
    ('gb4ebeacf', 'eco', 'share'),        # площадка etprf.ru
    ('g9b76cf8d', 'eco', 'share'),        # Reg.ru
    ('g9b76cf8d', 'eco', 'target_fin'),   # Reg.ru
    ('ge882f973', 'eco', 'share'),        # ВЭБ.РФ
    ('g74932d41', 'eco', 'share'),        # Delimobil Holding S.A.
    ('g221e9139', 'eco', 'share'),        # Mail.ru Group
]


def norm(s):
    return re.sub(r'\s+', ' ', str(s or '')).strip()


def sources(deal):
    eco = deal.get('eco') or {}
    return [norm(deal.get('extra')), norm(eco.get('rationale')), norm(eco.get('context'))]


def restore(current, source):
    """Дотянуть значение до конца предложения, в котором оно обрывается."""
    p = source.find(current)
    if p < 0:
        return None
    acc, bounds = 0, []
    for sent in SENT.split(source):
        bounds.append((acc, acc + len(sent)))
        acc += len(sent) + 1
    end = p + len(current)
    idx = next(i for i, (a, b) in enumerate(bounds) if a <= end <= b)
    return source[p:bounds[idx][1]].strip()


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    plan, done = [], []
    for deal_id, grp, key in CASES:
        deal = by_id.get(deal_id)
        assert deal is not None, 'нет сделки %s' % deal_id
        current = norm((deal.get(grp) or {}).get(key))
        assert current, '%s: поле %s.%s пусто' % (deal_id, grp, key)
        best = None
        for src in sources(deal):
            if not src or src == current:
                continue
            rec = restore(current, src)
            if rec and rec != current:
                best = rec
                break
        if best is None:
            done.append((deal_id, grp, key))   # уже восстановлено
            continue
        # Ничего не сочинено: новое значение начинается со старого и дословно
        # взято из текста карточки.
        assert best.startswith(current), '%s: восстановленный текст не продолжает старый' % deal_id
        assert best.endswith(('.', '!', '?')), '%s: восстановленный текст не закончен' % deal_id
        plan.append((deal_id, grp, key, current, best, deal))

    assert len(plan) + len(done) == len(CASES), 'часть полей изменилась вне скрипта'
    if not plan:
        print('Уже применено: все %d значений восстановлены.' % len(CASES))
        return

    print('Значений к восстановлению: %d' % len(plan))
    for deal_id, grp, key, cur, rec, _ in plan:
        print('  %s [%s.%s] %d -> %d знаков' % (deal_id, grp, key, len(cur), len(rec)))
        print('     было:  …%s' % cur[-60:])
        print('     стало: …%s' % rec[max(0, len(cur) - 60):][:120])

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return
    for deal_id, grp, key, _, rec, deal in plan:
        deal[grp][key] = rec
    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('\nЗаписано: %d значений.' % len(plan))


if __name__ == '__main__':
    main('--write' in sys.argv)
