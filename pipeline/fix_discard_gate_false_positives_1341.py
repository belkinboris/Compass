# -*- coding: utf-8 -*-
"""Приток 11 сентября 2026 (13:41 МСК) — две карточки прошли ворота
ошибочно:

- `gc78ff126` (Bending Spoons/Miro, incrussia.ru) — та же сделка, что уже
  сознательно отклонена ЭТИМ ЖЕ прогоном рутины утром (карточка
  `g20ec3d5e`, discarded_urls по vc.ru, 07:09 UTC, подтверждено повторно
  в 08:44 UTC по телеграм-репосту) — Miro давно американская компания
  (сама первая отклонённая карточка называла её «американский сервис...
  с основателями из Перми»), российского бенефициара сделки источники не
  называют. Не переоткрываем то же решение по третьему репосту той же
  новости.
- `gc3707f3b` («ЦБ сейчас продает золото в рамках бюджетного правила») —
  рутинная операция Банка России по бюджетному правилу (управление
  резервами), не сделка M&A; тот же класс, что уже отклонённая утром
  `gb7f99c8b` (ЦБ покупает юани) — валютно-товарные операции ЦБ никогда
  не сделки.

Запуск: python3 pipeline/fix_discard_gate_false_positives_1341.py [--write]
"""
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
STATE_PATH = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')

TARGETS = {
    'gc78ff126': ('https://incrussia.ru/news/sozdannuyu-rossiyanami-miro-pokupayut-za-1-36-mlrd-na-90-deshevle-pikovoj-otsenki/',
                  'Bending Spoons/Miro — третий репост уже отклонённого решения (g20ec3d5e)'),
    'gc3707f3b': ('https://1prime.ru/20260911/tsb-873242466.html',
                  'рутинная продажа золота ЦБ по бюджетному правилу, не сделка M&A'),
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
                '%s: адрес %s не найден среди src' % (c['id'], url)
            discarded[url] = {'id': c['id'], 'title': c.get('title'),
                               'at': datetime.datetime.utcnow().isoformat() + 'Z',
                               'note': reason}
            removed.append(c['id'])
        else:
            kept.append(c)

    assert set(removed) == set(TARGETS), 'не все карточки найдены: %r' % (set(TARGETS) - set(removed))
    pending['cards'] = kept

    print('Удалено карточек: %s' % ', '.join(removed))

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
