# -*- coding: utf-8 -*-
"""Восемь карточек несли `date`=«2022» (заглушка компактного импорта), хотя
единственный источник каждой сам датирован 2023 годом и описывает событие
как происходящее СЕЙЧАС, а не задним числом — дата в заголовке статьи
совпадает с временем действия глагола («заинтересовалась», «получил
разрешение», «расширяют», «обойдется»), а не отсылает к более раннему факту:

- g5cb74803 (VK/«Учи.ру»): interfax.ru — «10:30, 20 февраля 2023 VK
  выкупил 75% образовательной платформы "Учи.ру"...». Точный день назван.
- g0c19cd78 (Агросила/Пермская птицефабрика): kommersant.ru/doc/5841450 —
  «22.02.2023... холдинг «Продо» ВНОВЬ готовится продать Пермскую
  птицефабрику» — слово «вновь» показывает, что это новый, более поздний
  раунд due diligence, а не тот же процесс, что мог начаться в 2022 году;
  единственный источник карточки датирует именно эту стадию февралём 2023.
- gb1e062d2 (RBI/EKE, San Gally Park): kommersant.ru/doc/5824989, дата в
  заголовке «13.02.2023, 00:41».
- g87234072 (АФК «Система»/Allur, завод VW): kommersant.ru/doc/5810668,
  «06.02.2023, 00:26». Упоминание «завод простаивает с марта 2022 года» —
  факт истории самого завода, а не дата переговоров; в `eco.rationale`
  вдобавок протекла служебная пометка роли «(АФК «Система» и казахстанский
  автопроизводитель Allur (потенциальные покупатели))» — снята тем же
  прогоном.
- g8ea21d1b (СИБУР/Solvay, «РусВинил»): kommersant.ru/doc/5811024,
  «06.02.2023, 14:20».
- g412f413c (ГК О3/КиилтоКлин): kommersant.ru/doc/5795855, «31.01.2023,
  11:30».
- gbf1e6917 (Глеб Фетисов/картофельные хозяйства): kommersant.ru/doc/5797756,
  «01.02.2023, 01:16».
- g6ef203a1 (Виктор Харитонин/«Кама»): kommersant.ru/doc/5799156,
  «03.02.2023, 00:49».

Для сравнения: третья проверенная в этой партии карточка (gb6b5625e,
Лисин/Таганрогский порт) источник, хоть и опубликован в марте 2023 года,
прямо пишет «Сделка состоялась в 2022 году» — там год не менялся.

Почему не через review.py: перенос в другой год не поддержан
`date_is_supported()` намеренно (см. прецедент
`fix_osnova_sviblovo_date.py`); снятие протёкшей пометки роли — не перенос
факта из цитаты, а вычищение уже присутствующего в базе текста (см.
`strip_leaked_role_tags_2022.py`).

Запуск: python3 pipeline/fix_batch5_wrong_years.py
        python3 pipeline/fix_batch5_wrong_years.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

DATES = {
    'g5cb74803': '2023-02-20',
    'g0c19cd78': '2023-02-22',
    'gb1e062d2': '2023-02-13',
    'g87234072': '2023-02-06',
    'g8ea21d1b': '2023-02-06',
    'g412f413c': '2023-01-31',
    'gbf1e6917': '2023-02-01',
    'g6ef203a1': '2023-02-03',
}

TAG = ' (АФК «Система» и казахстанский автопроизводитель Allur (потенциальные покупатели))'
OLD_RATIONALE = (
    'Переговоры АФК «Система» совместно с казахстанским автопроизводителем '
    'Allur о приобретении завода Volkswagen в Калуге. АФК «Система» '
    'планирует создать машиностроительный холдинг за счет данной сделки. '
    'Завод находится в режиме простоя с марта 2022 года и имеет мощность '
    '225 тыс. автомобилей в год.' + TAG
)
NEW_RATIONALE = OLD_RATIONALE[:-len(TAG)]


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    cards = {d['id']: d for d in data['deals']}
    todo_dates = {}
    for cid, new in DATES.items():
        card = cards[cid]
        if card['date'] == new:
            print('УЖЕ ПРИМЕНЕНО %s (дата)' % cid)
            continue
        assert card['date'] == '2022', '%s: дата уже другая' % cid
        todo_dates[cid] = new
        print('ПРАВИМ  %s date: «2022» -> «%s»' % (cid, new))

    system = cards['g87234072']
    todo_tag = False
    if system['eco']['rationale'] == NEW_RATIONALE:
        print('УЖЕ ПРИМЕНЕНО g87234072 (пометка)')
    else:
        assert system['eco']['rationale'] == OLD_RATIONALE, 'g87234072: rationale уже другое'
        todo_tag = True
        print('ПРАВИМ  g87234072 eco.rationale: снята протёкшая пометка роли')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    for cid, new in todo_dates.items():
        cards[cid]['date'] = new
    if todo_tag:
        system['eco']['rationale'] = NEW_RATIONALE
    if todo_dates or todo_tag:
        json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
