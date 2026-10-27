"""База начинается с 2022 года: карточки старше — удалить вместе с профилями,
которые нужны только им (решение владельца, 27 октября 2026).

Сайт, описание страницы и ассистент старые карточки и так не показывали
(`SITE_MIN_YEAR = 2022`), но они оставались в файле и всплывали в счете
«всего сделок» всякий раз, когда кто-то считал по файлу: владелец —
«видимо пора просто удалить их, а то они постоянно возникают».

Что уходит:
  * сделки с годом даты меньше 2022 (193 на 27 октября 2026);
  * профили компаний, на которые не ссылается ни одна оставшаяся сделка,
    ни очередь (pending.json), ни реестр ФНС, ни `merged_companies`,
    ни сигналы, — их ключи сопоставления (`match_keys`) тоже;
  * записи `merged`, `merged_deal_stages`, `telegram_posts*`,
    `telegram_post_state`, `telegram_milestones`, адресованные удаленным
    сделкам.

    python3 pipeline/drop_pre_2022_deals.py            # сухой прогон
    python3 pipeline/drop_pre_2022_deals.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
SIGNALS = os.path.join(ROOT, 'static', 'data', 'signals.json')
MIN_YEAR = 2022


def year_of(deal):
    s = str(deal.get('date') or '')
    return int(s[:4]) if s[:4].isdigit() else None


def parties(deal):
    out = set()
    for k in ('buyer', 'seller_id', 'target', 'asset_id'):
        if deal.get(k):
            out.add(deal[k])
    for k in ('buyers', 'sellers', 'targets'):
        for v in deal.get(k) or []:
            out.add(v if isinstance(v, str) else (v or {}).get('id'))
    out.discard(None)
    return out


def _external_company_refs():
    """Профили, которые держат не сделки: очередь, реестр ФНС, сигналы."""
    refs = set()
    if os.path.exists(PENDING):
        for c in json.load(open(PENDING, encoding='utf-8')).get('cards') or []:
            refs |= parties(c)
    sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
    try:
        import fns_registry
        for row in getattr(fns_registry, 'REGISTRY', None) or []:   # список строк {company_id, inn, …}
            if isinstance(row, dict) and row.get('company_id'):
                refs.add(row['company_id'])
    except Exception:  # noqa: BLE001 — реестра может не быть в этом контуре
        pass
    if os.path.exists(SIGNALS):
        sig = json.load(open(SIGNALS, encoding='utf-8'))
        if isinstance(sig, dict):
            refs |= set(sig.keys())
    return refs


def plan(base):
    deals = base['deals']
    gone = {d['id'] for d in deals if (year_of(d) or MIN_YEAR) < MIN_YEAR}
    kept = [d for d in deals if d['id'] not in gone]
    held = set().union(*[parties(d) for d in kept]) if kept else set()
    held |= _external_company_refs()
    mc = base.get('merged_companies') or {}
    held |= set(mc.keys()) | set(mc.values())
    only_old = set().union(*[parties(d) for d in deals if d['id'] in gone]) if gone else set()
    orphans = (only_old - held) & set(base['companies'])
    return gone, orphans


def apply(base, gone, orphans):
    base['deals'] = [d for d in base['deals'] if d['id'] not in gone]
    for cid in orphans:
        base['companies'].pop(cid, None)
        (base.get('match_keys') or {}).pop(cid, None)
    for key in ('merged', 'merged_deal_stages', 'telegram_posts', 'telegram_posts_realty',
                'telegram_post_state', 'telegram_milestones'):
        table = base.get(key)
        if isinstance(table, dict):
            for k in [k for k, v in table.items() if k in gone or (isinstance(v, str) and v in gone)]:
                table.pop(k)
    return base


def main(argv):
    write = '--write' in argv
    base = json.load(open(DATA, encoding='utf-8'))
    gone, orphans = plan(base)
    print('Сделок до %d года: %d; профилей, нужных только им: %d.' % (MIN_YEAR, len(gone), len(orphans)))
    if not write:
        print('Сухой прогон. Применение — с ключом --write.')
        return 0
    fresh = json.load(open(DATA, encoding='utf-8'))   # перечитать прямо перед записью
    gone2, orphans2 = plan(fresh)
    assert gone2 == gone and orphans2 == orphans, 'база изменилась между прогоном и записью — повторите'
    before = len(fresh['deals'])
    apply(fresh, gone, orphans)
    assert len(fresh['deals']) == before - len(gone)
    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Удалено сделок: %d, профилей: %d. Осталось сделок: %d.' % (len(gone), len(orphans), len(fresh['deals'])))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
