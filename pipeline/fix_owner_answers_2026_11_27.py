# -*- coding: utf-8 -*-
"""Ответы владельца на вопросы консоли, 27 ноября 2026 (заметки 1814, 1815, 1816).

ЧТО ЧИНИТ.
  * g8e847626 «Отель „Савой“ … выставлен на продажу за 10 млрд ₽» — владелец:
    «Убираем». Единственное основание — объявление на «Авито», «Гута» в тот же
    день продажу опровергла; карточка снимается как неподтвержденное объявление.
  * g654a1ce5 «Особняк на Выборгской улице в Тюмени выставлен на продажу за
    128 млн ₽» — владелец: «Удаляем карту» (частное объявление, сделки нет).
  * g58ebb771 Softline — владелец на вопрос о символической цене у
    g4c30b416 (Trafigura / «Восток Ойл»): «Не раскрыта и тут и у Softline».
    Символический $1 — не цена сделки: сумма «Не раскрыта», $1 остается в
    оценке (eco.val уже говорит «Цена символическая — $1») и в условиях.
    Заголовок теряет «за $1», иначе он спорит с суммой.
    g4c30b416 уже несет «Не раскрыта» — не меняется.

ПОЧЕМУ РАЗОВЫЙ СКРИПТ, А НЕ review.py. Удаление карточки таблица FIXES не
умеет; сумма «Не раскрыта» — решение владельца, а не слова статьи (цитата в
fact_log — его ответ и фраза Интерфакса о символической цене). Удаление — тем
же порядком, что drop_open_auction_lots.py (drop_pre_2022_deals.apply):
профили, нужные только удаленным карточкам, и записи telegram_* уходят вместе.
Адреса источников удаленных карточек запоминаются в discarded_urls, чтобы
новость не вернулась из притока под новым id.

После записи: python3 pipeline/remove_fixes_for_id.py g8e847626 g654a1ce5 --write;
запись заголовка g58ebb771 в fixes/reread_2026_11_09_sc.py правится на месте
(одна запись на поле); python3 pipeline/facts_derive.py --write.

    python3 pipeline/fix_owner_answers_2026_11_27.py            # сухой прогон
    python3 pipeline/fix_owner_answers_2026_11_27.py --write
"""
import copy
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'ingest'))
import drop_pre_2022_deals as pre  # noqa: E402
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402
import promote  # noqa: E402

DATA = pre.DATA
BY = 'fix_owner_answers_2026_11_27'

REMOVE = {
    'g8e847626': ('Отель «Савой» в Москве выставлен на продажу за 10 млрд ₽',
                  'владелец 27.11.2026: «Убираем» — неподтвержденное объявление, собственник продажу опроверг'),
    'g654a1ce5': ('Особняк на Выборгской улице в Тюмени выставлен на продажу за 128 млн ₽',
                  'владелец 27.11.2026: «Удаляем карту» — частное объявление о продаже, сделки нет'),
}

SOFT = 'g58ebb771'
SOFT_URL = 'https://www.interfax.ru/russia/866876'
SOFT_QUOTE = ('Согласно сообщению компании, бизнес в РФ будет продан основателю всей группы Игорю Боровикову '
              'за символический $1.')
OWNER = 'Решение владельца 27 ноября 2026 (заметка 1815): «Не раскрыта и тут и у Softline». Источник: ' + SOFT_QUOTE
SOFT_SET = [  # (поле, старое, новое)
    ('sum', '1 $', 'Не раскрыта'),
    ('eco.sum', '1 $', 'Не раскрыта'),
    ('title', 'Игорь Боровиков купил российскую часть Softline за $1',
     'Игорь Боровиков купил российскую часть Softline'),
]


def plan(base):
    gone = set(REMOVE)
    kept = [d for d in base['deals'] if d['id'] not in gone]
    held = set().union(*[pre.parties(d) for d in kept])
    held |= pre._external_company_refs()
    mc = base.get('merged_companies') or {}
    held |= set(mc.keys()) | set(mc.values())
    only_gone = set().union(*[pre.parties(d) for d in base['deals'] if d['id'] in gone])
    return gone, (only_gone - held) & set(base['companies'])


def edit(base):
    by_id = {d['id']: d for d in base['deals']}
    for did, (title, _) in REMOVE.items():
        assert by_id[did]['title'] == title, (did, by_id[did]['title'])
    card = by_id[SOFT]
    for field, old, new in SOFT_SET:
        holder, key = (card['eco'], 'sum') if field == 'eco.sum' else (card, field)
        assert holder[key] == old, (field, holder[key])
        holder[key] = new
        fact_edit_guard.log(card, field, new, OWNER, SOFT_URL, BY)
    assert 'символическая — $1' in card['eco']['val']      # цена осталась в оценке
    urls = {did: [s[1] for s in by_id[did].get('src') or [] if len(s) > 1 and str(s[1]).startswith('http')]
            for did in REMOVE}
    gone, orphans = plan(base)
    pre.apply(base, gone, orphans)
    return gone, orphans, urls


def main(argv):
    write = '--write' in argv
    base = json.load(open(DATA, encoding='utf-8'))       # читается прямо перед записью
    old = copy.deepcopy(base)
    posted = [d for d in REMOVE if d in (base.get('telegram_posts') or {}) or d in (base.get('telegram_posts_realty') or {})]
    gone, orphans, urls = edit(base)
    print('Удаляются: %s; профили только этих карточек: %s' % (sorted(gone), sorted(orphans) or 'нет'))
    print('Посты в канале у удаляемых: %s' % (posted or 'нет'))
    for field, o, n in SOFT_SET:
        print('  %s %s: %r -> %r' % (SOFT, field, o, n))
    assert len(base['deals']) == len(old['deals']) - len(REMOVE)
    mass_edit_guard.check(old, base)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    json.dump(base, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    state = promote.load_state()
    now = datetime.now(timezone.utc).isoformat(timespec='seconds')
    for did, lst in urls.items():
        for u in lst:
            state.setdefault('discarded_urls', {})[u] = {'id': did, 'title': REMOVE[did][0], 'at': now,
                                                         'why': REMOVE[did][1]}
    promote.save_state(state)
    print('Записано. Сделок: %d.' % len(base['deals']))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
