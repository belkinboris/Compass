# -*- coding: utf-8 -*-
"""Две пары дублей, которые нашлись при разборе @LawFirms.

ЗАЧЕМ. Разбор постов 33 и 36 показал не только пропущенных консультантов, но
и две пары карточек об одной сделке:

- «Группа «Мать и дитя» покупает сеть клиник ГК «Эксперт»» (`cdd0958b3`,
  30.09.2025) и «MD Medical Group (ГК «Мать и дитя») приобрела 100% ООО «МЦ
  Эксперт»» (`g833a29f6`, 22.05.2025);
- ««Кама Капитал» покупает аутлеты «Белая Дача» и «Пулково» у фонда Hines»
  (`cc71682bd`, 30.09.2025) и «ИК «Кама капитал» выкупила Outlet Village
  Пулково и Outlet Village Белая Дача» (`g7596ae81`, 01.04.2025).

ПОЧЕМУ ИХ НЕ ВИДЕЛИ. Обе тонкие карточки пришли одной волной из подборки
«Коммерсантъ — «Сделки года»»: у них нет ни суммы, ни сторон, ни предмета —
только заголовок и консультант. Правило дубля «два общих названия при одной
сумме» на них не срабатывает, потому что суммы у них нет вообще, а правило
«общее название в кавычках + общие слова» требует разрыва в 45 дней — здесь
разрыв четыре и пять месяцев (подборка вышла позже самой сделки).

ЧТО СОХРАНЯЕТСЯ. Дубль удаляется не молча: его id остаётся в карте `merged`,
и `#/deal/<старый id>` открывает оставшуюся карточку — иначе адрес из
закладок показывал бы общую ленту. Консультант тонкой карточки переносится в
оставшуюся, если его там ещё нет; источник — тоже.

СВЕРЕНО С ОБЪЯВЛЕНИЯМИ ФИРМ. Обе тонкие карточки называли консультантом
Nextons — и оба объявления Nextons (t.me/LawFirms/9031 и 8944) описывают
именно эти сделки, подтверждая, что это одна и та же сделка, а не две.

Запуск:
    python3 pipeline/merge_lawfirms_duplicates_batch3.py            # сухой прогон
    python3 pipeline/merge_lawfirms_duplicates_batch3.py --write    # записать
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

# дубль -> оставшаяся карточка, и роль, под которой переносится консультант
PAIRS = [
    ('cdd0958b3', 'g833a29f6', 'Юридический консультант продавца (ГК «Эксперт»)'),
    ('cc71682bd', 'g7596ae81', 'Юридический консультант продавца (фонды группы Hines)'),
]


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    merged = data.setdefault('merged', {})

    for dup_id, keep_id, role in PAIRS:
        dup, keep = by_id.get(dup_id), by_id.get(keep_id)
        assert dup is not None, 'дубля %s нет в базе' % dup_id
        assert keep is not None, 'оставляемой карточки %s нет в базе' % keep_id
        assert dup_id not in merged, '%s уже помечен слитым' % dup_id
        # Тонкая карточка обязана быть именно тонкой: если у неё появились
        # свои факты, слияние потеряет их, и решать надо заново.
        assert not dup.get('sum') and not dup.get('seller') and not dup.get('buyer'), \
            '%s больше не тонкая: появились свои факты — перепроверьте' % dup_id
        keep_names = ' | '.join(str(a[1]) for a in (keep.get('law') or {}).get('adv') or []
                                if len(a) > 1).lower()
        moving = [a for a in (dup.get('law') or {}).get('adv') or []
                  if len(a) > 1 and str(a[1]).lower() not in keep_names]
        print('%s  «%s»' % (dup_id, str(dup.get('title'))[:62]))
        print('   -> %s  «%s»' % (keep_id, str(keep.get('title'))[:58]))
        print('   переносим консультантов: %s' % ([a[1] for a in moving] or 'нечего'))
        print('   переносим источников: %d' % len(dup.get('src') or []))

    print('\nпар к слиянию: %d' % len(PAIRS))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0

    for dup_id, keep_id, role in PAIRS:
        dup, keep = by_id[dup_id], by_id[keep_id]
        law = keep.setdefault('law', {})
        law.setdefault('adv', [])
        keep_names = ' | '.join(str(a[1]) for a in law['adv'] if len(a) > 1).lower()
        for a in (dup.get('law') or {}).get('adv') or []:
            if len(a) > 1 and str(a[1]).lower() not in keep_names:
                law['adv'].append([role, a[1], str(a[2]) if len(a) > 2 else ''])
        known = {str(s[1]) for s in (keep.get('src') or []) if len(s) > 1}
        for s in dup.get('src') or []:
            if len(s) > 1 and str(s[1]) not in known:
                keep.setdefault('src', []).append(list(s))
        merged[dup_id] = keep_id
        data['deals'] = [d for d in data['deals'] if d['id'] != dup_id]
        data.get('telegram_posts', {}).pop(dup_id, None)

    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО в %s' % os.path.relpath(DATA, ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
