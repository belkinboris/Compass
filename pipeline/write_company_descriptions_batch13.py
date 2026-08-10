# -*- coding: utf-8 -*-
"""Тринадцатая партия описаний профилей: чем компания занимается.

ЧТО СЛОМАНО. После двенадцати партий настоящее описание есть у 517
профилей из 1872 (28%). Кандидатов этой партии искали по узнаваемости
имени, а не по рангу участия в сделках (см. батчи 8–12) — каждый проверен
по тексту его собственной сделки в базе. Три узнаваемых имени намеренно
отложены — Азбука вкуса, Авилон, Деловые линии, БКС, БКИ «Эквифакс»: ни у
одного не нашлось ни одной связанной сделки в базе (роли
`buyer`/`target`/`seller_id`/`asset_id`), а без контекста своей сделки
нечем подтвердить, что профиль — именно та компания, о которой думаешь
(урок CLAUDE.md про «Акрон Холдинг»).

ЧТО ДЕЛАЕТ. Проставляет описание в 1–2 строки 13 профилям.

Запуск:
    python3 pipeline/write_company_descriptions_batch13.py            # сухой прогон
    python3 pipeline/write_company_descriptions_batch13.py --write    # записать
"""
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'
PLACEHOLDER = re.compile(r'^\s*(описание компании пока не добавлено'
                          r'|профиль сформирован по итогам чтения)', re.I)

# id профиля -> описание. Только компании, чей род занятий общеизвестен.
DESCRIPTIONS = {
    'g53308e89': 'Российский производитель игристых и тихих вин.',
    'g8d204e38': 'Российское страховое подразделение американской AIG, '
                 'продано инвесторам в 2022 году.',
    'g9adfbebe': 'Российский банк, ранее принадлежал страховой компании '
                 '«Ингосстрах».',
    'gec1422a6': 'Российская аптечная сеть.',
    'gdaa028e0': 'Российский финансовый маркетплейс: сравнение банковских '
                 'продуктов, кредитов и вкладов.',
    'g5075b0e6': 'Российский интернет-магазин инструментов и товаров для '
                 'дома.',
    'g126d62c8': 'Российский девелопер жилой недвижимости, работает в '
                 'Москве.',
    'g9c1a072e': 'Российская девелоперская компания, специализируется на '
                 'коммерческой и жилой недвижимости в Москве.',
    'g941bdcdf': 'Российский технологический холдинг: телеком-решения, '
                 'кибербезопасность, радиоэлектроника.',
    'g78c4654b': 'Российский банк, дочерняя структура турецкой Credit '
                 'Europe Bank.',
    'gc6091c34': 'Сибирская розничная сеть продуктовых магазинов.',
    'g2a70ebb1': 'Российская сеть гипермаркетов товаров для дома и '
                 'ремонта.',
    'gd2431ed3': 'Российская розничная сеть детских товаров.',
}

# Профили, отрасль которых унаследована от одной сделки и не отражает
# основной бизнес компании (см. докстринг). old — что было, для assert.
INDUSTRY_FIXES = {}

# Профили, которым описание не ставится в этой партии: неизвестно, что
# именно они обозначают, или падежная/предметная форма имени.
UNCLEAR = {}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']

    wrote, skipped = 0, []
    for cid, text in DESCRIPTIONS.items():
        c = comps.get(cid)
        assert c, 'профиля %s нет в базе' % cid
        assert 15 <= len(text) <= 220, 'описание %s вне 1–2 строк: %d' % (cid, len(text))
        assert cid not in UNCLEAR, 'профиль %s помечен неясным — описание ставить нельзя' % cid
        old = str(c.get('desc') or '')
        if old.strip() == text:
            continue
        # Своё описание не перетираем: прошлые партии и ручные правки старше этой.
        if old and not PLACEHOLDER.match(old):
            skipped.append((cid, c.get('name'), old[:60]))
            continue
        print('  %-12s %-34s %s' % (cid, str(c.get('name'))[:34], text[:56]))
        c['desc'] = text
        wrote += 1

    ind_fixed = 0
    for cid, (old_ind, new_ind) in INDUSTRY_FIXES.items():
        c = comps.get(cid)
        assert c, 'профиля %s нет в базе' % cid
        assert c.get('ind') == old_ind, ('отрасль %s уже другая: %r (ожидали %r)'
                                          % (cid, c.get('ind'), old_ind))
        print('  ОТРАСЛЬ  %-12s %-34s %s -> %s'
              % (cid, str(c.get('name'))[:34], old_ind, new_ind))
        c['ind'] = new_ind
        ind_fixed += 1

    print('\nОписаний записано: %d' % wrote)
    print('Отраслей исправлено: %d' % ind_fixed)
    if skipped:
        print('Пропущено (уже есть своё описание): %d' % len(skipped))
        for cid, name, old in skipped[:5]:
            print('   %s %s — %r' % (cid, name, old))
    print('Оставлено без описания намеренно: %d профилей (см. UNCLEAR)' % len(UNCLEAR))

    real = sum(1 for v in comps.values()
               if (v.get('desc') or '').strip() and not PLACEHOLDER.match(str(v.get('desc'))))
    print('Всего профилей с описанием: %d из %d (%d%%)'
          % (real, len(comps), round(100 * real / len(comps))))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
