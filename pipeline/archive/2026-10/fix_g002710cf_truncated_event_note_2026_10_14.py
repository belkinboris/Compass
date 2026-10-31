# -*- coding: utf-8 -*-
"""`enrich.py --write` (прогон 20:20 МСК, 14 октября) дописал карточке
`g002710cf` (Соликамскбумпром/Юнь Чоу) первый этап (`events[0]`) из
статьи URA.RU, которая ее и построила, — и обрезал цитату многоточием
на середине предложения: «...погасит его огромные…» вместо «...погасит
его огромные миллиардные долги и наладит производственный процесс.»
Тот же класс, что `truncated` в KNOWN_ISSUES.md (`fix_g21795ec9_
truncated_note.py`). Источник под рукой (data/inbox/raw/2026-10-14-
articles.jsonl) — дописываю до конца предложения, а не просто снимаю
многоточие.

Запуск:
    python3 pipeline/fix_g002710cf_truncated_event_note_2026_10_14.py            # сухой прогон
    python3 pipeline/fix_g002710cf_truncated_event_note_2026_10_14.py --write    # применить
"""
import json
import sys

DATA = '/home/user/Compass/static/data/deals_promoted.json'
CARD_ID = 'g002710cf'

OLD = ('Представители пермского АО «Соликамскбумпром» на судебном заседании по делу о '
       'банкротстве предприятия сообщили о планах заключить сделку с китайской компанией '
       '«Юнь Чоу». По их словам, зарубежный инвестор приобретет 83,3% акций комбината, '
       'погасит его огромные…')
NEW = ('Представители пермского АО «Соликамскбумпром» на судебном заседании по делу о '
       'банкротстве предприятия сообщили о планах заключить сделку с китайской компанией '
       '«Юнь Чоу». По их словам, зарубежный инвестор приобретет 83,3% акций комбината, '
       'погасит его огромные миллиардные долги и наладит производственный процесс. '
       'Подписание договора купли-продажи ожидается до конца года.')


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    assert card['events'][0]['note'] == OLD, card['events'][0]['note']

    print('ПРАВКА %s: events[0].note (убрано многоточие, дописано до конца предложений)' % CARD_ID)
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(DATA, encoding='utf-8'))
    fresh_card = next(d for d in fresh['deals'] if d['id'] == CARD_ID)
    assert fresh_card['events'][0]['note'] == OLD, 'кто-то уже поправил — перечитайте'
    fresh_card['events'][0]['note'] = NEW
    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
