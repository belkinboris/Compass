"""11 ноября 2026, владелец: «как упустили? Срочно делай проект карты и поста» — «Структуры Чачавы утратили контроль над АО „О23“» (фильтр счел новость не сделкой). Как 9 ноября с ККМП:
конечно сделки». Новости из архивов каналов юрфирм, остановленные воротами
(«заголовок обрезан», «предмет не установлен»), берутся в работу так же, как по
кнопке «Это сделка» (approve.py): черновик -> карточка в pending.json, решение
`take` в памяти сырья. Дальше карточку ведет приток: чтение, приемка, консоль.
Без --write — сухой прогон."""
import glob, json, os, sys
from datetime import datetime, timezone
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path[:0] = [os.path.join(ROOT, 'pipeline', 'ingest'), os.path.join(ROOT, 'pipeline')]
import promote, link_parties  # noqa: E402
IDS = ['d57485172']
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def drafts_by_id():
    out = {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'data', 'inbox', 'hold', '*.json'))) + \
            sorted(glob.glob(os.path.join(ROOT, 'data', 'inbox', 'drafts', '*.json'))):
        doc = json.load(open(f, encoding='utf-8'))
        for d in (doc.get('drafts') if isinstance(doc, dict) else doc) or []:
            if isinstance(d, dict) and d.get('draft_id') in IDS:
                out[d['draft_id']] = d
    return out


def main(write):
    found = drafts_by_id()
    missing = [i for i in IDS if i not in found]
    assert not missing, missing
    pending = json.load(open(PENDING, encoding='utf-8'))
    data = json.load(open(DATA, encoding='utf-8'))
    state = promote.load_state()
    ids = {c['id'] for c in pending['cards']} | {d['id'] for d in data['deals']}
    idx = link_parties.build_index(data['companies'])
    now = datetime.now(timezone.utc).isoformat(timespec='seconds')
    for did in IDS:
        draft = found[did]
        card = promote.to_card(draft, promote.new_id(ids))
        link_parties.link_card(card, idx, data['companies'])
        ids.add(card['id'])
        card['pending_since'] = now
        card['from_raw'] = {'draft_id': did, 'title': str(draft.get('title') or '')[:200]}
        pending['cards'].append(card)
        state.setdefault('decided_raw', {})[did] = 'take'
        state.setdefault('raw_titles', {})[promote.raw_key(draft.get('title'))] = 'take'
        print('  %s -> %s  %s' % (did, card['id'], str(draft.get('title'))[:80]))
    if write:
        json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        promote.save_state(state)
        print('Записано.')
    else:
        print('Сухой прогон. Запись — с ключом --write.')


if __name__ == '__main__':
    main('--write' in sys.argv)
