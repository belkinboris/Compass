# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), три карточки.
Все факты проверены ЛИЧНО прямым WebFetch (не только сводкой саб-агента).

1) citibank («"Ренессанс Капитал" приобрёл российский Ситибанк у
   Citigroup»): (а) переименование в АО «РенКап банк» подтверждено данными
   ЕГРЮЛ — личный WebFetch kommersant.ru/doc/8499666 (12.03.2026):
   «Коммерческий банк «Ситибанк» (бывшая «дочка» американской Citigroup)
   сменил название на АО «РенКап банк» после смены собственника в
   феврале. Это следует из данных ЕГРЮЛ.» (б) собственный пресс-релиз
   Citigroup о закрытии сделки называет юридического консультанта
   продавца и эффект на капитал — личный WebFetch
   citigroup.com/global/news/press-release/2026/citi-announces-sale-of-
   its-russian-business-to-renaissance-capital: «Skadden, Arps, Slate,
   Meagher & Flom LLP has acted as counsel to Citi.» и «...an estimated
   benefit to Citi's Common Equity Tier 1 (CET1) capital in the first
   quarter of 2026 of approximately $4 billion.» Оба факта — из ПЕРВИЧНОГО
   источника продавца, не из чужого пересказа. `law.adv` дополняется
   именем консультанта продавца (было «Не раскрывался»), `eco.context` —
   фактом переименования и эффектом на капитал Citi.

2) baltika («Carlsberg продал "Балтику": management buy-out через "ВГ
   Инвест"»): (а) чистая прибыль «Балтики» по РСБУ за 2025 год — личный
   WebFetch kommersant.ru/doc/8552277 (31.03.2026): «Чистая прибыль
   пивоваренной компании «Балтика» по РСБУ в 2025 году достигла 13,3 млрд
   руб.» — добавлено в `eco.target_fin` (поле уже несёт финансы предмета за
   2022 год, это тот же класс данных за более поздний период, самим полем
   уже отслеживаемый). Поле проходило вычитку (`proofread_absorbed`
   содержит 'eco.target_fin') — за основу слияния взят ТЕКУЩИЙ (уже
   вычитанный) текст с диска, а не старый `new` из FIXES.
   (б) отдельное мировое соглашение по денежному иску «Балтики» к
   структурам Carlsberg — личный WebFetch interfax.ru/business/1000191
   (дата публикации подтверждена лично — 23.12.2024, НЕ 2026 год, как
   можно было предположить по контексту поиска): «Арбитражный суд
   Санкт-Петербурга и Ленинградской области утвердил мировое соглашение по
   иску ООО «Пивоваренная компания «Балтика»» к структурам датской
   Carlsberg Group о взыскании долга в размере 4,411 млрд рублей» — это
   ОТДЕЛЬНЫЙ от товарно-знакового спора сюжет (денежный иск по договору
   займа 2021 года), новый факт для `eco.context`, добавлен с точной датой.

3) rosatom-mali («Росатом развивает литиевый проект в Мали (Бугула, регион
   Сикасо)»): (а) выход Индии из проекта подтверждён личным WebFetch —
   finance.yahoo.com/news/india-pulls-russian-backed-mali-075802579.html
   (Reuters, 12.02.2026): «The project is on hold because we cannot be
   spending on something where there is a chance we will lose our
   investment» — источник, участвовавший в решении, называет риски
   безопасности и осложнения, связанные с санкционным статусом Росатома
   (нашёл поиском точный URL после того, как tradingview.com/invezz.com/
   nv.ua дали 403 при прямом чтении — сам факт подтверждён на открывшемся
   зеркале, а не взят из чужой сводки). (б) более поздний, встречный факт —
   личный WebFetch kommersant.ru/doc/8654197 (12.05.2026): «Индия может
   вернуться к проекту по разведке лития... в Мали. По мнению собеседника
   агентства, это возможно, если... стабилизируется политическая
   ситуация.» Прежняя формулировка `law.terms` («Индия приостановила
   участие») заменена на обе датированные стадии: выход в феврале 2026 и
   переговоры о возврате в мае 2026.

Запуск: python3 pipeline/fix_monthly_2026_09_07_citibank_baltika_mali.py
        python3 pipeline/fix_monthly_2026_09_07_citibank_baltika_mali.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

# --- citibank ---
CITI_OLD_CONTEXT = (
    'Citi пыталась выйти из России с 2021 года: розничный портфель продан '
    '«Уралсибу» ещё в 2022-м, три претендента отказались из-за '
    'невозможности получить ИТ-системы под санкциями США'
)
CITI_NEW_CONTEXT = (
    CITI_OLD_CONTEXT + '. Переименование в АО «РенКап банк» подтверждено '
    'данными ЕГРЮЛ в марте 2026 года. Сам Citigroup в пресс-релизе о '
    'закрытии сделки оценил ожидаемый эффект от продажи на капитал '
    'Common Equity Tier 1 (CET1) в первом квартале 2026 года примерно в '
    '$4 млрд.'
)

CITI_OLD_ADV_SELLER = ['Продавец — Citigroup', 'Не раскрывался', '']
CITI_NEW_ADV_SELLER = [
    'Продавец — Citigroup',
    'Skadden, Arps, Slate, Meagher & Flom LLP',
    'Юридический консультант Citigroup в сделке (по данным собственного '
    'пресс-релиза Citigroup о закрытии продажи).',
]

# --- baltika ---
BALTIKA_OLD_TARGET_FIN = (
    '«Балтике» принадлежат пивоваренные заводы в 8 российских городах: '
    'Воронеже, Новосибирске, Ростове-на-Дону, Санкт-Петербурге, Туле, '
    'Хабаровске, Ярославле и Самаре. Портфель включает около 40 пивных '
    'национальных и региональных брендов и 2 непивных бренда. В 2022 году '
    'ООО «Пивоваренная компания „Балтика“» получило рекордную выручку — '
    'более 100 млрд ₽, прибыль составила 9,9 млрд ₽.'
)
BALTIKA_NEW_TARGET_FIN = (
    BALTIKA_OLD_TARGET_FIN + ' По РСБУ за 2025 год, уже под новым '
    'владением, чистая прибыль «Балтики» составила 13,3 млрд ₽.'
)

BALTIKA_OLD_CONTEXT = (
    'Продажа 2023 года сорвалась: активы передали в управление '
    'Росимуществу указом президента. 2 декабря 2024 года актив вывели '
    'из-под управления, и сделку закрыли за два дня.'
)
BALTIKA_NEW_CONTEXT = (
    BALTIKA_OLD_CONTEXT + ' Отдельно от сделки: 23 декабря 2024 года '
    'Арбитражный суд Санкт-Петербурга и Ленинградской области утвердил '
    'мировое соглашение по иску «Балтики» к структурам Carlsberg о '
    'взыскании долга в размере 4,411 млрд ₽ по договору займа 2021 года — '
    'это отдельный от спора о товарных знаках денежный иск.'
)

# --- rosatom-mali ---
MALI_OLD_TERMS = (
    'Условия концессии и распределения продукции публично не раскрыты. '
    'Есть страновой риск: Индия приостановила участие в проекте из-за '
    'вопросов безопасности'
)
MALI_NEW_TERMS = (
    'Условия концессии и распределения продукции публично не раскрыты. '
    'По неофициальным данным, в феврале 2026 года Индия вышла из проекта '
    'из-за риска потери инвестиций на фоне нестабильной обстановки в '
    'Мали и осложнений, связанных с санкционным статусом Росатома. '
    'В мае 2026 года появились сообщения, что Индия может вернуться к '
    'проекту, если политическая ситуация в стране стабилизируется.'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    citi = by_id['citibank']
    balt = by_id['baltika']
    mali = by_id['rosatom-mali']

    assert citi['eco']['context'] == CITI_OLD_CONTEXT
    assert citi['law']['adv'][1] == CITI_OLD_ADV_SELLER
    assert balt['eco']['target_fin'] == BALTIKA_OLD_TARGET_FIN
    assert balt['eco']['context'] == BALTIKA_OLD_CONTEXT
    assert mali['law']['terms'] == MALI_OLD_TERMS

    print('=== citibank: eco.context ===')
    print(CITI_NEW_CONTEXT)
    print()
    print('=== citibank: law.adv[1] ===')
    print(CITI_NEW_ADV_SELLER)
    print()
    print('=== baltika: eco.target_fin ===')
    print(BALTIKA_NEW_TARGET_FIN)
    print()
    print('=== baltika: eco.context ===')
    print(BALTIKA_NEW_CONTEXT)
    print()
    print('=== rosatom-mali: law.terms ===')
    print(MALI_NEW_TERMS)

    if write:
        citi['eco']['context'] = CITI_NEW_CONTEXT
        citi['law']['adv'][1] = CITI_NEW_ADV_SELLER
        balt['eco']['target_fin'] = BALTIKA_NEW_TARGET_FIN
        balt['eco']['context'] = BALTIKA_NEW_CONTEXT
        mali['law']['terms'] = MALI_NEW_TERMS
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
