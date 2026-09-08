# -*- coding: utf-8 -*-
"""Куда пушить этот коммит: только в `main`, или ещё и в `release`.

ЗАЧЕМ. Ветка `release` — единственный вход в СБОРКУ приложения на Timeweb:
каждый пуш туда пересобирает контейнер и перезапускает процесс. Данные на
сайт едут иначе — сами, из `main`, по расписанию (`data_refresh.py`). Значит,
пуш в `release` оправдан ровно тогда, когда изменился код, который ВЫПОЛНЯЕТ
боевой процесс, либо статика, которую он отдаёт.

ПОЧЕМУ ЭТО СКРИПТ, А НЕ ПРАВИЛО В ГОЛОВЕ. 7 сентября 2026 владелец заметил в
панели деплой коммита «Карточка «Базис»/Proto пересобрана» и спросил: зачем
для этого сборка, мы же такие правки возим через `main`? Он прав: в том
коммите были данные, скрипт пайплайна и тест — ни строчки того, что запускает
сайт. Лишняя сборка стоила перезапуска процесса на живом сайте, и это ровно
то, ради чего ветки и разводили в ночь на 3 сентября. Различить «код сайта» и
«код рутин» на глаз легко только пока помнишь список — поэтому список лежит
здесь, а не в памяти.

Запуск:
    python3 pipeline/where_to_push.py            # по незапушенным коммитам ветки
    python3 pipeline/where_to_push.py HEAD~3     # начиная с этой ревизии
"""
import subprocess
import sys

# Что реально исполняет или отдаёт боевой процесс. Всё остальное (pipeline/,
# tests, документация, data) на сайте не выполняется — только читается как
# данные, а данные приезжают из `main` сами.
#
# ИСКЛЮЧЕНИЕ, найденное 8 сентября 2026: `pipeline/fns_registry.py` и
# `pipeline/sync_fns.py` формально лежат в `pipeline/`, но `main.py` их
# ИМПОРТИРУЕТ («from pipeline.fns_registry import by_company_id», «from
# pipeline.sync_fns import sync_from_registry») — а любой модуль, загруженный
# в память процесса, отражает файл на диске на момент СБОРКИ, а не на момент
# git-пуша, ровно как и весь остальной код сайта. Правка REGISTRY (новая
# подтверждённая запись ИНН) простояла бы в `main` до следующей пересборки
# `release` по ДРУГОЙ причине — незаметно и без всякого предупреждения,
# потому что комментарий выше («всё остальное в pipeline/ — только данные»)
# для этих двух файлов неверен. Тот же класс дефекта, что и «правило,
# написанное для начала строки, не увидит того же дефекта в конце»: список
# ниже перечислял ФАЙЛЫ по расположению (корень репозитория), а не по тому,
# импортирует ли их процесс, — два файла из pipeline/ прошли мимо.
APP_FILES = {
    'main.py', 'facts.py', 'deal_multiples.py', 'deal_catalog.py', 'deal_export.py',
    'data_refresh.py', 'assistant_retrieval.py', 'yandex_search.py', 'fns_client.py',
    'cbr_client.py', 'notification_service.py', 'subscription_feed.py',
    'telegram_endpoint.py', 'requirements.txt', 'Procfile', 'runtime.txt',
    'pipeline/fns_registry.py', 'pipeline/sync_fns.py',
}
APP_DIRS = ('static/', 'db/')
# Данные внутри static/ сайт подтягивает сам из `main` — сборка им не нужна.
DATA_FILES = ('static/data/',)


def branches_for(paths):
    app = sorted(p for p in paths
                 if (p in APP_FILES or p.startswith(APP_DIRS))
                 and not p.startswith(DATA_FILES))
    return app


def main(since=None):
    if since:
        rng = f'{since}..HEAD'
    else:
        rng = 'origin/release..HEAD'
    paths = subprocess.run(['git', 'diff', '--name-only', rng],
                           capture_output=True, text=True).stdout.split()
    if not paths:
        print(f'В диапазоне {rng} изменений нет.')
        return 0
    app = branches_for(paths)
    print(f'Изменено файлов: {len(paths)} ({rng})')
    if app:
        print('Пушить в main И в release — сборку требуют:')
        for p in app:
            print('   ', p)
    else:
        print('Пушить ТОЛЬКО в main: сайт ничего из этого не выполняет,')
        print('данные он подтянет сам в течение DATA_REFRESH_MINUTES.')
        for p in paths[:12]:
            print('   ', p)
        if len(paths) > 12:
            print(f'    … и ещё {len(paths) - 12}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
