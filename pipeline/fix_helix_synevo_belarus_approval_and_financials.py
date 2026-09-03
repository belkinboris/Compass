# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`ge6349e21` («Хеликс приобрела Synevo в Беларуси у Medicover», закрыта
10.02.2023) — `law.appr` и `eco.target_fin` пустовали, хотя механизм
согласования (запретный список правительства Беларуси) и финансы
предмета названы в открытых источниках.

Проверено лично прямым WebFetch:
- director.by, https://director.by/home/sobytiya-delovoj-zhizni/8733-rossijskaya-helix-vse-taki-kupila-set-laboratorij-sinevo:
  «постановлением Совмина №782 от 16 ноября 2022 г.» «Синэво» и
  «Недвижимость Восток» были включены в перечень юрлиц, иностранным
  участникам которых запрещено распоряжаться акциями без разрешения
  властей; «в обновленном документе, который был утвержден 23 января,
  компании уже нет» — то есть исключены из перечня непосредственно
  перед закрытием сделки.
- Коммерсантъ, https://www.kommersant.ru/doc/5824931: выручка
  Medicover в Беларуси за 2021 год — «€21,7 млн», за девять месяцев
  2022 года — «€15,3 млн»; сеть — «58 пунктами в 23 городах»; по
  данным годового отчёта Medicover за 2021 год — 555 сотрудников,
  свыше 3000 анализов в сутки.

НЕ ВНЕСЕНО: точный механизм/переговорщик, убедивший власти исключить
компанию из перечня, — источник сам признаёт неясность («очевидно
договаривающимся сторонам удалось каким-то образом убедить власти»);
номер декрета проверен только по одному источнику (director.by), не
перепроверен по pravo.by/etalonline.by; ребрендинг в Helix и данные
2024-2026 годов — по докладу саб-агента, не перепроверены мной лично
прямым WebFetch в этом прогоне.

Запуск: python3 pipeline/fix_helix_synevo_belarus_approval_and_financials.py
        python3 pipeline/fix_helix_synevo_belarus_approval_and_financials.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'ge6349e21'

OLD_LAW_APPR = 'Публично не сообщалось'
NEW_LAW_APPR = (
    'Постановлением Совета министров Беларуси №782 от 16 ноября 2022'
    ' года «Синэво» и «Недвижимость Восток» были включены в перечень'
    ' юрлиц, иностранным участникам которых запрещено распоряжаться'
    ' акциями без разрешения властей; в обновлённом перечне от 23'
    ' января 2023 года компаний в списке уже не было — исключены'
    ' непосредственно перед закрытием сделки.'
)

OLD_ECO_TARGET_FIN = '—'
NEW_ECO_TARGET_FIN = (
    'Выручка Medicover в Беларуси за 2021 год составила €21,7 млн, за'
    ' девять месяцев 2022 года — €15,3 млн. Сеть насчитывала 58'
    ' пунктов в 23 городах; по данным годового отчёта Medicover за'
    ' 2021 год — 555 сотрудников, свыше 3000 анализов в сутки.'
)

NEW_SRC = [
    ['director.by', 'https://director.by/home/sobytiya-delovoj-zhizni/8733-rossijskaya-helix-vse-taki-kupila-set-laboratorij-sinevo'],
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/5824931'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['appr'] == OLD_LAW_APPR
    assert deal['eco']['target_fin'] == OLD_ECO_TARGET_FIN

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== law.appr: станет ===')
    print(NEW_LAW_APPR)
    print('\n=== eco.target_fin: станет ===')
    print(NEW_ECO_TARGET_FIN)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['law']['appr'] = NEW_LAW_APPR
        deal['eco']['target_fin'] = NEW_ECO_TARGET_FIN
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
