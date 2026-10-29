# -*- coding: utf-8 -*-
"""«Агропромкредит» (g1f8414a3): убрать второе «Сделка завершена» от 29 октября
2026 (пересказ Mergers.ru закрытия 27 октября — enrich принял дату новости за
дату события), ссылку Mergers.ru дописать источником к этапу 27 октября.
Без --write — сухой прогон. Правило теперь в enrich.proposals (закрытие у сделки одно)."""
import io, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
URL = 'https://mergers.ru/news/Bank-Agropromkredit-prodali-na-aukcione-za-14-mlrd-rublej-holdingu-SFI-87709'

def main(write):
    data = json.load(io.open(DATA, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == 'g1f8414a3')
    events = deal['events']
    assert [e['kind'] for e in events] == ['closed', 'closed'], events
    assert events[1]['date'] == '2026-10-29' and events[1]['source'][1] == URL, events[1]
    first = events[0]
    assert first['date'] == '2026-10-27'
    sources = [list(s) for s in (first.get('sources') or [first['source']])]
    if URL not in {u for _l, u in sources}:
        sources.append(['Mergers.ru', URL])
    first['sources'] = sources
    deal['events'] = [first]
    print('g1f8414a3: этапов %d -> 1; источников у закрытия: %d' % (len(events), len(sources)))
    if write:
        json.dump(data, io.open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('записано')
    else:
        print('сухой прогон; --write чтобы записать')

if __name__ == '__main__':
    main('--write' in sys.argv)
