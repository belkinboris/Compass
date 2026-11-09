# -*- coding: utf-8 -*-
"""Отметка вычитки после правок, сделанных уже после нее (9 ноября 2026).

20 карточек, вычитанных 2–6 ноября, наши же скрипты потом правили: консультанты из каналов
юрфирм (g1125c0ec, gf23149cf), заголовки по стандарту (g718e3d0e, g7cb5d8f8, g60c082cf,
g029b7531, gfebe16ad, g02eed099, g2b1fe015, g10f783e8, gc6fa5d80, g16dc5834, gde4f9941),
привязка сторон к профилям (g60c082cf, gd774ce6b, g029b7531, g8bc7aacf, gfebe16ad, g0cf6a562,
g2b1fe015 — юрлица «Точки» по сообщению МКПАО «ВК» в AK&M), имя профиля (g7e81d8e7),
основание даты (ga402c91b), дата, тип и продавец ТЦ «Июнь» (gde4f9941, Retail.ru/Ведомости:
сделка закрыта 2 сентября), сумма-диапазон «Ленты»/OBI по правилу card_money.md и Светлана Шорина
из CORE.XP (g02eed099, Деловой Петербург), «Опрошенные журналистами юристы» вместо RTVI
(gf174262b), санкционная оговорка AptarGroup (gcc75fe11, Mail.ru Финансы «Молоку — крышки»),
недельный обыск (g16dc5834, g10f783e8). Каждое изменение после отметки (найдено сверкой
снимка базы в коммите отметки с нынешним) проверено по источнику; неверное исправлено
скриптом fix_reread_2026_11_09_tail.py (gcc75fe11, g10f783e8, g16dc5834, gc6fa5d80).
Полная вычитка заново не делалась — по образцу restamp_reread_after_titles_2026_11_06.py
обновляется только отпечаток `reread_hash`, дата вычитки остается прежней.

    python3 pipeline/archive/2026-11/restamp_reread_after_changes_2026_11_09.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import readiness  # noqa: E402

BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
IDS = ['g718e3d0e', 'g02eed099', 'g7e81d8e7', 'g1125c0ec', 'g60c082cf', 'gd774ce6b', 'g029b7531', 'g2b1fe015',
       'g10f783e8', 'g8bc7aacf', 'gfebe16ad', 'gde4f9941', 'gf23149cf', 'ga402c91b', 'gf174262b', 'g0cf6a562',
       'g7cb5d8f8', 'g16dc5834', 'gcc75fe11', 'gc6fa5d80']


def _apply(data):
    comps = data['companies']
    by = {d['id']: d for d in data['deals']}
    for cid in IDS:
        card = by[cid]
        assert card.get('reread'), (cid, 'нет отметки вычитки')
        assert readiness.changed_after_check(card, comps), (cid, 'отпечаток и так совпадает')
        card['reread_hash'] = readiness.fingerprint(card, comps)


def main(argv):
    data = json.load(open(BASE, encoding='utf-8'))
    _apply(data)
    print('отметок к обновлению: %d' % len(IDS))
    if '--write' not in argv:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    fresh = json.load(open(BASE, encoding='utf-8'))     # перечитать прямо перед записью
    _apply(fresh)
    json.dump(fresh, open(BASE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
