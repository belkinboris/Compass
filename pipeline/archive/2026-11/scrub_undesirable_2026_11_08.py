"""8 ноября 2026, владелец: «проверь, нет ли больше у нас нежелательных
организаций, иноагентов… если есть — убрать». Снимает ссылки на издания из
расширенного source_names.UNDESIRABLE_HOSTS во всех полях карточек и
названия этих изданий из текста трех карточек (The Bell, RTVI, The Moscow
Times). Без --write — сухой прогон."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import source_names  # noqa: E402
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
TEXT = [  # (id, путь, старое, новое)
    ('g420cae8d', ('law', 'terms'), 'По данным The Bell со ссылкой на два источника', 'По данным СМИ со ссылкой на два источника'),
    ('gf174262b', ('eco', 'context'), 'Юристы, которых опросил RTVI,', 'Опрошенные журналистами юристы'),
    ('g2d90c4d5', ('law', 'appr'), 'По данным The Moscow Times,', 'По данным СМИ,'),
]


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    by = {d['id']: d for d in data['deals']}
    total = 0
    for d in data['deals']:
        n = source_names.scrub_undesirable(d)
        if n:
            print('  %s: снято ссылок %d — %s' % (d['id'], n, d['title'][:70]))
            total += n
    for k, c in data['companies'].items():
        n = source_names.scrub_undesirable(c)
        if n:
            print('  профиль %s: снято ссылок %d' % (k, n)); total += n
    for cid, (a, b), old, new in TEXT:
        v = by[cid][a][b]
        assert old in v, (cid, old)
        by[cid][a][b] = v.replace(old, new)
        print('  %s: текст «%s» → «%s»' % (cid, old, new))
    print('Всего ссылок снято: %d' % total)
    if write:
        fresh = json.load(open(DATA, encoding='utf-8'))
        assert len(fresh['deals']) == len(data['deals'])
        json.dump(data, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Записано.')
    else:
        print('Сухой прогон. Запись — с ключом --write.')


if __name__ == '__main__':
    main('--write' in sys.argv)
