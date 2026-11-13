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


def main():
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
