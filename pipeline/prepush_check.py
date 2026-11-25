# -*- coding: utf-8 -*-
"""Быстрая проверка перед push для всех, кто правит базу: тесты, которые читают данные.

ЗАЧЕМ. 11 ноября 2026 публикация дважды за день встала на красном тесте: вычитка
пушила, прогнав только `test_data.py`, а данные ломали чужие тесты — золотую
выборку аналитики (Sokolov) и поиск ассистента (заголовок без «кофеен»). Публикация
гоняет полный pytest и не выпускает посты, пока main красный; владелец узнал об
этом, спросив «а где вообще посты». Владелец: «если что-то ломается — сразу чини,
а то все встает».

ЧТО ГОНЯЕТ. Все наборы, которые читают `deals_promoted.json` и идут меньше минуты:
полный прогон занимает около двух минут. Не входят `test_ui.py` (браузер),
`test_kompas.py` и `test_launch_features.py` (сервер): их ломает код, а не данные,
и их гоняет тот, кто правит код.

Из `test_ingest.py` (весь — 1 мин 45 с) с 13 ноября 2026 входят тесты, которые
читают базу, таблицу правок или очередь (`ingest_data_tests`, около 100 тестов,
55 с). Вычитка 12–13 ноября оставила main красным на трех таких тестах — покрытие
правила отрасли, вторая запись правки на поле, карточка без приемки, — и
prepush их не видел: данные ломали тест притока, а не тест базы.

    python3 pipeline/prepush_check.py          # 0 — можно пушить, 1 — красное, не пушить
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SUITES = ['test_data.py', 'test_gold_analytics.py', 'test_assistant_retrieval.py', 'test_assistant_policy.py',
          'test_facts.py', 'test_docs.py', 'test_data_refresh.py', 'test_audit_queue.py', 'test_price_estimate.py',
          'test_proofread.py', 'test_sanctions.py', 'test_scraping.py']


# Признаки теста, который читает данные: фикстура `base` или прямое чтение базы,
# таблицы правок, очереди. Новый такой тест попадает в prepush сам.
DATA_MARKS = ('deals_promoted', 'review.FIXES', 'pending.json')


def ingest_data_tests(path=None):
    """Адреса тестов `test_ingest.py`, которые читают данные (см. DATA_MARKS)."""
    import ast
    path = path or os.path.join(ROOT, 'test_ingest.py')
    if not os.path.exists(path):
        return []
    src = open(path, encoding='utf-8').read()
    out = []
    for node in ast.parse(src).body:
        if not (isinstance(node, ast.FunctionDef) and node.name.startswith('test_')):
            continue
        body = ast.get_source_segment(src, node) or ''
        if 'base' in [a.arg for a in node.args.args] or any(m in body for m in DATA_MARKS):
            out.append('%s::%s' % (os.path.basename(path), node.name))
    return out


def lost_post_marks(old, new):
    """Отметки о постах, которые были в origin/main и пропали, хотя сделка в базе
    осталась. 23 ноября 2026 коммит притока записал `telegram_posts` из 221 записи
    вместо 1814 — стер 1593 отметки «пост не нужен»; через два дня владельцу пришли
    проектами постов давно вышедшие «Астра ИИ» и «Арнест» («что это и откуда»).
    git такую запись видит как обычную правку файла. Этап: ключ `<id сделки>-<вид>`."""
    ids = {d.get('id') for d in new.get('deals') or []}
    lost = []
    for key in ('telegram_posts', 'telegram_posts_realty', 'telegram_milestones'):
        o, n = old.get(key) or {}, new.get(key) or {}
        if not (isinstance(o, dict) and isinstance(n, dict)):
            continue
        gone = [k for k in o if k not in n
                and (k in ids or (key == 'telegram_milestones' and k.rsplit('-', 1)[0] in ids))]
        if gone:
            lost.append('%s: %d (%s)' % (key, len(gone), ', '.join(gone[:5])))
    return lost


def _lost_post_marks_against_main():
    import json
    try:
        raw = subprocess.run(['git', 'show', 'origin/main:static/data/deals_promoted.json'], cwd=ROOT,
                             capture_output=True, text=True, timeout=120).stdout
        old = json.loads(raw)
        new = json.load(open(os.path.join(ROOT, 'static', 'data', 'deals_promoted.json'), encoding='utf-8'))
    except Exception as e:                                   # noqa: BLE001 — не прочитали: тесты ниже скажут свое
        print('Отметки о постах не сверены (%s).' % e)
        return []
    return lost_post_marks(old, new)


def main():
    lost = [] if os.environ.get('POST_MARKS_OK') else _lost_post_marks_against_main()
    if lost:
        print('НЕ ПУШИТЬ: пропали отметки о постах у сделок, которые остались в базе — %s. '
              'Так стирается «пост уже вышел / не нужен», и старые сделки приходят владельцу новыми постами. '
              'Перечитайте базу перед записью; отметка снята намеренно — POST_MARKS_OK=1.' % '; '.join(lost))
        return 1
    # ПРАВКА ФАКТА БЕЗ ПОДТВЕРЖДАЮЩЕЙ ЦИТАТЫ НЕ УХОДИТ В MAIN (19 ноября 2026). Раньше
    # `fact_edit_guard` звали только те скрипты, что сами о нем помнили; теперь его проходит
    # каждый пуш базы: что изменилось в фактах против origin/main — у всего есть цитата,
    # а у суммы цитата несет само число.
    g = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fact_edit_guard.py'),
                        '--base', 'origin/main'], capture_output=True, text=True)
    if g.returncode:
        print((g.stdout + g.stderr).strip()[-1500:])
        print('НЕ ПУШИТЬ: правка факта без подтверждающей цитаты.')
        return 1
    # МАССОВАЯ ПРАВКА — ТОЖЕ ЗДЕСЬ (20 ноября 2026, владелец: «убедись, что проверка
    # качества, вычитка, все проверки ничего не ломают и проходят все проверки перед
    # внесением изменений»). Раньше `mass_edit_guard` звали только скрипты, которые о
    # нем помнили. Ключ одобренной пробы — переменная MASS_OK, как у review.py.
    me = [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mass_edit_guard.py'),
          '--base', 'origin/main'] + (['--mass-ok', os.environ['MASS_OK']] if os.environ.get('MASS_OK') else [])
    g = subprocess.run(me, capture_output=True, text=True)
    if g.returncode:
        print((g.stdout + g.stderr).strip()[-1500:])
        print('НЕ ПУШИТЬ: массовая правка опубликованных карточек без одобренной пробы.')
        return 1
    suites = [s for s in SUITES if os.path.exists(os.path.join(ROOT, s))] + ingest_data_tests()
    r = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', *suites],
                       cwd=ROOT, capture_output=True, text=True)
    tail = (r.stdout or '').strip().splitlines()
    failed = [l for l in tail if l.startswith('FAILED') or l.startswith('ERROR')]
    for l in failed[:20]:
        print(l)
    print(tail[-1] if tail else r.stderr[-500:])
    if r.returncode:
        print('КРАСНОЕ: не пушить. Публикация не выпустит посты, пока main красный — '
              'почините сейчас (данные или тест), а не оставляйте следующему прогону.')
        return 1
    print('Можно пушить.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
