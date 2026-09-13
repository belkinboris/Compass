# -*- coding: utf-8 -*-
"""G7 (PRODUCT_ROADMAP.md) — первое чтение трёх карточек, которые попали в
базу мимо обычного притока (`added: None`, ни разу не помеченных
`reviewed`) и потому выпадали из всех трёх уровней очереди дочитывания
(они считают возраст от `added`). Найдено прямым запросом «from_ingest без
reviewed» 13 сентября 2026 — таких карточек 6, в этом заходе прочитаны 3.

- `g0d72e1d5` (ООО «Гранит»/Елена Некрасова купила БЦ «Константа» у Raven
  Russia): проверено лично прямым WebFetch двух статей Коммерсанта —
  независимая оценка стоимости (NF Group, Станислав Бибик), причина
  продажи (непрофильный актив, Raven Russia фокусируется на складах) и
  личность покупателя (Елена Некрасова, жена члена Совета Федерации,
  также владеет структурами «Лидер Групп»).
- `gaec5231e` («Велес Менеджмент» купил портфель ТЦ «Мега» у
  Газпромбанка): проверено лично прямым WebFetch pravo.ru — состав
  портфеля (14 одноимённых торговых центров в 12 регионах России).
  НЕ ТРОНУТО намеренно: юридический механизм сделки (передача управления
  или продажа) источники не проясняют однозначно — карточка уже честно
  отражает это расхождение в `eco.context`, и решать классификацию по
  косвенным признакам не стал.
- `g04edfc17` («Дедал» получил долю Tawazun (36%) в Aurus): проверено
  лично прямым WebFetch того же источника, что уже стоит в `src`
  (kommersant.ru/doc/8211090) — сумма сделки «Газпром Тех»/Aurus 2025
  года (12–13 млрд ₽), которой в карточке не было. Бенефициар «Дедала» и
  причина выхода Tawazun остаются не установлены ни одним источником —
  карточка это уже честно говорит, новых утверждений не добавлено.

Запуск:
    python3 pipeline/fix_g7_first_read_batch1.py            # сухой прогон
    python3 pipeline/fix_g7_first_read_batch1.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

# --- g0d72e1d5: ООО «Гранит» / БЦ «Константа» ---
CID1 = 'g0d72e1d5'
OLD_VAL_1 = '—'
NEW_VAL_1 = (
    'Стоимость бизнес-центра могла составить 1 млрд рублей, оценивает '
    'партнёр NF Group Станислав Бибик. Ранее «Константа» в разное время '
    'предлагалась на рынке за 0,8–1 млрд руб.'
)
OLD_RATIONALE_1 = '—'
NEW_RATIONALE_1 = (
    'Raven Russia объясняет продажу тем, что компания фокусируется на '
    'складских проектах, а «Константа» была непрофильным активом.'
)
OLD_CONTEXT_1 = (
    'Сделка закрыта в ноябре 2024 года. Балансодержателем бизнес-центра '
    'выступало ООО «Петроэстейт» — оно перешло в собственность ООО '
    '«Гранит». Raven Russia называет актив непрофильным: компания '
    'фокусируется на складских проектах.'
)
NEW_CONTEXT_1 = OLD_CONTEXT_1 + (
    ' Покупатель, ООО «Гранит», подконтролен Елене Некрасовой, супруге '
    'члена Совета Федерации Александра Некрасова; она также владеет '
    'несколькими структурами застройщика жилья «Лидер Групп».'
)
NEW_SOURCES_1 = [
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/7310478'],
]

# --- gaec5231e: «Велес Менеджмент» / ТЦ «Мега» ---
CID2 = 'gaec5231e'
OLD_SHARE_2 = '—'
NEW_SHARE_2 = (
    'В группу входят УК «Мега» и 14 одноимённых торговых центров в '
    '12 регионах России.'
)

# --- g04edfc17: «Дедал» / Aurus ---
CID3 = 'g04edfc17'
OLD_CONTEXT_3 = (
    'Фонд Tawazun (ОАЭ) получил 36% акций Aurus в феврале 2019 года, '
    'вложив 110 млн евро; соглашение подписали в Абу-Даби на выставке '
    'IDEX-2019. В декабре 2024 года эта доля перешла к российской '
    'компании «Дедал», её бенефициар не установлен. Летом 2025 года она '
    'вместе с частью пакета ФГУП «НАМИ» вошла в контрольные 51% Aurus, '
    'которые купила «Газпром Тех».'
)
NEW_CONTEXT_3 = OLD_CONTEXT_3 + ' Сумма этой сделки оценивается в 12–13 млрд ₽.'


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    deals = {d['id']: d for d in data['deals']}

    c1 = deals[CID1]
    c2 = deals[CID2]
    c3 = deals[CID3]

    already_applied = (c1['eco']['val'] == NEW_VAL_1
                        and c1['eco']['rationale'] == NEW_RATIONALE_1
                        and c1['eco']['context'] == NEW_CONTEXT_1
                        and c2['eco']['share'] == NEW_SHARE_2
                        and c3['eco']['context'] == NEW_CONTEXT_3)
    if already_applied:
        print('Уже применено — нечего делать (скрипт идемпотентен).')
        return

    assert c1['eco']['val'] == OLD_VAL_1
    assert c1['eco']['rationale'] == OLD_RATIONALE_1
    assert c1['eco']['context'] == OLD_CONTEXT_1
    assert c2['eco']['share'] == OLD_SHARE_2
    assert c3['eco']['context'] == OLD_CONTEXT_3

    existing_urls_1 = {u for _, u in c1['src']}
    to_add_1 = [pair for pair in NEW_SOURCES_1 if pair[1] not in existing_urls_1]

    print('Правки:')
    print('  %s: eco.val, eco.rationale, eco.context (+бенефициар), src +%d'
          % (CID1, len(to_add_1)))
    print('  %s: eco.share (+состав портфеля)' % CID2)
    print('  %s: eco.context (+сумма сделки Газпром Тех/Aurus)' % CID3)

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    c1['eco']['val'] = NEW_VAL_1
    c1['eco']['rationale'] = NEW_RATIONALE_1
    c1['eco']['context'] = NEW_CONTEXT_1
    c1['src'].extend(to_add_1)

    c2['eco']['share'] = NEW_SHARE_2

    c3['eco']['context'] = NEW_CONTEXT_3

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
