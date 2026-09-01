# -*- coding: utf-8 -*-
"""Дописать тему «Создание СП» карточкам, которые её заслуживают, — и ТОЛЬКО её.

Почему так, а не перезапуск tag_themes.py --write: замечание партнёра
31 августа 2026 («Неужели создания СП реально 2?») показало, что тема
считалась только по структурному признаку kind == 'jv' (4 карточки).
Правило в tag_themes.py расширено текстом (см. комментарий там), но сухой
прогон всего теггера дал 230 изменений по ВСЕМ темам: поле themes в базе
давно живёт отдельно от текущих правил (его правили и другие скрипты, и
чтение), и перезапись целиком снесла бы ручные решения. Поэтому берём из
теггера только дельту по одной теме, а три ложных срабатывания расширенного
правила исключаем поимённо: опцион на выкуп доли в AliExpress Russia (СП уже
существовало), консолидация авиаактивов «Ростеха» внутри одной группы (не
совместное предприятие), покупка «Эталоном» 65% в уже созданном СП.

Запуск:
    python3 pipeline/add_jv_theme_batch.py          # сухой прогон
    python3 pipeline/add_jv_theme_batch.py --write  # записать
"""
import json
import sys

sys.path.insert(0, 'pipeline')
import tag_themes as tt  # noqa: E402

PATH = 'static/data/deals_promoted.json'
THEME = 'Создание СП'
EXCLUDE = {'g7e1b9b0c', 'gmru-rostech-avia-holding', 'g24b33459'}


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}
    for did in EXCLUDE:
        assert did in by_id, did
    added = []
    for d in data['deals']:
        if d['id'] in EXCLUDE:
            continue
        have = d.get('themes') or []
        if THEME in tt.themes_of(d) and THEME not in have:
            d['themes'] = have + [THEME]
            added.append((d['id'], d['title'][:90]))
    for a in added:
        print(' +', *a)
    print(f'добавлено: {len(added)}; всего с темой: '
          f'{sum(1 for d in data["deals"] if THEME in (d.get("themes") or []))}')
    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print('ЗАПИСАНО в', PATH)


if __name__ == '__main__':
    main(write='--write' in sys.argv)
