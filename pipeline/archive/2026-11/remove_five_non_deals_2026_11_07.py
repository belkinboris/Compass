# -*- coding: utf-8 -*-
"""Снять пять карточек, которые по разбору не сделки (владелец, 7 ноября 2026: «снять»).

Разбор 6 ноября (11 трудных карточек под стандарт заголовков) показал, что эти пять
записей не описывают сделку с долей или активом:
  * gf8549c5f — «Восход», Альфа-банк и Тинькофф собрали pre-IPO фонд: запуск фонда,
    деньги клиентов банков, доли в компании никто не покупал;
  * gf14ff7aa — А1, Альфа-банк и «Альфа-Капитал» запустили фонд специальных ситуаций:
    создание ЗПИФ, покупателя и покупаемой компании нет;
  * gc38bcf53 — «Замок на Затоне»: решение суда о возврате здания, а не продажа;
  * g3074f98b — фонд Норвегии решил продать российские активы: поручение продать акции
    на бирже, покупателя нет, поручение не отменено;
  * g9fdcb59d — предложение акционеров Альфа-Банка Украина: письмо-предложение, сделки не было.

Что делает: убирает карточки из `deals`. Запись в `telegram_posts` остается — это история
канала (пост выходил), по ней публикация не выпустит пост повторно; ссылка из старого поста
откроет ленту сделок (`renderDeal` без карточки). `consumed_urls` остается — приток не
соберет карточку заново из тех же статей. Записи FIXES на эти id снимает
`pipeline/remove_fixes_for_id.py` тем же коммитом (docs/card_editing.md).

    python3 pipeline/archive/2026-11/remove_five_non_deals_2026_11_07.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

REMOVE = {
    'gf8549c5f': '«Восход», Альфа-банк и Тинькофф',
    'gf14ff7aa': 'А1, Альфа-банк и «Альфа-Капитал»',
    'gc38bcf53': '«Замок на Затоне»',
    'g3074f98b': 'фонд Норвегии',
    'g9fdcb59d': 'Альфа-Банка Украина',
}


def check(data):
    found = {d['id']: d for d in data['deals'] if d['id'] in REMOVE}
    assert set(found) == set(REMOVE), 'нашли не все: %s' % sorted(found)
    for cid, expect in REMOVE.items():
        t = str(found[cid].get('title'))
        assert expect in t, (cid, t)
        assert cid not in (data.get('merged') or {}).values(), '%s — цель слияния' % cid
        print('  СНИМАЕМ %s %s' % (cid, t[:70]))


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    check(data)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    data = json.load(open(DATA, encoding='utf-8'))   # свежий снимок прямо перед записью
    check(data)
    data['deals'] = [d for d in data['deals'] if d['id'] not in REMOVE]
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('ЗАПИСАНО: снято %d.' % len(REMOVE))
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
