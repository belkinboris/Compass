# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
gf87a65f7 («Потанин и Алекперов подали заявки на покупку 51%
Яндекса», май 2023, статус «Обсуждается») — тот же класс, что уже
находили у S8 Capital/«Аквариус» и БКС/«Форштадт»: заявленные
кандидаты в итоге НЕ стали покупателями, но здесь причина отказа
названа прямо и документирована независимо, а не осталась
предположением.

Проверено лично прямым WebFetch (Meduza,
https://meduza.io/feature/2023/05/21/putin-soglasoval-spisok-pokupateley-rossiyskogo-kuska-yandeksa-kontrolnyy-paket-razdelit-konsortsium-rossiyskih-milliarderov):
17 мая 2023 года Путин согласовал список из четырёх покупателей —
Потанин («Интеррос»), Мордашов («Северсталь»), Алекперов («Лукойл»),
банк ВТБ — «Контрольный пакет... будет примерно поровну поделен между
всеми участниками»; фонд менеджеров с участием Алексея Кудрина
задумывался «коллективной заменой Воложу».

Проверено лично прямым WebFetch (Meduza,
https://meduza.io/feature/2023/06/23/sdelka-po-prodazhe-rossiyskoy-chasti-yandeksa-okazalas-na-grani-sryva-sovet-direktorov-ne-hochet-otdavat-kompaniyu-milliarderam-pod-zapadnymi-sanktsiyami):
«все участники «консорциума миллиардеров» находятся под теми или
иными западными санкциями» — совет директоров Yandex N.V. изначально
настаивал, «чтобы среди покупателей не было тех, кто находится под
санкциями», и это стало прямой причиной, по которой состав ИЮЛЯ 2024
года (`gd73fd825`, ЗПИФ «Консорциум.Первый») оказался полностью
другим: ни Потанина, ни Алекперова, ни Мордашова, ни ВТБ среди
итоговых пайщиков нет вовсе.

НЕ ВКЛЮЧЕНО: осенний 2023 года промежуточный вариант консорциума
(Таврин, Нечаев, Дмитриев, ВТБ, «Газфонд») — тоже не реализовался, но
это отдельный, третий по счёту состав, для отдельной оценки в рамках
ЭТОЙ карточки избыточен (сама карточка про майскую заявку, а не про
весь процесс); интерес Виктора Рашникова к небольшому пакету — эпизод,
не подтверждённый прямым WebFetch (только через пересказ), не
вносится без отдельной проверки.

Запуск: python3 pipeline/fix_yandex_potanin_alekperov_rejected_by_board.py
        python3 pipeline/fix_yandex_potanin_alekperov_rejected_by_board.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gf87a65f7'

OLD_ECO_CONTEXT = (
    'Потанин находится под санкциями Великобритании и США, Абрамович '
    'ограничен со стороны ЕС и Британии. Последняя также «присматривается» '
    'к Алекперову'
)
NEW_ECO_CONTEXT = (
    'Потанин находится под санкциями Великобритании и США, Абрамович '
    'ограничен со стороны ЕС и Британии. Последняя также «присматривается» '
    'к Алекперову. 17 мая 2023 года Путин согласовал список из четырёх '
    'покупателей — Потанин, Мордашов, Алекперов и банк ВТБ, — но совет '
    'директоров Yandex N.V. отверг этот состав именно из-за санкций: '
    '«все участники "консорциума миллиардеров" находятся под теми или '
    'иными западными санкциями», а совет изначально настаивал на '
    'покупателях без санкционных ограничений. В итоге, когда сделка '
    'закрылась в июле 2024 года (см. карточку о продаже консорциуму '
    '«Консорциум.Первый»), состав покупателей оказался полностью иным — '
    'ни Потанина, ни Алекперова, ни Мордашова, ни ВТБ среди них нет.'
)

NEW_SRC = [
    ['Meduza', 'https://meduza.io/feature/2023/05/21/putin-soglasoval-spisok-pokupateley-rossiyskogo-kuska-yandeksa-kontrolnyy-paket-razdelit-konsortsium-rossiyskih-milliarderov'],
    ['Meduza', 'https://meduza.io/feature/2023/06/23/sdelka-po-prodazhe-rossiyskoy-chasti-yandeksa-okazalas-na-grani-sryva-sovet-direktorov-ne-hochet-otdavat-kompaniyu-milliarderam-pod-zapadnymi-sanktsiyami'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
