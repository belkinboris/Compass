# -*- coding: utf-8 -*-
"""G8 (PRODUCT_ROADMAP.md) — четвёртая партия «Собственников», 21 августа
2026. Продолжает партии 2–3: следующий кусок из 221 механических
кандидатов (позиции 56–87 списка), проверенный вручную.

ДВА НОВЫХ TARGET-ДЕФЕКТА НАЙДЕНЫ И ПОЧИНЕНЫ ОТДЕЛЬНЫМИ СКРИПТАМИ ДО этой
партии (пятый и шестой случай за сессию того же класса, что Flocktory/
КИВИ и Таксиагрегатор/КИВИ):
  g52b8df38 (Сбербанк/девелопер «Южный») — target указывал на профиль
    «Банк «Санкт-Петербург»» вместо застройщика; см.
    `fix_sberbank_zastroy_target_profile.py`.
  ge848daa0 (МТС Банк/«РНКБ Страхование») — target указывал на профиль
    «РНКБ Банк» вместо страховой «дочки»; см.
    `fix_mtsbank_rnkb_strahovanie_target_profile.py`.
Оба новых профиля уже несут `ownership` из этой же партии.

ОТКЛОНЕНО ИЗ ЭТОГО КУСКА, С ПРИЧИНОЙ:
  gba72051d (Агрокомплекс им. Ткачева/«Юг Руси») — источник называет
    прямым держателем 100% долей «ООО «Ресурс» Камиля Музафарова», а
    связь с «Агрокомплексом им. Ткачева» в тексте — предположение
    источника («источники издания», «может стать покупателем»), не факт;
    слишком неопределённо для структурированной записи.
  g343154dd (Кредит Европа банк/Икано-банк) — карточка несёт
    ПРОТИВОРЕЧАЩИЕ ДАТЫ ЗАКРЫТИЯ (поле `date`: 2023-03-01, текст: «Сделка
    закрыта 1 марта 2022 года») — не вносил `ownership` с неопределённой
    датой, само расхождение дат — отдельная находка, не по этой задаче,
    записана в журнале.
  gd21bbce8 (Merlion/Натиксис-банк) — единственный % в тексте — диапазон
    ДИСКОНТА к капиталу при типичной продаже банковских активов, не доля
    владения.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

# (target_id, buyer_id, share, as_of, source)
ENTRIES = [
    ('g113002a7-target', 'ga2cfae5b', '100%', '2026-04',
     ['Interfax (англоязычная лента)', 'https://interfax.com/newsroom/top-stories/117223/']),
    ('ga0d716f2', 'g308a4b2a', '100%', '2025-12',
     ['Shoppers', 'https://shoppers.media/news/26121_krupneisii-proizvoditel-miasa-pticy-resurs-kupil-makaronnyi-biznes-granmulino']),
    ('g04328d0f', 'gaf65e2d9', '100%', '2025-08',
     ['Коммерсантъ', 'https://www.kommersant.ru/doc/7959262']),
    ('g4be5d079', 'gcb0304f5', '100%', '2024-12',
     ['Коммерсантъ', 'https://www.kommersant.ru/doc/7446674']),
    ('ge4025a60', 'g527da4e8', '100%', '2024-10',
     ['Интерфакс', 'https://www.interfax.ru/business/989592']),
    ('gb7270224', 'g1a359ad9', '30%', '2024-12',
     ['TAdviser', 'https://www.tadviser.ru/index.php/%D0%9A%D0%BE%D0%BC%D0%BF%D0%B0%D0%BD%D0%B8%D1%8F:%D0%A0%D0%B5%D0%B4_%D0%A1%D0%BE%D1%84%D1%82_(Red_Soft)']),
    ('gd6c3c0ff', 'g470a51f2', '62%', '2024',
     ['Коммерсантъ', 'https://www.kommersant.ru/doc/7267872']),
    ('g487268e0', 'gf9c226e4', '100%', '2025-12',
     ['Ведомости', 'https://www.vedomosti.ru/technology/news/2025/12/29/1167239-t2-priobrel-platformu']),
    ('g8ec70a1f', 'ga2cfae5b', '87,5%', '2025-12',
     ['Alfabank.ru', 'https://alfabank.ru/news/t/release/alfa-bank-zakril-sdelku-po-pokupke-krupneishego-nezavisimogo-avtolizingovogo-operatora-yevroplan']),
    ('gd395e578', 'ge8616484', '100%', '2025-12',
     ['Интерфакс', 'https://www.interfax.ru/business/1064841']),
    ('gea803245', 'g81045bed', '100%', '2025-12',
     ['Коммерсантъ', 'https://www.kommersant.ru/doc/8295554']),
    ('ge848daa0-target', 'g37d577dc', '100%', '2025-12',
     ['Коммерсантъ', 'https://www.kommersant.ru/doc/8339880']),
    ('g4949ccfd', 'ga64461ca', '99%', '2025-11',
     ['Retailer.ru', 'https://retailer.ru/svjazannaja-s-lentoj-struktura-poluchila-kosvennyj-kontrol-nad-setju-o-kej/']),
    ('g52b8df38-target', 'g28ff15bb', '20%', '2024-12',
     ['@dealsma (Telegram)', 'https://t.me/dealsma/5685']),
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
