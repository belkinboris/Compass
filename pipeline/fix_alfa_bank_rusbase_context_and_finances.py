# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g96674c34
(Альфа-банк приобрел 73% долей в издании Rusbase (RB.RU)) — `eco.context`
и `eco.target_fin` стояли прочерком, а сама судьба издания после сделки
не отслежена.

Финансы предмета — проверено лично прямым WebFetch (bg.ru): «По итогам
2023 года компания-владелец издания «Рбточкару» получила убыток в 5,7
миллиона рублей».

Судьба издания после сделки — проверено лично прямым WebFetch. Через
полгода после закрытия — обновление: «3 марта 2025 года деловое медиа
Русбейс объявило о масштабном обновлении», новым главным редактором стал
«Валерий Игуменов, который ранее занимал должность главного редактора
журнала РБК» (Comnews). Финалом стал полный ребрендинг: «На домене rb.ru
в рамках ребрендинга запустилось новое деловое медиа Russian Business»,
«Russian Business — это бывший Rusbase, независимое издание о
технологиях и бизнесе, запущенное в 2012 году» (bg.ru) — то есть бренд
Rusbase/RB.RU в итоге прекратил существование под старым именем, а не
продолжил работу как купленный актив без изменений. Позже, уже после
ребрендинга, Альфа-Банк увеличил долю: «АО «Альфа-Банк» увеличило долю
участия в ООО «РБТОЧКАРУ» до 92% с 91%. Сделка была реализована через
увеличение уставного капитала» (mergers.akm.ru, 29 октября 2025 года) —
добавлено как факт ПОСЛЕ сделки, структурные поля исходной сделки
(73%, 2024 год) не меняются.

Образовательная платформа «Курс», о которой шла речь в карточке как о
плане, — проверено лично прямым WebFetch (Comnews): «"Курс" — бесплатная
образовательная платформа, совместный проект Альфа-Банка и делового
издания «Русбейс»», с ростом метрик («Число новых регистраций выросло на
45%», «Время взаимодействия с пользователями выросло на 27%») — план
реализован, а не остался декларацией.

НЕ ВКЛЮЧЕНО: утверждение, что издание в версии марта 2025 просуществовало
всего ~4 месяца и было закрыто, а гендиректором стал Илья Афанасов, —
источник единственный (личный блог на vc.ru, не редакция), второй
независимый источник не нашёлся; сама Эльза Егорова ситуацию не
комментировала. Финансовые показатели «Рбточкару» за 2024-2025 годы —
не найдены ни в одном источнике.

Запуск: python3 pipeline/fix_alfa_bank_rusbase_context_and_finances.py
        python3 pipeline/fix_alfa_bank_rusbase_context_and_finances.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g96674c34'

OLD_TARGET_FIN = '—'
NEW_TARGET_FIN = (
    'По итогам 2023 года компания-владелец издания «Рбточкару» получила '
    'убыток в 5,7 млн руб. (bg.ru).'
)

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    '3 марта 2025 года издание объявило о масштабном обновлении: новым '
    'главным редактором стал Валерий Игуменов, ранее возглавлявший '
    'журнал РБК (Comnews). В итоге бренд Rusbase/RB.RU прекратил '
    'существование под старым именем: «На домене rb.ru в рамках '
    'ребрендинга запустилось новое деловое медиа Russian Business» —'
    ' «бывший Rusbase, независимое издание о технологиях и бизнесе, '
    'запущенное в 2012 году» (bg.ru). 29 октября 2025 года Альфа-Банк '
    'увеличил долю в ООО «РБТОЧКАРУ» до 92% с 91% через увеличение '
    'уставного капитала (mergers.akm.ru). Образовательная платформа '
    '«Курс», о которой шла речь как о плане, заработала: рост новых '
    'регистраций составил 45%, время взаимодействия с пользователями '
    'выросло на 27% (Comnews).'
)

NEW_SRC = [
    ['bg.ru', 'https://bg.ru/bg/business/comm-news/28784-rb-ru'],
    ['Comnews', 'https://www.comnews.ru/content/238071/2025-03-04/2025-w10/1018/rusbeys-obnovilsya-novaya-komanda-novaya-aydentika-novyy-sayt'],
    ['Comnews', 'https://www.comnews.ru/digital-economy/content/238156/2025-03-07/2025-w10/1012/alfa-bank-vnedril-geymifikaciyu-obrazovatelnuyu-platformu-kurs-dlya-predprinimateley'],
    ['mergers.akm.ru', 'https://mergers.akm.ru/news/alfa_bank_stal_vladeltsem_92_v_proekte_russian_business/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['target_fin'] == OLD_TARGET_FIN
    assert deal['eco']['context'] == OLD_CONTEXT

    new_src = deal['src'] + NEW_SRC

    print('=== eco.target_fin: станет ===')
    print(NEW_TARGET_FIN)
    print('\n=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['target_fin'] = NEW_TARGET_FIN
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
