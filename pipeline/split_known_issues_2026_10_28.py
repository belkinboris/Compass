# -*- coding: utf-8 -*-
"""Разрез KNOWN_ISSUES.md на папку known_issues/ по темам (28 октября 2026).

Владелец: «может нужно сделать систему файлов known issues, которые
открываются в разных ситуациях?» — да. Один файл на 587 записей никто не
открывает целиком, а по теме его открыть было нельзя. Теперь записи лежат
в known_issues/<тема>.md: у каждого документа подсистемы в docs/ есть своя
папка багов, которую открывают, когда чинят эту подсистему; поиск
`docs_budget.py --find` ищет по всем файлам папки. Записи переносятся
ДОСЛОВНО, порядок сохраняется, ничего не удаляется.

Тема записи выбирается по словам заголовка и тела (пути к файлам, имена
модулей, слова подсистемы); спорные уходят в тему «card» — это самая
широкая и ищется так же. Сухой прогон печатает распределение; --write
пишет файлы и заменяет KNOWN_ISSUES.md на оглавление.
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'KNOWN_ISSUES.md')
OUT = os.path.join(ROOT, 'known_issues')

TOPICS = {
    'intake': ('Приток: забор новостей, ворота, сырье, черновики, дубли',
               'чините pipeline/ingest/ (sweep, promote, draft, triage, fetch, дубли), разбираете, почему сделка пришла поздно или дважды'),
    'publication': ('Публикация и консоль: посты, канал, решения владельца, рутина публикации, отчеты',
                    'чините pipeline/publish/, send_drafts, approve, ship_decisions, ops_status, бота консоли'),
    'card': ('Карточка сделки: поля, чтение источника, приемка, факты, оценка',
             'собираете или чините карточку: стороны, сумма, статус, дата, отрасль, факты, review/accept/second_reading'),
    'text': ('Разбор текста: регулярные выражения, дословность цитат, имена, числа, кавычки',
             'пишете или чините правило разбора текста: регэксп, нормализация, проверка цитаты, границы имени'),
    'company': ('Профили компаний: ФНС, ИНН, ЕГРЮЛ, банки, санкции, слияние профилей',
                'создаете, переименовываете, сливаете профиль; чините ФНС, ИНН, банковскую отчетность'),
    'site': ('Сайт: экраны, телефон, ассистент, API, доступ, подписки, выкладка интерфейса',
             'правите static/index.html, main.py (экраны и API), проверяете экран в Playwright'),
    'ops': ('Инженерное: git, тесты, CI, выкладка, контейнеры, документы, токены',
            'падают тесты или сборка, конфликт в git, выкладка не доехала, правите документы'),
}
SIG = {
 'intake': [r'pipeline/ingest/(?:promote|draft|triage|fetch|sweep|raw_screen|resolve_duplicates|signals|enrich|merge)', r'\bворот', r'сырь', r'черновик', r'приток', r'забор новостей', r'дубл', r'triage', r'promote\.py', r'draft\.py', r'raw_', r'sweep'],
 'publication': [r'pipeline/publish', r'send_telegram', r'format_post', r'ship_decisions', r'approve\.py', r'ops_status', r'send_drafts', r'консол', r'модерац', r'\bпост', r'канал', r'telegram', r'рутин[аы] публикац', r'drop_pending', r'решени[ея] владельца', r'chat_id'],
 'card': [r'review\.py', r'accept_card', r'second_reading', r'facts', r'card_text', r'proofread', r'статус', r'заголов', r'продав', r'покупател', r'предмет', r'сумм', r'мультипликатор', r'eco\.|law\.', r'карточк', r'отрасл', r'консультант', r'дочит', r'второе чтение', r'price_estimate', r'analytics', r'audit'],
 'text': [r'регэксп|regex|регулярн', r'\\b', r'дословн', r'плейсхолдер', r'предложени', r'падеж', r'кавыч', r'сокращен', r'нормализ|normalize', r'\bre\.', r'\[А-Я', r'цитат', r'граница имени|границ[аы] слов', r'запят', r'заглавн', r'split'],
 'company': [r'fns|ФНС', r'ИНН', r'профил', r'companies', r'ЕГРЮЛ', r'\bбанк', r'санкц', r'company_profiles', r'link_parties', r'bank_finance', r'match_keys', r'псевдоним', r'переименован'],
 'site': [r'index\.html', r'main\.py', r'/api/', r'экран', r'телефон|iPhone|360|390', r'ассистент', r'витрин', r'кнопк', r'рендер', r'playwright', r'подписк', r'регистрац|вход|доступ', r'кабинет', r'seo_pages', r'scrape', r'css|z-index|overflow', r'app_settings', r'вкладк'],
 'ops': [r'\bgit\b', r'pytest', r'\bCI\b', r'release', r'выклад', r'контейнер', r'хук|hook', r'токен', r'ключ', r'docs_budget', r'CLAUDE\.md', r'KNOWN_ISSUES', r'бэклог', r'архив', r'документ', r'test_docs', r'roadmap', r'триггер', r'push', r'conftest'],
}
ORDER = ['site', 'company', 'intake', 'publication', 'ops', 'text', 'card']   # при равенстве — более частная тема


def classify(entry):
    title, body = entry.split('\n', 1)[0], entry
    scores = {}
    for t, rxs in SIG.items():
        scores[t] = sum(3 * len(re.findall(rx, title, re.I)) + len(re.findall(rx, body, re.I)) for rx in rxs)
    best = max(scores, key=lambda t: (scores[t], -ORDER.index(t)))
    return best if scores[best] > 0 else 'card'


HEAD = """# Известные ошибки: %s

%s.

**Когда открывать:** %s. Файл не читается целиком на каждом прогоне: его
открывают по теме или ищут по словам симптома —
`python3 pipeline/docs_budget.py --find "<слова>"` (ищет по всей папке и
архиву). Оглавление тем — `KNOWN_ISSUES.md`.

**Как писать:** сразу при первом обнаружении бага — симптом, причина одной
фразой, чем починено (файл, функция, тест). Одна запись под своим `##`,
не длиннее 12 тыс. знаков. Правило, которое нужно читать на шаге, уходит в
`docs/`; здесь остается история болезни.

---

"""

INDEX = """# Известные ошибки и их решения — оглавление

Справочник багов разрезан по темам (28 октября 2026): по одному файлу на
подсистему, чтобы его можно было открыть, когда чинишь именно ее, а не
только искать. Записи перенесены дословно, ничего не выброшено.

**Как читать — поиском или по теме.** `python3 pipeline/docs_budget.py
--find "<слова симптома>"` ищет по всем файлам папки и по архиву и
возвращает запись с адресом «файл:строка». Чините подсистему — откройте ее
файл: у каждого документа в `docs/` в шапке назван его файл багов.

| файл | о чем | когда открывать |
|---|---|---|
%s

**Когда сюда писать.** Сразу при первом обнаружении бага, не после повтора:
симптом, причина одной фразой, чем исправлено — в файл своей темы. Без
«кто нашел и когда», без отвергнутых гипотез. Потолка у файлов нет; потолок
у ОДНОЙ записи — 12 тыс. знаков (`test_docs.py`).
"""


def main(write=False):
    text = io.open(SRC, encoding='utf-8').read()
    parts = re.split(r'\n(?=## )', text)
    entries = parts[1:]
    assert len(entries) > 500, 'KNOWN_ISSUES.md уже разрезан?'
    buckets = {t: [] for t in TOPICS}
    for e in entries:
        buckets[classify(e)].append(e.rstrip('\n') + '\n')
    for t in TOPICS:
        print('%-12s %4d записей %7d знаков' % (t, len(buckets[t]), sum(len(x) for x in buckets[t])))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for t, (what, when) in TOPICS.items():
        path = os.path.join(OUT, t + '.md')
        io.open(path, 'w', encoding='utf-8').write(HEAD % (what, what, when) + '\n'.join(buckets[t]))
        rows.append('| `known_issues/%s.md` | %s | %s |' % (t, what, when))
    io.open(SRC, 'w', encoding='utf-8').write(INDEX % '\n'.join(rows))
    moved = sum(len(b) for b in buckets.values())
    print('Записано: %d записей в %d файлов; KNOWN_ISSUES.md — оглавление.' % (moved, len(TOPICS)))
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
