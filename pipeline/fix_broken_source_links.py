# -*- coding: utf-8 -*-
"""10 карточек с источником, который не ведёт ни на какую статью.

ЧТО СЛОМАНО. При исходном разборе (не в этом репозитории — см. известный
класс дефекта «источник перепутан») часть карточек получила в `src` не
ссылку на статью, а мусор:
  * 2 карточки — ссылка на кнопку «поделиться в WhatsApp» (`wa.me/?text=…`),
    у которой реальный адрес статьи и её заголовок закодированы ВНУТРИ
    query-параметра `text` — сам адрес `wa.me` никакой статьи не открывает.
  * 8 карточек — «домен» вида `http://Price.ru/`, `http://T.one/`,
    `http://ВЭБ.РФ/` без пути: похоже, что парсер принял название компании,
    упомянутой в тексте карточки (сторону, кредитора, конкурента), за адрес
    источника и собрал из него голую ссылку на главную страницу. Открыв
    такую ссылку, читатель не найдёт ни слова о самой сделке.

ЧТО ДЕЛАЕМ. 2 WhatsApp-ссылки чинятся МЕХАНИЧЕСКИ — просто разбором URL,
без догадок: адрес статьи и так лежит в самой ссылке. 8 «пустышек» —
живым поиском (WebSearch), каждая карточка проверена по существу: заголовок
найденной статьи сверен с содержанием карточки, а не просто «домен похож».
Все 8 фактов, уже записанных в карточке (сумма, доля, стороны), совпали с
найденной статьёй — значит, сама карточка была составлена по реальному
источнику, потерялась только ссылка.

ЧЕГО НЕ ДЕЛАЕМ. Не подписываем результат именем издания задним числом здесь
же — это делает отдельный скрипт `relabel_dealsma_sources.py` для всей базы
разом. Здесь только чиним САМ адрес, чтобы relabel потом отработал по нему
корректно (он трогает только записи с нормальным путём в URL и специально
пропускает голые /домены/, поэтому починка адреса должна идти первой).

Ещё 41 карточка с тем же классом «домен без пути» найдена тем же замером
(49 всего), но НЕ починена — для них живой поиск ещё не проводился (нужна
такая же проверка по существу, по одной карточке, а не скопом). Список — в
PRODUCT_ROADMAP.md.

Запуск:
    python3 pipeline/fix_broken_source_links.py            # сухой прогон
    python3 pipeline/fix_broken_source_links.py --write    # записать
"""
import json
import sys
import urllib.parse

PATH = 'static/data/deals_promoted.json'

# id -> (старый URL, новый URL). Label не трогаем здесь — его поправит
# relabel_dealsma_sources.py на основе домена нового URL.
URL_FIXES = {
    'gb7a4435d': (
        'https://wa.me/?text=https%3A%2F%2Fwww.kommersant.ru%2Fdoc%2F5843149%0AFreedom%20Holding%20%D0%B7%D0%B0%D0%BA%D1%80%D1%8B%D0%BB%20%D1%81%D0%B4%D0%B5%D0%BB%D0%BA%D1%83%20%D0%BF%D0%BE%20%D0%BF%D1%80%D0%BE%D0%B4%D0%B0%D0%B6%D0%B5%20%D1%80%D0%BE%D1%81%D1%81%D0%B8%D0%B9%D1%81%D0%BA%D0%BE%D0%B3%D0%BE%20%D0%B1%D0%B8%D0%B7%D0%BD%D0%B5%D1%81%D0%B0%20%2F%2F%20%D0%9F%D0%BE%D0%B4%D1%80%D0%BE%D0%B1%D0%BD%D0%B5%D0%B5%20%D0%BD%D0%B0%20%D1%81%D0%B0%D0%B9%D1%82%D0%B5',
        'https://www.kommersant.ru/doc/5843149',
    ),
    'gabc53206': (
        'https://wa.me/?text=https%3A%2F%2Fwww.kommersant.ru%2Fdoc%2F5771545%0A%C2%AB%D0%A0%D0%BE%D1%81%D0%B0%D1%82%D0%BE%D0%BC%C2%BB%20%D0%BF%D1%80%D0%B8%D0%BE%D0%B1%D1%80%D0%B5%D0%BB%20%D0%B4%D0%BE%D0%BB%D1%8E%20%D0%B2%20%D1%83%D1%81%D1%82%D0%B0%D0%B2%D0%BD%D0%BE%D0%BC%20%D0%BA%D0%B0%D0%BF%D0%B8%D1%82%D0%B0%D0%BB%D0%B5%20%D1%80%D0%B0%D0%B7%D1%80%D0%B0%D0%B1%D0%BE%D1%82%D1%87%D0%B8%D0%BA%D0%B0%20%D1%81%D0%B8%D0%BC%D1%83%D0%BB%D1%8F%D1%86%D0%B8%D0%B9%20%D0%BA%D0%B8%D0%B1%D0%B5%D1%80%D0%B0%D1%82%D0%B0%D0%BA%20%2F%2F%20%D0%9F%D0%BE%D0%B4%D1%80%D0%BE%D0%B1%D0%BD%D0%B5%D0%B5%20%D0%BD%D0%B0%20%D1%81%D0%B0%D0%B9%D1%82%D0%B5',
        'https://www.kommersant.ru/doc/5771545',
    ),
    'g139db8c2': ('http://Price.ru/', 'https://www.vedomosti.ru/finance/articles/2025/08/21/1133342-s8-maksima-sovladeltsami-akvariusa'),
    'gd2696c44': ('http://Tutu.ru/', 'https://iz.ru/2027534/2026-01-20/tutu-vedet-peregovory-o-pokupke-servisa-delovykh-poezdok-trivio-za-8-mlrd-rublei'),
    'g1cc071e4': ('http://Mail.ru/', 'https://www.kommersant.ru/doc/6863712'),
    'gc10da566': ('http://%D0%BF%D0%BE%D0%BB%D0%B5.%D1%80%D1%84/', 'https://xn--e1alid.xn--p1ai/journal/publication/demetra-treiyding-priobrel-elevator-nash-souz-v-orlovskoiy-oblasti'),
    'g77b24b1c': ('http://T.one/', 'https://www.cnews.ru/news/line/2024-09-11_hajv_investiruet_v_kompaniyu'),
    'g01b8b8f6': ('http://Sravni.ru/', 'https://www.rbc.ru/technology_and_media/18/04/2025/68012fca9a7947a813178b32'),
    'gedc0eb10': ('http://2be.lu/', 'https://www.rbc.ru/technology_and_media/04/09/2023/64ac04229a79471702101d28'),
    'g8348fea5': ('http://%D0%92%D0%AD%D0%91.%D0%A0%D0%A4/', 'https://www.kommersant.ru/doc/5839408'),
}


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    changes = []
    for did, (old_url, new_url) in URL_FIXES.items():
        d = by_id[did]
        src = d.get('src') or []
        idx = next((i for i, s in enumerate(src) if len(s) > 1 and s[1] == old_url), None)
        assert idx is not None, f'{did}: старый URL не найден в src — {old_url!r}'
        changes.append((did, old_url, new_url))
        if write:
            src[idx] = [src[idx][0], new_url]

    print(f'правок: {len(changes)}')
    for did, old, new in changes:
        print(f'  {did}:')
        print(f'    было:  {old[:90]}')
        print(f'    стало: {new}')

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print('\nЗАПИСАНО в', PATH)
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
