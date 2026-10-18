# -*- coding: utf-8 -*-
"""Снять тему «IPO / SPO» с карточек, где IPO — чужой план или фон, а не сделка.

Что чинит. Проверка ассистента на 100 вопросах (вторая волна, октябрь 2026):
на «Какие IPO прошли в 2024–2025 годах и на какие суммы?» в ответ попадала
покупка ЦОДа Ростелекомом за 26,3 млрд ₽ — и эта цена читалась как объём
размещения. Причина — в базе: тема «IPO / SPO» стоит у карточки, где IPO
упомянуто только как отложенный план ДОЧКИ покупателя. Такие темы ставились
старым правилом, которое искало слово «IPO» по всему тексту; нынешнее
правило (`tag_themes.head()` — заголовок и предмет) их не подтверждает и
обратно не допишет (`add_themes` только дописывает по нынешнему правилу).

Какие карточки (каждая прочитана, IPO в них — только упоминание):
  * g11d6e0bc — Ростелеком купил ЦОД 3data HyperScale: «РТК-ЦОД планировал
    провести IPO осенью 2024 года, но размещение отложили» — фон о дочке;
  * gdf93c62d — ЭТМ купил АВС Электро: «на фоне планов ЭТМ привлечь около
    10 млрд ₽ в ходе IPO» — фон о покупателе;
  * g676504a3 — KAMA FLOW инвестирует 500 млн ₽ в ROBO: «в перспективе ROBO
    рассматривает IPO» — план на будущее;
  * gdde6bef5 — слияние Whoosh и МТС Юрент: ликвидность «вместо отдельного
    IPO» — IPO как раз не было.

Сомнительные — НЕ правятся (IPO / pre-IPO связано с самой сделкой, решать
чтением): Медскан (g630c3361, g2197ed53, g7b4be1c4), Mixit и BASK (фонды
pre-IPO, g9fc75a9c, g1d003324), «Мать и дитя»/«Инвитро» (g4165ba00, «с
прицелом на IPO»), Юрченко/ВТБ (g4470332e, акции куплены в ходе SPO),
«Эталон»/«Бизнес-Недвижимость» (g321bdead, оплата из SPO), Альфа-Банк/«Медси»
(g4d7b2e19, pre-IPO раунд).

Снимается только эта тема; остальные темы карточки остаются. Файл базы
читается прямо перед записью; на каждой карточке `assert` на заголовок и на
то, что тема стоит.

Запуск:
    python3 pipeline/fix_ipo_theme_on_plain_deals_2026_10_18.py           # сухой прогон
    python3 pipeline/fix_ipo_theme_on_plain_deals_2026_10_18.py --write
После записи — python3 pipeline/facts_derive.py --write.
"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / 'static' / 'data' / 'deals_promoted.json'
THEME = 'IPO / SPO'
# id -> начало заголовка: основание правки — сама карточка, и если её
# заголовок поменялся, правку надо пересмотреть, а не применять вслепую.
CARDS = {
    'g11d6e0bc': 'Ростелеком приобрел ЦОД 3data HyperScale',
    'gdf93c62d': 'ЭТМ приобрел дистрибьютора АВС Электро',
    'g676504a3': 'KAMA FLOW подписала соглашение об инвестиции',
    'gdde6bef5': 'Слияние Whoosh и МТС Юрент',
}


def main(write: bool) -> None:
    data = json.loads(BASE.read_text(encoding='utf-8'))
    deals = {d['id']: d for d in data['deals']}
    todo = []
    for did, title in CARDS.items():
        card = deals[did]
        assert card['title'].startswith(title), f'{did}: заголовок изменился — пересмотреть правку'
        themes = list(card.get('themes') or [])
        if THEME not in themes:
            print(f'{did}: темы «{THEME}» уже нет — пропуск')
            continue
        assert str(card.get('type') or '') != 'IPO', f'{did}: тип IPO — тема верна'
        todo.append((did, themes, [t for t in themes if t != THEME]))
    for did, old, new in todo:
        print(f'{did}: themes {old} → {new}')
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    # Перечитать прямо перед записью: между чтением и записью могла пройти рутина.
    data = json.loads(BASE.read_text(encoding='utf-8'))
    deals = {d['id']: d for d in data['deals']}
    for did, old, new in todo:
        assert list(deals[did].get('themes') or []) == old, f'{did}: темы изменились с начала прогона'
        if new:
            deals[did]['themes'] = new
        else:
            deals[did].pop('themes', None)
    with open(BASE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print(f'Записано: {len(todo)}.')


if __name__ == '__main__':
    main('--write' in sys.argv)
