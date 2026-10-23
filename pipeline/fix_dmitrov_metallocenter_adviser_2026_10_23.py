"""«Северсталь»/«Дмитровский металлоцентр» (g0b187624) — консультант продавца АЛРУД, 23 октября 2026.

Владелец прислал пост t.me/LawFirms/11566 (23.10.2026): «АЛРУД сообщает: фирма
обеспечила юридическое сопровождение Продавца в сделке по продаже ООО
«Дмитровский металлоцентр» ПАО «Северсталь»». Команда — партнёр Александр
Жарский, советник Олег Ежов, юристы Олеся Клешева, Фёдор Трофимов, Анна
Кузнецова. Продавца пост не называет; в карточке он записан по ЕГРЮЛ
(ООО «Металлстандарт»), а в контексте стояло «Продавец сделки не раскрыт» —
фраза уточнена. Без ключа — сухой прогон.
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.source_names import settle_sources

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
URL = 'https://t.me/LawFirms/11566'
ADV = ['Юридический консультант продавца', 'АЛРУД',
       'Комплексное сопровождение на всех этапах: анализ юридических, налоговых и регуляторных '
       'рисков, структурирование условий сделки, непрерывность работы компании в переходный '
       'период, передача и интеграция ключевых активов. Команда — партнёр Александр Жарский, '
       'советник Олег Ежов, юристы Олеся Клешева, Фёдор Трофимов и Анна Кузнецова. '
       'Источник: t.me/LawFirms/11566']
OLD_CTX = 'Продавец сделки не раскрыт.'
NEW_CTX = ('В новостях продавца не называли; по ЕГРЮЛ прежним владельцем было ООО «Металлстандарт», '
           'его юридическим консультантом в сделке был АЛРУД.')


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    d = next(x for x in data['deals'] if x['id'] == 'g0b187624')
    if any(a[1] == 'АЛРУД' for a in d['law'].get('adv') or []):
        print('уже есть'); return
    assert not d['law'].get('adv'), d['law'].get('adv')
    assert d['eco']['context'].count(OLD_CTX) == 1
    d['law']['adv'] = [ADV]
    d['eco']['context'] = d['eco']['context'].replace(OLD_CTX, NEW_CTX)
    if URL not in {s[1] for s in d.get('src') or []}:
        d['src'].append(['АЛРУД (Telegram, @LawFirms)', URL])
    print('g0b187624: консультант продавца — АЛРУД; контекст уточнён')
    if write:
        data = json.load(open(DATA, encoding='utf-8'))  # перечитать прямо перед записью
        x = next(x for x in data['deals'] if x['id'] == 'g0b187624')
        assert not x['law'].get('adv') and x['eco']['context'].count(OLD_CTX) == 1
        x['law']['adv'] = [ADV]
        x['eco']['context'] = x['eco']['context'].replace(OLD_CTX, NEW_CTX)
        if URL not in {s[1] for s in x.get('src') or []}:
            x['src'].append(['АЛРУД (Telegram, @LawFirms)', URL])
        settle_sources(x)  # @LawFirms — агрегатор: в «где нашли», не в источники факта
        with open(DATA, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
            f.write('\n')


if __name__ == '__main__':
    main('--write' in sys.argv)
