# -*- coding: utf-8 -*-
"""Недельная очередь, 9 сентября 2026 — дельта-поиск по трём карточкам,
добавленным 2 сентября 2026 (`g2f5143f4` Шереметьево, `g672dcca1` НМТП,
`gb0f1f736` Альфа-Банк/WhoIsBlogger).

По Шереметьево и НМТП дельта-поиск (саб-агент + личная проверка) не
нашёл ничего нового сверх уже известного — оба сюжета за 2-9 сентября
2026 года не продвинулись (republish тех же цитат Моисеева с ВЭФ,
никаких новых сроков, механизмов или названных покупателей). Эти две
карточки не редактируются, только помечаются `--mark-weekly`.

По `gb0f1f736` («Альфа-Банк» купил WhoIsBlogger) нашлась одна
подтверждённая деталь, которой не было в карточке: имя основателя и
гендиректора платформы. Личный WebFetch (mergers.ru) подтвердил
дословно: «Лев Грунин, основатель и генеральный директор WhoIsBlogger».
Поле `eco.share` («Предмет / доля») стояло прочерком — заполнено этим
фактом.

Запуск:
    python3 pipeline/fix_whoisblogger_founder.py            # сухой прогон
    python3 pipeline/fix_whoisblogger_founder.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

OLD_ECO_SHARE = '—'
NEW_ECO_SHARE = 'Основатель и генеральный директор WhoIsBlogger — Лев Грунин.'


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['gb0f1f736']

    assert d['eco']['share'] == OLD_ECO_SHARE, \
        'gb0f1f736 eco.share уже другой: %r' % (d['eco']['share'],)

    print('gb0f1f736: eco.share "—" -> имя основателя (Лев Грунин)')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d['eco']['share'] = NEW_ECO_SHARE

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
