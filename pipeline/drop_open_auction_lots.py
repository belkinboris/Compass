"""Лоты на торгах без результата — удалить из базы (решение владельца,
21 ноября 2026).

Владелец: «все тендеры уберем незакрытые пожалуйста из аналитики и из
карточек и в консоль больше не предлагай». На вопрос «скрыть или удалить»:
«Удали. Мы уже пытались скрывать сделки до 2022 года, но они постоянно
где-то светились и возвращались в базу или попадали в аналитику».

Что уходит:
  * карточки типа «Продажа с торгов» со статусом не «Закрыта» (лот
    выставлен, торги не состоялись) — 92 на 21 ноября 2026;
  * профили компаний, нужные только им, и их ключи сопоставления;
  * записи `merged`, `merged_deal_stages`, `telegram_posts*`,
    `telegram_post_state`, `telegram_milestones`, адресованные удаленным
    карточкам (тем же порядком, что `drop_pre_2022_deals.py`).

Проданный на торгах лот (статус «Закрыта») остается: это сделка. Новые лоты
без результата не пускают ворота притока (`promote.is_open_listing`).
Правки к удаленным карточкам в `pipeline/ingest/fixes/` снимает
`remove_fixes_for_id.py` — список id печатается в конце.

    python3 pipeline/drop_open_auction_lots.py            # сухой прогон
    python3 pipeline/drop_open_auction_lots.py --write
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drop_pre_2022_deals as pre  # noqa: E402

DATA = pre.DATA


def is_open_lot(deal):
    return deal.get('type') == 'Продажа с торгов' and deal.get('status') != 'Закрыта'


def plan(base):
    deals = base['deals']
    gone = {d['id'] for d in deals if is_open_lot(d)}
    kept = [d for d in deals if d['id'] not in gone]
    held = set().union(*[pre.parties(d) for d in kept]) if kept else set()
    held |= pre._external_company_refs()
    mc = base.get('merged_companies') or {}
    held |= set(mc.keys()) | set(mc.values())
    only_gone = set().union(*[pre.parties(d) for d in deals if d['id'] in gone]) if gone else set()
    orphans = (only_gone - held) & set(base['companies'])
    return gone, orphans


def main(argv):
    write = '--write' in argv
    base = json.load(open(DATA, encoding='utf-8'))
    gone, orphans = plan(base)
    print('Лотов на торгах без результата: %d; профилей, нужных только им: %d.' % (len(gone), len(orphans)))
    for d in base['deals']:
        if d['id'] in gone:
            print('  %s  %-14s %s' % (d['id'], d.get('status'), str(d.get('title'))[:70]))
    if not write:
        print('Сухой прогон. Применение — с ключом --write.')
        return 0
    fresh = json.load(open(DATA, encoding='utf-8'))   # перечитать прямо перед записью
    gone2, orphans2 = plan(fresh)
    assert gone2 == gone and orphans2 == orphans, 'база изменилась между прогоном и записью — повторите'
    before = len(fresh['deals'])
    pre.apply(fresh, gone, orphans)
    assert len(fresh['deals']) == before - len(gone)
    assert not any(is_open_lot(d) for d in fresh['deals'])
    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Удалено карточек: %d, профилей: %d. Осталось сделок: %d.' % (len(gone), len(orphans), len(fresh['deals'])))
    print('Снять правки: python3 pipeline/remove_fixes_for_id.py %s --write' % ' '.join(sorted(gone)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
