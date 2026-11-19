# -*- coding: utf-8 -*-
"""Карточка gc708f8c0, СП Radius Group и частного инвестора для индустриального
парка «Северные Врата»: раскладка долей между двумя участниками СП — по
истории участников целевого общества в ЕГРЮЛ (datanewton), а не по статье
(пресс-релиз ALUMNI Partners называет инвестора только «частным», без цифр
и без юрлица).

ЧТО СТАВИТСЯ И ПОЧЕМУ.
  * eco.share — 87,5%/12,5%: доли участников ООО «Индустриальный парк
    Северные Врата» (ИНН 7718155620, ОГРН 1027739268369) по состоянию на
    19.11.2026 — ЗПИФ комбинированный «Пятый семейный фонд» (управляющая
    компания АО «УК «Экто Прайм», ИНН 9703220084) и ООО «Северные Врата
    Инвест» (ИНН 9702070020, структура Radius Group).
  * src + ЕГРЮЛ (datanewton) по ОГРН целевого общества — источник этой
    цифры, отдельный от Телеграм-поста ALUMNI Partners.
  * party_evidence — обе роли подтверждены реестром, не статьей.

Та же причина, что у pipeline/build_wylsacom_immortal_2026_11_18.py: цифра
взята из реестра участников, а не из текста источника карточки, — review.py
требует дословную цитату из кэша `data/inbox/raw`, которого для datanewton
(выдает JS-заглушку без браузера) нет, поэтому запись — прямым скриптом с
assert на старое значение, перечитывающим pending.json перед записью
(docs/card_editing.md).

Запуск:
    python3 pipeline/build_severnye_vrata_share_2026_11_19.py            # сухой прогон
    python3 pipeline/build_severnye_vrata_share_2026_11_19.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
CARD_ID = 'gc708f8c0'
EGRUL = 'https://datanewton.ru/contragents/1027739268369'
SHARE = ('87,5% индустриального парка «Северные Врата» — у частного инвестора '
         '(фонд «Пятый семейный фонд»), 12,5% — у структуры Radius Group '
         '(«Северные Врата Инвест»)')


def patch(card):
    assert card.get('eco', {}).get('share') in (None, '—'), card.get('eco', {}).get('share')
    assert [s[1] for s in card['src']] == ['https://t.me/alumnipartnerslawfirm/2232'], card['src']
    card.setdefault('eco', {})['share'] = SHARE
    card['src'].append(['ЕГРЮЛ: ООО «Индустриальный парк Северные Врата», участники', EGRUL])
    card['party_evidence'] = card.get('party_evidence') or {}
    card['party_evidence']['buyer'] = (card['party_evidence'].get('buyer') or []) + [
        {'value': 'Radius Group', 'field': 'buyer', 'method': 'manual_source_review', 'url': EGRUL}]
    card['party_evidence']['target'] = (card['party_evidence'].get('target') or []) + [
        {'value': 'Экто Прайм', 'field': 'target', 'method': 'manual_source_review', 'url': EGRUL}]
    return card


def main(write=False):
    pending = json.load(open(PENDING, encoding='utf-8'))   # читается прямо перед записью
    cards = [c for c in pending['cards'] if c['id'] == CARD_ID]
    if not cards:
        print('ОТКАЗ: %s нет в очереди' % CARD_ID)
        return 1
    if cards[0].get('eco', {}).get('share') == SHARE:
        print('УЖЕ ПРИМЕНЕНО')
        return 0
    card = patch(cards[0])
    print(json.dumps({k: card.get(k) for k in ('eco', 'src', 'party_evidence')}, ensure_ascii=False, indent=1))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
