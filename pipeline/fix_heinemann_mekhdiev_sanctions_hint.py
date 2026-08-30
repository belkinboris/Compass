# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g91d021c6
(Gebr. Heinemann продала магазины Duty free в Шереметьево и Домодедово
Аразу Мехдиеву) — причина продажи не была отражена вовсе. Проверено
лично прямым WebFetch pravo.ru и Коммерсанта.

`eco.rationale` (новое поле) — гипотеза юридического издания о причине.
Дословно (pravo.ru): «Действия немецкого холдинга могут быть связаны с
новыми ограничениями из 16-го пакета санкций ЕС» — формулировка
ГИПОТЕТИЧЕСКАЯ («могут быть связаны»), сама Gebr. Heinemann решение не
комментировала («Представитель Gebr. Heinemann на запрос РБК не
ответил»). Не утверждается как факт, только как названная изданием
версия.

НЕ ВКЛЮЧЕНО: точная дата закрытия (день) — ни один из ~9 проверенных
источников её не называет, все говорят только «в конце апреля 2024
года» (это уже стоит в `extra`); сумма — подтверждена нераскрытой
независимо («их сумма неизвестна», Коммерсантъ), в `sum` уже стоит
«Не раскрыта»; консультанты и согласования ФАС — не найдены ни в одном
источнике; находка о продаже Виталию Бавину в августе 2025 года — НЕ
ВКЛЮЧЕНА: юрлицо в этой новости («ООО «Трэвел ритейл Шереметьево»»)
формально отличается от юрлиц карточки («ТРЭВЕЛ РИТЕЙЛ ДОМОДЕДОВО»,
«ИМПЕРИАЛ ДЬЮТИ ФРИ»), и личная проверка (checko.ru — 403, tadviser —
404, retail.ru — материал не найден) не подтвердила связь между ними;
без подтверждения включать в карточку нельзя — кандидат на будущую
проверку, не на запись сейчас.

Запуск: python3 pipeline/fix_heinemann_mekhdiev_sanctions_hint.py
        python3 pipeline/fix_heinemann_mekhdiev_sanctions_hint.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g91d021c6'

NEW_RATIONALE = (
    'Причина продажи публично не подтверждена самой Gebr. Heinemann '
    '(«Представитель Gebr. Heinemann на запрос РБК не ответил»). По '
    'версии pravo.ru: «Действия немецкого холдинга могут быть связаны '
    'с новыми ограничениями из 16-го пакета санкций ЕС» — гипотеза '
    'издания, не подтверждённый факт.'
)

NEW_SRC = [
    ['pravo.ru', 'https://pravo.ru/news/258030/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert 'rationale' not in deal['eco'], 'eco.rationale уже существует'
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.rationale (новое поле): станет ===')
    print(NEW_RATIONALE)
    print('\n=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['rationale'] = NEW_RATIONALE
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
