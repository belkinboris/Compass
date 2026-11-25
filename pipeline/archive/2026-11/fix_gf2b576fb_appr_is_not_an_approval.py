"""«Поварская Плаза» (gf2b576fb): в «Согласованиях» стояла дата решения суда.

Решение суда об обращении в доход государства — не согласование органа
(`test_data.test_approval_names_a_body` остановил публикацию 25 ноября 2026).
Фраза переносится в «Структуру», «Согласования» — прочерк.

    python3 pipeline/archive/2026-11/fix_gf2b576fb_appr_is_not_an_approval.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OLD = 'Решение вынесено 23 ноября 2026 года и обращено к немедленному исполнению в день оглашения.'


def main(write):
    done = 0
    for rel, key in (('static/data/deals_promoted.json', 'deals'), ('static/data/pending.json', 'cards')):
        path = os.path.join(ROOT, rel)
        data = json.load(open(path, encoding='utf-8'))      # читается прямо перед записью
        for card in data.get(key) or []:
            if card.get('id') != 'gf2b576fb':
                continue
            law = card['law']
            if law.get('appr') == '—':
                print('%s: уже исправлено' % rel)
                continue
            assert law.get('appr') == OLD, law.get('appr')
            assert OLD not in law['struct']
            law['struct'] = law['struct'].rstrip() + ' ' + OLD
            law['appr'] = '—'
            done += 1
            print('%s: исправлено' % rel)
            if write:
                json.dump(data, open(path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Правок: %d%s' % (done, '' if write else ' (сухой прогон)'))


if __name__ == '__main__':
    main('--write' in sys.argv)
