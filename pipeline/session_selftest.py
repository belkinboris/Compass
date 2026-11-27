# -*- coding: utf-8 -*-
"""Самопроверка среды рутины в НОВОЙ сессии: все ли есть, чтобы работать и отправить работу.

ЗАЧЕМ (27 ноября 2026). Рутины переводятся с постоянных сессий на новую сессию на каждый
запуск (постоянные переполняются: качество — 514 тыс. токенов, приток встал на сутки).
Новая сессия отличается тремя вещами, и каждая уже ломала прогон: (1) репозиторий
клонируется ПОСЛЕ старта, поэтому хук `.claude/hooks/session-start.sh` сам не срабатывает —
нет pytest/httpx, сломан Pillow; (2) папок `data/inbox/raw|triage` (тексты статей) нет —
проверка цитат слепа, пока статью не скачали; (3) права записи в репозиторий может не быть.
Владелец: «то репозиторий не встает, то что-то забывается» — проверяем это скриптом, а не
на живом прогоне.

    python3 pipeline/session_selftest.py            # печать и код возврата (0 — все есть)
    python3 pipeline/session_selftest.py --json F   # еще и отчет в файл

Рутина в новой сессии начинает так: clone/pull → `CLAUDE_CODE_REMOTE=true bash
.claude/hooks/session-start.sh` → этот скрипт. Красная строка — чинить или PushNotification.
"""
import importlib
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run(cmd, timeout=120):
    try:
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr).strip()[-300:]
    except Exception as e:                                   # noqa: BLE001
        return 1, repr(e)[:300]


def checks():
    out = []

    def add(name, ok, note=''):
        out.append({'check': name, 'ok': bool(ok), 'note': str(note)[:300]})
    for mod in ('httpx', 'pytest', 'playwright', 'PIL.Image', 'pymorphy3', 'fastapi'):
        try:
            importlib.import_module(mod)
            add('import ' + mod, True)
        except Exception as e:                               # noqa: BLE001
            add('import ' + mod, False, repr(e))
    add('браузер /opt/pw-browsers/chromium', os.path.exists('/opt/pw-browsers/chromium'))
    for var in ('TELEGRAM_BOT_TOKEN', 'API_FNS_KEY'):
        add('переменная %s задана' % var, bool(os.environ.get(var)), 'значение не печатается')
    code, txt = _run(['git', 'config', 'core.hooksPath'])
    add('git-хук перед push подключен (.githooks)', code == 0 and '.githooks' in txt, txt)
    code, txt = _run(['git', 'fetch', 'origin', 'main'])
    add('git fetch origin main', code == 0, txt)
    code, txt = _run(['git', 'push', '--dry-run', '--no-verify', 'origin', 'HEAD:main'])
    add('право записи в репозиторий (push --dry-run)', code == 0, txt)
    code, txt = _run([sys.executable, 'pipeline/reading_due.py'])
    add('очередь проверок по срокам считается', code == 0, txt)
    code, txt = _run([sys.executable, '-m', 'pytest', 'test_data.py', '-q', '-x', '-p', 'no:cacheprovider'], 600)
    add('pytest test_data.py', code == 0, txt)
    raw = os.path.join(ROOT, 'data', 'inbox', 'raw')
    n = len(os.listdir(raw)) if os.path.isdir(raw) else 0
    add('тексты статей на диске (data/inbox/raw)', True,
        '%d файлов; 0 — норма для новой сессии: статьи карточки скачать '
        '`python3 pipeline/ingest/fetch_article_texts.py <id …> --write` до проверки цитат' % n)
    try:
        import urllib.request
        urllib.request.urlopen('https://projectcompass.ru/health', timeout=30).read(50)
        add('сеть: сайт отвечает', True)
    except Exception as e:                                   # noqa: BLE001
        add('сеть: сайт отвечает', False, repr(e))
    return out


def main(argv):
    rows = checks()
    for r in rows:
        print('%s %s%s' % ('ok ' if r['ok'] else 'НЕТ', r['check'], (' — ' + r['note']) if r['note'] else ''))
    if '--json' in argv:
        path = argv[argv.index('--json') + 1]
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        json.dump(rows, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    sys.exit(0 if all(r['ok'] for r in rows) else 1)


if __name__ == '__main__':
    main(sys.argv[1:])
