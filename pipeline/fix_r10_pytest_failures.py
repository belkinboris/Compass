# -*- coding: utf-8 -*-
"""15 августа 2026: `python3 -m pytest -q` после партии дочитывания тонких
карточек нашёл два настоящих дефекта в СВЕЖЕ записанных полях — ровно то,
для чего обязательный прогон перед коммитом и существует.

  c4fcc6d29 (МГКЛ): `law.appr` нёс факт не про согласование, а про то, КАКУЮ
      лицензию МГКЛ хочет видеть у банка-цели — это характеристика предмета
      покупки (структура сделки), а не согласующий орган. `test_approval_names_a_body`
      справедливо не нашёл в тексте ни одного органа. Переносится в
      `law.struct` (сейчас пусто) — там та же цитата уместна без изменений.
  c1aa8b20d (Fesco/Камчатка): `law.appr` начинался с дословного повтора
      начала заголовка («Петропавловск-Камчатский морской торговый порт») —
      `test_law_value_does_not_repeat_the_title` ловит ровно такую
      склейку. Тот же факт (решение суда, май 2025, иск Генпрокуратуры),
      просто без повторного называния порта — его уже назвал заголовок.

Запуск:
    python3 pipeline/fix_r10_pytest_failures.py            # сухой прогон
    python3 pipeline/fix_r10_pytest_failures.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

MGKL_TEXT = ('Группа обсуждает приобретение банка с универсальной лицензией, а также '
             'лицензией на операции с драгметаллами, чтобы запустить розничное '
             'кредитование и организацию полноценных золотых обменников')

FESCO_OLD = ('Петропавловск-Камчатский морской торговый порт национализирован по '
             'решению Ленинского районного суда Владивостока, принятого в мае 2025 '
             'года. Суд удовлетворил иск Генеральной прокуратуры России о конфискации '
             'имущества, полученного в нарушение законодательства о противодействии '
             'коррупции.')
FESCO_NEW = ('Национализирован по решению Ленинского районного суда Владивостока, '
             'принятого в мае 2025 года: суд удовлетворил иск Генеральной прокуратуры '
             'России о конфискации имущества, полученного в нарушение законодательства '
             'о противодействии коррупции.')


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    mgkl = by_id['c4fcc6d29']
    assert mgkl.get('law', {}).get('appr') == MGKL_TEXT, 'c4fcc6d29: law.appr уже другое'
    assert mgkl.get('law', {}).get('struct') is None, 'c4fcc6d29: law.struct уже не пусто'

    fesco = by_id['c1aa8b20d']
    assert fesco.get('law', {}).get('appr') == FESCO_OLD, 'c1aa8b20d: law.appr уже другое'

    print('c4fcc6d29: law.appr -> law.struct (та же цитата, поле не подходило)')
    print('c1aa8b20d: law.appr переформулирован без повтора заголовка')

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    mgkl['law'].pop('appr')
    mgkl['law']['struct'] = MGKL_TEXT

    fesco['law']['appr'] = FESCO_NEW

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
