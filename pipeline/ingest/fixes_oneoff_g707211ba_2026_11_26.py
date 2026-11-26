# -*- coding: utf-8 -*-
"""Разовая правка, 26 ноября 2026 (приток): карточка g707211ba (ЛУКОЙЛ / консорциум
Тодда Боэли). enrich.py по статье «Коммерсанта» https://www.kommersant.ru/doc/9130738
дописал этап «Переговоры» от 25 ноября ПОСЛЕ уже стоящего «Документы подписаны»:
статья рассказывает о том же подписанном соглашении. Этап не удаляется (дедуп
enrich ищет «уже видели» по (вид, адрес) — удаленный вернется через час), а
переписывается: что это подробности подписанного соглашения, своими словами.
Без ключа — сухой прогон, запись — --write.
"""
import json, sys, os
BASE = os.path.join(os.path.dirname(__file__), '..', '..', 'static', 'data', 'deals_promoted.json')
URL = 'https://www.kommersant.ru/doc/9130738'

def main():
    base = json.load(open(BASE, encoding='utf-8'))          # перечитываем прямо перед записью
    deal = next(d for d in base['deals'] if d['id'] == 'g707211ba')
    assert deal['status'] == 'Подписана', deal['status']
    ev = [e for e in deal['events'] if e.get('kind') == 'negotiations' and (e.get('source') or [0, 0])[1] == URL]
    assert len(ev) == 1, len(ev)
    e = ev[0]
    assert e['title'] == 'Переговоры' and e['note'].startswith('Подпавший более года назад'), e
    e['title'] = 'Подробности подписанного соглашения'
    e['note'] = ('«Коммерсантъ» рассказал подробности уже подписанного соглашения: зарубежный бизнес '
                 'ЛУКОЙЛа покупает консорциум во главе с Eldridge Тодда Боэли.')
    print('g707211ba events: этап «Переговоры» 2026-11-25 переписан ->', e['title'])
    if '--write' in sys.argv:
        with open(BASE, 'w', encoding='utf-8') as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
        print('Записано.')
    else:
        print('Сухой прогон.')

if __name__ == '__main__':
    main()
