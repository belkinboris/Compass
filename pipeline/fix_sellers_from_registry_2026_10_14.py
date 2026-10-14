"""Продавцы, найденные по ЕГРЮЛ (история участников, datanewton.ru) и в
тексте самих карточек — 14 октября 2026, поручение владельца: «если это ООО,
то по реестру точно можно проверить, кто им владел… источник нужно дописать
в список источников». Берутся только случаи без сомнений: смена участника
«было → стало» в реестре на дату сделки и полное имя (у остальных находок
реестр открывает физлиц только инициалами — их не пишем, чтобы не гадать
с именами). Доказательство — `party_evidence.seller`, адрес — в `src`.
Без ключа — сухой прогон, запись по --write."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
DN = 'https://datanewton.ru/contragents/%s/history/timeline'
ROWS = [
    # id, продавец, адрес доказательства, имя источника (None — уже в src карточки)
    ('g0b187624', 'ООО «Металлстандарт»', DN % '1185050008274', 'ЕГРЮЛ: история участников ООО «ДМЦ»'),
    ('gf080e8f0', 'ООО «Управление»', DN % '1257800029398', 'ЕГРЮЛ: история участников «ЦОД СПб»'),
    ('gda6baa02', 'SBDA Group', DN % '1137746959900', 'ЕГРЮЛ: история участников Rubbles'),
    ('g0bbc9e9e', 'Дмитрий Черобаев', DN % '1247800129631', 'ЕГРЮЛ: история акционеров АО «МПСТАТС ТЕХ»'),
    ('g7e81d8e7', 'Анастасия Чучалова', DN % '1027700404797', 'ЕГРЮЛ: история участников SuperJob'),
    ('g9edfa8d8', 'Александр и Сергей Ле-Захаровы', DN % '1117847115198', 'ЕГРЮЛ: история участников «Фотомеханики»'),
    ('g1f2895c0', 'ООО «Смарт сервис ЛТД»', 'https://www.kommersant.ru/doc/8636902', None),
]
raw = open(B, encoding='utf-8').read()
base = json.loads(raw)
cards = {d['id']: d for d in base['deals']}
for cid, seller, url, name in ROWS:
    c = cards[cid]
    assert not c.get('seller') and not c.get('seller_id'), (cid, c.get('seller'))
    c['seller'] = seller
    c.setdefault('party_evidence', {})['seller'] = [{'value': seller, 'method': 'registry_owner_history'
                                                     if 'datanewton' in url else 'manual_source_review', 'url': url}]
    if name and url not in {s[1] for s in c.get('src') or [] if len(s) > 1}:
        c.setdefault('src', []).append([name, url])
    print('%s  %-34s  %s' % (cid, seller, c['title'][:60]))
if '--write' in sys.argv:
    open(B, 'w', encoding='utf-8').write(json.dumps(base, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))
    print('записано')
