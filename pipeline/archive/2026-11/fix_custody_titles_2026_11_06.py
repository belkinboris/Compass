"""Заголовки карточек временного управления, где указ «забрал» / компания «лишилась» активов (6 ноября 2026).
Владелец: «Как указ что-то может забрать?» Временное управление собственность не меняет — заголовок
говорит «переданы во временное управление». Названия в кавычках не склоняются. Запуск: [--write]."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
P = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
NEW = {
 'g8a599c40': ('Указ забрал у Tarkett российские активы — временно управлять ими назначили «Центр Капитал»',
               'Российские активы Tarkett переданы во временное управление УК «Центр Капитал»'),
 'g19410fc2': ('«Каппа Рус» лишилась своих активов — временным управляющим назначен «Центр Капитал»',
               'Акции «Каппа Рус» переданы во временное управление УК «Центр Капитал»'),
}
d = json.load(open(P, encoding='utf-8'))
for card in d['deals']:
    if card['id'] in NEW:
        old, new = NEW[card['id']]
        assert card['title'] == old, (card['id'], card['title'])
        card['title'] = new
        print(card['id'], '→', new)
if '--write' in sys.argv:
    json.dump(d, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1); open(P, 'a').write('\n'); print('Записано.')
