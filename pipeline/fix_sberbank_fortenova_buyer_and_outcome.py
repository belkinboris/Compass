# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g4402f70f` («Продажа доли Сбербанка в Fortenova Group», 2022-10-31,
Закрыта) — покупатель не был назван вовсе (`buyer`/`buyer_name` —
оба пусты), хотя `law.terms` уже упоминал «переговоры с тремя
покупателями»; фактическая цена сделки и дальнейшая судьба доли тоже
не прослеживались.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- kommersant.ru/doc/5651345: покупатель — «Саиф Алькетби», инвестор из
  ОАЭ, «занимающийся IT и недвижимостью»; другие два претендента —
  «американо-венгерский холдинг Indotek и немецкий конгломерат
  Allianz» — им, в отличие от Алькетби, требовалось одобрение
  европейских и хорватских властей;
- frankmedia.ru/106662: «Сбер продал долю в балканском ритейлере за
  400 млн евро» (не «более $1 млрд», как оценивали изначально);
  «сделку профинансировал Газпромбанк»; «Сбербанк вышел из актива с
  потерями примерно на 700 млн евро»;
- en.wikipedia.org/wiki/Fortenova_Group (с прямыми цитатами
  судебных документов): Совет ЕС включил SBK ART (структуру,
  купившую долю Сбербанка) в санкционный список в декабре 2022 года;
  амстердамский суд решил, что «SBK ART as a sanctioned company had
  no voting rights whatsoever at the Shareholders' Meetings»; 9 июля
  2024 года завершена «трансформация структуры собственности» —
  «Open Pass has become the majority equity holder with a 93.78%
  stake», более 80 миноритариев держат оставшиеся 6,22%.

НЕ ВНЕСЕНО: (1) точная организационно-правовая форма и бенефициары
самого Алькетби — известно только имя и страна; (2) связь Open Pass
(новый мажоритарный владелец, хорватский бизнесмен Павао Вуйновац) с
прежними сторонами сделки — не установлена, это независимая структура;
(3) судьба доли ВТБ (7,4%) в Fortenova — тот же класс списания
санкционных держателей, но не предмет этой карточки; (4) юридические
консультанты покупателя — не найдены, известен только консультант
продавца (Orion, уже в карточке).

Запуск: python3 pipeline/fix_sberbank_fortenova_buyer_and_outcome.py
        python3 pipeline/fix_sberbank_fortenova_buyer_and_outcome.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g4402f70f'

OLD_BUYER_NAME = None
NEW_BUYER_NAME = 'Саиф Алькетби (через SBK ART LLC, ОАЭ)'

OLD_ECO_CONTEXT = (
    'В первой половине 2022 года Сбербанк начал вести переговоры по '
    'продаже актива, однако этот процесс был осложнён введением '
    'блокирующих санкций ЕС.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' Покупателем стал инвестор из ОАЭ Саиф Алькетби '
    '— в отличие от двух других претендентов (Indotek и Allianz), ему '
    'не требовалось одобрение европейских и хорватских властей.'
    ' Фактическая цена оказалась ниже первоначальной оценки: «Сбер '
    'продал долю... за 400 млн евро» при финансировании сделки '
    'Газпромбанком, потеряв на выходе около 700 млн евро. Но '
    'Евросоюз в декабре 2022 года включил структуру покупателя (SBK '
    'ART) в санкционный список, а амстердамский суд лишил её права '
    'голоса в Fortenova; 9 июля 2024 года санкционные держатели были '
    'полностью выведены из капитала — мажоритарным акционером (93,78%) '
    'стала хорватская Open Pass.'
)

OLD_SRC = [['Orion', 'https://orion-law.com/news/yuristy-orion-partners-osushestvili-pravovoe-soprovozhdenie-prodazhi-doli-sberbanka-v-kapitale-fortenova-group']]
NEW_SRC = OLD_SRC + [
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/5651345'],
    ['Frank Media', 'https://frankmedia.ru/106662'],
    ['Wikipedia (EN)', 'https://en.wikipedia.org/wiki/Fortenova_Group'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal.get('buyer_name') == OLD_BUYER_NAME
    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== buyer_name: станет ===')
    print(NEW_BUYER_NAME)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['buyer_name'] = NEW_BUYER_NAME
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
