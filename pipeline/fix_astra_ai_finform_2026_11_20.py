# -*- coding: utf-8 -*-
"""Правка 20 ноября 2026, тем же днем, что и
`merge_astra_ai_control_2026_11_20.py`: механика расчета по ноябрьскому
траншу (оплата акциями «Группы Астра» из квазиказначейского пакета,
ограничение на перепродажу до 2027 года) была по ошибке дописана в
`eco.val`, а по `docs/card_money.md` («Форма расчётов, показатели,
оценка») это поле `eco.fin` — «как и чем платят», а не `eco.val`
(премии/альтернативные оценки). Абзац переносится в `eco.fin` (было
«—»), `eco.val` возвращается к тексту, который описывал только майский
транш.

Запуск:
    python3 pipeline/fix_astra_ai_finform_2026_11_20.py            # сухой прогон
    python3 pipeline/fix_astra_ai_finform_2026_11_20.py --write
"""
import json
import os
import sys

ROOT = '/home/user/Compass'
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
CARD_ID = 'g2777a4b6'

OLD_VAL = ('Официально сумму не раскрывали. По оценке сооснователя «МойОфис» Дмитрия Комиссарова, сделка могла '
           'обойтись примерно в 100 млн ₽; другие эксперты оценивают ее в 80–100 млн ₽.\n\n'
           'Цену ноябрьского транша стороны не назвали; по данным CNews, оплата прошла акциями '
           'самой «Группы Астра» из квазиказначейского пакета, а ограничение на их перепродажу будет сниматься '
           'по частям в течение 2027 года.')
RESTORED_VAL = ('Официально сумму не раскрывали. По оценке сооснователя «МойОфис» Дмитрия Комиссарова, сделка могла '
                'обойтись примерно в 100 млн ₽; другие эксперты оценивают ее в 80–100 млн ₽.')
OLD_FIN = '—'
NEW_FIN = ('Доплата по ноябрьскому траншу прошла не деньгами: по данным CNews, «Группа Астра» расплатилась '
           'собственными акциями из квазиказначейского пакета, а ограничение на их перепродажу снимается '
           'поэтапно в течение 2027 года.')


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    card = by_id.get(CARD_ID)
    if card is None:
        print('ОТКАЗ: карточки %s нет в базе' % CARD_ID)
        return 1

    assert card['eco']['val'] == OLD_VAL, card['eco']['val']
    assert card['eco']['fin'] == OLD_FIN, card['eco']['fin']

    print('ПРАВКА %s' % CARD_ID)
    print('  eco.val -> (транш мая без абзаца об оплате акциями)')
    print('  eco.fin : %r -> (текст об оплате акциями)' % OLD_FIN)
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    card['eco']['val'] = RESTORED_VAL
    card['eco']['fin'] = NEW_FIN

    fresh = json.load(open(DATA, encoding='utf-8'))
    fresh_by_id = {d['id']: d for d in fresh['deals']}
    fresh_card = fresh_by_id[CARD_ID]
    assert fresh_card['eco']['val'] == OLD_VAL, 'карточку кто-то уже поправил — перечитайте'
    idx = fresh['deals'].index(fresh_card)
    fresh['deals'][idx] = card

    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
