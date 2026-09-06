#!/bin/bash
# Зависимости проекта в одноразовом контейнере сессии.
#
# ЗАЧЕМ. Рутины притока и публикации живут в контейнере, который поднимается
# пустым: 6 августа там не оказалось ни httpx, ни pytest. Отсюда два молчаливых
# отказа. Первый: все четыре телеграм-скрипта (send_drafts, approve,
# send_telegram, setup_telegram_webhook) импортируют httpx — без него шаг
# падает на ModuleNotFoundError, и черновики не доходят до основателей. Второй
# опаснее: обязательная проверка перед коммитом «python3 -m pytest -q» отвечала
# «No module named pytest», то есть зелёного прогона не было НИ РАЗУ, а рутина
# всё равно коммитила. Приток при этом работал и создавал видимость нормы:
# fetch ходит в сеть на urllib и в httpx не нуждается.
#
# Тестовые пакеты ставятся отдельной строкой: requirements.txt — список для
# боевого хоста (Timeweb), pytest и playwright там не нужны. Разделение ровно
# то же, что в .github/workflows/tests.yml.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-.}"
python3 -m pip install --quiet --disable-pip-version-check -r requirements.txt
python3 -m pip install --quiet --disable-pip-version-check pytest playwright
# pymorphy3 — нормализация падежа предмета сделки (pipeline/ingest/casing.py):
# нужна только конвейеру притока, на боевом хосте её никто не импортирует.
python3 -m pip install --quiet --disable-pip-version-check pymorphy3 pymorphy3-dicts-ru

# Браузер предустановлен (PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers), и ставить
# его правилами репозитория запрещено — здесь только питоновский пакет.

# cffi — без него в контейнере сессии не импортируется cryptography, а с ней
# и pdfminer: приёмка (pipeline/acceptance_check.py) не могла прочитать текст
# скачанного PDF — импорт падал паникой pyo3, а не обычным исключением
# (6 сентября 2026). pdfminer стоит в образе, не хватало только cffi.
python3 -m pip install --quiet --disable-pip-version-check cffi
