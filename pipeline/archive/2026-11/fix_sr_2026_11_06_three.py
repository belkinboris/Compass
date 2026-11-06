# -*- coding: utf-8 -*-
"""Второе чтение 6 ноября 2026, птицефабрика «Островная» (g8317fa58): то, что не
умеют review.py и proofread.py.

1. Описание профиля g0a8a70c9. Строка поста «Предмет» читалась «Птицефабрика
   «Островная» — юрлицо — АО «Птицефабрика «Островная»», 100% акций держит
   правительство…»: format_post._pick_novel_sentences берет первым кандидатом
   предложение с «кавычками», а им было второе, служебное («Юрлицо — АО …»).
   Юрлицо уже стоит в `legal_short` профиля, поэтому из описания оно уходит,
   а первое предложение говорит, что это за предприятие и чье оно: пост
   печатает «Птицефабрика «Островная» — единственная птицефабрика на
   Сахалине, все ее акции принадлежат правительству Сахалинской области.»
   (проверено рендером format_post.render на карточке очереди). Факты те же,
   что в прежнем описании и в статьях: «единственным предприятием этого
   профиля на Сахалине» (1prime.ru), «Все акции предприятия принадлежат
   областному правительству» (Life.ru).
2. Снятый предмет «100% акций АО «Птицефабрика «Островная»»» — в
   `retracted.asset` карточки (docs/card_editing.md, «Снятое значение — в
   retracted»): акции не переходили и в управление не передавались, новый
   предмет — «управление птицефабрикой «Островная»» — ставит запись
   pipeline/ingest/fixes/written_sr_2026_11_06_three.py через review.py.

Запуск: python3 pipeline/archive/2026-11/fix_sr_2026_11_06_three.py [--write]
Без ключа — сухой прогон. Файлы перечитываются прямо перед записью.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

PROFILE = 'g0a8a70c9'
DESC_OLD = ('Единственный производитель яиц на Сахалине. Юрлицо — АО «Птицефабрика «Островная»», '
            '100% акций держит правительство Сахалинской области; в 2022 и 2024 годах предприятие '
            'теряло поголовье из-за вспышек птичьего гриппа, а в мае 2026 года временно '
            'останавливало продажи.')
DESC_NEW = ('Единственная птицефабрика на Сахалине, все ее акции принадлежат правительству '
            'Сахалинской области. В 2022 и 2024 годах предприятие теряло поголовье из-за вспышек '
            'птичьего гриппа, а в мае 2026 года временно останавливало продажи.')

CARD = 'g8317fa58'
ASSET_RETRACTED = '100% акций АО «Птицефабрика «Островная»»'


def main(write=False):
    base = json.load(open(BASE, encoding='utf-8'))
    pending = json.load(open(PENDING, encoding='utf-8'))
    changed_base = changed_pending = False

    prof = base['companies'][PROFILE]
    if prof.get('desc') == DESC_NEW:
        print('%s desc: уже исправлено' % PROFILE)
    else:
        assert prof.get('desc') == DESC_OLD, prof.get('desc')
        assert prof.get('legal_short') == 'АО «Птицефабрика «Островная»»', prof.get('legal_short')
        prof['desc'] = DESC_NEW
        changed_base = True
        print('%s desc -> %s' % (PROFILE, DESC_NEW))

    card = next(c for c in pending['cards'] if c['id'] == CARD)
    gone = card.setdefault('retracted', {}).setdefault('asset', [])
    if ASSET_RETRACTED in gone:
        print('%s retracted.asset: уже есть' % CARD)
    else:
        # Предмет на карточке — либо еще старый (review.py --write не прошел),
        # либо уже новый; другое значение значит, что карточку правили без нас.
        assert card.get('asset') in (ASSET_RETRACTED, 'управление птицефабрикой «Островная»'), card.get('asset')
        gone.append(ASSET_RETRACTED)
        changed_pending = True
        print('%s retracted.asset += %s' % (CARD, ASSET_RETRACTED))
    if not card['retracted'].get('asset'):
        card['retracted'].pop('asset', None)
    if not card['retracted']:
        card.pop('retracted')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    if changed_base:
        json.dump(base, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        open(BASE, 'a', encoding='utf-8').write('\n')
    if changed_pending:
        json.dump(pending, open(PENDING, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        open(PENDING, 'a', encoding='utf-8').write('\n')
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
