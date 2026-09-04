# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g303803bc` («Twiga приобрела 60% в digital-агентстве «Апрель»»,
закрыта, 2023-05-15) — дочитывание нашло структуру владения до сделки,
обещание сохранить бренд и команду, и независимые комментарии рынка.

Проверено (по докладу саб-агента, дословные цитаты):
- kommersant.ru/doc/5985458 (источник карточки, перепрочитан
  полностью): «до сделки ООО «Агентство "Апрель"» принадлежало на
  60,75% Всеволоду Шеховцеву и на 39,25% — Сергею Кокареву»; «"Мы
  надеемся, что "Апрель" станет важной частью нашей PR-SMM-вертикали",
  — добавил управляющий директор Twiga Сергей Оганджанян»; гендиректор
  PR Development Алла Аксёнова — «в этой связи хорошим вариантом для
  сохранения бизнеса и команд становится консолидация».
- adindex.ru/news/releases/2023/05/15/312621.phtml (пресс-релиз):
  «"Апрель" останется независимым в принятии решений на уровне
  агентства и сохранит сотрудников», продолжит работу под своим
  именем; «в PR-SMM-вертикали будет свыше 100 сотрудников».
- adpass.ru/aprel-prodalsya-v-mae-twiga-konsolidirovala-ubytochnoe-
  agentstvo/: скептический комментарий рынка — «"Апрель" обслуживал в
  основном ушедшие из России западные бренды и не даст Twiga новых
  клиентов».

НЕ ВНЕСЕНО: (1) юридический/финансовый консультант, механизм оплаты
(единовременно/траншами), опцион на оставшиеся 40% — ноль по всем
проверенным источникам (Коммерсантъ, AdIndex, ADPASS); (2) финансовые
показатели «Апреля» за 2023-2025 годы — саб-агент получил их только
через агрегатор audit-it.ru без подтверждения дословной цитатой
первички, не вносятся; (3) состав учредителей ООО «Агентство "Апрель"»
по открытому реестру на 2026 год не показывает Twiga среди владельцев
(только Шеховцев, Кокарев и с декабря 2025 года Терегулова Т.В.) — это
не повод сомневаться в самой сделке (она подтверждена тремя
независимыми изданиями с прямыми цитатами руководителей ОБЕИХ сторон
в момент закрытия), а вероятный предел бесплатного агрегатора
(доля Twiga может держаться через непубличную/номинальную структуру);
не вносится в карточку без дополнительной проверки платным реестром.

Запуск: python3 pipeline/fix_twiga_april_fullscan.py
        python3 pipeline/fix_twiga_april_fullscan.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g303803bc'

OLD_ECO_SHARE = '—'
NEW_ECO_SHARE = (
    'До сделки ООО «Агентство «Апрель»» принадлежало на 60,75% '
    'Всеволоду Шеховцеву и на 39,25% — Сергею Кокареву.'
)

OLD_LAW_TERMS = '—'
NEW_LAW_TERMS = (
    '«Апрель» останется независимым в принятии решений на уровне '
    'агентства и сохранит сотрудников, продолжив работу под своим '
    'именем.'
)

OLD_ECO_CONTEXT = (
    'Twiga Communication Group приобрела 60% digital-агентства '
    '«Апрель». Раньше «Апрель» продвигал зарубежные бренды Estee '
    'Lauder, Red Bull, Audi, Porsche и другие.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' Управляющий директор Twiga Сергей Оганджанян '
    'рассчитывает, что «Апрель» станет важной частью PR-SMM-вертикали '
    'группы, где после сделки работает свыше 100 сотрудников. Рынок '
    'воспринял покупку неоднозначно: гендиректор PR Development Алла '
    'Аксёнова считает консолидацию хорошим способом сохранить бизнес и '
    'команды, а другие комментаторы отмечали, что «Апрель» обслуживал '
    'в основном ушедшие из России западные бренды и не даст Twiga '
    'новых клиентов.'
)

OLD_SRC = [['Коммерсантъ', 'https://www.kommersant.ru/doc/5985458']]
NEW_SRC = OLD_SRC + [
    ['AdIndex', 'https://adindex.ru/news/releases/2023/05/15/312621.phtml'],
    ['ADPASS', 'https://adpass.ru/aprel-prodalsya-v-mae-twiga-konsolidirovala-ubytochnoe-agentstvo/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['share'] == OLD_ECO_SHARE
    assert deal['law']['terms'] == OLD_LAW_TERMS
    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== eco.share: станет ===')
    print(NEW_ECO_SHARE)
    print('\n=== law.terms: станет ===')
    print(NEW_LAW_TERMS)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['eco']['share'] = NEW_ECO_SHARE
        deal['law']['terms'] = NEW_LAW_TERMS
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
