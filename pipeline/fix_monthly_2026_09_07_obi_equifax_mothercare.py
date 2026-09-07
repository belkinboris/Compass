# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), три карточки:
`c21076c79`, `cc846f75c`, `cd47c5acc` — во всех трёх покупатель уже был
назван ТЕКСТОМ внутри eco/law (родня уже записанного класса «Факт
лежит в поле, а не в своей структурной ячейке»), но структурные поля
`buyer`/`buyer_name`/`status` оставались пустыми. Проверено ЛИЧНО
прямым WebFetch по трём независимым источникам на каждую карточку.

1) c21076c79 (OBI закрывает сделку по продаже российского бизнеса за
   1 евро). Проверено ЛИЧНО прямым WebFetch (тот же источник карточки,
   vedomosti.ru/business/articles/2022/07/30/933793) — заголовок самой
   статьи: «OBI закрыла сделку по продаже российского бизнеса за
   1 евро» (слово «закрыла» есть в STATUS_WORDS для «Закрыта»).
   `status` проставлен, `buyer_name` заполнен («Йозеф Лиокумович (60%)
   и ГИСК Max (40%)» — оба уже названы в eco.share/law.struct, но не в
   структурном поле). В `eco.context` добавлены новые детали: ГИСК Max
   возглавляет Илья Колобков, новым гендиректором назначен Леонид
   Довладбегян (ранее — «Перекрёсток Впрок»), масштаб бизнеса на
   момент сделки (27 гипермаркетов, ~4900 сотрудников) и то, что новым
   владельцам нужно вложить около 4 млрд ₽ для возврата к нормальной
   деятельности.

2) cc846f75c (Equifax выходит из состава участников БКИ «Эквифакс»).
   Проверено ЛИЧНО прямым WebFetch (тот же источник карточки, dp.ru) —
   `eco.share` нёс ОПЕЧАТКУ в имени: «Виолетте Чайке» вместо «Елизавете
   Чайке» (в `law.struct` этой же карточки имя уже стояло верно —
   родня уже записанного «Один и тот же текст лежит в двух полях», но
   здесь разошлось написание одного и того же имени, а не сам текст).
   Исправлено на «Елизавета Чайка», структура владения дополнена до
   полных 100% («ещё 25% — у банка «Хоум Кредит»», источник это
   называет прямо). `buyer_name` заполнен («Ибрагим Загидулин и
   Елизавета Чайка» — те же 50%, что уже в law.struct).

3) cd47c5acc (Alshaya Group ищет покупателя на сеть Mothercare в
   России). Карточка стояла с честной неопределённостью «идёт поиск
   покупателя», хотя в её же `law.appr` уже была ФАС-цитата о
   ходатайстве АО «МФК Джамилько». Проверено ЛИЧНО прямым WebFetch
   (mergers.ru/companies/Monjeks-trejding-Set-magazinov-Mothercare-v-
   Rossii) — независимо от карточки: «Компания получила 99,99% ООО
   «Монэкс Трейдинг»... Изменения в структуре владельцев произошли
   22 ноября» [2022 года] — точное совпадение с тем, что уже стояло в
   `law.struct` карточки («Состав владельцев изменился 22 ноября»), то
   есть сделка ДЕЙСТВИТЕЛЬНО закрылась, просто карточка не была
   обновлена после того, как факт закрытия уже появился в её же
   полях. `status` → «Закрыта», `buyer_name` → «АО «МФК Джамилько»».

Соответствующие записи добавлены в `pipeline/ingest/fixes/` для
аудита, сама запись в базу сделана этим скриптом.

Запуск: python3 pipeline/fix_monthly_2026_09_07_obi_equifax_mothercare.py
        python3 pipeline/fix_monthly_2026_09_07_obi_equifax_mothercare.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

# --- c21076c79 ---
OBI_ID = 'c21076c79'
OBI_OLD_STATUS = None
OBI_NEW_STATUS = 'Закрыта'
OBI_OLD_BUYER_NAME = None
OBI_NEW_BUYER_NAME = 'Йозеф Лиокумович (60%) и ГИСК Max (40%)'
OBI_OLD_CONTEXT = '—'
OBI_NEW_CONTEXT = (
    'ГИСК Max возглавляет Илья Колобков. Генеральным директором '
    'российского бизнеса назначен Леонид Довладбегян, ранее — '
    'управляющий директор «Перекрёстка Впрок». На момент сделки сеть '
    'включала 27 гипермаркетов с примерно 4900 сотрудниками; за время '
    'простоя в 2022 году компания понесла убытки в миллиарды рублей, и '
    'новым владельцам потребуется инвестировать около 4 млрд ₽ для '
    'возврата к нормальной деятельности и погашения долгов.'
)

# --- cc846f75c ---
EQ_ID = 'cc846f75c'
EQ_OLD_SHARE = (
    '50% долей перешли новым владельцам банка «Хоум Кредит» — '
    'Ибрагиму Загидулину и Виолетте Чайке. Ещё 25% ранее получил '
    'экс-глава РТС Иван Тырышкин.'
)
EQ_NEW_SHARE = (
    '50% долей перешли новым владельцам банка «Хоум Кредит» — '
    'Ибрагиму Загидулину и Елизавете Чайке (по 25% каждому). Ещё 25% '
    'ранее получил экс-глава РТС Иван Тырышкин, и ещё 25% осталось у '
    'банка «Хоум Кредит».'
)
EQ_OLD_BUYER_NAME = None
EQ_NEW_BUYER_NAME = 'Ибрагим Загидулин и Елизавета Чайка'

# --- cd47c5acc ---
MC_ID = 'cd47c5acc'
MC_OLD_STATUS = None
MC_NEW_STATUS = 'Закрыта'
MC_OLD_BUYER_NAME = None
MC_NEW_BUYER_NAME = 'АО «МФК Джамилько»'


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    obi = by_id[OBI_ID]
    eq = by_id[EQ_ID]
    mc = by_id[MC_ID]

    assert obi.get('status') == OBI_OLD_STATUS
    assert obi.get('buyer_name') == OBI_OLD_BUYER_NAME
    assert obi['eco']['context'] == OBI_OLD_CONTEXT
    assert eq['eco']['share'] == EQ_OLD_SHARE
    assert eq.get('buyer_name') == EQ_OLD_BUYER_NAME
    assert mc.get('status') == MC_OLD_STATUS
    assert mc.get('buyer_name') == MC_OLD_BUYER_NAME

    print('=== obi: status ===', OBI_NEW_STATUS)
    print('=== obi: buyer_name ===', OBI_NEW_BUYER_NAME)
    print('=== obi: eco.context ===')
    print(OBI_NEW_CONTEXT)
    print()
    print('=== eq: eco.share ===')
    print(EQ_NEW_SHARE)
    print('=== eq: buyer_name ===', EQ_NEW_BUYER_NAME)
    print()
    print('=== mc: status ===', MC_NEW_STATUS)
    print('=== mc: buyer_name ===', MC_NEW_BUYER_NAME)

    if write:
        obi['status'] = OBI_NEW_STATUS
        obi['buyer_name'] = OBI_NEW_BUYER_NAME
        obi['eco']['context'] = OBI_NEW_CONTEXT
        eq['eco']['share'] = EQ_NEW_SHARE
        eq['buyer_name'] = EQ_NEW_BUYER_NAME
        mc['status'] = MC_NEW_STATUS
        mc['buyer_name'] = MC_NEW_BUYER_NAME
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
