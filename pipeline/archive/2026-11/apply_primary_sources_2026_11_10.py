"""Первоисточники за заметками mergers.ru (10 ноября 2026, бэклог G21): статьи, на
которые ссылается заметка агрегатора, — первыми в src карточки. Берутся только
адреса из draft_primary_*.json, которые помощник открыл, признал статьей о той же
сделке и которые лежат в кэше (fetch_article_texts.py) — непрочитанные (РБК, ТАСС,
Forbes отдают роботу пустую страницу) не вносятся. Без ключа — сухой прогон."""
import glob, json, os, sys
sys.path.insert(0, 'pipeline/ingest'); sys.path.insert(0, 'pipeline')
import accept_card  # noqa: E402
FILES = sorted(glob.glob('data/inbox/seizure_cards/draft_primary_*.json'))
SKIP = {'gfebe16ad', 'gb89d3a84'}   # ссылка о другой сделке (аукцион 2021) / уже исправлена


def plan():
    out = []
    for f in FILES:
        for it in json.load(open(f, encoding='utf-8'))['items']:
            if it['id'] in SKIP or not it.get('fetched'):
                continue
            for label, url in it.get('add') or []:
                if accept_card.cached_text_available(url):
                    out.append((it['id'], label, url))
    return out


def apply(paths, adds):
    done = 0
    for path, key in paths:
        data = json.load(open(path, encoding='utf-8'))
        for c in data[key]:
            mine = [(l, u) for cid, l, u in adds if cid == c['id']]
            have = {accept_card._url_key(s[1]) for s in c.get('src') or []}
            new = [[l, u] for l, u in mine if accept_card._url_key(u) not in have]
            if new:
                c['src'] = new + list(c.get('src') or [])
                done += len(new)
        if '--write' in sys.argv:
            json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            open(path, 'a').write('\n') if path.endswith('deals_promoted.json') else None
    return done


adds = plan()
for a in adds:
    print(*a)
print('адресов к записи: %d, карточек: %d' % (len(adds), len({a[0] for a in adds})))
n = apply([('static/data/deals_promoted.json', 'deals'), ('static/data/pending.json', 'cards')], adds)
print(('записано: %d' if '--write' in sys.argv else 'сухой прогон: %d') % n)
