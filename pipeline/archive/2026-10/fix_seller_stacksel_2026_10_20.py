"""«Экспанта»/«Стаксель» (ga09376f6) — продавец по решению партнера, 20 октября 2026.

Партнер: «Добавить в качестве продавца чувака из ЕГРЮЛ, который единственный
акционер там». До сделки 100% ООО «СиЭс Технологии» по ЕГРЮЛ принадлежали
Владимиру Скороходу (запись 25.05.2018, datanewton), значит 25% «Экспанта»
получила от него. Вписываем продавца, источник — история участников ЕГРЮЛ;
оговорка, что переход доли в реестре еще не отражен, остается в law.struct.
Сбрасываем post_draft_sent: send_drafts.py --write пришлет новый проект поста.
Без ключа — сухой прогон; --write перечитывает pending.json и пишет.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'static', 'data', 'pending.json')
DN = 'https://datanewton.ru/contragents/1137746030982/history/timeline'
SELLER = 'Владимир Скороход'
STRUCT = (
    'Продавец — Владимир Скороход: по истории участников ЕГРЮЛ (проверено 19 октября 2026 года) он '
    'единственный участник ООО «СиЭс Технологии», ему принадлежат 100% с 25 мая 2018 года, уставный '
    'капитал — 10 тыс. ₽. Переход 25% к «Экспанте» в реестре пока не отражен. Сделка рассчитана на два '
    'транша: после второго доля «Экспанты» дойдет до 50%.')
NOTE = ('продавец — единственный участник по ЕГРЮЛ до сделки (datanewton, ОГРН 1137746030982, запись '
        '25.05.2018: Владимир Скороход 100%); вписан по решению партнера 20.10.2026; физлицо, профиль не ставится')


def main(write):
    pending = json.load(open(P, encoding='utf-8'))
    c = next(c for c in pending['cards'] if c['id'] == 'ga09376f6')
    if c.get('seller') == SELLER:
        print('уже вписан'); return
    assert not c.get('seller') and not c.get('seller_id'), c.get('seller')
    assert c['law']['struct'].startswith('По истории участников ЕГРЮЛ'), c['law']['struct'][:60]
    c['seller'] = SELLER
    c['law']['struct'] = STRUCT
    c.setdefault('party_evidence', {})['seller'] = [
        {'value': SELLER, 'method': 'registry_sole_owner', 'url': DN}]
    c.setdefault('accepted_notes', {}).setdefault('no_profile', {})['seller'] = NOTE
    c['post_draft_sent'] = False
    c.pop('post_preview', None)
    print('ga09376f6 продавец:', SELLER)
    if write:
        with open(P, 'w', encoding='utf-8') as f:
            json.dump(pending, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('записано')
    else:
        print('сухой прогон')


if __name__ == '__main__':
    main('--write' in sys.argv)
