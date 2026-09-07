# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), две карточки:
`c151696b4`, `c011c4ee1` — новые факты вне кэша притока, проверено
ЛИЧНО прямым WebFetch. Третья карточка захода, `c220a77df` (Mars/завод
соусов в Луховицах), прочитана — ничего нового о судьбе завода не
нашлось ни в одном источнике, оставлена как честная неопределённость.

1) c151696b4 (Национализация Ловозерского ГОК). Проверено ЛИЧНО прямым
   WebFetch: kommersant.ru/doc/5938876 (15.04.2023, тот же информпоод,
   что и источник карточки) — «ФАС через суд добилась признания
   недействительными сделок, по которым офшоры приобрели эти доли в
   2014 году»; «с 13 апреля... в собственности федерального органа
   находятся 100% долей». `status` проставлен «Закрыта» (слово
   «перешл(о)» есть в STATUS_WORDS). Дальнейшая судьба: sialuch.com
   (официальный сайт АО «НИИ НПО «ЛУЧ»), 18.08.2023 — «Распоряжением
   Правительства Российской Федерации №2198-р от 15 августа 2023 года
   в качестве имущественного взноса Российской Федерации передана в
   Госкорпорацию «Росатом» находящаяся в федеральной собственности
   доля в размере 25,03%» — то есть доля, только что отсуженная у
   Пестрикова и Кирпичева, в тот же год ушла Росатому. Дополнено
   `eco.context`.

2) c011c4ee1 (GeoPost ведёт переговоры о продаже DPD Rus, 2023).
   Проверено ЛИЧНО прямым WebFetch: interfax.com/newsroom/top-
   stories/94328 (07.09.2023) — гендиректор DPD в России Николай
   Войнов ПРЯМО ОПРОВЕРГ переговоры о продаже конкурентам («GeoPost in
   principal did not consider and is not considering competitors as
   partners of DPD in Russia»). Дальше сюжет получил отдельный, более
   серьёзный поворот: retail.ru (23.10.2024) — Арбитражный суд Москвы
   запретил любые сделки с акциями АО «ДПД Рус» — обеспечительная мера
   по делу о банкротстве сети постаматов PickPoint (единственный
   акционер ДПД Рус, Armadillo Holding GmbH, тоже совладелец PickPoint
   с долгом 2,6 млрд ₽). Исход заседания 2 апреля 2025 года не найден
   ни в одном источнике. `status` НЕ меняется (компания отрицает сам
   факт переговоров, а не подтверждает срыв сделки словом из
   STATUS_WORDS) — дополнен только `eco.context`.

Запуск: python3 pipeline/fix_monthly_2026_09_07_lovozero_dpd.py
        python3 pipeline/fix_monthly_2026_09_07_lovozero_dpd.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

LZ_ID = 'c151696b4'
LZ_OLD_STATUS = None
LZ_NEW_STATUS = 'Закрыта'
LZ_OLD_CONTEXT = (
    'Росимущество установило полный контроль над стратегическим '
    'Ловозерским ГОК — ключевым поставщиком сырья для магниевого '
    'завода в Соликамске.'
)
LZ_NEW_CONTEXT = (
    LZ_OLD_CONTEXT + ' Впоследствии, распоряжением Правительства РФ '
    '№2198-р от 15 августа 2023 года, доля в Ловозерском ГОК в размере '
    '25,03% передана в Госкорпорацию «Росатом» в качестве '
    'имущественного взноса Российской Федерации.'
)

DPD_ID = 'c011c4ee1'
DPD_OLD_CONTEXT = (
    'В отчёте за 2022 год GeoPost сообщила, что обесценила активы '
    'российской «дочки» на €149 млн.'
)
DPD_NEW_CONTEXT = (
    DPD_OLD_CONTEXT + ' Сама компания эти переговоры опровергла: '
    'гендиректор DPD в России Николай Войнов заявил, что GeoPost не '
    'рассматривала и не рассматривает конкурентов в качестве партнёров '
    'для передачи бизнеса в России. Позже сюжет получил другой '
    'поворот: в октябре 2024 года Арбитражный суд Москвы запретил '
    'любые сделки с акциями АО «ДПД Рус» — обеспечительная мера по '
    'делу о банкротстве сети постаматов PickPoint (единственный '
    'акционер ДПД Рус, Armadillo Holding GmbH, был также совладельцем '
    'PickPoint с долгом 2,6 млрд ₽).'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    lz = by_id[LZ_ID]
    dpd = by_id[DPD_ID]

    assert lz.get('status') == LZ_OLD_STATUS
    assert lz['eco']['context'] == LZ_OLD_CONTEXT
    assert dpd['eco']['context'] == DPD_OLD_CONTEXT

    print('=== c151696b4: status ===', LZ_NEW_STATUS)
    print('=== c151696b4: eco.context ===')
    print(LZ_NEW_CONTEXT)
    print()
    print('=== c011c4ee1: eco.context ===')
    print(DPD_NEW_CONTEXT)

    if write:
        lz['status'] = LZ_NEW_STATUS
        lz['eco']['context'] = LZ_NEW_CONTEXT
        dpd['eco']['context'] = DPD_NEW_CONTEXT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
