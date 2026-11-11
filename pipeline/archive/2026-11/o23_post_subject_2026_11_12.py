# -*- coding: utf-8 -*-
"""Карточка очереди g90767425 («О23» / Ozon): строка «Предмет» в проекте поста.

Второе чтение 12 ноября 2026: шаблон поста ставит в «Предмет» имя и описание профиля
(«О23 — акционерное общество, крупнейший акционер Ozon»), и из поста пропадает главное —
что передан контролирующий пакет и что у «О23» 34,95% Ozon. Долю из `eco.share` шаблон
берет, только когда она начинается с числа. Описание профиля под одну сделку не
переписывается (profile_desc_is_event), поэтому проект поста задан текстом
(`post_override`) — те же строки, что дает шаблон, отличается только «Предмет».
Владелец правит и одобряет его в консоли, как любой проект поста.

    python3 pipeline/archive/2026-11/o23_post_subject_2026_11_12.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path[:0] = [os.path.join(ROOT, 'pipeline', 'publish'), os.path.join(ROOT, 'pipeline'), ROOT]
import format_post  # noqa: E402

PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
CID = 'g90767425'
OLD_LINE = '<b>Предмет:</b> О23 — акционерное общество, крупнейший акционер Ozon.'
NEW_LINE = '<b>Предмет:</b> контролирующий пакет акций АО «О23», которому принадлежит 34,95% акций Ozon'
LINK = '\n\nПодробнее в <a href="https://projectcompass.ru/#/deal/%s">карточке сделки</a>' % CID


def apply(doc, companies):
    c = next(x for x in doc['cards'] if x['id'] == CID)
    if c.get('post_override'):
        assert NEW_LINE in c['post_override'], c['post_override']
        return None
    assert c.get('seller') == 'Александр Чачава' and c.get('asset') == 'Контролирующий пакет акций АО «О23»'
    auto = format_post.render(c, companies)
    # Берем текст шаблона как есть и меняем одну строку; ссылку на карточку
    # `send_drafts.draft_post_text` допишет сам (with_card_link).
    assert auto.count(OLD_LINE) == 1 and auto.endswith(LINK), auto
    c['post_override'] = auto[:-len(LINK)].replace(OLD_LINE, NEW_LINE)
    return c['post_override']


def main(write):
    companies = json.load(open(DATA, encoding='utf-8'))['companies']
    text = apply(json.loads(open(PENDING, encoding='utf-8').read()), companies)
    print(text if text else 'Уже записано.')
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    fresh_raw = open(PENDING, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    if apply(fresh, companies):
        with open(PENDING, 'w', encoding='utf-8') as f:
            f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
        print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
