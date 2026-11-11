# -*- coding: utf-8 -*-
"""Быстрая проверка перед push для всех, кто правит базу: тесты, которые читают данные.

ЗАЧЕМ. 11 ноября 2026 публикация дважды за день встала на красном тесте: вычитка
пушила, прогнав только `test_data.py`, а данные ломали чужие тесты — золотую
выборку аналитики (Sokolov) и поиск ассистента (заголовок без «кофеен»). Публикация
гоняет полный pytest и не выпускает посты, пока main красный; владелец узнал об
этом, спросив «а где вообще посты». Владелец: «если что-то ломается — сразу чини,
а то все встает».

ЧТО ГОНЯЕТ. Все наборы, которые читают `deals_promoted.json` и идут меньше минуты:
полный прогон занимает около двух минут. Не входят `test_ingest.py` (6 минут, код
притока), `test_ui.py` (браузер), `test_kompas.py` и `test_launch_features.py`
(сервер): их ломает код, а не данные, и их гоняет тот, кто правит код.

    python3 pipeline/prepush_check.py          # 0 — можно пушить, 1 — красное, не пушить
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SUITES = ['test_data.py', 'test_gold_analytics.py', 'test_assistant_retrieval.py', 'test_assistant_policy.py',
          'test_facts.py', 'test_docs.py', 'test_data_refresh.py', 'test_audit_queue.py', 'test_price_estimate.py',
          'test_proofread.py', 'test_sanctions.py', 'test_scraping.py']


def main():
    suites = [s for s in SUITES if os.path.exists(os.path.join(ROOT, s))]
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
