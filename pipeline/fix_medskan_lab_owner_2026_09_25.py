# -*- coding: utf-8 -*-
"""«Медскан Лаб» и Сбер: решение владельца 25 сентября 2026 (заметка 778).

Вопрос из разбора аудита: вход «Сбербанк Инвестиций» в «Медскан Лаб»
летом 2023 года — покупка доли у «Медскана» или вложение в капитал?
Владелец ответил цитатой Vademecum: «Управляющая компания Сбербанка вошла в
капитал сети клиник «Медскан лаб» летом 2023 года, получив 49% долей… Объем
сделки в момент входа оценивался примерно в 2,49 млрд рублей» — то есть
вложение в капитал, как и у AK&M по данным реестра («внес вклад в уставный
капитал ООО «Медскан Лаб» 2.49 млрд руб., став собственником 49% доли»).
И заметил, что источники карточки говорят о выходе Сбера в 2025 году.

Правки:
  1. `g0410fde2` (вход, 2023): продавца нет — снят «Медскан» (строка
     читателя по «Ведомостям» — «продал 49% долей» — снята в
     `fixes/batch_agents059_r9.py`); доля — «49% долей ООО «Медскан Лаб»»;
     добавлен источник AK&M с данными реестра.
  2. Выход Сбера (октябрь 2025, 39% за 4,767 млрд ₽ головной компании АО
     «Медскан») был описан ДВАЖДЫ: `gc9461b5c` «Сбербанк Инвестиции вышли
     из капитала Медскан Лаб» и `c54966856` «Медскан выкупил долю Сбербанка
     Инвестиций в KDL». Остаётся `gc9461b5c` (точнее заголовок, полнее
     механика и контекст); из `c54966856` переносятся привязка покупателя
     (ГК «Медскан»), доля и два источника; `c54966856` уходит в `merged`,
     его строки таблицы правок сняты. Поста в канале ни у одной нет.

    python3 pipeline/fix_medskan_lab_owner_2026_09_25.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

AKM_2023 = ['AK&M', 'https://www.akm.ru/news/_sberbank_investitsii_investiroval_v_biznes_meditsinskikh_laboratoriy_2_5_mlrd_rub_novaya_redaktsiya/']


def add_src(card, src):
    if not any(len(s) > 1 and s[1] == src[1] for s in card.get('src') or []):
        card.setdefault('src', []).append(src)


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    entry = by_id['g0410fde2']
    assert entry['type'] == 'Инвестиция', entry['type']
    entry.pop('seller', None)
    entry.pop('seller_id', None)
    if entry['eco'].get('share') in (None, '', '—'):
        entry['eco']['share'] = '49% долей ООО «Медскан Лаб»'
    add_src(entry, AKM_2023)

    if 'c54966856' in by_id:
        dup, keep = by_id['c54966856'], by_id['gc9461b5c']
        assert dup['sum'] == keep['sum'] == '4,767 млрд ₽'
        assert not data['telegram_posts'].get('c54966856') and not data['telegram_posts'].get('gc9461b5c')
        assert not keep.get('buyer') and not keep.get('buyer_name')
        keep['buyer'] = dup['buyer']                      # ГК «Медскан» (g729ef6c5)
        if keep['eco'].get('share') in (None, '', '—'):
            keep['eco']['share'] = '39% долей ООО «Медскан Лаб»'
        for src in dup.get('src') or []:
            if 't.me' in src[1]:
                add_src(keep, src)
        data['deals'] = [d for d in data['deals'] if d['id'] != 'c54966856']
        data.setdefault('merged', {})['c54966856'] = 'gc9461b5c'
        data['telegram_posts'].pop('c54966856', None)
        print('c54966856 слита в gc9461b5c')
    print('g0410fde2: продавец снят, доля 49%, источник AK&M')
    if write:
        with open(DATA, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('Записано.')
    else:
        print('Сухой прогон. Запись — с ключом --write.')


if __name__ == '__main__':
    main('--write' in sys.argv)
