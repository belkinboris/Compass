"""Карточка gdc686ec2 (Positive Technologies/CyberOK): отпечаток записи FIXES
по «Финансам покупаемой компании» после того, как приёмка переписала поле.

Что чинит. 11 сентября 2026 приёмка карточки (pipeline/ingest/accept_card.py)
заменила в `eco.target_fin` описание технологий CyberOK на выручку, убыток и
численность из ГИР БО/ЕГРЮЛ, а описание перенесла в `extra`. Описание туда
ставила запись таблицы FIXES (fix_pt_cyberok_deep_read.py), и после замены
`test_review_table_is_applied_and_not_pending` считал её неприменённой —
поле больше не совпадает с `new` записи посимвольно.

Почему это сломано. Шаг приёмки не запоминал отпечаток вытесненной записи —
в отличие от вычитки, которая для того же случая пишет `proofread_absorbed`.
Шаг починен в самом accept_card.py (`_absorb_applied_fixes`); этот скрипт
дописывает отпечаток единственной карточке, которую приёмка успела пройти до
починки. Факт не потерян: описание стоит в `extra` дословно.

Запуск: `python3 pipeline/fix_pt_cyberok_target_fin_absorbed.py` — сухой
прогон; `--write` — запись. Идемпотентен.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'pipeline' / 'ingest'))
import review  # noqa: E402

DEAL = 'gdc686ec2'
FIELD = 'eco.target_fin'
DATA = ROOT / 'static' / 'data' / 'deals_promoted.json'


def main(write=False):
    data = json.loads(DATA.read_text(encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == DEAL)
    fixes = [f for f in review.FIXES if f['id'] == DEAL and f['field'] == FIELD]
    assert len(fixes) == 1, fixes
    fix = fixes[0]
    assert 'ГИР БО' in (card.get('eco') or {}).get('target_fin', ''), 'поле уже другое'
    assert review.flat(fix['new']) in review.flat(card.get('extra') or ''), \
        'описание не в extra — факт потерян, отпечаток ставить нельзя'
    fp = review.fix_fingerprint(fix['new'])
    absorbed = card.setdefault('proofread_absorbed', {}).setdefault(FIELD, [])
    if fp in absorbed:
        print('уже записано:', fp)
        return
    absorbed.append(fp)
    print('отпечаток %s для %s.%s' % (fp, DEAL, FIELD))
    assert review.already_applied(fix, card)
    if write:
        DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        print('Записано.')
    else:
        print('Сухой прогон. --write для записи.')


if __name__ == '__main__':
    main('--write' in sys.argv)
