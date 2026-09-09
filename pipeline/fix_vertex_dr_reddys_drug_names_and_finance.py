# -*- coding: utf-8 -*-
"""Месячная очередь, 9 сентября 2026 — дочитывание карточки `gf70a43e6`
(«"Вертекс" продала Dr. Reddy's права на три гинекологических
препарата», добавлена в базу 8 сентября 2026).

Дельта-поиск (саб-агент + личная проверка) нашёл названия препаратов,
финансовые показатели «Вертекса» и дополнительный комментарий эксперта.
Личный WebFetch подтвердил дословно:

1) Названия препаратов. gxpnews.net: «передав ей права на три
   гинекологических препарата — «Эльжину», «Миражэль» и «Орниону»».
   pharmvestnik.ru независимо подтверждает состав портфеля
   («противомикробное лекарство и два гормональных препарата»), но
   имена не называет — карточка получает названия из gxpnews.net.

2) Финансовые показатели «Вертекса» за 2025 год (для контекста
   масштаба компании, не самой сделки): pharmprom.news: «"Вертекс"
   превысила 24,9 млрд рублей выручки (без НДС) по итогам 2025 года,
   что почти на 14% больше показателя предыдущего года».

3) Дополнительный комментарий эксперта. gxpnews.net: «Директор RNC
   Pharma Николай Беспалов отметил, что для успешного продвижения
   брендов потребуются серьезные маркетинговые вложения» — и, по его
   мнению, «у «Вертекса» ресурсов на это сейчас нет».

НЕ внесено: цитата гендиректора «Вертекса» Георгия Побелянского (второй
WebFetch того же источника её не подтвердил — воспроизводимость не
установлена, записывать нельзя); консультанты сделки (не названы ни в
одном источнике); выручка от продажи именно этих трёх препаратов до
сделки (нигде не встретилась).

Запуск:
    python3 pipeline/fix_vertex_dr_reddys_drug_names_and_finance.py            # сухой прогон
    python3 pipeline/fix_vertex_dr_reddys_drug_names_and_finance.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

OLD_ECO_SHARE = '—'
NEW_ECO_SHARE = (
    'Проданы права на три препарата: противомикробное средство '
    '«Эльжина» и гормональные препараты «Миражэль» и «Орниона».'
)

OLD_ECO_TARGET_FIN = '—'
NEW_ECO_TARGET_FIN = (
    'Выручка «Вертекса» по итогам 2025 года превысила 24,9 млрд ₽ '
    '(без НДС) — почти на 14% больше, чем годом раньше.'
)

OLD_ECO_VAL = (
    'Исполнительный директор RNC Pharma Николай Беспалов оценивает '
    'портфель препаратов в 550–610 млн ₽.'
)
NEW_ECO_VAL = OLD_ECO_VAL + (
    ' По его мнению, для успешного продвижения брендов потребуются '
    'серьёзные маркетинговые вложения, а у «Вертекса» ресурсов на это '
    'сейчас нет.'
)

NEW_SRC = [
    ['GxP News', 'https://gxpnews.net/2026/08/dr-reddys-priobrela-u-verteksa-tri-ginekologicheskih-preparata/'],
    ['PharmProm.news', 'https://pharmprom.news/vyruchka-farmkompanii-verteks-v-2025-godu-prevysila-249-mlrd-rublej/'],
]


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['gf70a43e6']

    assert d['eco']['share'] == OLD_ECO_SHARE, \
        'gf70a43e6 eco.share уже другой: %r' % (d['eco']['share'],)
    assert d['eco']['target_fin'] == OLD_ECO_TARGET_FIN, \
        'gf70a43e6 eco.target_fin уже другой: %r' % (d['eco']['target_fin'],)
    assert d['eco']['val'] == OLD_ECO_VAL, \
        'gf70a43e6 eco.val уже другой: %r' % (d['eco']['val'],)
    urls = {s[1] for s in d['src']}
    for src in NEW_SRC:
        assert src[1] not in urls, 'источник уже добавлен: %s' % src[1]

    print('gf70a43e6: eco.share заполнен (названия трёх препаратов); '
          'eco.target_fin заполнен (выручка «Вертекса» за 2025 год); '
          'eco.val дополнен (комментарий Беспалова о маркетинговых '
          'вложениях); добавлены источники gxpnews.net, pharmprom.news')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d['eco']['share'] = NEW_ECO_SHARE
    d['eco']['target_fin'] = NEW_ECO_TARGET_FIN
    d['eco']['val'] = NEW_ECO_VAL
    d['src'].extend(NEW_SRC)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
