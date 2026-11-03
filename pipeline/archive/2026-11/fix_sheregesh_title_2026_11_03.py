# -*- coding: utf-8 -*-
"""Шерегеш (g03475792), 3 ноября 2026: заголовок — формулировка владельца;
снимок поста пересобран чисто (прежний ушел в канал с текстом консоли, владелец
пост удалил). Пост выйдет только по кнопке «Пост в канал».

    python3 pipeline/archive/2026-11/fix_sheregesh_title_2026_11_03.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'publish'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, ROOT)
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
NEW = 'Компания из ОАЭ получила контроль над ООО «Каскад восток»'


def main(argv):
    import send_drafts
    raw = open(BASE, encoding='utf-8').read()
    data = json.loads(raw)
    c = [d for d in data['deals'] if d['id'] == 'g03475792'][0]
    assert c['title'] == 'Компания из ОАЭ получила контроль над подъемниками Шерегеша', c['title']
    assert not c.get('post_approved')
    c['title'] = NEW
    c['post_preview'] = send_drafts.draft_post_text(c, data['companies'])
    print(c['post_preview'])
    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return
    assert open(BASE, encoding='utf-8').read() == raw, 'база изменилась — перезапустите'
    open(BASE, 'w', encoding='utf-8').write(json.dumps(data, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))
    print('\nзаписано')


if __name__ == '__main__':
    main(sys.argv[1:])
