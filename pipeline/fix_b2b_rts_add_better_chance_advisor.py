# -*- coding: utf-8 -*-
"""Разовая правка g12a761e4 (IPO B2B-РТС): второй юридический консультант.

ЧТО ДОБАВЛЯЕТСЯ. `law.adv` нёс только «BGP Litigation» — консультанта
компании, без независимого подтверждения в источниках (саб-агент партии 4
REVISION_BRIEF проверил отдельно и не нашёл ни одного упоминания роли
BGP Litigation в этой сделке нигде, кроме самой карточки). Официальный
пресс-релиз юрфирмы Better Chance (до присоединения — АБ «Проспект»)
называет её консультантом И компании, И банков-организаторов (Т-Банк,
Совкомбанк) — с именами юристов проектной команды и прямыми цитатами
представителей обоих банков-организаторов, подтверждающих её роль:
https://www.betterchance.ru/media_center/news/better-chance-soprovodila-pervoe-ipo-na-rossiyskom-rynke-v-2026-godu-publichnoe-predlozhenie-aktsiy-/

ПОЧЕМУ НЕ ЧЕРЕЗ review.py. `law.adv` — список кортежей (структурное поле),
а не текст: review.py сравнивает ВСЁ поле как единую дословную цитату, а
`str([['роль','имя','описание'], ...])` никогда не совпадёт с прозой
источника. BGP Litigation НЕ удаляется (отсутствие независимого
подтверждения — не доказательство ошибки, см. CLAUDE.md «признак дефекта —
повод прочитать, а не основание стереть»), Better Chance ДОБАВЛЯЕТСЯ
отдельной записью.

Запуск:
    python3 pipeline/fix_b2b_rts_add_better_chance_advisor.py            # сухой прогон
    python3 pipeline/fix_b2b_rts_add_better_chance_advisor.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g12a761e4'
OLD_ADV = [
    ["Юридический консультант", "BGP Litigation",
     "юридический консультант на стороне ПАО «B2B-РТС»"],
]
NEW_ENTRY = [
    "Юридический консультант компании и организаторов", "Better Chance",
    "консультировала компанию и банков-организаторов (Т-Банк, Совкомбанк) "
    "по структуре размещения, договорной документации, лок-апу и "
    "юридическому заключению по сделке; команду возглавлял партнёр Илья "
    "Барейша (до присоединения фирмы к Better Chance — АБ «Проспект»)",
]


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['adv'] == OLD_ADV, 'law.adv карточки уже другой'

    print('БЫЛО:', json.dumps(OLD_ADV, ensure_ascii=False))
    print('СТАНЕТ: + ', json.dumps(NEW_ENTRY, ensure_ascii=False))

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    deal['law']['adv'].append(NEW_ENTRY)
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
