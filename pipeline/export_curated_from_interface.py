# -*- coding: utf-8 -*-
"""Выгрузить захардкоженные в интерфейсе карточки в JSON — чтобы приток их видел.

ЗАЧЕМ. В `static/index.html` лежат ТРИ набора сделок, помимо основной базы:
`DEALS` (19 кураторских карточек), `MINI_DEALS` (21) и `CHANNEL_DEALS` (14) —
всего 54 сделки. `match.py` строит индекс только по `deals_promoted.json`, то
есть приток структурно слеп ко всем 54: новость о любой из них считается новой
сделкой и заводит дубль. Именно это и произошло: разбор архива @LawFirms
объявил «новыми» сделки Яндекс/«Заряд!», «Стокманн»/Hugo Boss и
Т-Девелопмент/«Турист», которые все три уже были на сайте.

ПОЧЕМУ ЧЕРЕЗ БРАУЗЕР. Наборы — это JavaScript-литералы с вложенными объектами,
а не JSON (ключи без кавычек, есть шаблонные строки). Разбор регуляркой уже
однажды дал неполный результат: он видел только `DEALS` и пропустил
`MINI_DEALS` с `CHANNEL_DEALS`. Браузер исполняет файл так же, как настоящий
посетитель, и отдаёт данные точно — никакого своего парсера JS.

ГРАНИЦА. Скрипт ничего не решает и не правит: он снимает копию того, что
уже есть в интерфейсе, в файл, который читает `pipeline/ingest/curated.py`.
Перезапускать после каждой правки захардкоженных наборов в `index.html`.

Запуск (нужен локальный сервер: `uvicorn main:app --port 8931`):
    python3 pipeline/export_curated_from_interface.py            # показать счёт
    python3 pipeline/export_curated_from_interface.py --write    # записать файл
"""
import asyncio
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'static', 'data', 'curated_deals.json')
URL = os.environ.get('KOMPAS_URL', 'http://127.0.0.1:8931')
CHROMIUM = '/opt/pw-browsers/chromium'

# Ожидаемый счёт. Если наборы в index.html изменятся, скрипт упадёт, а не
# молча выгрузит другое количество: приток не должен незаметно ослепнуть на
# часть базы во второй раз.
EXPECTED = {'DEALS': 19, 'MINI_DEALS': 21, 'CHANNEL_DEALS': 14}


async def dump():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        launch = {'executable_path': CHROMIUM} if os.path.exists(CHROMIUM) else {}
        browser = await p.chromium.launch(**launch)
        page = await browser.new_page()
        # Рвём загрузку большой базы: нужны ИМЕННО захардкоженные наборы, а
        # после подмешивания deals_promoted.json в DEALS будет 1178 записей.
        # Звёздочка в конце обязательна — адрес идёт с ?v=…, и без неё
        # правило не совпадает (проверено: перехват молча не срабатывал).
        await page.route('**/deals_promoted.json*', lambda r: asyncio.ensure_future(r.abort()))
        await page.route('**/bulk_deals.json*', lambda r: asyncio.ensure_future(r.abort()))
        await page.goto(URL + '/#/')
        await page.wait_for_timeout(2500)
        data = await page.evaluate("""() => ({
            DEALS: DEALS, MINI_DEALS: MINI_DEALS, CHANNEL_DEALS: CHANNEL_DEALS,
            COMPANIES: COMPANIES
        })""")
        await browser.close()
        return data


def main(write=False):
    data = asyncio.run(dump())
    counts = {k: len(data[k]) for k in EXPECTED}
    print('выгружено:', counts)
    assert counts == EXPECTED, (
        'счёт не сошёлся: ожидали %s, получили %s — наборы в index.html '
        'изменились, поправьте EXPECTED осознанно' % (EXPECTED, counts))

    # Складываем в один список: для притока это всё «сделки, которые уже есть».
    # Происхождение сохраняем в поле `origin` — оно объясняет, почему у части
    # записей нет разбора по линзам (мини-записи и записи канала короче).
    out = []
    for key, origin in (('DEALS', 'curated'), ('MINI_DEALS', 'mini'), ('CHANNEL_DEALS', 'channel')):
        for i, deal in enumerate(data[key]):
            row = dict(deal)
            row.setdefault('id', '%s-%d' % (origin, i))
            row['origin'] = origin
            out.append(row)
    print('всего записей:', len(out))
    print('из них с id из интерфейса:', sum(1 for r in out if not r['id'].startswith(('mini-', 'channel-'))))

    if write:
        json.dump(out, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО в', os.path.relpath(OUT, ROOT))
    else:
        print('\nПоказ без записи. Запись — с ключом --write.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
