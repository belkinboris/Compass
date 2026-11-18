# -*- coding: utf-8 -*-
"""g772c17d9: карточка ушла в консоль (черновик + пост) со снимком поста ДО
правки sum/eco.sum (добавлена пометка «(по оценке)» и sum_basis: estimate,
18 ноября 2026) и ДО переписки law.struct про покупателя-SPV. `post_preview`
несет СТАРЫЙ текст — «Сумма: 5–8 млрд ₽» без пометки «(по оценке)», а
send_telegram.py при публикации отдает приоритет сохраненному post_preview
перед автоформатом (см. докстрою у `_post_text_for` в send_telegram.py).
Не снять — значит опубликовать в канал цену сделки как состоявшийся факт,
хотя это оценка СМИ (находка второго чтения).

Снимаем draft_sent/post_draft_sent/post_preview, чтобы send_drafts.py
отправил карточку заново с верным текстом — тот же прием, что
fix_geddb685d_resend_2026_11_06.py (docs/intake_run.md, «Шаг 15: правка
задела то, что владелец видел»).

Без ключа — сухой прогон; запись — --write (файл перечитывается перед записью).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PENDING = os.path.join(ROOT, '..', 'static', 'data', 'pending.json')

DEAL_ID = 'g772c17d9'


def apply(data):
    n = 0
    for c in data['cards']:
        if c['id'] != DEAL_ID:
            continue
        if not any(c.get(k) for k in ('draft_sent', 'post_draft_sent', 'post_preview')):
            continue
        c.pop('draft_sent', None)
        c.pop('post_draft_sent', None)
        c.pop('post_preview', None)
        n += 1
        print('%s: draft_sent/post_draft_sent/post_preview сняты' % c['id'])
    return n


def main(write):
    apply(json.load(open(PENDING, encoding='utf-8')))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    data = json.load(open(PENDING, encoding='utf-8'))
    if apply(data):
        with open(PENDING, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
