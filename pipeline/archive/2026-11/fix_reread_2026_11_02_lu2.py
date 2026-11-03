# -*- coding: utf-8 -*-
"""Вычитка 2 ноября 2026, партии l–u: развязка с прежними записями FIXES (после fix_reread_2026_11_02_lu.py).

- g304f9065 (Louis Dreyfus/«Горизонт Индастриз»): статус Обсуждается → Подписана
  (партия o: предварительные договоры купли-продажи заключены 25 мая 2026 года)
  спорит с архивной записью аудита «Закрыта → Обсуждается». По docs/card_editing.md
  новая правка структурного поля кладет отпечаток прежнего `new` в proofread_absorbed.
- g796316fe («Делимобиль»): fix_reread_2026_11_02_lu.py поставил покупателем Винченцо
  Трани, но архивная запись аудита (ROLE_WRONG) снимала его: «покупателем выступило
  ООО «Делимобиль Холдинг»». Решать без статьи, которой нет на диске, нельзя —
  покупатель возвращается к прежнему профилю g3ff23b62, карточка переходит на завтра.

    python3 pipeline/archive/2026-11/fix_reread_2026_11_02_lu2.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import review  # noqa: E402

BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def main(argv):
    raw = open(BASE, encoding='utf-8').read()
    data = json.loads(raw)
    D = {d['id']: d for d in data['deals']}
    c = D['g304f9065']
    assert c['status'] == 'Подписана'
    marks = c.setdefault('proofread_absorbed', {}).setdefault('status', [])
    fp = review.fix_fingerprint('Обсуждается')
    if fp not in marks:
        marks.append(fp)
    c = D['g796316fe']
    assert c['buyer'] == 'g33023870', c['buyer']
    c['buyer'] = 'g3ff23b62'
    print('g304f9065: отпечаток «Обсуждается» в proofread_absorbed.status; g796316fe: покупатель → g3ff23b62')
    if '--write' not in argv:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    assert open(BASE, encoding='utf-8').read() == raw
    open(BASE, 'w', encoding='utf-8').write(json.dumps(data, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))
    print('записано')


if __name__ == '__main__':
    main(sys.argv[1:])
