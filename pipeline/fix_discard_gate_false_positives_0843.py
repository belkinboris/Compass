# -*- coding: utf-8 -*-
"""Приток 11 сентября 2026 (08:43 МСК) — четыре карточки прошли ворота
ошибочно, механический разбор не понял структуру новости (поля собраны из
случайных кусков заголовка/текста поста, а не из настоящих сторон сделки):

- `ge419f326` (Mento VC/Pin) — тот же нероссийский стартап без российского
  элемента, что уже оценивался этой рутиной ранее (американский ИИ-стартап
  Pin, без связи с российским рынком) — решение то же, отклоняем.
- `geafce7e1` (Bending Spoons/Miro) — та же сделка, что уже была заведена
  карточкой `g20ec3d5e` и впоследствии осознанно отклонена другим прогоном
  притока (запись в `discarded_urls` по адресу vc.ru, отметка времени
  2026-09-11T07:09:07) — не переоткрываем то же решение по дублирующему
  источнику (телеграм-репост той же новости).
- `g969c0676` («Россия качает, Китай покупает: тандем БРИКС меняет рынок
  нефти») — аналитическая статья о динамике нефтяного рынка между Россией и
  Китаем, не сделка M&A; `buyer_name`/`asset` — обрывки заголовка («Россия
  качает, Китай» / «тандем БРИКС меняет рынок нефти»).
- `gb7f99c8b` («Банк России купил юаней на внутреннем рынке на 1,9
  миллиардов рублей») — рутинная валютная операция ЦБ, а не сделка M&A;
  ровно та категория макроэкономики/курсов, которую ворота не должны
  пропускать.

Запуск: python3 pipeline/fix_discard_gate_false_positives_0843.py [--write]
"""
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE_PATH = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

TARGETS = {
    'ge419f326': ('https://t.me/rusven/7722',
                  'Mento VC/Pin — иностранный стартап без российского элемента'),
    'geafce7e1': ('https://t.me/rusven/7724',
                  'Bending Spoons/Miro — дубль уже отклонённого решения (g20ec3d5e)'),
    'g969c0676': ('https://1prime.ru/20260911/briks-873221617.html',
                  'аналитическая статья о нефтяном рынке, не сделка'),
    'gb7f99c8b': ('https://1prime.ru/20260911/tsentrobank-873218366.html',
                  'рутинная валютная операция ЦБ, не сделка M&A'),
}


def main(write=False):
    with open(PENDING_PATH, encoding='utf-8') as f:
        pending = json.load(f)
    with open(STATE_PATH, encoding='utf-8') as f:
        state = json.load(f)

    discarded = state.setdefault('discarded_urls', {})
    kept = []
    removed = []
    for c in pending['cards']:
        if c['id'] in TARGETS:
            url, reason = TARGETS[c['id']]
            assert any(len(s) > 1 and s[1] == url for s in (c.get('src') or [])), \
                f'{c["id"]}: адрес {url} не найден среди src'
            assert url not in discarded, f'{url} уже в discarded_urls'
            discarded[url] = {
                'id': c['id'], 'title': c.get('title'),
                'at': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
                'note': reason,
            }
            removed.append((c['id'], reason))
        else:
            kept.append(c)

    assert len(removed) == len(TARGETS), \
        f'ожидались все 4 карточки, снято {len(removed)}: {removed}'
    pending['cards'] = kept

    for cid, reason in removed:
        print(f'Снята карточка {cid} — {reason}.')

    if write:
        with open(PENDING_PATH, 'w', encoding='utf-8') as f:
            json.dump(pending, f, ensure_ascii=False, indent=1)
            f.write('\n')
        with open(STATE_PATH, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('(сухой прогон, для записи — --write)')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
