# -*- coding: utf-8 -*-
"""Слияние дубля: `cc108d4d8` («Gunvor предложил купить зарубежные активы
Лукойла (LUKOIL International GmbH)») и `c71e19cc1` («Gunvor отказался от
покупки международных активов Лукойла») — ОДНА И ТА ЖЕ несостоявшаяся
сделка (предложение 30 октября 2025 года, отзыв 6-7 ноября 2025 года),
описанная двумя карточками с разных концов её короткой жизни: заголовок
одной — про предложение, другой — про отказ, у обеих `status: "Не
состоялась"`, и обе несут в `eco.context` полный рассказ про оба события
сразу. Найдено при чтении месячной очереди 8 сентября 2026 — не было в
списке ни одного автоматического сканера дублей (обе карточки
`from_compact: bulk`, не «мини»).

Оставлена `c71e19cc1` — она полнее по структуре: `law.struct` несёт точную
дату объявления (30 октября) и условия закрытия, `eco.val` — независимую
оценку LUKOIL International в $21 млрд (2023 год), `eco.rationale» —
стратегическое обоснование, и на одно название источника больше
(Bloomberg + РИА Новости против Ведомостей + пресс-релиза).

Перенесено из `cc108d4d8` (единственные факты, которых не было у
`c71e19cc1`, оба подтверждены личным WebFetch пресс-релиза LUKOIL):
1) `eco.share` (было пусто «—») — точная формулировка предмета: «Gunvor
   Group Ltd. предложила купить 100% акций LUKOIL International GmbH» —
   личный WebFetch (lukoil.com/PressCenter/…): «100% subsidiary of PJSC
   "LUKOIL"… Gunvor Group Ltd.».
2) `law.appr` — дополнена общим пояснением партнёра NSP Ильи Рачкова о
   механизме лицензий OFAC (зачем она вообще нужна для такой сделки) —
   этого объяснения у `c71e19cc1` не было, только констатация отказа.

Запуск:
    python3 pipeline/merge_gunvor_lukoil_dup.py            # сухой прогон
    python3 pipeline/merge_gunvor_lukoil_dup.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'
KEEP_ID = 'c71e19cc1'
DROP_ID = 'cc108d4d8'

OLD_SHARE = '—'
NEW_SHARE = (
    'Gunvor Group Ltd. предложила купить 100% акций LUKOIL International '
    'GmbH — «дочки» ПАО «Лукойл», которой принадлежат зарубежные активы '
    'группы.'
)

OLD_APPR = (
    'Gunvor отозвала предложение о приобретении дочерней компании '
    '«Лукойла» LUKOIL International GmbH после того, как Минфин США '
    'заявил об отказе выдать ей лицензию для ведения бизнеса.'
)
NEW_APPR = OLD_APPR + (
    ' Партнёр адвокатского бюро NSP Илья Рачков поясняет: Минфин США '
    'выдаёт лицензии, позволяющие «лицам США» заключать сделки с '
    'компаниями под санкциями и их «дочками».'
)


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    deals = data['deals']
    by_id = {d['id']: d for d in deals}

    assert DROP_ID in by_id, '%s должна существовать до слияния' % DROP_ID
    keep = by_id[KEEP_ID]
    assert keep['eco']['share'] == OLD_SHARE, \
        'eco.share уже другой: %r' % (keep['eco']['share'],)
    assert keep['law']['appr'] == OLD_APPR, \
        'law.appr уже другой: %r' % (keep['law']['appr'],)

    print('eco.share: %r -> %r' % (OLD_SHARE, NEW_SHARE))
    print('law.appr: дополняется пояснением о механизме лицензий OFAC')
    print('deals: было %d, станет %d' % (len(deals), len(deals) - 1))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    keep['eco']['share'] = NEW_SHARE
    keep['law']['appr'] = NEW_APPR

    merged = data.setdefault('merged', {})
    merged[DROP_ID] = KEEP_ID
    data['deals'] = [d for d in deals if d['id'] != DROP_ID]

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано. Сделок было: %d, стало: %d' % (len(deals), len(data['deals'])))


if __name__ == '__main__':
    main('--write' in sys.argv)
