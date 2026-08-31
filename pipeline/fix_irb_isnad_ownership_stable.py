# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g8a8ae3f7
(Передача 12,75% доли International Restaurant Brands от Marathon Group
к Isnad For Business) — искали, не перепродавалась ли доля дальше и не
прояснилась ли природа сделки (рыночная продажа vs корпоративная
реструктуризация, вопрос уже честно оставлен открытым в `extra`).

Проверено лично прямым WebFetch (kommersant.ru/doc/8636902, 07.05.2026):
«Владельцами IRB через ООО "Кьюэсар инвестментс" выступают закрытые
паевые инвестфонды "Горизонт капитал" (26,5%), "Форум-инвест" (25,49%) и
"Гратус инвест" (11,75%)... Еще 23,5% и 12,75% соответственно принадлежат
оманским компаниям Al Shafaq Second Investment и Isnad For Business» —
спустя почти год после передачи доля Isnad For Business в 12,75%
осталась прежней, дальше не перепродавалась.

Природа сделки (рыночная/реструктуризация) осталась неразрешённой — новых
источников с бо́льшим весом, чем уже процитированный в `extra`, не
нашлось; мнение стороннего юриста (Forward Legal) в пользу версии
«реструктуризация» не добавлено — оно не сильнее уже стоящей в карточке
оговорки и повторило бы тот же тезис другим голосом.

НЕ ВКЛЮЧЕНО: связь Isnad For Business/Али Изхара с Marathon Group или
другими уже известными сторонами базы — не нашлась ни в одном источнике,
включая специально проверенные (RuMafia пишет общо, без утверждения об
общем бенефициаре). Сумма сделки по-прежнему только экспертная оценка
(уже в `eco.val`). Отдельная, более поздняя сделка — покупка IRB 20% в
«Юнирест» (Коммерсантъ, та же статья) — уже заведена своей карточкой
(`g1f2895c0`), дублирования нет.

Запуск: python3 pipeline/fix_irb_isnad_ownership_stable.py
        python3 pipeline/fix_irb_isnad_ownership_stable.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g8a8ae3f7'

OLD_CONTEXT = (
    'Контролирующий IFB Али Изхар, по данным госреестра Омана, уроженец '
    'Пакистана. Согласно LinkedIn, человек с таким же именем возглавляет '
    'Izhar Group, специализирующуюся на строительстве жилой и '
    'коммерческой недвижимости в Пакистане. Среди клиентов компании — '
    'Unilever, Pepsi, Suzuki, Honda, P&G, Nestle и прочие.'
)
NEW_CONTEXT = OLD_CONTEXT + (
    ' Спустя почти год доля не перепродавалась: «Владельцами IRB через '
    'ООО "Кьюэсар инвестментс" выступают закрытые паевые инвестфонды '
    '"Горизонт капитал" (26,5%), "Форум-инвест" (25,49%) и "Гратус '
    'инвест" (11,75%)... Еще 23,5% и 12,75% соответственно принадлежат '
    'оманским компаниям Al Shafaq Second Investment и Isnad For '
    'Business» (Коммерсантъ, 7 мая 2026 года).'
)

NEW_SRC_KOMMERSANT = ['Коммерсантъ', 'https://www.kommersant.ru/doc/8636902']


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT

    new_src = deal['src'] + [NEW_SRC_KOMMERSANT]

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('\n=== src: добавится ===')
    print(NEW_SRC_KOMMERSANT)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
