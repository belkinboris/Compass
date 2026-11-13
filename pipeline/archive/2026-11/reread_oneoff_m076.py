# -*- coding: utf-8 -*-
"""Вычитка 12 ноября 2026, партия m076 (часть 1): правки, которые не ложатся в таблицу FIXES.

Зачем: review.py не снимает сумму и ссылку на профиль стороны, не пишет текст предмета-имущества и описание профиля.
Каждое поле-факт пишется с fact_edit_guard.log (цитата и адрес статьи, сохраненной save_source.py в
sources_2026-11-12_m076.json). Повторный запуск ничего не ломает: уже записанное пропускается («уже применено»),
иначе assert на старое значение.

    python3 pipeline/archive/2026-11/reread_oneoff_m076.py            # сухой прогон
    python3 pipeline/archive/2026-11/reread_oneoff_m076.py --write    # запись (перечитывает базу перед записью)
"""
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PIPE = os.path.dirname(os.path.dirname(HERE))
ROOT = os.path.dirname(PIPE)
for p in (os.path.join(PIPE, 'ingest'), PIPE):
    if p not in sys.path:
        sys.path.insert(0, p)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
_BY = 'reread m076'
_DROP = object()

_RT = 'https://rt-capital.ru/deals/19192/'
_IFX_B = 'https://www.interfax.ru/russia/1006634'
_KO_B = 'https://www.kommersant.ru/doc/7606644'

# (id, поле, старое, новое, цитата, адрес); новое _DROP — поле снимается
ONE_OFF = [
 # Продавец лота по карточке торгов — АО НПК «Северная заря», а не госкорпорация: ссылка на профиль Ростеха снята,
 # текст продавца поставлен таблицей правок (reread_2026_11_12_m076.py)
 ('c2d0c1dcd', 'seller_id', 'g7802e51e', _DROP, 'Собственник АО НПК «Северная заря»', _RT),
 ('c2d0c1dcd', 'asset', None, 'Имущественный комплекс АО «НПК «Северная заря»» в Санкт-Петербурге',
  'Имущественный комплекс расположен в Санкт-Петербурге, на Республиканской улице, в муниципальном округе Малая Охта. '
  'Собственник АО НПК «Северная заря»', _RT),
 # «Более 2 млрд ₽» — вывод средств за границу по данным Росфинмониторинга и ФНС, а не цена: изъятие по суду цены не имеет
 ('c382b7c7d', 'sum', 'Более 2 млрд ₽', _DROP,
  'Росфинмониторинг и ФНС России зафиксировали факты вывода за границу в 2024 году финансовых активов стратегических '
  'предприятий ГК «Борец» на сумму более 2 млрд руб.', _KO_B),
 ('c382b7c7d', 'eco.sum', 'Более 2 млрд ₽', '—',
  'Росфинмониторинг и ФНС России зафиксировали факты вывода за границу в 2024 году финансовых активов стратегических '
  'предприятий ГК «Борец» на сумму более 2 млрд руб.', _KO_B),
 ('c382b7c7d', 'sum_basis', 'not_a_price', _DROP, 'сумма снята: это не цена сделки', _KO_B),
 ('c382b7c7d', 'asset', None, 'ООО «Производственная компания «Борец»»',
  'требует взыскать в доход РФ 100% его основной структуры - ООО "Производственная компания "Борец"', _IFX_B),
]
_RETRACT = [('c382b7c7d', 'sum', 'Более 2 млрд ₽')]
# (компания, поле, старое, новое)
_COMPANY = [
 ('gf0cad61e', 'desc',
  'Покупатель имущества научно-производственного комплекса «Северная заря» в Санкт-Петербурге на торгах Ростеха. Юрлицо — ООО «Антресоль».',
  'ООО «Антресоль» купило на торгах в октябре 2025 года имущественный комплекс АО «НПК «Северная заря»» в Санкт-Петербурге. '
  'По данным «Контур.Фокус», одно из семи действующих ООО с таким названием, екатеринбургское, принадлежит основателю «Брусники» '
  'Алексею Круковскому; «Брусника» подтвердила покупку.'),
]


def _get(obj, field):
    for p in field.split('.'):
        obj = obj.get(p) if isinstance(obj, dict) else None
    return obj


def _set(obj, field, value):
    parts = field.split('.')
    for p in parts[:-1]:
        obj = obj.setdefault(p, {})
    if value is _DROP:
        obj.pop(parts[-1], None)
    else:
        obj[parts[-1]] = value


def _apply(data):
    import fact_edit_guard
    deals = {d['id']: d for d in data['deals']}
    done = 0
    for cid, field, old, new, quote, url in ONE_OFF:
        card = deals[cid]
        cur = _get(card, field)
        if (new is _DROP and cur is None) or (new is not _DROP and cur == new):
            continue
        assert cur == old, (cid, field, cur)
        _set(card, field, new)
        fact_edit_guard.log(card, field, None if new is _DROP else new, quote, url, _BY)
        done += 1
    for cid, field, value in _RETRACT:
        if not isinstance(deals[cid].get('retracted'), dict):
            deals[cid]['retracted'] = {}
        cur = deals[cid]['retracted'].setdefault(field, [])
        if value not in cur:
            cur.append(value)
            done += 1
    for comp, field, old, new in _COMPANY:
        c = data['companies'][comp]
        if c.get(field) == new:
            continue
        assert c.get(field) == old, (comp, field, c.get(field))
        c[field] = new
        done += 1
    return done


if __name__ == '__main__':
    import mass_edit_guard  # noqa: E402
    data = json.load(open(DATA, encoding='utf-8'))
    before = copy.deepcopy(data)
    n = _apply(data)
    mass_edit_guard.check(before, data)
    print('Разовая часть m076: изменений %d — проверки пройдены.%s' % (n, '' if n else ' Уже применено.'))
    if '--write' in sys.argv and n:
        fresh = json.load(open(DATA, encoding='utf-8'))      # перечитать прямо перед записью
        before = copy.deepcopy(fresh)
        _apply(fresh)
        mass_edit_guard.check(before, fresh)
        with open(DATA, 'w', encoding='utf-8') as fh:
            json.dump(fresh, fh, ensure_ascii=False, indent=1)
        print('Записано.')
    elif '--write' not in sys.argv:
        print('Сухой прогон. Запись — с ключом --write.')
