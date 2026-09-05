# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g2dc1ba74` («Алексей Сагал через «Арнест» приобрел российские заводы
Ball по производству алюминиевых банок», октябрь 2022, Закрыта) —
судьба заводов после сделки (переименование, реорганизация) не
прослеживалась.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- interfax.ru/business/886448: новое название — «Арнест упаковочные
  решения»; «Изменения распространяются исключительно на фирменное
  наименование, при этом все реквизиты и адреса местонахождения
  остались без изменения» (переименование опубликовано 16 февраля
  2023 года);
- abn.agency/2024/08/27/kompaniya-arnest-upakovochnye-resheniya-zavershila-reorganizacziyu/:
  «ООО «АУР Всеволожск» присоединилось к ООО «Арнест Упаковочные
  Решения Наро-Фоминск»»; «ООО «АУР Ростов» присоединилось к ООО
  «Арнест Упаковочные Решения Наро-Фоминск»»; «предприятие во
  Всеволожске будет филиалом, а называться он будет Всеволожским
  филиалом ООО «Арнест Упаковочные Решения Наро-Фоминск»» — дата
  реорганизации 26 августа 2024 года.

НЕ ВНЕСЕНО: (1) финансовые показатели группы за 2023-2025 годы — сама
разведка нашла расходящиеся цифры между разными юрлицами группы (АО
«АУР» и ООО «...Наро-Фоминск»), без личной проверки каждой цифры
вносить нельзя; (2) запуск нового завода в Ульяновске (март 2024) и
линии по производству крышек (сентябрь 2024) — известны только по
поисковым снимкам, не по личному прочтению первоисточника, требуют
отдельной проверки; (3) юридические/финансовые консультанты сделки —
ни один источник их не называет; (4) написание держателя российских
юрлиц («АО «Оникс»» против «АО «Орикс»» в разных источниках) —
расхождение не разрешено, в карточку не вносится.

Запуск: python3 pipeline/fix_arnest_ball_rebrand_and_merger.py
        python3 pipeline/fix_arnest_ball_rebrand_and_merger.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g2dc1ba74'

OLD_LAW_STRUCT = (
    'В России Ball представлена тремя заводами, расположенными в '
    'Наро-Фоминске (Московская область), Всеволожске (Ленинградская '
    'область) и Аргаяше (Челябинская область).'
)
NEW_LAW_STRUCT = (
    OLD_LAW_STRUCT + ' В феврале 2023 года бизнес переименован в '
    '«Арнест упаковочные решения» — реквизиты и адреса не изменились. '
    '26 августа 2024 года заводы во Всеволожске и Ростове присоединены '
    'к головному юрлицу в Наро-Фоминске: Всеволожский завод стал '
    'филиалом объединённой компании.'
)

OLD_SRC = [
    ['Forbes', 'https://www.forbes.ru/biznes/493935-kupivsij-zavody-amerikanskoj-ball-biznesmen-za-tri-mesaca-otbil-20-ot-summy-sdelki'],
    ['РБК (Кавказ)', 'https://kavkaz.rbc.ru/kavkaz/freenews/632c1ce19a7947fb06f8222f'],
]
NEW_SRC = OLD_SRC + [
    ['Интерфакс', 'https://www.interfax.ru/business/886448'],
    ['ABN.Agency', 'https://abn.agency/2024/08/27/kompaniya-arnest-upakovochnye-resheniya-zavershila-reorganizacziyu/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['struct'] == OLD_LAW_STRUCT
    assert deal['src'] == OLD_SRC

    print('=== law.struct: станет ===')
    print(NEW_LAW_STRUCT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['law']['struct'] = NEW_LAW_STRUCT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
