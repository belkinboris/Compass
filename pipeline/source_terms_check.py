# -*- coding: utf-8 -*-
"""Ежемесячная проверка источников: не запрещает ли сайт собирать его
материалы автоматически — не техническими средствами, а словами.

Просьба владельца 3 октября 2026: «раз в месяц надо защиты проверять на всех
источниках (не технические запреты, а именно текстовые запреты собирать
информацию автоматическими средствами). Если где-то есть такой запрет, надо
чтобы ты сообщал нам».

Что проверяется у каждого источника из `pipeline/ingest/sources.json`
(кроме телеграм-каналов):
  1. robots.txt — запрет всем роботам («Disallow: /» для `*`), запрет
     поимённо ИИ-ботам, или открыт. Это технический сигнал, но прочитанный
     как текст: он тоже говорит о воле владельца сайта.
  2. Пользовательское соглашение, правила, страница о копирайте — страницы,
     на которые ведут ссылки с главной со словами «соглашение», «правила»,
     «условия», «копирайт», «terms», «legal». В них ищутся предложения, где
     рядом стоят слово про автоматизацию (автоматизированн-, робот, парсинг,
     скрапинг, crawl, scrap, bot) и слово про запрет или согласие
     (запрещ-, не допуска-, без согласия, without permission). Так 26 сентября
     2026 нашлись запреты у РБК («запрещается автоматизированное извлечение
     информации сайта любыми сервисами без официального разрешения»),
     TAdviser, Lenta.ru, InvestFuture — при полностью открытом robots.txt.

Итог сравнивается с прошлым (`pipeline/source_terms.json`): новые запреты и
снятые запреты — в отчёт; `--write` обновляет память; `--console` шлёт отчёт
в консоль (тема «Общая информация»). Молчание — когда ничего не изменилось.

Найденные предложения — повод для человека прочитать страницу, а не
приговор: скрипт не отличает «запрещаем парсинг» от «мы не собираем ваши
данные автоматически» идеально, поэтому в отчёте всегда есть цитата и адрес.

    python3 pipeline/source_terms_check.py              # проверить и показать разницу
    python3 pipeline/source_terms_check.py --write      # и запомнить
    python3 pipeline/source_terms_check.py --write --console
    python3 pipeline/source_terms_check.py --host rbc.ru   # один источник, подробно
"""
import json
import os
import re
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = os.path.join(ROOT, 'pipeline', 'ingest', 'sources.json')
STATE = os.path.join(ROOT, 'pipeline', 'source_terms.json')
# Как часто проверять: рутина качества зовёт скрипт каждый день, а сам он
# решает, прошёл ли месяц. `--force` проверяет сразу.
EVERY_DAYS = 28
# Только латиница: заголовок HTTP с кириллицей httpx не отправляет вовсе.
UA = 'KompasBot/0.1 (+https://projectcompass.ru; terms-of-use check)'
TIMEOUT = 15
MAX_LEGAL_PAGES = 8

AI_BOTS = ['GPTBot', 'ChatGPT-User', 'OAI-SearchBot', 'CCBot', 'ClaudeBot', 'Claude-Web',
           'anthropic-ai', 'Google-Extended', 'Bytespider', 'PerplexityBot', 'Applebot-Extended',
           'Diffbot', 'cohere-ai', 'Amazonbot', 'meta-externalagent', 'AI2Bot', 'DuckAssistBot']

LEGAL_LINK_WORDS = ('соглашен', 'правил', 'услови', 'автор', 'copyright', 'copyr', 'terms', 'legal',
                    'privacy', 'юридич', 'ограничен', 'правов', 'disclaimer', 'оферт',
                    'пользовательск', 'контент', 'материал', 'о проекте', 'о компании', 'about')

AUTO = re.compile(
    r'автоматиз\w*|автоматическ\w*|\bробот\w*|парсинг\w*|парсер\w*|скрапинг\w*|скрейпинг\w*'
    r'|\bбот[ыао]?\b|краул\w*|\bcrawl\w*|\bscrap\w*|\bspider\w*|data\s+mining|\bbot(s)?\b', re.I)
PROHIBIT = re.compile(
    r'запрещ\w*|не\s+допуска\w*|не\s+разреша\w*|только\s+с\s+(письменн\w+\s+)?(согласия|разрешения)'
    r'|без\s+(письменн\w+\s+)?(согласия|разрешения)|is\s+prohibit\w*|not\s+permit\w*'
    r'|you\s+shall\s+not|you\s+may\s+not|without\s+(our|the|prior|express)\s+(written\s+)?(permission|consent)'
    r'|не\s+вправе', re.I)
# Предложения, которые на самом деле не про сбор материалов сайта: про
# cookies и аналитику самого сайта, права субъекта персональных данных
# (GDPR «automated means»), металлолом («scrap supplies»), рекламные
# технологии, которые «crawl» контент самого сайта.
NOISE = re.compile(
    r'cookie|веб-маяк|маяк|персональн\w*\s+данн\w*\s+(без\s+идентификации|субъект)'
    r'|сбор\w*\s+сведений\s+без\s+идентификации|processed\s+by\s+automated\s+means'
    r'|carried\s+out\s+by\s+automated\s+means|scrap\s+(supplies|metal)|crawls\s+and\s+categori'
    r'|персональн\w*\s+данн\w*\s+других\s+пользовател|информацию\s+о\s+других\s+пользовател'
    r'|рассылка\s+ушла|промокод', re.I)
SENT_SPLIT = re.compile(r'(?<=[.!?…])\s+(?=[А-ЯA-Z«"])')
TAG_RE = re.compile(r'<script.*?</script>|<style.*?</style>', re.S | re.I)
TAGS_RE = re.compile(r'<[^>]+>')
LINK_RE = re.compile(r'<a\s[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.S | re.I)


def hosts_from_sources():
    out = {}
    for src in json.load(open(SOURCES, encoding='utf-8'))['sources']:
        if src.get('kind') == 'telegram':
            continue
        host = urllib.parse.urlparse(src['url']).netloc.replace('www.', '')
        if not host or '%' in host:
            continue
        row = out.setdefault(host, {'name': src['name'], 'deals_seen': 0, 'enabled': False})
        row['deals_seen'] += int(src.get('deals_seen') or 0)
        row['enabled'] = row['enabled'] or bool(src.get('enabled'))
    return out


BROWSER_UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
              '(KHTML, like Gecko) Chrome/124.0 Safari/537.36')


def fetch(url):
    """Сначала представляемся честно; сайт, который отказал боту (403/нет
    ответа), читаем как браузер — это чтение условий, а не сбор материалов,
    и без него проверка молчала бы ровно о тех, кто строже всех."""
    import httpx
    for ua in (UA, BROWSER_UA):
        try:
            r = httpx.get(url, headers={'User-Agent': ua}, timeout=TIMEOUT, follow_redirects=True)
            if r.status_code in (401, 403, 429) or r.status_code >= 500:
                continue
            return r.status_code, r.text
        except Exception:                                   # noqa: BLE001
            continue
    return 0, ''


def clean_text(html):
    text = TAGS_RE.sub(' ', TAG_RE.sub(' ', html))
    for a, b in (('&nbsp;', ' '), ('&laquo;', '«'), ('&raquo;', '»'), ('&mdash;', '—'),
                 ('&ndash;', '–'), ('&amp;', '&'), ('&quot;', '"')):
        text = text.replace(a, b)
    return re.sub(r'\s+', ' ', re.sub(r'&#\d+;', ' ', text)).strip()


# ---------- robots.txt: честный разбор по правилам REP ----------
def parse_groups(text):
    groups, agents, rules, in_agents = [], [], [], True
    for raw in text.splitlines():
        line = raw.split('#', 1)[0].strip()
        if ':' not in line:
            continue
        key, _, val = line.partition(':')
        key, val = key.strip().lower(), val.strip()
        if key == 'user-agent':
            if not in_agents:
                if agents:
                    groups.append((agents, rules))
                agents, rules = [], []
            agents.append(val.lower())
            in_agents = True
        elif key in ('disallow', 'allow'):
            rules.append((key, val))
            in_agents = False
    if agents:
        groups.append((agents, rules))
    return groups


def _pattern_rx(pattern):
    return '^' + ''.join('.*' if ch == '*' else r'\Z' if ch == '$' else re.escape(ch) for ch in pattern)


def can_fetch(groups, agent, path='/'):
    agent = agent.lower()
    star, best, best_len = None, None, -1
    for agents, rules in groups:
        if '*' in agents:
            star = rules
        if agent == '*':
            continue
        for a in agents:
            if a and a != '*' and (a in agent or agent in a) and len(a) > best_len:
                best, best_len = rules, len(a)
    rules = best if best is not None else star
    if rules is None:
        return True
    verdict = None
    for directive, pattern in rules:
        if not pattern:
            continue
        if re.match(_pattern_rx(pattern), path):
            score = len(pattern)
            if verdict is None or score > verdict[0] or (score == verdict[0] and directive == 'allow'):
                verdict = (score, directive == 'allow')
    return True if verdict is None else verdict[1]


def robots_verdict(host):
    code, text = fetch('https://%s/robots.txt' % host)
    if code == 0:
        return 'не проверить', ''
    if code != 200:
        return 'нет robots.txt' if code == 404 else 'блокирует запрос', ''
    if text.lstrip()[:1] == '<':
        return 'блокирует запрос', ''
    groups = parse_groups(text)
    if not can_fetch(groups, '*'):
        return 'запрещает всё', ''
    named = [b for b in AI_BOTS if not can_fetch(groups, b)]
    return ('запрещает ИИ-ботам поимённо', ', '.join(named)) if named else ('разрешено', '')


# ---------- пользовательское соглашение ----------
def legal_candidates(host, html):
    base = 'https://%s/' % host
    scored = {}
    for href, label in LINK_RE.findall(html or ''):
        text = (href + ' ' + clean_text(label)).lower()
        score = sum(1 for w in LEGAL_LINK_WORDS if w in text)
        if not score:
            continue
        url = urllib.parse.urljoin(base, href.strip())
        p = urllib.parse.urlparse(url)
        if p.scheme not in ('http', 'https') or p.netloc.replace('www.', '') != host:
            continue
        key = (p.netloc, p.path)
        scored[key] = max(scored.get(key, (0, url))[0], score), url
    ranked = sorted(scored.values(), key=lambda x: -x[0])
    return [u for _s, u in ranked[:MAX_LEGAL_PAGES]]


def prohibitions(text):
    out = []
    for sent in SENT_SPLIT.split(text):
        if len(sent) > 700:
            continue
        if AUTO.search(sent) and PROHIBIT.search(sent) and not NOISE.search(sent):
            out.append(sent.strip())
    return out


def check_host(host):
    rb, rb_note = robots_verdict(host)
    code, home = fetch('https://%s/' % host)
    found = []
    pages = legal_candidates(host, home) if code == 200 else []
    for s in prohibitions(clean_text(home)) if code == 200 else []:
        found.append({'url': 'https://%s/' % host, 'text': s})
    for url in pages:
        pc, page = fetch(url)
        if pc != 200:
            continue
        for s in prohibitions(clean_text(page)):
            found.append({'url': url, 'text': s})
    seen, uniq = set(), []
    for f in found:
        k = f['text'][:160]
        if k not in seen:
            seen.add(k)
            uniq.append(f)
    return {'robots': rb, 'robots_note': rb_note, 'homepage': 'ok' if code == 200 else ('нет ответа' if code == 0 else 'код %d' % code),
            'tos': uniq[:6], 'checked': date.today().isoformat()}


def run(hosts, workers=12):
    results = {}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for host, res in zip(hosts, ex.map(check_host, hosts)):
            results[host] = res
    # Соглашение издания действует на все его поддомены: у quote.rbc.ru своей
    # страницы с правилами нет, но правила РБК — те же. Наследуем находку
    # родительского домена, если у поддомена своей нет.
    for host, res in results.items():
        parent = '.'.join(host.split('.')[-2:])
        if parent != host and parent in results and not res['tos'] and results[parent]['tos']:
            res['tos'] = [dict(f, inherited_from=parent) for f in results[parent]['tos']]
    return results


def has_ban(res):
    return res.get('robots') == 'запрещает всё' or bool(res.get('tos'))


def diff_report(old, new, meta):
    """Отчёт для человека: что появилось, что исчезло, что есть сейчас."""
    appeared, gone = [], []
    for host, res in new.items():
        was = old.get(host) or {}
        if has_ban(res) and not has_ban(was):
            appeared.append(host)
        if has_ban(was) and not has_ban(res) and res.get('homepage') == 'ok':
            gone.append(host)
    lines = []
    banned = sorted((h for h, r in new.items() if has_ban(r)),
                    key=lambda h: -meta.get(h, {}).get('deals_seen', 0))
    enabled_banned = [h for h in banned if meta.get(h, {}).get('enabled')]
    lines.append('Проверили условия использования у %d источников.' % len(new))
    lines.append('Прямо запрещают автоматический сбор: %d, из них сейчас включены в приток: %d.'
                 % (len(banned), len(enabled_banned)))
    if appeared:
        lines.append('')
        lines.append('НОВЫЕ запреты (с прошлой проверки): %s' % ', '.join(appeared))
        for h in appeared:
            r = new[h]
            if r.get('robots') == 'запрещает всё':
                lines.append('  • %s — robots.txt закрыт для всех роботов' % h)
            for f in r.get('tos', [])[:2]:
                lines.append('  • %s — «%s» (%s)' % (h, f['text'][:220], f['url']))
    if gone:
        lines.append('')
        lines.append('Запрет снят: %s' % ', '.join(gone))
    if not appeared and not gone:
        lines.append('Новых запретов нет, снятых нет.')
    if enabled_banned:
        lines.append('')
        lines.append('Включённые источники с запретом (нужно решение): %s'
                     % ', '.join('%s (%d сделок)' % (h, meta[h]['deals_seen']) for h in enabled_banned))
    return '\n'.join(lines), appeared, gone


def send_to_console(text):
    sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
    sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
    sys.path.insert(0, ROOT)
    import console_topics                                  # noqa: E402
    import send_drafts                                     # noqa: E402
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
    chats = send_drafts.send_targets()
    if not token or not chats:
        print('Консоль не настроена — отчёт только на экране.')
        return False
    import httpx
    thread = console_topics.thread_id('info')
    with httpx.Client(timeout=20) as client:
        for chat in chats:
            send_drafts.send_one(client, token, chat, '📜 Условия использования источников\n\n' + text, None, thread)
    return True


def main(argv):
    write, console, force = '--write' in argv, '--console' in argv, '--force' in argv
    only = argv[argv.index('--host') + 1] if '--host' in argv else None
    meta = hosts_from_sources()
    old = json.load(open(STATE, encoding='utf-8')) if os.path.exists(STATE) else {'checked': '', 'hosts': {}}
    if only:
        res = check_host(only)
        print(json.dumps(res, ensure_ascii=False, indent=1))
        return 0
    last = old.get('checked') or ''
    if last and not force:
        days = (date.today() - date.fromisoformat(last)).days
        if days < EVERY_DAYS:
            print('Проверяли %s (%d дн. назад) — следующая через %d дн. Сразу — с ключом --force.'
                  % (last, days, EVERY_DAYS - days))
            return 0
    new = run(sorted(meta))
    report, appeared, gone = diff_report(old.get('hosts') or {}, new, meta)
    print(report)
    if write:
        json.dump({'checked': date.today().isoformat(), 'hosts': new},
                  open(STATE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('\nЗапомнено: %s' % STATE)
    if console and (appeared or gone or not (old.get('hosts'))):
        send_to_console(report)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
