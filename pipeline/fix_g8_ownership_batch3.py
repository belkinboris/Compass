# -*- coding: utf-8 -*-
"""G8 (PRODUCT_ROADMAP.md) — третья партия «Собственников», 21 августа
2026. Продолжает партию 2 (`fix_g8_ownership_batch2.py`): следующий кусок
из 221 механических кандидатов (закрытая M&A-сделка, единственный % в
тексте), проверенный вручную — той же дисциплиной, тот же результат:
из 30 рассмотренных кандидатов (позиции 26–55 списка) верных 21 (70%),
9 отклонены как ложные срабатывания.

ОТКЛОНЕНО, С ПРИЧИНОЙ (не вносится этой или следующей партией):
  ga218f75c (Акульчев/«Колос») — единственный % в тексте относится к доле
    Сулеймановой в ИСКЛЮЧЁННОМ из сделки бренде «Руслада», не к «Колосу».
  gdf51a7ca (Аренадата/«Убик») — 49% — доля ОДНОГО из нескольких
    продавцов (Саттаров), проданное покупателю целиком могло быть больше.
  g3ece5143 (Росспиртпром/ТВЗ) — 51% относится к «Бренд менеджмент»,
    структуре ТВЗ, а не к самому ТВЗ (профиль карточки).
  g139db8c2 (S8 Capital/«Аквариус») — 79% приобретали ДВА покупателя
    совместно (S8 Capital и «МТ-Интеграция»), неясно, кому какая часть.
  g81510c02 (ТОО «Сейф-Ломбард»/МФО «Береке») — тот самый класс дефекта,
    уже описанный в CLAUDE.md («Прямой юридический покупатель и конечный
    бенефициар — разные роли»): 98,988% — доля Ли В САМОМ «Сейф-Ломбарде»
    (покупающей структуре), а не доля «Сейф-Ломбарда» в МФО «Береке».
  g5880d206 (структуры Кима/«Фольксваген банк Рус») — 60% — минимальный
    ДИСКОНТ К ЦЕНЕ при продаже санкционного актива, не доля владения.
  g433cfd40 (Ригла/«Столичные аптеки») — сделка вообще не о покупке доли:
    аренда помещений аптек, а 12,5% — доля сети НА МОСКОВСКОМ РЫНКЕ, не
    доля в предмете сделки.
  g09242ae2 (ООО «Плодородие»/молочный комплекс в Воронеже) и
  gddc29a8d (Медкапитал/ГК «Эксперт») — оставлены без правки: % относится
    к структуре, отличной от профиля-цели (дочернему юрлицу внутри лота
    или группы), требуют более внимательного чтения, чем в рамках партии.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

# (target_id, buyer_id, share, as_of, source)
ENTRIES = [
    ('gc2c803f9', 'g0324fa7b', '100%', '2025-11',
     ['Коммерсантъ', 'https://www.kommersant.ru/doc/8212273']),
    ('g3a6a6971', 'g4b480566', '50%', '2025-11',
     ['Ведомости', 'https://www.vedomosti.ru/realty/articles/2025/11/13/1154433-kitaiskaya-gruppa-siic-prodala-dolyu-v-torgovom-tsentre-zhemchuzhnaya-plaza']),
    ('g7e5ae30b', 'gc536440f', '75%', '2025-10',
     ['Коммерсантъ', 'https://www.kommersant.ru/doc/8178089']),
    ('g623a59a1', 'g968f4166', '100%', '2025-09',
     ['РБК', 'https://www.rbc.ru/society/19/09/2025/68cd54079a79474263e9c71e']),
    ('g354705fa', 'g65dd4e82', '73%', '2025-08',
     ['Коммерсантъ', 'https://www.kommersant.ru/doc/7958520']),
    ('g537f60da', 'gfd1c35bc', '100%', '2025-07',
     ['Коммерсантъ', 'https://www.kommersant.ru/doc/7940459']),
    ('gb78854b9', 'gf3a4398a', '15,9%', '2025-06',
     ['Коммерсантъ', 'https://www.kommersant.ru/doc/8141110']),
    ('g9da789c2', 'g0087fb92', '51%', '2025-06',
     ['РБК', 'https://www.rbc.ru/technology_and_media/09/06/2025/6846e5fc9a79470af38977f3']),
    ('g03800837', 'gd51874a0', '100%', '2025-06',
     ['Ведомости', 'https://www.vedomosti.ru/finance/articles/2025/06/26/1120440-zaimer-pokupaet-nebolshoi-kommercheskii-bank']),
    ('ge1a73976', 'gdb108d96', '100%', '2025-05',
     ['РБК', 'https://www.rbc.ru/business/27/05/2025/683578269a7947de72690dd2']),
    ('g1eff47f6', 'g096e521d', '50%', '2025-04',
     ['РБК', 'https://www.rbc.ru/business/24/04/2025/680920149a794727a019629e']),
    ('g22f45541', 'gf7340794', '100%', '2025-04',
     ['Ведомости', 'https://www.vedomosti.ru/finance/news/2025/04/24/1106409-balchug-kapital-zakrila']),
    ('gb316113e', 'g6699fc6f', '50%', '2025-03',
     ['Коммерсантъ', 'https://www.kommersant.ru/doc/8516012']),
    ('gbae7f513', 'g34aa2579', '100%', '2025-03',
     ['Коммерсантъ', 'https://www.kommersant.ru/doc/7659963']),
    ('g6f4bb996', 'g28ff15bb', '100%', '2025-03',
     ['Orion', 'https://orion-law.com/news/komanda-orion-konsultirovala-ooo-sberbank-investicii-v-sdelke-po-priobreteniyu-100-dolej-ooo-sdm-tk-2-i-dalnejshej-prodazhe-50-dolej-ooo-logopark-7']),
    ('gb5b00fcd', 'g7802e51e', '25%', '2025-02',
     ['РБК', 'https://www.rbc.ru/politics/17/02/2025/67af76c09a79471f8ccb069d']),
    ('g0e121b1b', 'g12111389', '76%', '2025-01',
     ['РБК', 'https://www.rbc.ru/technology_and_media/16/01/2025/67866dc99a7947060ab34c50']),
    ('g56e4248d', 'g924985ab', '51%', '2025',
     ['@dealsma (Telegram)', 'https://t.me/dealsma/6841']),
    ('g5e535262', 'g28ff15bb', '100%', '2025',
     ['РБК', 'https://www.rbc.ru/business/30/09/2025/68dab0ab9a7947241bfb0fdc?from=from_main_4']),
    ('gb9abea75', 'g4233e198', '51%', '2025-09',
     ['РБК', 'https://www.rbc.ru/technology_and_media/22/09/2025/68cbfee39a79470ded583d72']),
    ('g04e0aaee', 'g5ff0a3de', '100%', '2024-12',
     ['Shoppers', 'https://shoppers.media/news/19710_cernogolovka-kupila-proizvoditelia-napitkov-s-aloe-i-kusockami-fruktov-iz-penzy']),
]


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    companies = data['companies']

    for target_id, buyer_id, share, as_of, source in ENTRIES:
        assert target_id in companies, f"нет профиля {target_id}"
        assert buyer_id in companies, f"нет профиля {buyer_id}"
        assert 'ownership' not in companies[target_id], \
            f"{target_id} уже несёт ownership"
        entry = dict(name=companies[buyer_id]['name'], id=buyer_id,
                     share=share, as_of=as_of, source=source)
        print(f"{target_id} ({companies[target_id]['name']}): "
              f"+= {entry['name']} — {share} (на {as_of})")
        companies[target_id]['ownership'] = [entry]

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
