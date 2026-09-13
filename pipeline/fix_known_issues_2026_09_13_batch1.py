# -*- coding: utf-8 -*-
"""Три точечные правки из повторного чтения раздела CLAUDE.md «Известные
проблемы» (задача #134, 13 сентября 2026, пять параллельных читателей,
21 карточка) — только те случаи, где свежее чтение дало ЧИСТЫЙ,
дословно подтверждённый факт, а не просто усилило прежнее подозрение.

1. **`g6e8ceb3a`** (профиль «М Холдинг Лтд») — `desc` утверждал
   несостоявшуюся сделку («в 2022 году... купила у Morgan Stanley и
   Hines торговый центр «Метрополис»») как факт, хотя собственный
   `eco.context` карточки `g56342584` уже год как честно фиксирует: эта
   сделка сорвалась после двойного одобрения (ФАС + правкомиссия), а
   реальным покупателем в апреле 2023 года стал армянский Balchug
   Capital. Профиль и карточка молча противоречили друг другу.

2. **`gbfe2ee65`** (Дмитрий Зеленин / «Русское молоко») — независимо
   подтверждено (не «по докладу саб-агента», а прямым чтением
   audit-it.ru/rusprofile.ru), что АО «Рузское молоко» с апреля 2024
   года в процедуре наблюдения (дело №А41-34237/24, иск ФНС), убыток
   за 2025 год — 334,77 млн ₽. Дописано в `eco.context`; вопрос о
   судьбе долей Зеленина/«Дебаркадера» остаётся открытым — это не
   разрешает его, только добавляет уже проверенный факт, которого в
   карточке не было вовсе.

3. **`ga4082daa`** (Мечел / зарубежные активы) — расхождение версий
   Moneyhouse и LRT.lt РАЗРЕШЕНО прямой проверкой официального
   швейцарского торгового реестра (northdata.com, номера юрлиц
   CHE-109.385.824 и CHE-114.168.474): «Mechel International Holdings
   GmbH» переименована в «A Group Switzerland Holdings GmbH» (август
   2024), ликвидирована 17.03.2025, за три дня до этого (20.03.2025)
   поглощена «Teiwaz A Group AG» (бывшая «Mechel Carbon AG»); имя «Fehu
   Services GmbH» из версии LRT.lt в официальной истории цепочки не
   встречается ни разу. Последнее предложение `eco.context`
   («Какая версия верна... не подтверждает») заменено на разрешённую
   версию с указанием источника.

Assert на исходном состоянии — как везде.
"""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__)).rsplit(os.sep + 'pipeline', 1)[0]
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

OLD_DESC_M_HOLDING = (
    'Структура Capital Partners; в 2022 году с существенным дисконтом купила у '
    'Morgan Stanley и Hines торговый центр «Метрополис» (Morgan Stanley купил его '
    'в 2013 году за $1,2 млрд).'
)
NEW_DESC_M_HOLDING = (
    'Структура Capital Partners; в 2022 году договорилась о покупке торгового '
    'центра «Метрополис» у Morgan Stanley и Hines со скидкой, но сделка не '
    'состоялась (сорвалась в 2023 году уже после одобрения ФАС и правкомиссии) — '
    'реальным владельцем ТЦ с апреля 2023 года стал армянский инвестфонд Balchug '
    'Capital, купивший его у Morgan Stanley и Hines напрямую.'
)

GBFE_ADDITION = (
    ' Сам актив, АО «Рузское молоко», с апреля 2024 года находится в процедуре '
    'банкротства (наблюдение, дело №А41-34237/24 по иску ФНС), за 2025 год чистый '
    'убыток составил 334,77 млн ₽ (audit-it.ru, rusprofile.ru) — судьба долей '
    'Зеленина/«Дебаркадера» в обанкротившемся активе по-прежнему нигде не '
    'прослежена.'
)

OLD_MECHEL_TAIL = (
    'Источники расходятся даже в судьбе самих швейцарских холдингов, через '
    'которые был устроен владевший активами контур: по данным сервиса Moneyhouse, '
    '«Mechel Carbon AG» и «Mechel International Holdings GmbH» в августе сменили '
    'названия на «Teiwaz A Group AG» и «A Group Switzerland Holdings GmbH»; '
    'литовское издание LRT.lt, со ссылкой на реестровые данные, пишет, что '
    '«Mechel International Holdings GmbH» была передана другой швейцарской '
    'компании — «Fehu Services GmbH». Какая версия верна и кто настоящий '
    'бенефициар, ни один источник не подтверждает.'
)
NEW_MECHEL_TAIL = (
    'Официальный швейцарский торговый реестр (Handelsregister, по данным '
    'northdata.com) подтверждает версию Moneyhouse, а не LRT.lt: «Mechel '
    'International Holdings GmbH» переименована в «A Group Switzerland Holdings '
    'GmbH» (август 2024) и 20 марта 2025 года поглощена компанией «Teiwaz A Group '
    'AG» (бывшая «Mechel Carbon AG»); само юрлицо ликвидировано 17.03.2025. '
    'Упоминаемая LRT.lt «Fehu Services GmbH» в официальной истории этой цепочки '
    'не значится. Кто сегодня конечный бенефициар «Teiwaz A Group AG», реестр не '
    'раскрывает.'
)


def main(write):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    comps = data['companies']
    by_id = {d['id']: d for d in data['deals']}

    m_holding = comps['g6e8ceb3a']
    assert m_holding.get('desc') == OLD_DESC_M_HOLDING, 'desc М Холдинг уже другой'

    gbfe = by_id['gbfe2ee65']
    old_gbfe_context = gbfe['eco']['context']
    assert GBFE_ADDITION.strip() not in old_gbfe_context

    mechel = by_id['ga4082daa']
    assert OLD_MECHEL_TAIL in mechel['eco']['context'], 'хвост eco.context уже другой'

    m_holding['desc'] = NEW_DESC_M_HOLDING
    print('g6e8ceb3a: desc исправлен (сделка не состоялась, а не куплена)')

    gbfe['eco']['context'] = old_gbfe_context + GBFE_ADDITION
    print('gbfe2ee65: eco.context дополнен фактом банкротства «Рузского молока»')

    mechel['eco']['context'] = mechel['eco']['context'].replace(OLD_MECHEL_TAIL, NEW_MECHEL_TAIL)
    print('ga4082daa: eco.context — расхождение версий разрешено по реестру')

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('Сухой прогон — для записи передайте --write')


if __name__ == '__main__':
    import sys
    main('--write' in sys.argv)
