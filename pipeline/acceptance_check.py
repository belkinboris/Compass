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
import urllib.error
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
    # Слой фактов: каждая показанная сделка обязана нести подтверждение двумя
    # чтениями и чистую арифметику (facts.number_checks) — по ответу сайта.
    unverified = [row['id'] for row in m['deals'] if not str(row.get('verified_by', '')).startswith(('model×2', 'human'))]
    dirty = [(row['id'], row.get('checks')) for row in m['deals'] if row.get('checks')]
    ok = not forbidden and not bad_share and not bad_basis and not unverified and not dirty
    excluded = ', '.join('%s — %s' % (x['label'], x['count']) for x in m.get('excluded', [])[:4])
    p.add('Мультипликаторы: только сделки с фактами, подтверждёнными двумя чтениями, без долей <95% и не-цен', ok,
          base + '/api/analytics/multiples',
          f"показано {m['clean_total']} (подтверждённых {m.get('verified_total')}, ждут чтения {m.get('awaiting_reading')}, "
          f"по тексту проходят {m['candidates_total']}); медианы {'скрыты' if not m.get('show_medians') else 'показаны'}; "
          f"запрещённые: {forbidden or 'нет'}; доля <95%: {bad_share or 'нет'}; не цена: {bad_basis or 'нет'}; "
          f"без подтверждения: {unverified or 'нет'}; арифметика: {dirty or 'чисто'}; исключены: {excluded}")


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


def _pdf_text(body: bytes) -> str | None:
    """Текст PDF любой доступной библиотекой. Импорт pdfminer в этой среде
    роняет процесс паникой из cryptography (PanicException — не Exception,
    обычный except его не ловит), поэтому ловится BaseException, а запасной
    путь — pypdf; нет ни того ни другого — None, и сценарий помечается
    непроверенным, а не проваленным."""
    import io
    try:
        from pdfminer.high_level import extract_text
        return extract_text(io.BytesIO(body)) or ''
    except BaseException:  # noqa: BLE001
        pass
    try:
        from pypdf import PdfReader
        return '\n'.join((pg.extract_text() or '') for pg in PdfReader(io.BytesIO(body)).pages)
    except BaseException:  # noqa: BLE001
        return None


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
    text = _pdf_text(body)
    if text is None:
        p.add('PDF карточки — текст файла', None, base + f'/api/deals/{deal_id}/export', 'ни pdfminer, ни pypdf в этой среде не работают')
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
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900},
                                  ignore_https_errors=bool(external and proxy))
        if external:
            # Headless-браузер из среды разработки до внешних адресов не доходит
            # (прокси среды режет соединение), а urllib доходит. Поэтому каждый
            # запрос страницы к сайту выполняется urllib и отдаётся браузеру как
            # ответ: браузер рисует НАСТОЯЩИЕ страницу, скрипт и данные боевого
            # сайта, только доставленные рабочим каналом среды. Это проверка
            # содержимого сайта, а не его сети — и в протоколе так и написано.
            host = re.sub(r'^https?://', '', base).split('/')[0]

            def relay(route, request):
                url = request.url
                if host not in url:
                    return route.abort()
                if url.rstrip('/').endswith('/api/me'):
                    # Вход по заявке (ACCESS_GATE) — визуальная дверь: API сделок открыт,
                    # закрыт только экран. Приёмке нужны экраны, а аккаунта у неё нет —
                    # дверь обходится ТОЛЬКО здесь, в браузере приёмки: страницы,
                    # скрипт и данные при этом настоящие, с боевого сайта.
                    return route.fulfill(status=200, headers={'content-type': 'application/json'},
                                         body=b'{"logged_in": false, "gate": false}')
                try:
                    data = request.post_data_buffer if request.method == 'POST' else None
                    req = urllib.request.Request(url, data=data, method=request.method,
                                                 headers={k: v for k, v in request.headers.items()
                                                          if k.lower() in ('accept', 'content-type', 'accept-language')} | UA)
                    with urllib.request.urlopen(req, timeout=90) as r:
                        route.fulfill(status=r.status, headers={'content-type': r.headers.get('Content-Type', '')}, body=r.read())
                except urllib.error.HTTPError as e:
                    route.fulfill(status=e.code, body=e.read())
                except Exception as e:  # noqa: BLE001
                    route.abort()
            ctx.route('**/*', relay)
        page = ctx.new_page()
        errors: list[str] = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(base + '/#/analytics')
        page.wait_for_function('typeof DEALS!=="undefined" && DEALS.length>1000', timeout=90000)
        page.wait_for_selector('.an-c-topsum .an-deal', timeout=60000)
        rows = [x.inner_text() for x in page.locator('.an-c-topsum .an-deal').all()]
        soft = [r.replace('\n', ' | ')[:80] for r in rows if SOFT_WORDS.search(r)]
        where = base + '/#/analytics' + (' (страницы боевого сайта, доставленные каналом среды)' if external else '')
        p.add('«Только покупки» на «Аналитике» без оценок, диапазонов, IPO и финансирования', not soft and bool(rows),
              where, f'{len(rows)} строк; лишние: {soft or "нет"}')
        # Список крупнейших — только сделки, чья цена прочитана в источнике
        # (facts.admitted.top_purchases); сверяется с тем, что видно на экране.
        shown = page.evaluate('[...document.querySelectorAll(".an-c-topsum .an-deal")].map(a => a.getAttribute("href").split("/").pop())')
        unread = [i for i in shown if not ((DEALS.get(i) or {}).get('facts') or {}).get('admitted', {}).get('top_purchases')]
        p.add('Крупнейшие покупки: у каждой строки цена прочитана в источнике', not unread and bool(shown),
              where, f'{len(shown)} строк; без прочитанной цены: {unread or "нет"}')
        page.wait_for_function('document.getElementById("multiplesBody") && !document.getElementById("multiplesBody").innerText.includes("Считаем")', timeout=120000)
        mult = page.inner_text('#multiplesCard')
        medians_hidden = 'Медиану по ним не показываем' in mult or 'не прошла все проверки' in mult
        p.add('Блок мультипликаторов: медианы скрыты, показанные сделки помечены «проверено»', medians_hidden and ('проверено' in mult or 'не прошла все проверки' in mult),
              where, mult[:160].replace(chr(10), ' | '))
        # Блок «Проверено по источникам» стоит на «Обзоре» — его видит каждый
        # посетитель, не только тот, кто открыл «Экономиста».
        verified_deal = next((i for i, d in DEALS.items()
                              if ((d.get('facts') or {}).get('price') or {}).get('basis') == 'verified'
                              and (d['facts']['price'] or {}).get('meaning') == 'disclosed'), None)
        if verified_deal:
            page.goto(base + '/#/deal/' + verified_deal)
            page.wait_for_selector('.fact-verified', timeout=15000)
            text = page.inner_text('.fact-verified')
            quote = ((DEALS[verified_deal]['facts']['price'] or {}).get('quote') or '')[:30]
            # .label рисуется заглавными (text-transform), innerText отдаёт текст после CSS
            ok = 'проверено по источникам' in text.lower() and (not quote or quote[:20].lower() in text.lower())
            p.add(f'Карточка {verified_deal}: блок «Проверено по источникам» с цитатой на «Обзоре»', ok,
                  base + '/#/deal/' + verified_deal, text[:140].replace(chr(10), ' | '))
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
