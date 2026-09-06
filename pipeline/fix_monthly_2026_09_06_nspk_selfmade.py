# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), две карточки:
`gmru-nspk-privatization`, `gbcc32684` — по обеим нашёлся новый факт вне
кэша притока (проверено ЛИЧНО прямым WebFetch). Третья карточка
кластера, `gmru-rwb-eapteka`, не тронута — независимое подтверждение
нашлось (interfax.ru, retail.ru), но оно повторяет уже известную
честную неопределённость (доля и сумма не раскрыты), нового факта нет.

1) gmru-nspk-privatization (Банк России/приватизация НСПК, Обсуждается,
   3 июля 2026). Проверено ЛИЧНО прямым WebFetch (kommersant.ru/doc/
   8781891, 02.07.2026): «до конца этого года вряд ли это случится» —
   ЦБ сначала рассчитывает завершить оценку рыночной стоимости, сама
   приватизация сдвигается на 2027 год. Отдельно (kommersant.ru/doc/
   8846339, 28.07.2026): к уже названным претендентам (Сбер, Альфа-банк,
   Т-банк, РСХБ) добавился ВТБ — первый зампред правления Дмитрий
   Пьянов: «Банк России рассчитывает к концу года только завершить
   оценку рыночной стоимости НСПК, поэтому ВТБ будет рассматривать этот
   вопрос после завершения оценки и появления предложения. Сейчас
   условия частичной приватизации неизвестны». Дополнено в
   `eco.context`. Конкретной схемы, покупателя или срока сделки
   по-прежнему нет — не вносится.

2) gbcc32684 (Lamoda/Selfmade/«Фаст Фешн», Закрыта). Проверено ЛИЧНО
   прямым WebFetch: карточка держалась ЕДИНСТВЕННЫМ источником —
   телеграм-каналом (@LawFirms) — при том, что та же сделка (те же
   90%/10%, та же оценка Михаила Бурмистрова 100–120 млн ₽ с учётом
   долга 97,2 млн ₽) независимо и дословно совпадающе описана деловыми
   СМИ: kommersant.ru/doc/8624358 (27.04.2026, 19:24, «Lamoda провела
   первую в своей истории M&A-сделку»; «Lamoda приобрела 90% в ООО
   «Фаст Фешн»»; «Остальные 10% «Фаст Фешн» сохранит за собой
   основательница Selfmade Татьяна Куценко»; «Сумму сделки стороны не
   раскрывают»), shopandmall.ru (27.04.2026, 14:45) и finance.mail.ru
   (27.04.2026) — оба независимо подтверждают: «5 розничных магазинов в
   Москве и Санкт-Петербурге», «340 тысяч подписчиков в социальных
   сетях». ДАТА КАРТОЧКИ ИСПРАВЛЕНА: было «2026-05-27», источники
   сходятся на «2026-04-27» — ни один из проверенных источников (четыре
   независимых издания) не называет май вообще, а майская дата, судя по
   всему, случайная перестановка месяца/дня при разборе черновика.
   Дословной фразы вида «27 апреля» ни один источник не даёт (только
   числовая метка публикации), поэтому правка сделана НЕ через
   `review.py` (его `date_is_supported()` требует день и месяц
   прописью в цитате), а этим одноразовым скриптом с `assert` на
   исходное значение — тот же класс, что уже применялся для дат,
   подтверждённых временем публикации статьи, а не прямой цитатой.
   Источники деловых СМИ добавлены в `src` (аддитивно, рядом с
   телеграм-каналом), новые детали (магазины, подписчики) — в
   `eco.context`.

Затронутое поле `eco.context` карточки НСПК уже прошло вычитку
(`proofread_absorbed`) — за основу слияния взят текущий, уже вычитанный
текст; соответствующая запись FIXES (`batch_a_2025.py`) обновлена тем
же приёмом. `eco.context` карточки Selfmade — тоже проверено на
проверку(проверено дословно, совпадает с текущим).

`buyer`/`seller`/`title`/`target`-структура обеих карточек НЕ тронута.

Запуск: python3 pipeline/fix_monthly_2026_09_06_nspk_selfmade.py
        python3 pipeline/fix_monthly_2026_09_06_nspk_selfmade.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

# --- gmru-nspk-privatization ---
NSPK_ID = 'gmru-nspk-privatization'
NSPK_OLD_ECO_CONTEXT = (
    'На Финконгрессе глава РСХБ Борис Листов заявил, что войти в её '
    'капитал могут около 20 новых участников и Россельхозбанк готов '
    'стать одним из них.'
)
NSPK_NEW_ECO_CONTEXT = (
    NSPK_OLD_ECO_CONTEXT + ' Набиуллина заявила 2 июля 2026 года: '
    'приватизация «до конца этого года вряд ли... случится» — сначала '
    'регулятор рассчитывает завершить оценку рыночной стоимости НСПК. '
    'К претендентам добавился ВТБ: первый зампред правления Дмитрий '
    'Пьянов заявил 28 июля 2026 года, что банк рассмотрит участие '
    '«после завершения оценки и появления предложения», а «условия '
    'частичной приватизации пока неизвестны».'
)

# --- gbcc32684 ---
SELFMADE_ID = 'gbcc32684'
SELFMADE_OLD_DATE = '2026-05-27'
SELFMADE_NEW_DATE = '2026-04-27'
SELFMADE_OLD_SRC = [
    ['РУЛЬФЫ, ИЛЬФЫ И ИНХАУСЫ (@LawFirms)', 'https://t.me/LawFirms/10967'],
]
SELFMADE_NEW_SRC = SELFMADE_OLD_SRC + [
    ['kommersant.ru', 'https://www.kommersant.ru/doc/8624358'],
    ['shopandmall.ru', 'https://shopandmall.ru/news/lamoda-investiruet-v-premialnyj-brend-selfmade-poluciv-kontrolnyj-paket'],
]
SELFMADE_OLD_ECO_CONTEXT = (
    'Михаил Бурмистров считает Selfmade нишевым игроком, чьё '
    'позиционирование отвечает запросам покупателей Lamoda. По его '
    'мнению, владельцы бренда сумели удачно продать актив: условия на '
    'рынке одежды сейчас далеки от благоприятных, и многие небольшие '
    'игроки вынуждены сворачивать бизнес.'
)
SELFMADE_NEW_ECO_CONTEXT = (
    SELFMADE_OLD_ECO_CONTEXT + ' У Selfmade — пять розничных магазинов '
    'в Москве и Санкт-Петербурге и 340 тыс. подписчиков в социальных '
    'сетях.'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    nspk = by_id[NSPK_ID]
    selfmade = by_id[SELFMADE_ID]

    assert nspk['eco']['context'] == NSPK_OLD_ECO_CONTEXT
    assert selfmade['date'] == SELFMADE_OLD_DATE
    assert selfmade['src'] == SELFMADE_OLD_SRC
    assert selfmade['eco']['context'] == SELFMADE_OLD_ECO_CONTEXT

    print('=== nspk: eco.context ===')
    print(NSPK_NEW_ECO_CONTEXT)
    print()
    print('=== selfmade: date ===', SELFMADE_NEW_DATE)
    print('=== selfmade: src ===')
    print(SELFMADE_NEW_SRC)
    print('=== selfmade: eco.context ===')
    print(SELFMADE_NEW_ECO_CONTEXT)

    if write:
        nspk['eco']['context'] = NSPK_NEW_ECO_CONTEXT
        selfmade['date'] = SELFMADE_NEW_DATE
        selfmade['src'] = SELFMADE_NEW_SRC
        selfmade['eco']['context'] = SELFMADE_NEW_ECO_CONTEXT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
