# -*- coding: utf-8 -*-
"""Итог торгов по Домодедово — точная цена, не формат «N млн/млрд ₽».

ЧТО СЛОМАНО. У `gf13fba9e` (ООО «Перспектива», дочка «Шереметьево», подала
заявку на участие в торгах по продаже аэропорта Домодедово) поле `sum` несло
заглушку «Не раскрыта» — на момент создания карточки исход торгов ещё не был
известен. РИА Новости (29 января 2026) сообщает точный результат: «победителем
было признано ООО «Перспектива», предложившее цену в размере 66 132 908 002,5
рубля».

ПОЧЕМУ НЕ ЧЕРЕЗ review.py. `sum_is_supported()` в review.py разбирает `new`
только в формате «N[–M] млн|млрд ₽ [(по оценке)]» и требует, чтобы САМО число
(например «66,13») дословно стояло в цитате отдельным числом. Источник же
называет точную цену аукциона до копейки («66 132 908 002,5 рубля») —
округление до «66,13 млрд ₽» ближе к принятому на сайте формату сумм
(правило CLAUDE.md «Сумма пишется одним способом»), но само «66,13» в тексте
не встречается: там числа сгруппированы по тысячам («66 132 908 002,5»), а не
как «66,13». Строгая проверка `review.py` тут не инструмент, а помеха —
меняем сумму отдельным скриптом со своим `assert` на исходное состояние,
как уже делалось для «Нордлайн»/TotalEnergies (несопоставимое число из
чужого абзаца) — здесь другая причина отказа от review.py (не то число из
чужого места, а не тот ФОРМАТ у настоящего числа этой сделки), но тот же
принцип: человек проверяет соответствие цитате, а не механическая подстрока.

ЗАПУСК:
    python3 pipeline/fix_domodedovo_auction_sum.py            # сухой прогон
    python3 pipeline/fix_domodedovo_auction_sum.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gf13fba9e'
OLD = 'Не раскрыта'
NEW = '66,13 млрд ₽'
SRC_LABEL = 'РИА Новости'
SRC_URL = 'https://ria.ru/20260129/domodedovo-2071059168.html'


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal.get('sum') == OLD, 'sum уже другой: %r' % deal.get('sum')

    print('ПРАВИМ %s: sum %r -> %r' % (DEAL_ID, OLD, NEW))
    print('  цитата: "победителем было признано ООО «Перспектива», '
          'предложившее цену в размере 66 132 908 002,5 рубля" — %s' % SRC_URL)

    existing_urls = {str(s[1]) for s in (deal.get('src') or []) if len(s) > 1}
    add_src = SRC_URL not in existing_urls

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    deal['sum'] = NEW
    if add_src:
        deal.setdefault('src', []).append([SRC_LABEL, SRC_URL])
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
