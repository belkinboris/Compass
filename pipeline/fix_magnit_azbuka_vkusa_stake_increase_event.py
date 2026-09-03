# -*- coding: utf-8 -*-
"""«Магнит»/«Азбука вкуса» (`g91ec3558`, закрыта 30.04.2025) — почасовой
приток 3 сентября 2026 нашёл продолжение сюжета: retailer.ru сообщил, что
в июне 2026 года «Магнит» докупил ещё 0,49% ООО «Городской супермаркет»
(управляет «Азбукой вкуса») за 177,4 млн руб., увеличив прямую долю с
86,19% до 86,68% (эффективную — с 87,06% до 87,55%), сославшись на
отчётность ритейлера. Проверено дословно (WebFetch retailer.ru).

Не через `pipeline/ingest/review.py` FIXES по двум причинам сразу:
(1) `events[]` — список, FIXES умеет только скалярные поля (тот же
приём, что `fix_yugc_bts_most_minority_offer_event.py`); (2) `eco.context`
уже занят фактом из ДРУГОГО источника о том же июле 2025 года («доля
выросла с 81,55% до 84,05%») — процент расходится с тем, что называет
retailer.ru («ещё 4,64%», то есть примерно до 86,19%). Числа не сведены
друг с другом принудительно: возможно, речь о разных величинах (прямая
доля против эффективной) или один из источников неточен — ни то ни
другое не проверить без прямого доступа к отчётности «Магнита». Старое
предложение о июле 2025 года остаётся как есть, новый факт про июнь 2026
дописан ОТДЕЛЬНЫМ предложением, с указанием, откуда он взят.

Запуск: python3 pipeline/fix_magnit_azbuka_vkusa_stake_increase_event.py
        python3 pipeline/fix_magnit_azbuka_vkusa_stake_increase_event.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g91ec3558'
OLD_CONTEXT = ('Общая торговая площадь приобретаемых активов составила 100,4 '
               'тыс. кв. м. В июле «Магнит» нарастил свою долю в «Азбуке '
               'вкуса» с 81,55% до 84,05%.')
ADDED_SENTENCE = (' По данным RETAILER.ru со ссылкой на отчётность ритейлера, '
                   'в июне 2026 года «Магнит» приобрёл ещё 0,49% ООО '
                   '«Городской супермаркет» за 177,4 млн руб., увеличив '
                   'прямую долю с 86,19% до 86,68% (эффективную долю с '
                   'учётом структуры владения — с 87,06% до 87,55%).')
NEW_CONTEXT = OLD_CONTEXT + ADDED_SENTENCE

NEW_EVENT = {
    'kind': 'closed',
    'date': '2026-06-01',
    'title': 'Доля «Магнита» в «Азбуке вкуса» выросла до 86,68%',
    'note': ('«Магнит» в июне 2026 года приобрел 0,49% ООО «Городской '
             'супермаркет» (управляет сетью «Азбука вкуса»), сообщается в '
             'отчетности ритейлера. Сумма сделки составила 177,4 млн руб. '
             'Продавец пакета не раскрывается. После сделки прямая доля '
             '«Магнита» увеличилась с 86,19% до 86,68%, эффективная доля с '
             'учетом структуры владения — с 87,06% до 87,55%.'),
    'source': ['RETAILER.ru',
               'https://retailer.ru/magnit-uvelichil-dolju-v-azbuke-vkusa-do-86-68/'],
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card['eco'].get('context') == OLD_CONTEXT, (
        'eco.context уже другой: %r' % card['eco'].get('context'))
    events = card.get('events') or []
    already_has_event = any(e.get('date') == NEW_EVENT['date'] for e in events)
    already_has_context = ADDED_SENTENCE.strip() in (card['eco'].get('context') or '')

    print('ДОБАВЛЯЕТСЯ В eco.context:', repr(ADDED_SENTENCE))
    print('ДОБАВЛЯЕТСЯ СОБЫТИЕ:', repr(NEW_EVENT['title']))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 1
    if not already_has_context:
        card['eco']['context'] = NEW_CONTEXT
    if not already_has_event:
        card.setdefault('events', []).append(NEW_EVENT)
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv[1:]))
