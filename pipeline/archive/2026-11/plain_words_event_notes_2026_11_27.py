"""27.11.2026: правило «сам/сама» (text_rules.plain_words) теперь держит любую запись —
снять слово в шести записях истории событий (смысл не меняется)."""
import json, sys
P = 'static/data/deals_promoted.json'
R = [('gx4padel01', 0, 'а не сами компании', 'а не компании'),
     ('g55008cf1', 0, '— сам покупатель называет', '— покупатель называет'),
     ('gbb89fc13', 0, 'сама покупка намечена', 'покупка намечена'),
     ('gfa14411d', 0, 'Сама компания подчеркивает', 'Компания подчеркивает'),
     ('gafde5488', 1, 'Само издание называет', 'Издание называет'),
     ('g002710cf', 1, '(сам комбинат, «СБП-Инвест»', '(комбинат, «СБП-Инвест»')]
d = json.load(open(P, encoding='utf-8'))
cards = {c['id']: c for c in d['deals']}
for cid, k, old, new in R:
    e = cards[cid]['events'][k]
    if new in e['note'] and old not in e['note']:
        continue
    assert e['note'].count(old) == 1, (cid, k)
    e['note'] = e['note'].replace(old, new); print('fix', cid, k)
if '--write' in sys.argv:
    json.dump(d, open(P, 'w', encoding='utf-8'), indent=1, ensure_ascii=False); print('written')


# Языковая правка eco.share gx4padel01 («сами юрлица» → «юрлица») — подтверждение для fact_edit_guard.
if '--log-share' in sys.argv:
    sys.path.insert(0, 'pipeline')
    import fact_edit_guard
    d = json.load(open(P, encoding='utf-8'))
    c = next(x for x in d['deals'] if x['id'] == 'gx4padel01')
    v = c['eco']['share']
    assert 'юрлица Rocket Padel' in v and 'сами юрлица' not in v
    if not any(r.get('field') == 'eco.share' and r.get('new') == v for r in c.get('fact_log') or []):
        fact_edit_guard.log(c, 'eco.share', v, 'Он не раскрыл условия сделки, но объяснил, что в ее периметр вошли 3 действующих клуба в Кемерово, Волгограде и Уфе на 18 кортов, а также бренд.',
                            'https://www.kommersant.ru/doc/9042452', 'вычитка 27.11.2026')
        json.dump(d, open(P, 'w', encoding='utf-8'), indent=1, ensure_ascii=False); print('logged')
