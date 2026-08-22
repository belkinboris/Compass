# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gb4923dfc (Home Shopping
Europe/Shopping Live): найден дефект того же класса, что уже не раз
описан в CLAUDE.md — «Стороной сделки может быть записан её предмет».

`buyer` карточки указывал на профиль `g874226d9` — но этот профиль назван
«Shopping Live» и его собственное описание («его... выкупил у Home
Shopping Europe основатель Илья Кирик») однозначно говорит, что это
профиль ПРЕДМЕТА сделки (актива), а не покупателя. `target` при этом был
`null` — то есть у сделки не было предмета вовсе, а был лишний
«покупатель», совпадающий с самим активом.

Источник (Коммерсантъ, доп. подтверждено RB.RU, Retail.ru, New-Retail.ru
дословно теми же цифрами): прямым юридическим покупателем выступила
компания «К2 Инвест», где 99,9% принадлежит Илье Кирику, а 0,1% —
Дмитрию Кузнецову: «По данным ЕГРЮЛ, с 25 июня 2024 года управляющее
этим бизнесом ООО «Директ Трейд» принадлежит компании «К2 Инвест», где
99,9% у Ильи Кирика, 0,1% — у Дмитрия Кузнецова».

Починка (родня прецеденту Пулково/Domina — профиль не переименовывается,
роль перевешивается на верную запись):
1. `target` := `g874226d9` («Shopping Live») — актив остаётся активом.
2. Заведён новый профиль `gb4923dfc-buyer` («К2 Инвест») — прямой
   юридический покупатель, с долями Кирика/Кузнецова в описании; заголовок
   карточки по-прежнему называет узнаваемое имя (Кирик), как и предписывает
   принцип «заголовок — бренд, buyer/seller_id — юрлицо».
3. `buyer` := `gb4923dfc-buyer`.

Профиль `g874226d9` используется только этой одной сделкой (проверено:
grep по всей базе не нашёл других decков c buyer/target/seller_id на
этот id) — безопасно перевесить роль без создания второго профиля-твина.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gb4923dfc'
ASSET_PROFILE_ID = 'g874226d9'
NEW_BUYER_ID = 'gb4923dfc-buyer'
NEW_BUYER = {
    'name': 'К2 Инвест',
    'ind': 'E-commerce',
    'desc': 'Холдинговая компания, через которую Илья Кирик (99,9%) и '
            'Дмитрий Кузнецов (0,1%) в 2024 году выкупили у Home Shopping '
            'Europe 100% телемагазина Shopping Live («Директ Трейд»).',
    'kpi': ['Профиль', 'Автоматический'],
}


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['buyer'] == ASSET_PROFILE_ID, \
        f"buyer: неожиданное значение {deal['buyer']!r}"
    assert deal['target'] is None, f"target: неожиданное значение {deal['target']!r}"
    assert data['companies'][ASSET_PROFILE_ID]['name'] == 'Shopping Live'
    assert NEW_BUYER_ID not in data['companies'], 'профиль покупателя уже существует'

    print(f"{DEAL_ID} target: null -> {ASSET_PROFILE_ID} (Shopping Live — предмет)")
    deal['target'] = ASSET_PROFILE_ID

    print(f"{DEAL_ID} buyer: {ASSET_PROFILE_ID} -> {NEW_BUYER_ID} (новый профиль «К2 Инвест»)")
    deal['buyer'] = NEW_BUYER_ID
    data['companies'][NEW_BUYER_ID] = NEW_BUYER

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
