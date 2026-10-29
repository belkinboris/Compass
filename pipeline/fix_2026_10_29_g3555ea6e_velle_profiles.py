# -*- coding: utf-8 -*-
"""Velle / «Логика молока» (g3555ea6e, очередь pending.json): профили сторон и
заметка этапа после приемки 29 октября 2026.

Что чинится (находки accept_card.py --check, которые review.py не правит):
  * описание профиля предмета «Velle (Велле Холдинг)» (g8eb3f1af) пересказывало
    сделку 2023 года («34,96% долей купил … Петр Жуков») — пост брал эту фразу
    в строку «Предмет» как действие стороны; теперь описание — о компании,
    с юрлицом и новым владельцем с датой (docs/company_profiles.md,
    «Новая сделка — перечитать описания сторон»);
  * описание покупателя (g53717e9e): растительные бренды группы — Planto, а
    с октября 2026 года также 5Yes! и Velle;
  * events[0].note карточки — 14 слов подряд из пресс-релиза (цитата Закриева
    без кавычек); review.py заметки этапов не правит;
  * отпечаток старого предмета «Velle» — в `proofread_absorbed.asset`: запись
    `g3555ea6e_struct_2026_10_29.py` (asset → «Velle») перекрыта приемкой
    (asset → «ООО «Велле Холдинг» — владелец бренда Velle»), и без отпечатка
    `test_review_table_is_applied_and_not_pending` считает ее непримененной.

    python3 pipeline/fix_2026_10_29_g3555ea6e_velle_profiles.py           # сухой прогон
    python3 pipeline/fix_2026_10_29_g3555ea6e_velle_profiles.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
DEAL, TARGET, BUYER = 'g3555ea6e', 'g8eb3f1af', 'g53717e9e'

OLD_TARGET_DESC = ('Производитель растительных аналогов молока, йогуртов, каш и десертов под брендом Velle '
                   '(ООО «Велле Холдинг»); в 2023 году 34,96% долей купил основатель Indigo Capital Partners '
                   'Петр Жуков для интеграции с «Фрутти».')
# Первая редакция («…под брендом Velle: йогурты… Юрлицо — ООО «Велле Холдинг». С октября
# 2026 года — в составе группы…») в посте давала «Предмет: Velle (Велле Холдинг) — С октября
# 2026 года — в составе группы»: `_pick_novel_sentences` ставит предложения с «елочками»
# вперед, а «Юрлицо — …» отсеивает, — поэтому юрлицо теперь внутри первого предложения.
MID_TARGET_DESC = ('Производитель растительных аналогов молочных продуктов под брендом Velle: йогурты, каши, '
                   'сливки, сметана, кофейные напитки; выпускает их с 2004 года, производство — под '
                   'Санкт-Петербургом. Юрлицо — ООО «Велле Холдинг». С октября 2026 года — в составе группы '
                   '«Логика молока».')
NEW_TARGET_DESC = ('Производитель растительных йогуртов, каш, сливок, сметаны и кофейных напитков под брендом '
                   'Velle; работает с 2004 года, производство — под Санкт-Петербургом, юрлицо — ООО «Велле '
                   'Холдинг». С октября 2026 года входит в группу «Логика молока».')
OLD_BUYER_PART = 'собственный растительный бренд — Planto.'
NEW_BUYER_PART = 'растительные бренды — Planto, а с октября 2026 года также 5Yes! и Velle.'
OLD_NOTE = ('Генеральный директор компании Якуб Закриев отметил, что Velle за годы работы заслужил достойное '
            'место в числе лучших брендов в этой категории, а также выразил надежду, что "Логика молока" '
            'сможет придать ему новый импульс развития')
NEW_NOTE = ('«Логика молока» объявила, что купила ООО «Велле Холдинг» — владельца бренда Velle; цену стороны '
            'не раскрыли, в ЕГРЮЛ переход на день объявления еще не отражен.')


def apply(base, pending):
    t = base['companies'][TARGET]
    assert t['desc'] in (OLD_TARGET_DESC, MID_TARGET_DESC, NEW_TARGET_DESC), t['desc']
    t['desc'] = NEW_TARGET_DESC
    b = base['companies'][BUYER]
    assert OLD_BUYER_PART in b['desc'] or NEW_BUYER_PART in b['desc'], b['desc']
    b['desc'] = b['desc'].replace(OLD_BUYER_PART, NEW_BUYER_PART)
    card = next(c for c in pending['cards'] if c['id'] == DEAL)
    assert card['events'][0]['note'] in (OLD_NOTE, NEW_NOTE), card['events'][0]['note']
    card['events'][0]['note'] = NEW_NOTE
    sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
    from review import fix_fingerprint
    absorbed = card.setdefault('proofread_absorbed', {}).setdefault('asset', [])
    if fix_fingerprint('Velle') not in absorbed:
        absorbed.append(fix_fingerprint('Velle'))


def main(argv):
    write = '--write' in argv
    base = json.load(open(DATA, encoding='utf-8'))
    pending = json.load(open(PENDING, encoding='utf-8'))
    apply(base, pending)
    print('Профиль %s: описание о компании; профиль %s: бренды Planto, 5Yes!, Velle; %s events[0].note — пересказ.'
          % (TARGET, BUYER, DEAL))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    base = json.load(open(DATA, encoding='utf-8'))
    pending = json.load(open(PENDING, encoding='utf-8'))
    apply(base, pending)
    json.dump(base, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
