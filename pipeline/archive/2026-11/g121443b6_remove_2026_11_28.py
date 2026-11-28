"""g121443b6 («Государство передаст ВСК акции восьми обществ»): снята с сайта, поста нет.
Владелец, 28 ноября 2026: «убери карту и не делай пост. Государство просто внесло в имущество
публично-правовой компании» — взнос в имущество, а не сделка. Адреса источников запоминаются в
`discarded_urls`, чтобы новость не вернулась. Профиль ВСК (gc99d37c0) не трогается.
    python3 pipeline/archive/2026-11/g121443b6_remove_2026_11_28.py [--write]"""
import json, os, sys
from datetime import datetime, timezone
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
STATE = os.path.join(ROOT, 'data', 'inbox', 'moderation_state.json')
ID = 'g121443b6'
data = json.load(open(BASE, encoding='utf-8'))
deal = next(x for x in data['deals'] if x['id'] == ID)
assert deal.get('no_post'), 'у карточки должен стоять no_post'
print('снимаем:', deal['title'], '| метка поста:', data.get('telegram_posts', {}).get(ID))
if '--write' not in sys.argv:
    print('сухой прогон'); sys.exit()
data['deals'] = [x for x in data['deals'] if x['id'] != ID]
data.get('telegram_posts', {}).pop(ID, None)
json.dump(data, open(BASE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
state = json.load(open(STATE, encoding='utf-8'))
now = datetime.now(timezone.utc).isoformat(timespec='seconds')
for s in deal.get('src') or []:
    if len(s) > 1 and str(s[1]).startswith('http'):
        state.setdefault('discarded_urls', {})[str(s[1])] = {'id': ID, 'title': deal.get('title'), 'at': now, 'by': 'owner_chat'}
json.dump(state, open(STATE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('записано')
