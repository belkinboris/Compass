# -*- coding: utf-8 -*-
"""Хвост круга 3 вычитки: law.struct у g7632fe9f (Skillbox/Grafika).

После перевода карточки в «Закрыта» Playwright-проверка «запрещённых слов»
нашла на экране остаток будущего времени: law.struct нёс цитату 2022 года
«…до конца 2022 года купит 10%…» — время спорит со статусом, а по
содержанию поле дублирует предмет (10%, юрлицо — теперь в eco.share) и
extra. Единственный уникальный факт («Skillbox входит в VK вместе с
GeekBrains») переезжает в контекст; поле снимается. Тот же класс, что
«одно поле — одна линза».

Запуск: python3 pipeline/fix_skillbox_struct_tense.py [--write]
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
OLD = ('Образовательная платформа Skillbox (входит в VK вместе с GeekBrains) '
       'до конца 2022 года купит 10% в сети школ рисования для взрослых и '
       'детей Grafika (ООО «Творческое образование»), рассказали «Ъ» в '
       'компаниях.')
ADD = 'Skillbox входит в VK вместе с GeekBrains.'

def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    d = {x['id']: x for x in data['deals']}['g7632fe9f']
    assert d['law'].get('struct') == OLD, 'law.struct уже другое: %r' % d['law'].get('struct')[:60]
    print('g7632fe9f: law.struct снимается (дубль в устаревшем времени), '
          'факт про VK -> eco.context')
    if '--write' not in argv:
        print('Сухой прогон. Запись — с ключом --write.'); return 0
    d['law'].pop('struct')
    d['eco']['context'] = d['eco']['context'].rstrip() + ' ' + ADD
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.'); return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
