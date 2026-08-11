# -*- coding: utf-8 -*-
"""Двадцать первая партия описаний профилей: чем компания занимается.

ЧТО СЛОМАНО. После двадцати партий настоящее описание есть у 584
профилей из 1856 (31%). Кандидатов искали по числу связанных сделок
среди профилей без описания (тот же приём, что в партии 20) — каждый
проверен по тексту его собственных сделок в базе (урок CLAUDE.md про
«Акрон Холдинг»).

ЧТО ДЕЛАЕТ. Проставляет описание в 1–2 строки 4 профилям.

Запуск:
    python3 pipeline/write_company_descriptions_batch21.py            # сухой прогон
    python3 pipeline/write_company_descriptions_batch21.py --write    # записать
"""
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'
PLACEHOLDER = re.compile(r'^\s*(описание компании пока не добавлено'
                          r'|профиль сформирован по итогам чтения)', re.I)

# id профиля -> описание. Только компании, чей род занятий общеизвестен и
# подтверждён текстом собственной сделки в базе.
DESCRIPTIONS = {
    'g76b394c1': 'Петербургский девелопер жилой недвижимости, '
                 'принадлежит Эдуарду Тиктинскому.',
    'g578c62cd': 'Российский маркетплейс цветов и подарков.',
    'gfc303539': 'Нидерландская холдинговая компания, владеет '
                 'сервисом такси и доставки «Яндекс.Такси»/Yango; '
                 'ранее совместное предприятие с Uber.',
    'g17f3d2f6': 'Золоторудное месторождение на Ямале, ранее входило '
                 'в портфель Petropavlovsk.',
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']

    wrote, skipped = 0, []
    for cid, text in DESCRIPTIONS.items():
        c = comps.get(cid)
        assert c, 'профиля %s нет в базе' % cid
        assert 15 <= len(text) <= 220, 'описание %s вне 1–2 строк: %d' % (cid, len(text))
        old = str(c.get('desc') or '')
        if old.strip() == text:
            continue
        if old and not PLACEHOLDER.match(old):
            skipped.append((cid, c.get('name'), old[:60]))
            continue
        print('  %-12s %-34s %s' % (cid, str(c.get('name'))[:34], text[:56]))
        c['desc'] = text
        wrote += 1

    print('\nОписаний записано: %d' % wrote)
    if skipped:
        print('Пропущено (уже есть своё описание): %d' % len(skipped))
        for cid, name, old in skipped[:5]:
            print('   %s %s — %r' % (cid, name, old))

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
