# -*- coding: utf-8 -*-
"""G8 (PRODUCT_ROADMAP.md) — заполнение `holding` для профилей, чьё
собственное описание (`desc`) уже прямо называет группу, а профиль этой
группы уже существует в базе (тот же случай, что «Тele2»/«Центральный
телеграф» → «Ростелеком», уже связаны раньше). Замер 13 сентября 2026:
24 профиля с `holding: None`, чей `desc` говорит «входит в группу/холдинг»
или «дочерняя структура», из них у 4 профиль группы нашёлся в базе под
точным именем — остальные либо ссылаются на иностранную материнскую
структуру без профиля (STADA, BPCE, Credit Europe Bank, IKEA — профиль
«четыре фабрики IKEA» описывает ПРОДАННЫЙ АКТИВ, а не саму группу IKEA),
либо описывают группу ДРУГОЙ компании, упомянутой в тексте мимоходом
(«Smartway (входит в холдинг «1С»)» у профиля АТН — это группа Smartway,
не самого АТН; «ООО «УК Центр» (входит в группу IBS)» у профиля IBS — это
группа дочернего юрлица, а не самого IBS).

Четыре связи:
- ga51369c2 (АО «ЮниКредит Банк») -> g456f45fa (UniCredit)
- gc904414e (Федеральная грузовая компания) -> g8ec7e7bf (РЖД)
- g30bcda98 (Окуловская бумажная фабрика) -> gbf2a776d (Каппа РУС)
- g2eaee278 (Parametr) -> gkpik (ГК ПИК)

Источник факта в каждом случае — уже стоящий в базе `desc` самого профиля
(это не новое утверждение, а перенос уже написанного текста в структурное
поле, как и было сделано для Tele2/Центрального телеграфа 18 августа) —
поэтому `source` не проставляется, только `id`/`confidence`, тем же
минимальным составом, что и у этой пары.

`test_holding_target_is_always_flagged_as_group` (test_data.py) поймал
недостающую половину правки: все четыре профиля-цели (РЖД, ГК ПИК,
UniCredit, «Каппа РУС») — настоящие группы/холдинги, но ни у одного не
стоял `group: true`, а тест требует этого у ЛЮБОГО профиля, на который
ссылается чей-то `holding.id` (иначе на карточке рисуется список «В группу
входит: N» без бейджа «Группа компаний» рядом с именем — та же путаница,
которую владелец просил не допускать 23 августа). Все четыре — заголовки/
описания сами называют их группой (РЖД — «железнодорожная монополия»
общероссийского масштаба, ГК ПИК — «крупнейший российский девелопер»,
UniCredit — «итальянская банковская группа», «Каппа РУС» — материнская
структура, под именем которой числится Окуловская фабрика), поэтому
`group: true` ставится тем же скриптом, а не отдельным.

Запуск:
    python3 pipeline/fix_g8_holding_links_from_own_desc.py            # сухой прогон
    python3 pipeline/fix_g8_holding_links_from_own_desc.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_HOLDING = {
    'ga51369c2': {'id': 'g456f45fa', 'confidence': 'disclosed'},
    'gc904414e': {'id': 'g8ec7e7bf', 'confidence': 'disclosed'},
    'g30bcda98': {'id': 'gbf2a776d', 'confidence': 'disclosed'},
    'g2eaee278': {'id': 'gkpik', 'confidence': 'disclosed'},
}

# Профили-цели holding обязаны нести group:true (test_holding_target_is_
# always_flagged_as_group) — все четыре реальные группы/холдинги.
GROUP_TARGETS = {'g8ec7e7bf', 'gkpik', 'g456f45fa', 'gbf2a776d'}


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    companies = data['companies']

    pending_holding = {}
    for cid, holding in NEW_HOLDING.items():
        assert cid in companies, 'нет такого профиля: %s' % cid
        assert holding['id'] in companies, 'нет такого профиля группы: %s' % holding['id']
        current = companies[cid].get('holding')
        if current:
            assert current == holding, 'holding уже занят другим значением у %s: %r' % (cid, current)
            continue
        pending_holding[cid] = holding

    pending_group = {}
    for cid in GROUP_TARGETS:
        assert cid in companies, 'нет такого профиля: %s' % cid
        if companies[cid].get('group') is True:
            continue
        assert companies[cid].get('group') is None, 'group уже занято другим значением у %s: %r' % (cid, companies[cid].get('group'))
        pending_group[cid] = True

    if not pending_holding and not pending_group:
        print('Все профили уже связаны и помечены — нечего применять.')
        return

    print('Заполняю holding:')
    for cid, holding in pending_holding.items():
        print('  %s (%s) -> %s (%s)' % (
            cid, companies[cid]['name'], holding['id'], companies[holding['id']]['name']))
    print('Ставлю group:true:')
    for cid in pending_group:
        print('  %s (%s)' % (cid, companies[cid]['name']))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    for cid, holding in pending_holding.items():
        companies[cid]['holding'] = holding
    for cid in pending_group:
        companies[cid]['group'] = True

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
