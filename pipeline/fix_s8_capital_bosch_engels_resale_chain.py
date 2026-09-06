# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`gafda8e29` («S8 Capital приобрел активы Bosch в Энгельсе», апрель
2023, Закрыта) — актив с тех пор дважды перепродан, а производство
сначала встало, потом перезапустилось под новым брендом.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- mergers.ru/news/Severgrupp-Mordashova-prodala-OOO-Jengels-Jelektroinstrumenty-byvshij-zavod-Bosch-85439:
  «В апреле 2023-го бизнес приобрел холдинг S8 Capital Армена
  Саркисяна» (подтверждает уже стоящую в карточке дату и покупателя);
  «Осенью 2024-го S8 Capital перепродал бизнес Bosch «Севергрупп»»
  (Алексея Мордашова), покупателем в реестре выступило ООО «Интернет
  проекты»; на 2023 год в «Энгельс Электроинструменты» числились 159
  сотрудников;
- comnews.ru/content/244038/...: «25 февраля 2026 г. ООО "Энгельс
  Электроинструменты" вошло в состав активов АО "Е1 Групп"» — третий
  владелец; «Сейчас предприятие состоит из 210 сотрудников, 96%
  которых были сотрудниками международного концерна Bosch»; «На пике
  развития предприятие выпускало 1,5 млн единиц инструмента в год»;
  производство под брендом «Энгельс» возобновлено «с августа 2025 г.» —
  то есть между продажей «Севергрупп» (осень 2024) и перезапуском
  (август 2025) завод, судя по всему, простаивал.

НЕ ВНЕСЕНО: (1) финансовые показатели 2023 года (выручка 632 млн ₽,
убыток 206 млн ₽) — встретились только в агрегированной выдаче поиска,
не в дословно прочитанной странице; (2) причина, по которой
«Севергрупп» решила продать актив меньше чем через год после покупки —
ни один источник не объясняет.

Запуск: python3 pipeline/fix_s8_capital_bosch_engels_resale_chain.py
        python3 pipeline/fix_s8_capital_bosch_engels_resale_chain.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gafda8e29'

OLD_ECO_CONTEXT = (
    'В июле 2022 года S8 Capital купил активы американского производителя '
    'лифтов Otis. Холдинг получил контроль над заводом компании в '
    'Санкт-Петербурге; сумма той сделки могла составить 3 млрд ₽. '
    'Производство лифтов на заводе возобновили под брендом «Метеор».'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' Сам энгельсский завод Bosch с тех пор дважды '
    'сменил владельца: осенью 2024 года S8 Capital перепродал его группе '
    '«Севергрупп» Алексея Мордашова, а 25 февраля 2026 года завод перешёл '
    'к холдингу «Е1 Групп». Производство электроинструмента под новым '
    'брендом «Энгельс» возобновилось в августе 2025 года; сейчас на заводе '
    '210 сотрудников, 96% из них — бывшие работники Bosch, а на пике '
    'при немцах завод выпускал 1,5 млн единиц инструмента в год.'
)

OLD_SRC = [
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/5965150'],
]
NEW_SRC = OLD_SRC + [
    ['Mergers.ru', 'https://mergers.ru/news/Severgrupp-Mordashova-prodala-OOO-Jengels-Jelektroinstrumenty-byvshij-zavod-Bosch-85439'],
    ['ComNews', 'https://www.comnews.ru/content/244038/2026-03-02/2026-w10/1010/engels-elektroinstrumenty-voshel-sostav-aktivov-kholdinga-e1-grupp'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
