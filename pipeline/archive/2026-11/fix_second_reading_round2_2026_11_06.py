# -*- coding: utf-8 -*-
"""Второе чтение, круг 2 (6 ноября 2026), gcc6ff548 и g5b2cf7bd.

gcc6ff548: в «Оценке и цене» ценность участков подана фактом (у Коммерсанта «могут представлять»);
«История и окружение» повторяла строку «Предмет» (квоты на пять рек) и описывала группу RBE.
g5b2cf7bd: в посте и на «Обзоре» не было сказано, кто такие «Цифровые привычки» — добавлено в
«Историю и окружение» и в описание профиля; описание Umbrella IT в посте укорочено.
Поля в pending.json правятся здесь (снятие имен и чисел proofread.py не принимает), записи
fixes/written_2026_11_05_vm.py подогнаны под новый текст, иначе review.py откажет «поле уже другое».

Запуск: python3 pipeline/archive/2026-11/fix_second_reading_round2_2026_11_06.py [--write]
"""
import importlib.util
import json
import os
import pprint
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
WRITTEN = os.path.join(ROOT, 'pipeline', 'ingest', 'fixes', 'written_2026_11_05_vm.py')

A_VAL = ('Цену стороны не назвали. Инвестконсультант Иван Пешков полагает, что при таких финансовых '
         'показателях компания вряд ли стоит больше нескольких миллионов рублей. Он допускает, что '
         'ценными могут оказаться закрепленные участки для рыбалки и инфраструктура, но назвать их цену затруднился.')
A_CTX = ('«Сильвер Салмон» зарегистрирована в Петропавловске-Камчатском, ее виды деятельности — туризм и '
         'рыбный промысел.\n\nПоследние несколько лет группа RBE активно вкладывается в пищевые активы: '
         'Балаковский молочный комбинат в Саратовской области, торговля зерном в ДНР, предприятие по '
         'выпуску рационов и пайков.')
C_LEAD = ('«Цифровые привычки» — российская группа: пишет свое программное обеспечение и берется за '
          'разработку на заказ для крупных корпоративных клиентов. ')


def main(write):
    pend = json.load(open(PENDING, encoding='utf-8'))
    cards = {c['id']: c for c in pend['cards']}
    a, c = cards['gcc6ff548']['eco'], cards['g5b2cf7bd']['eco']
    old_c = c['context']
    if old_c.startswith('«Цифровые привычки» —'):
        old_c = old_c[old_c.index('Umbrella IT работает'):]       # лид правился: круг 2, повторный запуск
    new_c = C_LEAD + old_c
    changes = {('gcc6ff548', 'eco.val'): A_VAL, ('gcc6ff548', 'eco.context'): A_CTX,
               ('g5b2cf7bd', 'eco.context'): new_c}
    a['val'], a['context'], c['context'] = A_VAL, A_CTX, new_c
    spec = importlib.util.spec_from_file_location('w', WRITTEN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for fx in mod.FIXES:
        key = (fx['id'], fx['field'])
        if key in changes:
            fx['new'] = changes[key]
            print('written:', key)
    base = json.load(open(BASE, encoding='utf-8'))
    comps = base['companies']
    comps['g6017899e']['desc'] = ('Российская группа компаний по разработке программного обеспечения. Делает собственные '
                                  'продукты и заказную разработку для крупных корпоративных заказчиков. '
                                  'Юрлицо — АО «Цифровые привычки».')
    comps['g578eec68']['desc'] = ('Разработчик корпоративных информационных систем и приложений. Оказывает услуги '
                                  'ИТ-консалтинга; работает 17 лет, более 500 специалистов. Юрлицо — ООО «Амбрелла Альянс».')
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    json.dump(pend, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    head = open(WRITTEN, encoding='utf-8').read().split('FIXES = ')[0]
    open(WRITTEN, 'w', encoding='utf-8').write(head + 'FIXES = ' + pprint.pformat(mod.FIXES, width=100, sort_dicts=False) + '\n')
    raw = open(BASE, encoding='utf-8').read()
    out = json.dumps(base, ensure_ascii=False, indent=1)
    open(BASE, 'w', encoding='utf-8').write(out + ('\n' if raw.endswith('\n') else ''))
    print('записано')


if __name__ == '__main__':
    main('--write' in sys.argv)
