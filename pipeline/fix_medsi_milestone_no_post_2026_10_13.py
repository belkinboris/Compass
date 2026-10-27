"""Веха gcf05509a-closed («Альфа-банк купил долю в «Медси»») — без поста.

13 октября 2026 Артем: в черновике вехи «Предмет: Cosmos Hotel Group и сеть
клиник «Медси», Статус: Обсуждается, Отрасль: Гостиницы и туризм» — покупку
Альфа-Банком 4,85% «Медси» приклеили этапом к общей карточке «IPO Cosmos и
«Медси»». Сделка получает свою карточку и свой пост; веху гасим так же, как
это делает кнопка «без поста» (`telegram_milestones[id] = {'no_post': True}`),
чтобы молчание ее не выпустило. Без --write — сухой прогон."""
import json, sys
from datetime import datetime, timezone
DATA = 'static/data/deals_promoted.json'
EID = 'gcf05509a-closed'

def apply(data):
    m = data.setdefault('telegram_milestones', {})
    assert EID not in m, m.get(EID)
    m[EID] = {'no_post': True, 'at': datetime.now(timezone.utc).isoformat(timespec='seconds')}
    print(EID, '->', m[EID])

apply(json.load(open(DATA, encoding='utf-8')))
if '--write' in sys.argv:
    data = json.load(open(DATA, encoding='utf-8'))
    apply(data)
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1); f.write('\n')
    print('записано')
