# -*- coding: utf-8 -*-
"""G3 (1 ноября 2026): 129 заголовков переписаны под единый стиль. Снимок поста
(`telegram_post_state[id].title`) обновляется до нового заголовка, чтобы
публикация НЕ переписывала старые посты в канале из-за смены стиля: правка
поста по заголовку задумана для свежего поста с плохим заголовком (Baggins
Coffee, 29 октября), а не для массовой чистки; старые посты владелец мог
править руками до того, как сайт стал это помнить (21 октября). Без ключа —
сухой прогон, запись по --write.
"""
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BATCH = os.path.join(ROOT, 'pipeline', 'ingest', 'fixes', 'written_titles_g3_2026_11_01.py')


def main(write):
    spec = importlib.util.spec_from_file_location('g3', BATCH)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    new_titles = {f['id']: f['new'] for f in m.FIXES if f['field'] == 'title'}
    data = json.load(open(DATA, encoding='utf-8'))
    state = data.get('telegram_post_state') or {}
    titles = {d['id']: d.get('title') for d in data['deals']}
    todo = [i for i in new_titles if i in state and state[i].get('title') != titles.get(i)]
    for i in todo:
        print('  %s: снимок поста «%s» -> «%s»' % (i, str(state[i].get('title'))[:50], str(titles[i])[:50]))
    print('Снимков обновить: %d из %d переписанных.' % (len(todo), len(new_titles)))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    data = json.load(open(DATA, encoding='utf-8'))
    state = data['telegram_post_state']
    for i in todo:
        assert state[i].get('title') != titles[i]
        state[i]['title'] = titles[i]
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
