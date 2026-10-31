"""Swordfish Security (gf6c084b9) — консультант продавцов ALUMNI Partners, 21 октября 2026.

Владелец прислал канал ALUMNI Partners (t.me/alumnipartnerslawfirm), которого
не было в источниках притока. Пост 2844: «Команда ALUMNI Partners
консультировала основателей ГК Swordfish Security в знаковой сделке для
российского рынка» (кибербезопасности) — консультант стороны продавцов.
Канал добавлен в sources.json тем же коммитом. Без ключа — сухой прогон.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
URL = 'https://t.me/alumnipartnerslawfirm/2844'
ADV = ['Консультант продавца', 'ALUMNI Partners',
       '«Команда ALUMNI Partners консультировала основателей ГК Swordfish Security в знаковой сделке для '
       'российского рынка» кибербезопасности; руководитель — партнер Антон Панченков. Источник: '
       't.me/alumnipartnerslawfirm/2844']


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    d = next(x for x in data['deals'] if x['id'] == 'gf6c084b9')
    if any(a[1] == 'ALUMNI Partners' for a in d['law'].get('adv') or []):
        print('уже есть'); return
    assert not d['law'].get('adv'), d['law'].get('adv')
    d['law']['adv'] = [ADV]
    if URL not in {s[1] for s in d.get('src') or []}:
        d['src'].append(['ALUMNI Partners (Telegram)', URL])
    print('gf6c084b9: консультант продавца — ALUMNI Partners')
    if write:
        with open(DATA, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
            f.write('\n')


if __name__ == '__main__':
    main('--write' in sys.argv)
