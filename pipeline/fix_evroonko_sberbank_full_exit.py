# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`gff6e08fe` («Сбербанк инвестиции приобрел 9,99% доли в «Евроонко»»,
август 2023, Закрыта) — `eco.context` был заглушкой («—»), хотя у
Сбербанка есть большое продолжение: он не увеличил, а ПОЛНОСТЬЮ вышел
из капитала «Евроонко» в рамках продажи всей группы структуре
совладельца «Медскана» Евгения Туголукова.

Проверено ЛИЧНО прямым WebFetch/чтением PDF (дословные цитаты):
- circular SGX (Don Agro International → UpHealth Group Limited, PDF
  https://links.sgx.com/FileOpen/4.%20Don%20Agro-Circular_301225.ashx?App=Announcement&FileID=873377,
  извлечено напрямую из PDF через pypdf): «On 12 September 2024, the
  Company announced... that Tetra had, on 6 September 2024, entered
  into the following agreements in respect of the proposed
  acquisitions of 99.99% of the shares in 812 Capital... from Vendor 1
  [Mr. Khvicha Akubardia] and Vendor 2 [Mr. Aleksander Sviridov]»;
  «Based on Company information, Hogan Lovells understands that SBI, a
  subsidiary of SBB, currently owns 9.99% of 812 Capital... SBI will
  remain as a 0.01% shareholder of 812 Capital. SBI would be considered
  a Specially Designated National as the result of it being owned 50
  percent or more by Sberbank, which is on OFAC's Specially Designated
  Nationals and Blocked Persons List» — из-за санкций против Сбербанка
  выход SBI структурирован через опционы с Вендором 1, а не напрямую
  Тетре, но итог тот же: доля Сбербанка сокращается с 9,99% до 0,01%;
- Full Yearly Results 2025 (тот же эмитент, PDF, извлечено напрямую):
  «The Proposed Acquisitions in relation to the balance Stake of 89.01%
  of the shares in 812 Capital LLC and 11.5% of shares CIMT LLC have
  been completed... as announced by the Company on 12 February 2026»;
  «Revenue 16,013 33,263 39,438 19,113 25,973» (S$'000, FY2022/FY2023/
  FY2024/1H2024/1H2025) — «revenue increased by approximately S$6.2
  million or 18.6% from approximately S$33.3 million in FY2023 to
  approximately S$39.4 million in FY2024».

НЕ ВНЕСЕНО: (1) точная дата исполнения опциона на оставшиеся 9,98% SBI
— найдена только во вторичных агрегаторах, не проверена личным чтением
первоисточника; (2) сумма сделки Тетры (3,04 млрд ₽ по Ведомостям) —
относится к ДРУГОЙ, более крупной сделке (выкуп 99,99% группы), а не к
предмету этой карточки (продажа доли Сбербанка в 2023 году), в
структурные поля этой карточки не переносится; (3) расхождение между
прибылью 497,6 млн ₽ по РСБУ за 2023 год (medvestnik) и убытком по МСФО
за 2024 год из циркуляра — разные стандарты учёта и периметр, причина
расхождения не выяснена; (4) какая из двух одноимённых «812 Капитал»
(разные ИНН) сейчас основная — не проверено прямой выпиской ЕГРЮЛ.
Судьба всей группы «Евроонко» (продажа Туголукову) — самостоятельный,
более крупный сюжет; заводить ли для него отдельную карточку — решение
притока, не этой рутины.

Запуск: python3 pipeline/fix_evroonko_sberbank_full_exit.py
        python3 pipeline/fix_evroonko_sberbank_full_exit.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gff6e08fe'

OLD_ECO_CONTEXT = '—'
NEW_ECO_CONTEXT = (
    'Сбербанк не увеличил, а полностью вышел из этой доли: в сентябре '
    '2024 года структура совладельца «Медскана» Евгения Туголукова '
    '(сингапурская Tetra, «дочка» публичной Don Agro International, '
    'позже переименованной в UpHealth Group Limited) договорилась о '
    'выкупе 99,99% ООО «812 капитал» у Хвичи Акубардии и Александра '
    'Свиридова. Из-за санкций против Сбербанка его выход оформлен через '
    'опционы с Акубардией, а не напрямую покупателю: доля Сбербанка '
    'должна сократиться с 9,99% до символических 0,01%. Сделка Тетры '
    'завершена и объявлена 12 февраля 2026 года. Выручка группы по МСФО '
    'выросла с S$33,3 млн в 2023 году до S$39,4 млн в 2024-м (+18,6%).'
)

OLD_SRC = [['Медицинский вестник', 'https://medvestnik.ru/content/news/Sberbank-priobrel-dolu-v-klinikah-Evroonko.html']]
NEW_SRC = OLD_SRC + [
    ['Ведомости', 'https://www.vedomosti.ru/business/articles/2024/09/13/1062146-sovladelets-medskan-pokupaet-evroonko'],
    ['SGX Circular (UpHealth Group)', 'https://links.sgx.com/FileOpen/4.%20Don%20Agro-Circular_301225.ashx?App=Announcement&FileID=873377'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
