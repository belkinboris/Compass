# -*- coding: utf-8 -*-
"""Шерегеш (g03475792), 3 ноября 2026, замечание партнера: «Как устроена сделка»
рассказывало о нашем поиске («найти сведения о покупателе не удалось»), а не о
сделке; то же в описании покупателя. Финансы из «Контекста» — дубль «Финансов».

    python3 pipeline/archive/2026-11/fix_sheregesh_struct_2026_11_03.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def main(argv):
    raw = open(BASE, encoding='utf-8').read()
    data = json.loads(raw)
    c = [d for d in data['deals'] if d['id'] == 'g03475792'][0]
    assert c['law']['struct'].startswith('По данным «Контур.Фокуса», контроль перешел')
    c['law']['struct'] = ('1 июля 2026 года все 100% долей ООО «Каскад восток» перешли от Татьяны Прокудиной '
                          'к компании из ОАЭ — это видно по истории участников в ЕГРЮЛ. Цена и условия '
                          'сделки не раскрывались.')
    ctx = c['eco']['context']
    tail = (' По данным «Контур.Фокуса», выручка компании за прошлый год — 1,1 млрд ₽, чистый убыток — '
            '52,4 млн ₽; по отчетности компания убыточна с конца 2023 года.')
    assert tail in ctx
    c['eco']['context'] = ctx.replace(tail, ' По отчетности компания убыточна с конца 2023 года.')
    b = data['companies'][c['buyer']]
    assert 'источник не нашел' in b['desc']
    b['desc'] = ('Компания, зарегистрированная в ОАЭ. В 2026 году получила 100% ООО «Каскад восток» — '
                 'оператора подъемников Шерегеша.')
    print('struct, context, описание покупателя')
    if '--write' not in argv:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    assert open(BASE, encoding='utf-8').read() == raw
    open(BASE, 'w', encoding='utf-8').write(json.dumps(data, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))
    print('записано')


if __name__ == '__main__':
    main(sys.argv[1:])
