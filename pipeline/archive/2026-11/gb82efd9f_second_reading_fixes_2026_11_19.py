# -*- coding: utf-8 -*-
"""Применено 19 ноября 2026. «Медскан»/KDL (gb82efd9f): правки по второму чтению
(data/inbox/acceptance/2026-11-19-gb82efd9f-sr2.json, вердикт fix):
- law.terms: опцион и гарантия от 18 ноября — не условия этой продажи (статья их только
  ставит рядом) → в контекст, с пояснением, кто такой АО «Медицинский актив», и прямой
  оговоркой, что связь с продажей не раскрыта; в «Условиях» — «—».
- eco.val: сказано, что «Медскан Лаб» — лабораторная компания группы; цифры прошлой
  сделки (39% за 4,8 млрд ₽, оценка 31 млрд ₽) — обе, как в РБК, без пересчета.
- eco.context: убраны привилегированные акции и возможная доля Газпромбанка в головной
  компании (подталкивали считать покупателем Газпромбанк) и финансы за полугодие 2025 года;
  добавлены слова Туголукова о сделках «в рамках pre-IPO» (та же статья).
- law.struct: вместо повтора доли — что видно в реестре (datanewton, история участников
  ООО «Медскан Лаб», ОГРН 1227700484076: последняя запись 2025-10-24, 100% у АО «Медскан»).
Источник всех цифр — зеркало РБК https://news.mail.ru/society/73165759/; «Медицинский
актив» — карточка g7b4be1c4 (Известия, shoppers.media, sz-fo.ru).
Записи FIXES этих полей в fixes/gb82efd9f_medskan_kdl_2026_11_19.py синхронизированы.

    python3 pipeline/archive/2026-11/gb82efd9f_second_reading_fixes_2026_11_19.py pipeline/archive/2026-11/gb82efd9f_second_reading_fixes_2026_11_19.json [--write]
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
P = os.path.join(ROOT, 'static', 'data', 'pending.json')
NEW = json.load(open(sys.argv[1], encoding='utf-8'))
OLD_START = {'eco.val': 'Цена этой продажи не названа. Ближе всего по времени',
             'eco.context': 'У «Медскана» сеть на 105 городов',
             'law.struct': '«Медскан» продал 49% лабораторного бизнеса KDL, оставив себе',
             'law.terms': '18 ноября «Медскан» раскрыл связанные сделки'}

def apply(data):
    c = [x for x in data['cards'] if x['id'] == 'gb82efd9f']
    assert len(c) == 1
    c = c[0]
    for k, v in NEW.items():
        a, b = k.split('.')
        assert c[a][b].startswith(OLD_START[k]), (k, c[a][b][:60])
        c[a][b] = v
    return data

data = apply(json.load(open(P, encoding='utf-8')))
print('проверено: %d полей' % len(NEW))
if '--write' in sys.argv:
    raw = open(P, encoding='utf-8').read()
    data = apply(json.loads(raw))  # перечитать прямо перед записью
    out = json.dumps(data, ensure_ascii=False, indent=1)
    if raw.endswith('\n'): out += '\n'
    open(P, 'w', encoding='utf-8').write(out)
    print('записано')
