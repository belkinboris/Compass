# -*- coding: utf-8 -*-
"""Заметка владельца 782 (25 сентября 2026, ответ на вопрос аудита
audit-ce1b2321f-g4e3ec471): «Да, можно одну» — про две карточки одной и
той же сделки «Сбербанк Инвестиции»: покупка 100% ООО «СДМ ТК-2» и
продажа 50% ООО «Логопарк 7» (тот же покупатель, продавец, предмет и
источник Orion, разница только в дате).

`g4e3ec471» полнее (профиль покупателя, статус «Закрыта», полный текст
про юристов Orion) — остаётся она. У `ce1b2321f» было два факта, которых
не было в `g4e3ec471»: источник Коммерсантъ (доп. деталь о цели покупки
и истории склада) и предыстория склада (бывший «Пивдом», банкротство
2016, торги, покупка СДМ ТК-2 в 2021 году за 4,64 млрд ₽) — переносятся
в `g4e3ec471.eco.context`, сейчас там «—». Источник Коммерсанта
добавляется в `src`.

Дубль удаляется, `merged` перенаправляет старый id на выжившую карточку.

Запуск: python3 pipeline/fix_merge_sberinvest_sdm_tk2_dup.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DUP_ID = 'ce1b2321f'
SURVIVOR = 'g4e3ec471'

KOMMERSANT_SRC = ["Коммерсантъ", "https://www.kommersant.ru/doc/8077927"]

NEW_CONTEXT = (
    "Купленный склад ранее принадлежал компании «Пивдом», которая в 2000-х "
    "была одним из лидеров дистрибуции пива в Московском регионе, но в "
    "2016 году была признана банкротом по заявлению Промсвязьбанка, и её "
    "имущество продали на торгах: логопарк в 2021 году за 4,64 млрд ₽ "
    "приобрела «СДМ ТК-2», принадлежавшая на тот момент холдингу «Индустри "
    "Партнерс Корпорейшн». Представитель Сбербанка уточнил, что актив "
    "приобретён в инвестиционных целях, а на следующем этапе банк "
    "планирует привлечь партнёра для операционного управления объектом — "
    "тогда распределение долей в капитале «СДМ ТК-2» изменится."
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)

    ids = {c['id'] for c in data['deals']}
    assert DUP_ID in ids
    assert SURVIVOR in ids

    survivor = next(c for c in data['deals'] if c['id'] == SURVIVOR)
    assert survivor['eco']['context'] == '—'
    survivor['eco']['context'] = NEW_CONTEXT
    assert list(survivor['src']) == [
        ["Orion", "https://orion-law.com/news/komanda-orion-konsultirovala-ooo-sberbank-investicii-v-sdelke-po-priobreteniyu-100-dolej-ooo-sdm-tk-2-i-dalnejshej-prodazhe-50-dolej-ooo-logopark-7"]
    ]
    survivor['src'].append(KOMMERSANT_SRC)

    data['deals'] = [c for c in data['deals'] if c['id'] != DUP_ID]
    data.setdefault('merged', {})[DUP_ID] = SURVIVOR

    print(f'{SURVIVOR}: добавлен eco.context и источник Коммерсанта')
    print(f'Удалена дублирующая карточка {DUP_ID} (-> {SURVIVOR})')

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('(сухой прогон, для записи — --write)')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
