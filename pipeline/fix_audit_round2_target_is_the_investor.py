# -*- coding: utf-8 -*-
"""Предметом сделки стоит сам покупатель (инвестор) — 23 карточки, найденные
замером по общему профилю предмета (аудит перед бетой, раунд 2, 6 сентября 2026).

КАК НАШЛОСЬ. `pipeline/find_duplicate_deal_candidates.py` ищет дубли по общему
ПРОФИЛЮ предмета — и вместе с дублями вытащил пары вроде «Приобретение «Лентой»
сети «Семья»» / «Приобретение «Лентой» сети «Билла»» с общим предметом... «Группа
Лента». Ни одна из них не дубль: у карточек одна и та же ошибка — в `target`
записан покупатель, а сам предмет (Семья, Билла, Solar Security, YouDo,
Brain4Net, «Южный полюс», Five AI, «Профилум», The Mashina, Martlet, Real,
Cosmos/«Медси», AliExpress Russia, «Зеленая точка») не назван ни профилем, ни
текстом. Это класс «предметом стоит покупатель», записанный в CLAUDE.md как
«механически не измерен: наивное правило даёт кандидатов, и все они — верные
записи о buyback и MBO». Замер здесь другой и точнее: `target` без `buyer`, при
этом профиль предмета в ДРУГИХ карточках стоит покупателем, а заголовок
начинается с его имени как действующего лица. Из 14 таких карточек верных
записей три (SPO Яндекса, привлечение «Медскана», раунд «Моторики» — там
компания и есть предмет), остальные — дефект; ещё 9 пришли из пар «общий
предмет» напрямую.

ЧТО ДЕЛАЕТ. Покупатель переезжает в `buyer` (или `buyer_name` текстом, когда
инвесторов двое или профиля нет), предмет — в `target`, если профиль есть
(«Эталон Груп», ГК «Солар» — нынешнее имя Solar Security, AliExpress Россия,
«Лента» у «Севергрупп», фонд «Восход»), иначе текстом в `asset` в именительном
падеже из заголовка. Раунды, допэмиссии и взносы в СП, стоявшие типом «M&A»,
получают тип «Инвестиция»: деньги идут компании, продавца нет — та же граница
cash-in/cash-out, что у ПСБ/«Атом» (CLAUDE.md). Отдельно, по замечанию аудита о
«финансировании внутри покупок», тип «Инвестиция» получают шесть cash-in
размещений (допэмиссия Segezha на 113 млрд ₽, SPO «Аэрофлота», ВЭБ.РФ в
капитал РЖД, SPO Яндекса, Mail.ru и «Эталона») — они попадали в «Крупнейшие
покупки» «Аналитики» как M&A. Вторичные SPO, где акционер продаёт свои акции
(HeadHunter/Goldman Sachs, TCS/Rigi Trust), остаются M&A: там есть продавец.

Каждая правка — под assert на исходное состояние; применённая правка узнаётся
и пропускается, повторный прогон безопасен.

Запуск:
    python3 pipeline/fix_audit_round2_target_is_the_investor.py           # сухой прогон
    python3 pipeline/fix_audit_round2_target_is_the_investor.py --write
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'
FROM_TARGET = '<из target>'
INVEST = 'Инвестиция'

# id: {buyer|buyer_name, target|asset, [type]} — buyer=FROM_TARGET значит «профиль, стоявший в target».
FIXES = {
    'gcf05509a': dict(buyer=None, target=None, asset='Cosmos Hotel Group и сеть клиник «Медси»'),
    'g7dcbe19d': dict(buyer_name='Консорциум SCP Group / x+bricks', target=None, asset='сеть гипермаркетов Real (Германия)'),
    'gf01b71ff': dict(target=None, asset='британский стартап Five AI (беспилотное вождение)'),
    'g34d8c65b': dict(buyer=FROM_TARGET, target='ga37e3cf6', type=INVEST),  # Эталон Груп
    'g8102258a': dict(target=None, asset='профориентационная платформа «Профилум»'),
    'g64831887': dict(target=None, asset='ГК «Зеленая точка»'),
    'gec65b08d': dict(buyer=FROM_TARGET, target=None, asset='YouDo Web Technologies Limited (сервис YouDo)', type=INVEST),
    'g8b512496': dict(target=None, asset='маслозавод «Южный полюс» в Кропоткине'),
    'g836fc39b': dict(buyer_name='Агентство Blacklight (Максим Перлин)', target=None, asset='бренд базовой женской одежды Martlet', type=INVEST),
    'gb1a695c9': dict(buyer_name='ФРИИ и Sistema SmartTech', target=None, asset='сервис подписки на автомобили The Mashina', type=INVEST),
    'gfb07021f': dict(buyer_name='«Коммит Кэпитал» (фонд «Ростелекома») и Typhoon Digital Development', target=None,
                      asset='разработчик SDN-решений Brain4Net', type=INVEST),
    'gd73a6964': dict(buyer=FROM_TARGET, target='gc2c7aaba'),  # ГК «Солар» — нынешнее имя Solar Security
    'g1658eff4': dict(buyer=FROM_TARGET, target=None, asset='пермская розничная сеть «Семья» (ГК «ЭКС»)'),
    'g17babf0c': dict(buyer=FROM_TARGET, target=None, asset='сеть супермаркетов «Билла Россия» (Billa Russia GmbH)'),
    'g221e9139': dict(buyer=FROM_TARGET, target='g16938a37', type=INVEST),  # AliExpress Россия
    'gabc867f3': dict(buyer=FROM_TARGET, target=None, asset='ООО «Изобилие» (6,7 тыс. га в Ставропольском крае)'),
    'ge3195449': dict(buyer=FROM_TARGET, target='gcca31da7'),  # Группа Лента
    'g68323715': dict(buyer=FROM_TARGET, target=None, asset='Dixy Holding Limited (сеть «Дикси»)'),
    'gb2ab7521': dict(buyer=FROM_TARGET, target=None, asset='Rambler Group', type=INVEST),
    'g29be3540': dict(buyer=FROM_TARGET, target=None, asset='Global Telecom Holding (GTH)'),
    'gdd45b5d5': dict(buyer=FROM_TARGET, target='g427bcb12'),  # Венчурный фонд «Восход»
    'g9e6dec61': dict(buyer=FROM_TARGET, target=None, asset='ПАО «Аэропорт Кольцово»'),
    'ga0db1bef': dict(buyer=FROM_TARGET, target=None, asset='завод каменной ваты в Польше (Выкроты, Нижняя Силезия)'),
}

# cash-in размещения, стоявшие типом M&A
RETYPE = {'g042073c4': INVEST, 'gc7c69679': INVEST, 'g9180c0a6': INVEST, 'gf2dec612': INVEST,
          'gc9a96521': INVEST, 'ga4abadd2': INVEST}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    deals = {d['id']: d for d in data['deals']}
    comps = data['companies']
    done = 0
    for did, fix in FIXES.items():
        d = deals[did]
        old_target = d.get('target')
        if old_target is None and not (fix.get('target') is None and 'target' not in fix):
            print(f'{did}: уже применено (target пуст)'); done += 1; continue
        if fix.get('target') and old_target == fix['target']:
            print(f'{did}: уже применено (target={old_target})'); done += 1; continue
        assert old_target and old_target in comps, (did, old_target)
        assert not d.get('asset'), (did, d.get('asset'))
        new_buyer = fix.get('buyer')
        if new_buyer == FROM_TARGET:
            new_buyer = old_target
            assert not d.get('buyer') and not d.get('buyer_name'), (did, d.get('buyer'), d.get('buyer_name'))
        if fix.get('target'):
            assert fix['target'] in comps, fix['target']
            assert fix['target'] != new_buyer
        print(f'{did}: target {old_target} ({comps[old_target]["name"]}) -> {fix.get("target")}'
              f'{" (" + comps[fix["target"]]["name"] + ")" if fix.get("target") else ""}; '
              f'buyer={new_buyer or d.get("buyer")}; buyer_name={fix.get("buyer_name", d.get("buyer_name"))!r}; '
              f'asset={fix.get("asset")!r}; type={fix.get("type", d.get("type"))}')
        if write:
            d['target'] = fix.get('target')
            if 'asset' in fix:
                d['asset'] = fix['asset']
            if new_buyer:
                d['buyer'] = new_buyer
                d['buyer_name'] = None
            if 'buyer_name' in fix:
                d['buyer_name'] = fix['buyer_name']
                d['buyer'] = None
            if fix.get('type'):
                d['type'] = fix['type']
                d['kind'] = 'financing'
    for did, new_type in RETYPE.items():
        d = deals[did]
        if d.get('type') == new_type:
            print(f'{did}: тип уже {new_type}'); continue
        assert d.get('type') == 'M&A', (did, d.get('type'))
        print(f'{did}: type M&A -> {new_type} ({d["title"][:60]})')
        if write:
            d['type'] = new_type
            d['kind'] = 'financing'
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
