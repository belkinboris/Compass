# -*- coding: utf-8 -*-
"""Кандидаты в дубли карточек — по ОДНОМУ ПОКУПАТЕЛЮ И ОДНОЙ ДАТЕ,
БЕЗ требования общего предмета/суммы (в отличие от
`find_duplicate_deal_candidates.py`).

ЗАЧЕМ. Месячная очередь дочитывания 6-7 сентября 2026 года нашла шесть
пар дублей подряд (`c46d3e581`/`g63c7d1bb` — «Амбер Талвис»,
`c09e39da9`/`absolut-strah` — «Абсолют Страхование»,
`c9bad29b7`/`g4f1b5909` — Газпромбанк/«Мега», `cc2929a95`/`g15f35a5d` —
ОКТО/Zapadnaya Gold Mining, `c514e8712`/`gdda3e685` — Sminex/«Инград»,
`c985468d2`/`g300d56ed` — «Лента»/«Молния», `ksk`/`g656645d5` — «Дело»/
КСК) — все одного класса: старая тонкая карточка из партии 2022-2024
годов (прочерк в `target`/`asset_id`, покупатель только текстом или
короткой ссылкой) дублирует новую, богатую карточку о ЗАКРЫТИИ той же
сделки, у которой уже есть нормальная связка `buyer`. Существующий
`find_duplicate_deal_candidates.py` требует общий `target`/`asset_id`
ИЛИ (общий `buyer` И общий год И общая сумма) — а у тонких старых
карточек `target`/`asset_id` пуст, а сумма часто записана иначе
(«$2 млрд (по оценке)» против «не более $2 млрд (193 млрд ₽)»), и обе
проверки дают ноль совпадений. Это правило ШИРЕ: общий `buyer` (у него
уже стоит ссылка на профиль-покупателя ОБЕИХ карточек) и общая ТОЧНАЯ
дата — этого достаточно, чтобы отобрать пару для чтения; шире не значит
точнее, поэтому это тоже список ДЛЯ ЧТЕНИЯ, а не приговор (МТС/Avito
дают пары с тем же покупателем и датой, но РАЗНЫМИ предметами —
консолидация или отдельные сделки одного года, не дубли).

Запуск:
    python3 pipeline/find_duplicate_deal_candidates_by_buyer_date.py
"""
import json
from collections import defaultdict
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / 'static' / 'data' / 'deals_promoted.json'


def main():
    data = json.load(open(DATA, encoding='utf-8'))
    merged_ids = set((data.get('merged') or {}).keys())
    by_buyer_date = defaultdict(list)
    for d in data['deals']:
        if d['id'] in merged_ids:
            continue
        b, dt = d.get('buyer'), d.get('date')
        if b and dt:
            by_buyer_date[(b, dt)].append(d)

    groups = [g for g in by_buyer_date.values() if len(g) > 1]
    print('Групп «один покупатель + одна дата», карточек больше одной: %d' % len(groups))
    for g in groups:
        print()
        for d in g:
            print('  %s | %s | сумма: %s | src: %d' % (
                d['id'], d.get('title', '')[:70], d.get('sum'), len(d.get('src') or [])))


if __name__ == '__main__':
    main()
