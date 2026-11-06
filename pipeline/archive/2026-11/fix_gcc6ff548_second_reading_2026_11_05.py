# -*- coding: utf-8 -*-
"""gcc6ff548 (RBE / «Сильвер Салмон»), второе чтение 5 ноября 2026.

Что было: в «Истории и окружении» абзац про соседние компании прежней учредительницы (не эта сделка)
и фраза про 16,4%: по Росстату это число гостей в средствах размещения края, а не спрос и не про
компанию; в «Цели сделки» второе предложение не про мотив.
Что стало: абзац снят, второе предложение цели снято. proofread.py такое не принимает (снятые
числа и имена), поэтому разовый скрипт с assert на старое значение.

Запуск: python3 pipeline/archive/2026-11/fix_gcc6ff548_second_reading_2026_11_05.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
OLD_RAT = 'Инвестконсультант Иван Пешков видит в покупке, скорее всего, попытку группы занять место на рынке туризма. Он отмечает, что квоты на любительскую рыбалку — не то же самое, что промышленный вылов для столовых и пищевых производств. По неофициальным данным, группа еще два года назад хотела работать с рыбой для госконтрактов по поставкам продовольствия.'
NEW_RAT = 'Инвестконсультант Иван Пешков видит в покупке, скорее всего, попытку группы занять место на рынке туризма. По неофициальным данным, группа еще два года назад хотела работать с рыбой для госконтрактов по поставкам продовольствия.'


def main(write):
    data = json.load(open(PATH, encoding='utf-8'))          # перечитано прямо перед записью
    card = [c for c in data['cards'] if c['id'] == 'gcc6ff548'][0]
    eco = card['eco']
    if eco['rationale'] == NEW_RAT:
        print('уже применено')
        return
    assert eco['rationale'] == OLD_RAT, eco['rationale']
    paras = eco['context'].split('\n\n')
    assert len(paras) == 3 and 'Кинг Салмон' in paras[1], paras
    eco['context'] = paras[0] + '\n\n' + paras[2]
    eco['rationale'] = NEW_RAT
    print('eco.context: снят абзац про соседние компании; eco.rationale переписан')
    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print('записано')
    else:
        print('Сухой прогон. Запись — с ключом --write.')


if __name__ == '__main__':
    main('--write' in sys.argv)
