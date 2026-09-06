# -*- coding: utf-8 -*-
"""Приёмка на живом сайте: «готово» — это показанный результат, а не зелёный тест.

ЗАЧЕМ. Два аудита подряд (5 и 6 сентября 2026) находили дефекты, которые
наши проверки объявили закрытыми: правило «доля 95% и выше» пропустило 30%
Guess, цена здания делилась на прибыль продавца, ассистент отрицал карточку,
на которую сам сослался. Приёмка тогда состояла из юнит-тестов на
придуманных примерах и счётчиков («кандидатов 57 → 29») — она проверяла,
что код делает заложенное, и не смотрела, что ВИДИТ посетитель. Этот скрипт
— вторая половина приёмки: он открывает сайт (боевой или локальный) и
проходит пользовательские сценарии, затронутые изменениями данных,
аналитики, ассистента или экспорта. Запускать после каждого существенного
изменения этих частей; результат — короткий протокол по каждому сценарию:
что проверяли, где, что увидели.

Ожидания берутся из контрольной выборки `pipeline/gold/analytics_gold.json`
(зафиксированы чтением, не кодом) и из базы, лежащей рядом со скриптом.

Запуск:
    python3 pipeline/acceptance_check.py                                  # https://projectcompass.ru
    python3 pipeline/acceptance_check.py --base http://127.0.0.1:8777     # локальный сервер
    python3 pipeline/acceptance_check.py --no-browser                     # только HTTP-сценарии
Код выхода 1, если хотя бы один сценарий не прошёл.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import deal_multiples as dm  # noqa: E402

GOLD = json.loads((ROOT / 'pipeline' / 'gold' / 'analytics_gold.json').read_text(encoding='utf-8'))
BASE_DATA = json.loads((ROOT / 'static' / 'data' / 'deals_promoted.json').read_text(encoding='utf-8'))
DEALS = {d['id']: d for d in BASE_DATA['deals']}
UA = {'User-Agent': 'compass-acceptance'}
SOFT_WORDS = re.compile(r'неофициально|допэмисси|(?:^|[^а-яё])около|по оценке|под залог|структурн[а-яё]* сделк|\d\s*(?:тыс|млн|млрд|трлн)?\.?\s*[–—-]\s*\d', re.I)


class Protocol:
    def __init__(self):
        self.rows: list[tuple[str, bool | None, str, str]] = []

    def add(self, scenario: str, ok: bool | None, where: str, seen: str) -> None:
        """ok=None — сценарий не удалось проверить ИЗ ЭТОЙ СРЕДЫ (не «прошёл»
        и не «упал»): печатается отдельным знаком и в число провалов не идёт,
        но в протоколе остаётся — читатель видит, что именно не проверено."""
        self.rows.append((scenario, ok, where, seen))
        mark = '✓' if ok else ('–' if ok is None else '✗')
        print(f"{mark} {scenario}\n    где: {where}\n    результат: {seen}")

    @property
    def failed(self) -> int:
        return sum(1 for r in self.rows if r[1] is False)

    @property
    def unchecked(self) -> int:
        return sum(1 for r in self.rows if r[1] is None)


def get_json(base: str, path: str, data: dict | None = None, timeout: int = 90):
    req = urllib.request.Request(base + path, headers=dict(UA, **({'Content-Type': 'application/json'} if data is not None else {})),
                                 data=json.dumps(data).encode() if data is not None else None)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8'))


def check_data_is_current(base: str, p: Protocol) -> None:
    """Сайт показывает ту же базу, что лежит в репозитории: иначе остальные
    сценарии проверяют вчерашние данные (база подтягивается из main раз в
    несколько минут, а после деплоя откатывается к версии ветки сборки)."""
    try:
        served = get_json(base, '/static/data/deals_promoted.json', timeout=180)
    except Exception as e:  # noqa: BLE001
        p.add('База на сайте совпадает с репозиторием', False, base + '/static/data/deals_promoted.json', f'ошибка: {e}')
        return
    same = len(served['deals']) == len(DEALS) and set(served.get('merged', {})) >= set(BASE_DATA.get('merged', {}))
    p.add('База на сайте совпадает с репозиторием', same, base + '/static/data/deals_promoted.json',
          f"на сайте {len(served['deals'])} сделок, в репозитории {len(DEALS)}")


def check_multiples(base: str, p: Protocol) -> None:
    """Мультипликаторы: ни одной сделки из «нельзя» контрольной выборки, ни
    диапазона, ни доли ниже 95% — по ТОМУ, что отдаёт сайт, а не по коду."""
    m = get_json(base, '/api/analytics/multiples')
    ids = {row['id'] for row in m['deals']}
    forbidden = [r['id'] for r in GOLD['deals'] if not r['in_multiples'] and r['id'] in ids]
    bad_share = [row['id'] for row in m['deals'] if (dm.stake_established(DEALS.get(row['id'], {})) or 0) < dm.MIN_STAKE_PERCENT]
    bad_basis = [row['id'] for row in m['deals'] if dm.sum_basis(DEALS.get(row['id'], {})) != 'disclosed']
    ok = not forbidden and not bad_share and not bad_basis
    excluded = ', '.join('%s — %s' % (x['label'], x['count']) for x in m.get('excluded', [])[:4])
    p.add('Мультипликаторы без запрещённых выборкой сделок, долей <95% и не-цен', ok, base + '/api/analytics/multiples',
          f"чистых {m['clean_total']} из {m['candidates_total']} кандидатов, медиана {m['median']}; "
          f"запрещённые: {forbidden or 'нет'}; доля <95%: {bad_share or 'нет'}; не цена: {bad_basis or 'нет'}; "
          f"исключены: {excluded}")


def check_assistant_chain(base: str, p: Protocol) -> None:
    """Цепочка вопросов: уточняющий вопрос без имени сущности остаётся на
    той же сделке (аудит, раунд 2: «перепроверь» → «в Компасе нет сделки»)."""
    for chain in GOLD['assistant']:
        history: list[dict] = []
        seen: list[str] = []
        ok = True
        for q in chain['chain']:
            try:
                r = get_json(base, '/api/assistant/lookup', {'question': q, 'context_type': 'general', 'history': history})
            except Exception as e:  # noqa: BLE001
                ok = False
                seen.append(f'{q!r}: ошибка {e}')
                break
            answer = r.get('answer') or ''
            hit = chain['must_mention'] in answer
            ok = ok and hit
            seen.append(f"{q!r}: {'ссылается на карточку' if hit else 'карточки НЕТ в ответе'} — {answer[:90]!r}")
            history += [{'role': 'user', 'body': q}, {'role': 'assistant', 'body': answer}]
        p.add(f"Ассистент держит сделку {chain['must_mention']} по цепочке из {len(chain['chain'])} вопросов", ok,
              base + '/api/assistant/lookup', ' | '.join(seen))


def check_pdf(base: str, p: Protocol) -> None:
    """PDF карточки: настоящий PDF с кириллическим шрифтом (аудит, раунд 1:
    квадраты вместо русского текста)."""
    deal_id = next((i for i, d in DEALS.items() if any(isinstance(a, list) and len(a) > 2 and 'Источник:' in str(a[2])
                                                        for a in (d.get('law') or {}).get('adv') or [])), 'g21ef1542')
    req = urllib.request.Request(base + f'/api/deals/{deal_id}/export', headers=dict(UA, **{'Content-Type': 'application/json'}), data=b'{}')
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            ctype, body = r.headers.get('Content-Type', ''), r.read()
    except Exception as e:  # noqa: BLE001
        p.add('PDF карточки', False, base + f'/api/deals/{deal_id}/export', f'ошибка: {e}')
        return
    ok = ctype.startswith('application/pdf') and body[:5] == b'%PDF-' and b'DejaVuSans' in body
    p.add('PDF карточки — настоящий PDF с кириллическим шрифтом', ok, base + f'/api/deals/{deal_id}/export',
          f'{ctype}, {len(body)} байт, шрифт DejaVu: {"есть" if b"DejaVuSans" in body else "НЕТ"}')
    # Проверяется САМ скачанный файл, а не его заголовки (разбор рецензента,
    # 6 сентября 2026): текст извлекается из PDF — в нём обязан читаться
    # заголовок сделки по-русски и не должно быть служебных пометок притока
    # («Источник: обогащение», «веб-поиск»), которые аудит видел в файле.
    try:
        import io
        from pdfminer.high_level import extract_text
        text = extract_text(io.BytesIO(body)) or ''
    except Exception as e:  # noqa: BLE001
        p.add('PDF карточки — текст файла', None, base + f'/api/deals/{deal_id}/export', f'pdfminer недоступен: {e}')
        return
    title_words = [w for w in re.findall(r'[А-Яа-яЁё]{5,}', DEALS[deal_id]['title'])][:3]
    flat = re.sub(r'\s+', ' ', text)
    has_title = all(w in flat for w in title_words) if title_words else bool(re.search(r'[А-Яа-я]{5,}', flat))
    leaks = re.findall(r'Источник:\s*(?:обогащ|веб-поиск|web)', flat, re.I)
    p.add('PDF карточки — в тексте файла заголовок по-русски и нет служебных пометок', has_title and not leaks,
          base + f'/api/deals/{deal_id}/export',
          f'слова заголовка {title_words}: {"найдены" if has_title else "НЕ найдены"}; служебных пометок: {len(leaks)}')


def check_browser(base: str, p: Protocol) -> None:
    """Сценарии, видимые только в браузере: топ «Только покупки» на
    «Аналитике» и адреса слитых дублей."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        p.add('Экраны в браузере', False, base, 'playwright не установлен')
        return
    exe = '/opt/pw-browsers/chromium'
    # Из среды разработки наружу ходят через прокси с собственным CA: браузер
    # его не знает, поэтому для внешнего адреса — прокси из окружения и
    # доверие его сертификату; локальный сервер — напрямую.
    import os
    external = not re.match(r'https?://(127\.0\.0\.1|localhost)', base)
    proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
    launch_kw = {'executable_path': exe} if Path(exe).exists() else {}
    if external and proxy:
        launch_kw['proxy'] = {'server': proxy}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(**launch_kw)
        page = browser.new_context(viewport={'width': 1280, 'height': 900},
                                   ignore_https_errors=bool(external and proxy)).new_page()
        errors: list[str] = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(base + '/#/analytics')
        page.wait_for_function('typeof DEALS!=="undefined" && DEALS.length>1000', timeout=90000)
        page.wait_for_selector('.an-c-topsum .an-deal', timeout=60000)
        rows = [x.inner_text() for x in page.locator('.an-c-topsum .an-deal').all()]
        soft = [r.replace('\n', ' | ')[:80] for r in rows if SOFT_WORDS.search(r)]
        p.add('«Только покупки» на «Аналитике» без оценок, диапазонов, IPO и финансирования', not soft and bool(rows),
              base + '/#/analytics', f'{len(rows)} строк; лишние: {soft or "нет"}')
        for pair in GOLD['duplicates']:
            page.goto(base + '/#/deal/' + pair['drop'])
            page.wait_for_timeout(700)
            text = page.inner_text('#app')
            title = DEALS[pair['keep']]['title']
            p.add(f"Адрес дубля {pair['drop']} открывает оставшуюся карточку {pair['keep']}", title[:40] in text,
                  base + '/#/deal/' + pair['drop'], f"на экране: {text[:70].replace(chr(10), ' | ')!r}")
        p.add('Ошибок страницы (pageerror) нет', not errors, base, '; '.join(errors[:3]) or 'чисто')
        browser.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='https://projectcompass.ru')
    ap.add_argument('--no-browser', action='store_true')
    args = ap.parse_args()
    base = args.base.rstrip('/')
    p = Protocol()
    print(f'Приёмка на {base}\n')
    check_data_is_current(base, p)
    check_multiples(base, p)
    check_assistant_chain(base, p)
    check_pdf(base, p)
    if not args.no_browser:
        try:
            check_browser(base, p)
        except Exception as e:  # noqa: BLE001 — сбой браузера — тоже строка протокола, а не обрыв
            msg = str(e)
            external = not re.match(r'https?://(127\.0\.0\.1|localhost)', base)
            if external and ('ERR_CONNECTION_RESET' in msg or 'ERR_PROXY' in msg or 'ERR_TUNNEL' in msg):
                # Из среды разработки headless-браузер не доходит до внешних адресов
                # (прокси среды режет соединение; curl и urllib ходят). Это не дефект
                # сайта: браузерные сценарии проверяются локальным сервером на том же
                # коммите — `--base http://127.0.0.1:<порт>` — и об этом сказано прямо.
                p.add('Экраны в браузере (внешний адрес)', None, base,
                      'из этой среды браузер не доходит до внешних адресов — проверить локальным сервером на том же коммите: '
                      f'{msg.splitlines()[0][:100]}')
            else:
                p.add('Экраны в браузере', False, base, f'ошибка браузера: {msg[:160]}')
    tail = f', не проверено из этой среды: {p.unchecked}' if p.unchecked else ''
    print(f'\nСценариев: {len(p.rows)}, не прошли: {p.failed}{tail}')
    return 1 if p.failed else 0


if __name__ == '__main__':
    sys.exit(main())
