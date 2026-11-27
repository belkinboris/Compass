# -*- coding: utf-8 -*-
"""gdc13aeb3 (очередь): запись этапа переписана своими словами, тема снята.

Черновик положил в events[0].note начало статьи АБН дословно и оборвал его многоточием
(находки приемки: «текст обрывается», «23 слова подряд как в источнике»). Этап — заявление
Altria от 26 ноября 2026 года: «Altria Group, Inc. (“Altria”) notes the recent press speculation
and confirms that it is considering a possible offer for Imperial Brands.»
(https://6ix.com/news/statement-re-possible-offer-94, уже в src). Тема «Правкомиссия / указ
президента» пришла из слов об указе в заголовке новости; сама сделка — покупка британской
компании, указ к ней не относится.

    python3 pipeline/fix_gdc13aeb3_event_2026_11_27.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
ID = 'gdc13aeb3'
U_ALTRIA = 'https://6ix.com/news/statement-re-possible-offer-94'
NEW = {'kind': 'negotiations', 'date': '2026-11-26',
       'title': 'Altria подтвердила, что рассматривает покупку Imperial Brands',
       'note': 'Altria официально сообщила, что изучает возможность сделать предложение о покупке '
               'Imperial Brands и обсуждает с третьей стороной продажу ей части бизнеса. '
               'Совет директоров Imperial Brands ответил, что обращений не получал.',
       'source': ['Altria, заявление о возможном предложении (26.11.2026)', U_ALTRIA]}


def main(write):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next(c for c in data['cards'] if c.get('id') == ID)
    ev = card.get('events') or []
    if ev and ev[0] == NEW:
        print('уже применено'); return
    assert len(ev) == 1 and ev[0]['note'].startswith('Японская Japan Tobacco (JT) и американская Altria'), ev
    assert card.get('themes') == ['Правкомиссия / указ президента'], card.get('themes')
    print('events[0]:', ev[0]['title'], '->', NEW['title'])
    print('themes:', card['themes'], '-> []')
    if write:
        card['events'] = [NEW]
        card['themes'] = []
        json.dump(data, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
