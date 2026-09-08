# -*- coding: utf-8 -*-
"""Месячная очередь, 8 сентября 2026 — карточка `cf9e8af73» (X5 Group
приобретает 70% в «Красном Яре» и «Слате», август 2022). Найдены два
факта, оба лично проверены прямым WebFetch.

1) Продавцы исходной сделки (70%, 2022 год) не были названы — источник
   X5.ru (пресс-релиз о завершающей сделке 2025 года) называет обоих:
   «Вячеслав Заяц» (совладелец «Слаты» и «ХлебСоли») и «Дмитрий Саенко»
   (совладелец «Красного Яра» и «Батона»). Добавлено в `extra`.

2) НЕ внесено в структурные поля (отдельная, более поздняя сделка —
   кандидат на свою карточку, записано в «Известные проблемы»
   CLAUDE.md): 5 марта 2025 года X5 закрыла сделку по выкупу ОСТАВШИХСЯ
   30% и стала 100%-м владельцем всех четырёх брендов (Красный Яр,
   Батон, Слата, ХлебСоль) — условие о выкупе остатка через три года
   было согласовано ещё в 2022-м. Личный WebFetch (x5.ru/en/news/
   x5-completes-acquisition-of-krasny-yar-and-slata/): «5 March 2025 –
   X5 Group… has closed a deal to acquire 100% of Krasny Yar, Baton,
   Slata and KhlebSol». Ребрендинг части магазинов «Красный Яр» в
   «Слату» уже идёт (malls.ru).

Поле `extra` не проходило вычитку — правка обычная.

Запуск:
    python3 pipeline/fix_x5_krasny_yar_slata_followup.py            # сухой прогон
    python3 pipeline/fix_x5_krasny_yar_slata_followup.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'
CARD_ID = 'cf9e8af73'

OLD_EXTRA = (
    'Покупатель получает 70% в каждой из двух групп — это более 226 '
    'магазинов в Красноярском крае, Хакасии, Туве, Иркутской области и '
    'Бурятии. Аналитики оценивали эти доли в 1,8–2,6 млрд ₽ и 2–3 млрд ₽ '
    'соответственно, сделка ожидала одобрения ФАС.'
)
NEW_EXTRA = OLD_EXTRA + (
    ' Продавцами выступили Вячеслав Заяц (совладелец «Слаты» и '
    '«ХлебСоли») и Дмитрий Саенко (совладелец «Красного Яра» и '
    '«Батона»).'
)


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}
    card = by_id[CARD_ID]

    assert card['extra'] == OLD_EXTRA, 'extra уже другой: %r' % (card['extra'],)

    print('extra: добавляются имена продавцов (X5.ru, пресс-релиз 2025 '
          'года)')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    card['extra'] = NEW_EXTRA

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
