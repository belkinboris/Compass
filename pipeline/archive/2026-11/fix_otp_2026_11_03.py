# -*- coding: utf-8 -*-
"""OTP Group / ОТП Банк (gd937c845), 3 ноября 2026 — по замечаниям партнера.

- law.struct и eco.val были общей справкой о правилах выхода иностранцев
  (постановление №295, дисконт 60%), а не описанием этой сделки — Артем:
  «Это неправильно». Теперь — что известно о самой продаже.
- Этап «Продажа не состоялась» (3 ноября, РБК: гендиректор Петер Чани —
  покупателя, одобренного Москвой и с приемлемой ценой, банк не нашел) уже
  записан; статус карточки оставался «Обсуждается» → «Не состоялась».
- Заголовок карточки «рассматривает продажу» устарел — своей фразой.
- Заголовок вехи был заголовком РБК дословно; владелец переписал пост
  сам — берем его формулировку.

    python3 pipeline/archive/2026-11/fix_otp_2026_11_03.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def main(argv):
    raw = open(BASE, encoding='utf-8').read()
    data = json.loads(raw)
    c = [d for d in data['deals'] if d['id'] == 'gd937c845'][0]
    assert c['law']['struct'].startswith('Покупатель российского бизнеса не определен.'), c['law']['struct']
    assert c['eco']['val'].startswith('Продажа бизнеса в России регулируется постановлением'), c['eco']['val']
    assert c['status'] == 'Обсуждается', c['status']
    assert c['title'] == 'OTP Group рассматривает продажу российской «дочки» на фоне покупки Luminor'
    ev = [e for e in c['events'] if e.get('kind') == 'cancelled'][0]
    assert ev['headline'] == 'Крупнейший банк Венгрии не смог продать российскую «дочку»'
    c['law']['struct'] = ('OTP Group искала покупателя на свой российский банк — АО «ОТП Банк». Покупатель '
                          'должен был получить одобрение российских властей и предложить цену, устраивающую '
                          'группу. Такого покупателя группа не нашла, сказал в ноябре 2026 года ее гендиректор '
                          'Петер Чани.')
    c['eco']['val'] = '—'
    c['status'] = 'Не состоялась'
    c['title'] = 'OTP Group не нашла покупателя на российский ОТП Банк'
    ev['headline'] = 'Крупнейший банк Венгрии OTP Group не смог продать свое российское дочернее общество'
    print('gd937c845: struct, eco.val, статус, заголовок, заголовок вехи')
    if '--write' not in argv:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    assert open(BASE, encoding='utf-8').read() == raw, 'база изменилась во время прогона — перезапустите'
    open(BASE, 'w', encoding='utf-8').write(json.dumps(data, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))
    print('записано')


if __name__ == '__main__':
    main(sys.argv[1:])
