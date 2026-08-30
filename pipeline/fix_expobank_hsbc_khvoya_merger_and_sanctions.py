# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка ga5b07998
(Экспобанк приобрел российскую дочку HSBC) — карточка не отражала судьбу
банка после сделки (переименование, слияние) и эскалацию санкций против
Экспобанка/его бенефициара в 2025 году. Проверено лично прямым WebFetch
шести источников.

1) `eco.context` (дополнено) — судьба банка: переименование и слияние.
Дословно (TASS, май 2024): «HSBC Bank will continue operations under a
new name. Renaming of the credit institution is expected within a
month» — новое имя не названо в этой статье, но по дальнейшим
источникам это «Хвоя банк». Интерфакс (2024): «Акционеры Экспобанка
приняли решение о реорганизации в форме присоединения к нему Хвоя
банка», «Предполагаемый срок завершения реорганизации – четвертый
квартал 2024 года», «В результате реорганизации к Экспобанку переходят
все права и обязанности Хвоя банка». Profbanking.com (16.12.2024):
«ООО «Хвоя Банк» присоединен к АО «Экспобанк» (лицензия № 2998) и
перестал существовать». Bankinform.ru: «капитал Экспобанка достиг 56
млрд рублей», банк «вошел в топ-30 банков России», «Активы банка
увеличились до 254 млрд рублей».

2) `eco.context` (дополнено) — эскалация санкций 2025. Interfax
(24.02.2025): бенефициар Экспобанка Игорь Ким включён в санкционный
список Великобритании — «Ким включен в него как контролирующее лицо
Экспобанка». Vc.ru: Экспобанк — один из банков в 18-м пакете санкций ЕС
(«Новые санкции ЕС затронули «Т-Банк», «Яндекс Банк», «Ozon Банк», банк
«Финама», «Экспобанк», «Локо-Банк» и других»), анонс 18 июля 2025,
вступление в силу 9 августа 2025.

3) `eco.context` (дополнено) — независимая регуляторная норма дисконта
и число, которое НЕ цена. Frankmedia.ru: «Минфин определил, что активы
должны продаваться с дисконтом в 50% к рыночной стоимости, определенной
независимым оценщиком» — обсуждавшиеся в карточке ~90% заметно выше
законной нормы; там же: «OFAC выдал лицензию на завершение операций с
банком до 21 марта 2024 года» (сделка закрылась позже, в мае — лицензия
могла быть продлена, отдельно не проверялось). Yahoo Finance: «In 2023,
HSBC said that it took a $300-million loss on the expected sale of its
Russia business» — это УБЫТОК ПРОДАВЦА от сделки, а не цена актива (тот
же класс числа, что уже описан в CLAUDE.md на примере Reckitt/Arnest),
в `sum`/`eco.val` не идёт, только сюда с явной пометкой.

4) `law.terms` (новое поле) — объём мандата Better Chance. Дословно:
«Наша команда консультировала HSBC по всему спектру корпоративных и
регуляторных вопросов, в том числе по вопросам интеграции двух банков:
АО «Экспобанк» и ООО «Эйч-эс-би-си Банк (РР)» в течение переходного
периода».

НЕ ВКЛЮЧЕНО: финансовый консультант Экспобанка — не найден ни в одном
источнике; судьба клиентов/сотрудников бывшего HSBC — конкретики не
нашлось нигде; условия сделки (earn-out, гарантии) — ни один источник
их не называет.

Запуск: python3 pipeline/fix_expobank_hsbc_khvoya_merger_and_sanctions.py
        python3 pipeline/fix_expobank_hsbc_khvoya_merger_and_sanctions.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'ga5b07998'

OLD_CONTEXT = (
    'В декабре 2023 года Экспобанк попал в санкционный список Минфина '
    'США, что сделало туманными перспективы продажи «Эйч-эс-би-си '
    'банка», к тому же на тот момент отсутствовало одобрение '
    'регуляторов.'
)
NEW_CONTEXT = OLD_CONTEXT + (
    ' После закрытия банк переименован («Renaming of the credit '
    'institution is expected within a month», TASS) — в «Хвоя банк», '
    'который затем присоединён к Экспобанку: «Предполагаемый срок '
    'завершения реорганизации – четвертый квартал 2024 года» '
    '(Интерфакс), завершено 16 декабря 2024 года — «ООО «Хвоя Банк» '
    'присоединен к АО «Экспобанк»... и перестал существовать» '
    '(profbanking.com). В результате «капитал Экспобанка достиг 56 млрд '
    'рублей», банк «вошел в топ-30 банков России», активы выросли до '
    '254 млрд рублей (bankinform.ru). В 2025 году санкции против '
    'Экспобанка усилились: 24 февраля бенефициар банка Игорь Ким '
    'включён в санкционный список Великобритании как «контролирующее '
    'лицо Экспобанка» (Интерфакс); Экспобанк также попал в 18-й пакет '
    'санкций ЕС (анонс 18 июля, вступление в силу 9 августа 2025, vc.ru '
    '— в списке из нескольких российских банков). Независимая '
    'регуляторная норма: «Минфин определил, что активы должны '
    'продаваться с дисконтом в 50% к рыночной стоимости, определенной '
    'независимым оценщиком» (frankmedia.ru) — обсуждавшиеся ~90% выше '
    'этой нормы. HSBC заявляла об убытке от сделки: «In 2023, HSBC said '
    'that it took a $300-million loss on the expected sale of its '
    'Russia business» (Yahoo Finance) — это убыток продавца, а не цена '
    'актива.'
)

NEW_TERMS = (
    'Better Chance (юридический консультант продавца): «консультировала '
    'HSBC по всему спектру корпоративных и регуляторных вопросов, в том '
    'числе по вопросам интеграции двух банков... в течение переходного '
    'периода».'
)

NEW_SRC = [
    ['TASS', 'https://tass.com/economy/1795299'],
    ['Интерфакс', 'https://www.interfax.ru/business/990831'],
    ['profbanking.com', 'https://profbanking.com/only-news/5051-khvoya-the-end'],
    ['bankinform.ru', 'https://bankinform.ru/news/136273'],
    ['Интерфакс', 'https://www.interfax.ru/business/1010565'],
    ['vc.ru', 'https://vc.ru/money/2108288-sanktsii-es-protiv-rossijskih-bankov'],
    ['frankmedia.ru', 'https://frankmedia.ru/158943'],
    ['Yahoo Finance', 'https://finance.yahoo.com/news/hsbc-completes-transfer-russia-unit-154700766.html'],
    ['Better Chance', 'https://betterchance.ru/media_center/news/better-chance-konsultiruet-hsbc-v-svyazi-s-prodazhey-dochernego-banka-v-rossii/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT
    assert deal['law']['terms'] == '—'
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('\n=== law.terms: станет ===')
    print(NEW_TERMS)
    print('\n=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['law']['terms'] = NEW_TERMS
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
