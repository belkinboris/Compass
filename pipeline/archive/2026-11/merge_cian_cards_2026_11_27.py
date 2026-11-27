"""Слияние двух карточек одной сделки «Циана»: gd1bf6d5e («Леван Назаров купил 21,97%», в базе, пост
в обоих каналах) и g1a8709ea («Основные акционеры продали 52%», в очереди). Решение владельца,
27 ноября 2026: «сливаем карточки». Это одно событие — три акционера вышли из капитала, две
структуры (Назарова и «Атона») получили по ~21–22%.

Остается gd1bf6d5e (уже опубликована, у нее пост, id в каналах): ей переходят проверенные поля
очередной карточки; публикация сама поправит пост (правка поста по разошедшимся полям).
g1a8709ea после слияния убирается из очереди отдельно (`drop_pending.py`).

Правка факта — с цитатой через `fact_edit_guard.log` (слова официального сообщения «Циана»).

    python3 pipeline/archive/2026-11/merge_cian_cards_2026_11_27.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
KEEP, DROP = 'gd1bf6d5e', 'g1a8709ea'
BY = 'слияние карточек «Циана» 27.11.2026 (решение владельца)'
RBC = 'https://www.rbc.ru/business/27/11/2026/6b0879f6d31da4b02bb5fea9'
Q_SELLERS = ('"Из акционерного капитала МКПАО "Циан" полностью вышли структуры Дмитрия Крюкова (32,99%), '
             'Дмитрия Демина (7,16%) и Максима Мельникова (6,24%)", - сказано в пресс-релизе.')
Q_52 = 'В общей сложности было реализовано чуть более 52% голосующих акций компании.'
Q_BUYERS = ('Компания ООО "Технологии недвижимости" Левана Назарова приобрела 21,97% МКПАО "Циан", сообщил сам "Циан". '
            'Новым владельцем еще 21,41% МКПАО стала инвестиционная группа "Атон холдинг".')
FACT_QUOTES = {   # поле -> цитата (слова официального сообщения «Циана» в РБК, «Ведомостях», «Интерфаксе»)
    'title': Q_52, 'asset': Q_52, 'eco.share': Q_52, 'buyer_name': Q_BUYERS, 'seller': Q_SELLERS,
    'date': Q_SELLERS, 'sum': Q_52, 'eco.sum': Q_52,
}


def get(c, f):
    a, _, b = f.partition('.')
    return (c.get(a) or {}).get(b) if b else c.get(a)


def put(c, f, v):
    a, _, b = f.partition('.')
    if b:
        c.setdefault(a, {})[b] = v
    else:
        c[a] = v


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))            # читается прямо перед записью
    pend = json.load(open(PENDING, encoding='utf-8'))
    keep = next(d for d in data['deals'] if d['id'] == KEEP)
    drop = next(c for c in pend['cards'] if c['id'] == DROP)
    assert KEEP not in (data.get('merged') or {}) and DROP not in (data.get('merged') or {})
    assert KEEP in data['telegram_posts'], 'у выжившей нет поста'
    copy = ['title', 'asset', 'buyer_name', 'seller', 'seller_src', 'date',
            'eco.share', 'eco.sum', 'eco.val', 'eco.context', 'law.struct', 'events']
    for f in copy:
        new = get(drop, f)
        old = get(keep, f)
        if new == old:
            continue
        print('%-12s %s\n%12s -> %s' % (f, json.dumps(old, ensure_ascii=False)[:110], '', json.dumps(new, ensure_ascii=False)[:110]))
        put(keep, f, new)
        if f in FACT_QUOTES:
            fact_edit_guard.log(keep, f, new, FACT_QUOTES[f], RBC, BY)
    # сумма сделки не раскрыта: оценка пакета Назарова осталась в eco.val; основание оценки снимается
    if keep.get('sum') != 'Не раскрыта':
        print('sum', keep.get('sum'), '-> Не раскрыта')
        keep['sum'] = 'Не раскрыта'
        fact_edit_guard.log(keep, 'sum', 'Не раскрыта', FACT_QUOTES['sum'], RBC, BY)
    keep.pop('sum_basis', None)
    keep.pop('date_basis', None)          # дата теперь годом — основания дня нет
    keep.pop('facts', None)               # пересчитает facts_derive.py
    # источники: очередной карточки — первыми (официальное сообщение и пересказы), прежние — следом
    urls = {s[1] for s in drop['src']}
    keep['src'] = [list(s) for s in drop['src']] + [list(s) for s in keep['src'] if s[1] not in urls]
    keep['related_deal_ids'] = [i for i in (drop.get('related_deal_ids') or []) if i != KEEP]
    data.setdefault('merged', {})[DROP] = KEEP
    print('src:', [s[1].split('/')[2] for s in keep['src']], '| related:', keep['related_deal_ids'])
    if not write:
        print('сухой прогон')
        return
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('записано; теперь: drop_pending.py g1a8709ea, facts_derive.py --write')


if __name__ == '__main__':
    main('--write' in sys.argv)
