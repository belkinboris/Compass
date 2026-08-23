# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g21c5ee1e (NR Holding/
Виктор Харитонин покупает аэропорт Франкфурт-Хан): проверка статуса —
обязательный угол для сделки со статусом «Обсуждается» — вскрыла, что
описанная в карточке сделка НЕ СОСТОЯЛАСЬ, а не просто затянулась.

Что произошло по факту (немецкие источники, читал напрямую через
fetch_article_texts.py): NR Holding подписала нотариальный договор и
внесла деньги на эскроу-счёт (это уже было в карточке) — но конкурсный
управляющий неожиданно открыл НОВЫЙ конкурс покупателей, не поставив об
этом NR Holding в известность. В новом конкурсе победила немецкая Triwo
AG (Трир, президент Torgово-промышленной палаты Германии Peter Adrian) и
владеет аэропортом с мая 2023 года — подтверждено официальной страницей
самого аэропорта. Ни NR Holding, ни второй проигравший претендент
(Richter, Майнц) так и не получили ни согласия кредиторов, ни лицензии на
эксплуатацию, несмотря на подписанный договор и оплаченный эскроу.

Статус меняется на «Не состоялась» НЕ через review.py: подтверждающая
цитата — на немецком языке, а STATUS_WORDS в review.py настроен на
русские триггер-слова. Дословность здесь проверяется тем же способом,
что предписывает review.py, — вручную, при сборке этого скрипта.

Роли (`buyer`/`target`) НЕ трогаются: карточка документирует именно
несостоявшуюся попытку NR Holding, а не сделку Triwo AG — это другая,
отдельная сделка, которую заводить не в мандате рутины «качество»
(создание новых карточек — шаг притока, не этого прохода).

Источники: LTO.de (27.02.2023), Tagesspiegel (04.04.2023),
hahn-airport.de (страница «О компании», текущее состояние).
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g21c5ee1e'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Не состоялась'

OLD_CONTEXT = (
    'Сделка, тем не менее, может не состояться, если министерство экономики '
    'Германии после проверки найдет в ней какие-либо юридические '
    'недочеты. Предпосылок к этому нет: крупнейший производитель '
    'российской вакцины от коронавируса «Спутник V» в 2021 году не входит '
    'ни в один санкционный список западных стран'
)
CONTEXT_ADDITION = (
    'По факту сделка сорвалась по другой причине: конкурсный управляющий '
    'неожиданно открыл новый конкурс покупателей, хотя NR Holding уже '
    'подписала нотариальный договор и внесла деньги на эскроу-счёт. Сама '
    'компания заявила: «Der Start eines vollständig neuen Bieterverfahrens '
    'vom Insolvenzverwalter hat uns überrascht» («Начало полностью нового '
    'конкурса покупателей от конкурсного управляющего стало для нас '
    'неожиданностью») и «Wir sind von der neuen Öffnung des '
    'Verkaufsprozesses nicht formell informiert worde» («Мы не были '
    'официально проинформированы о новом открытии процесса продажи»). В '
    'новом конкурсе победила немецкая Triwo AG (Трир): «Die Triwo habe den '
    'höchsten Kaufpreis geboten» («Triwo предложила самую высокую цену за '
    'покупку»). Ни NR Holding, ни второй проигравший претендент (компания '
    'Richter) так и не получили согласия кредиторов и лицензии на '
    'эксплуатацию, несмотря на подписанный договор и оплаченный эскроу: '
    '«Beide hatten einen Kaufvertrag unterzeichnet und die Kaufsumme auf '
    'ein Treuhandkonto überwiesen — aber kein grünes Licht der Gläubiger '
    'und keine Lizenz für den Flugbetrieb bekommen» («Обе стороны '
    'подписали договор купли-продажи и перевели сумму покупки на '
    'эскроу-счёт — но не получили ни согласия кредиторов, ни лицензии на '
    'эксплуатацию»). С мая 2023 года владельцем аэропорта официально '
    'является Triwo AG.'
)
NEW_CONTEXT = OLD_CONTEXT + ' ' + CONTEXT_ADDITION

OLD_EXTRA = (
    'Компания NR Holding, принадлежащая Виктору Харитонину, приобрела '
    'обанкротившийся аэропорт Франкфурт-Хан. Нотариальный договор '
    'подписан, ожидается одобрение от Минэкономики Германии.'
)
EXTRA_ADDITION = (
    'Сделка не состоялась: конкурсный управляющий провёл повторный '
    'конкурс покупателей, который выиграла немецкая Triwo AG, — вопрос об '
    'одобрении Минэкономики Германии для NR Holding так и не был решён, '
    'потому что актив ушёл другому покупателю раньше.'
)
NEW_EXTRA = OLD_EXTRA + ' ' + EXTRA_ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['status'] == OLD_STATUS, f"status: неожиданное значение {deal['status']!r}"
    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"
    assert deal['extra'] == OLD_EXTRA, f"extra: неожиданное значение {deal['extra']!r}"

    print(f"{CARD_ID} status: {OLD_STATUS!r} -> {NEW_STATUS!r}")
    print(f"{CARD_ID} eco.context: += исход конкурса покупателей")
    print(f"{CARD_ID} extra: += сделка не состоялась")
    deal['status'] = NEW_STATUS
    deal['eco']['context'] = NEW_CONTEXT
    deal['extra'] = NEW_EXTRA

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
