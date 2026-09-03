# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка `g4bb21315`
(«АФК «Система» купила Natura Siberica», закрыта в мае 2023 года) —
дальнейшая судьба компании после сделки не была отражена, а `eco.val`
нёс путаную, дважды повторяющую саму себя формулировку оценки.

Проверено лично прямым WebFetch:
- Коммерсантъ, https://www.kommersant.ru/doc/5966876, 02.05.2023: «Теперь
  он [Феликс Либ] намерен сделать ее пригодной для IPO»; «"Ъ" сообщал о
  планах Natura Siberica импортозаместить средства для окрашивания»;
  «АФК "Система" могла купить Natura Siberica за $50–70 млн, полагает
  партнер юридической группы GRM Сергей Новиков».
- Oborot.ru, https://oborot.ru/news/osnovnoj-akcioner-ozona-kupil-natura-siberica-skolko-eto-moglo-stoit-i185102.html,
  02.05.2023: «покупка могла обойтись АФК "Система" не более чем в 3 млрд
  рублей» (оценка Михаила Бурмистрова, Infoline-аналитика).
- Ведомости, https://www.vedomosti.ru/business/articles/2024/04/27/1034533-natura-siberica-namerena-uvelichit-dolyu-eksporta-v-viruchke,
  27.04.2024: «Выручка ООО "Натура Сиберика" (головное юрлицо группы) по
  РСБУ в 2023 г. составила 4,85 млрд руб.» (2022 год — 5,1 млрд руб.);
  «Чистая прибыль – 24,8 млн руб. за 2023 г. против 399 млн руб. годом
  ранее».
- BFM.ru, https://www.bfm.ru/news/524518, 02.05.2023 — НЕ прямая цитата
  Либа, пересказ журналиста от третьего лица: «компания сохранила все
  международные сертификаты качества и продолжит продвижение за
  рубежом... в России она также будет развивать свою розничную сеть и
  экспериментировать с онлайн-форматами» — вношу как факт статьи, а не
  как цитату персоны.

`eco.context` уже говорит о выручке ГК ЦЕЛИКОМ за 2022 год (10,2 млрд ₽)
— выручка ООО «Натура Сиберика» за 2023 год (4,85 млрд ₽) относится к
ГОЛОВНОМУ ЮРЛИЦУ, а не ко всей группе; формулировка новой правки прямо
называет это различие, чтобы не создать впечатление противоречия
(родня урока CLAUDE.md «Соседние числа считаются от разных
знаменателей»).

НЕ ВНЕСЕНО: `seller` — ни один из проверенных источников (Коммерсантъ,
Ведомости, Inc. Russia, retailer.ru) не называет продавца дословно
применительно к этой конкретной сделке; есть только косвенные данные о
наследниках Андрея Трубникова (дети Дмитрий, Екатерина, Елизавета,
возможно первая жена Ирина), но прямой связи «эти люди продали долю
именно АФК "Система"» текст не устанавливает — вносить имя без такого
подтверждения значило бы досочинить факт. `law.terms`/`law.appr` — ни
один источник не упоминает ФАС или условия сделки («сумма и условия не
раскрываются» — во всех источниках).

Запуск: python3 pipeline/fix_natura_siberica_sistema_aftermath.py
        python3 pipeline/fix_natura_siberica_sistema_aftermath.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g4bb21315'

OLD_ECO_VAL = 'Эксперты: 3–7,9 млрд руб; не раскрыта (эксперты: 3–7,9 млрд ₽)'
NEW_ECO_VAL = (
    'Аналитик GRM Сергей Новиков оценивал сделку в $50–70 млн '
    '(Коммерсантъ), Infoline-аналитика — не выше 3 млрд ₽ (Oborot.ru); '
    'обе оценки укладываются в общий диапазон 3–7,9 млрд ₽.'
)

OLD_ECO_CONTEXT = (
    'На сегодня доля Natura Siberica на российском косметическом рынке '
    'составляет не более 4%, сказал в интервью газете «Ведомости» '
    'гендиректор компании Феликс Либ.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' После сделки Либ заявил о намерении подготовить '
    'компанию к IPO и импортозаместить красители (Коммерсантъ); по '
    'данным BFM.ru, компания сохранила международные сертификаты '
    'качества и планирует развивать розничную сеть и онлайн-продажи в '
    'России. Выручка ГОЛОВНОГО ЮРЛИЦА группы, ООО «Натура Сиберика», в '
    '2023 году составила 4,85 млрд ₽ (годом ранее — 5,1 млрд ₽), чистая '
    'прибыль — 24,8 млн ₽ против 399 млн ₽ годом ранее (Ведомости) — эти '
    'цифры относятся к юрлицу, а не ко всей группе, чья выручка за 2022 '
    'год (10,2 млрд ₽) уже указана выше.'
)

NEW_SRC = [
    ['Oborot.ru', 'https://oborot.ru/news/osnovnoj-akcioner-ozona-kupil-natura-siberica-skolko-eto-moglo-stoit-i185102.html'],
    ['BFM.ru', 'https://www.bfm.ru/news/524518'],
    ['Ведомости', 'https://www.vedomosti.ru/business/articles/2024/04/27/1034533-natura-siberica-namerena-uvelichit-dolyu-eksporta-v-viruchke'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['val'] == OLD_ECO_VAL
    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== eco.val: станет ===')
    print(NEW_ECO_VAL)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['eco']['val'] = NEW_ECO_VAL
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
