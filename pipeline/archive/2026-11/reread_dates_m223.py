# -*- coding: utf-8 -*-
"""Вычитка 12 ноября 2026, партия m223 (часть 1): даты событий, консультант, правовая форма сторон.

Чего не умеет review.py: дата без дня прописью в цитате, консультант (не прозаическое поле), правовая форма
профиля, элемент списка (events.0.date), заметка приемки.

g931e89e1 (ТЦ «Аура» в Сургуте): статус «Не состоялась» держится на опровержении собственника центра
  АО «Риалрен» — день события 18 марта 2026 года (СургутИнформ-ТВ, «16:18 18.03.2026»), а не 6 марта, день
  статьи «Ведомостей». «Ведомости»: «В CORE.XP, выступавшей консультантом данной сделки, от комментариев
  отказались» — «Публично не сообщалось» неверно. Профиль Grand Line (ПО «Металлист»): правовая форма
  записана с прямой кавычкой и строчной буквой — «ООО «ПО «Металлист»»». Профиль Renaissance Development:
  турецкий девелопер; сайт сопоставил ему ООО «Ренессанс Девелопмент» (ИНН 7701306504), которым владеют
  ООО «Объединенные инвестиции» (89,2%) и ООО «Промышленные инвестиции» (10,8%) — однофамилец, а не
  российская компания турецкой группы; правовая форма снята.
g5ffcce01 (ДОМ.РФ, недострои в Липецке): торги — день первого объявления. Рамблер («Новости Липецка»),
  01 июля 2026: «Три объекта незавершенного строительства продают с молотка в Липецке на территории Военного
  городка» (прием заявок до 24 августа; вторые торги объявлены 18 сентября). Имя издания — «Абирег».
g1f1d470a (ДОМ.РФ, Красково): РИАМО: «Аукцион состоится 18 сентября»; РИА Недвижимость 22 сентября — день
  публикации итогов.
g685f1e39 («1С» и «Райтек»): где искали вторые источники и юрлицо СП.

    python3 pipeline/archive/2026-11/reread_dates_m223.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY, DAY = 'reread_dates_m223', '2026-11-12'
SITV = 'https://sitv.ru/arhiv/news/sdelki-ne-zaklyuchalis-sobstvennik-aury-oproverg-informacziyu-o-prodazhe-tcz/'
VED = ('https://www.vedomosti.ru/realty/articles/2026/03/06/1181122-proizvoditel-stroimaterialov-grand-line-'
       'zakril-sdelku-po-pokupke-torgovih-tsentrov?from=copy_text')
RAMBLER = 'https://finance.rambler.ru/business/56691795-v-lipetske-realizuyut-s-torgov-tri-nedostroya-v-voennom-gorodke/'
RIAMO = 'https://riamo.ru/news/nedvizhimost/domrf-vystavil-na-torgi-kompleks-v-ljuberetskom-okruge/'

DATES = {
    'g931e89e1': ('2026-03-06', '2026-03-18', 'announcement',
                  '16:18 18.03.2026 … В редакцию СургутИнформ-ТВ обратился руководитель акционерного общества '
                  '«Риалрен», которому на праве собственности принадлежит ТЦ «Аура» в Сургуте. Он заявил, что '
                  'информация о продаже местного центра, озвученная ранее газетой «Ведомости», не соответствует '
                  'действительности.', SITV),
    'g5ffcce01': ('2026-09-18', '2026-07-01', 'announcement',
                  'В Липецке реализуют с торгов три недостроя в Военном городке. 01 июля 2026, 17:16. Три объекта '
                  'незавершенного строительства продают с молотка в Липецке на территории Военного городка. '
                  'Информация опубликована на портале Дом.РФ', RAMBLER),
    'g1f1d470a': ('2026-09-22', '2026-09-18', None,
                  'Аукцион по продаже имущественного комплекса пройдет в Люберецком округе Подмосковья 18 сентября. '
                  '… Аукцион состоится 18 сентября.', RIAMO),
}
FINADV = ('g931e89e1', 'Публично не сообщалось', 'CORE.XP (консультант одной из сторон)',
          'В CORE.XP, выступавшей консультантом данной сделки, от комментариев отказались.', VED)
SEARCHED = ('g685f1e39',
            'CNews (22 сентября 2026, сообщение «1С»); ComNews о выделении ООО «Райтек Промышленность» '
            '(25 августа 2026) — о СП ни слова; ComNews об ИИ-агенте «Райтек» (8 сентября 2026); поиск '
            '«1С» «Райтек» совместное предприятие, ООО, ИНН; hh.ru и Хабр Карьера «Райтек ДТГ». Второго '
            'сообщения о СП и его юрлица не нашлось.')


def apply(data):
    by = {d['id']: d for d in data['deals']}
    comps = data['companies']
    n = 0
    for cid, (old, new, basis, quote, url) in DATES.items():
        c = by[cid]
        if c['date'] == new:
            continue
        assert c['date'] == old, (cid, c['date'])
        c['date'] = new
        if basis:
            c['date_basis'] = basis
        fact_edit_guard.log(c, 'date', new, quote, url, BY, DAY)
        n += 1
    c = by['g1f1d470a']
    ev = c.get('events') or []
    if ev and ev[0].get('kind') == 'closed' and ev[0].get('date') == '2026-09-22':
        ev[0]['date'] = '2026-09-18'
        n += 1
    c = by['g5ffcce01']
    for s in c.get('src') or []:
        if s[0].startswith('Абireg'):
            s[0] = 'Абирег'
            n += 1
    cid, old, new, quote, url = FINADV
    c = by[cid]
    if c['eco'].get('finadv') != new:
        assert c['eco'].get('finadv') == old, c['eco'].get('finadv')
        c['eco']['finadv'] = new
        fact_edit_guard.log(c, 'eco.finadv', new, quote, url, BY, DAY)
        n += 1
    if comps['g9200defd'].get('legal_short') != 'ООО «ПО «Металлист»»':
        assert comps['g9200defd'].get('legal_short') == 'ООО «ПО "металлист»', comps['g9200defd'].get('legal_short')
        comps['g9200defd']['legal_short'] = 'ООО «ПО «Металлист»»'
        n += 1
    if comps['g5bae9612'].get('legal_short'):
        assert comps['g5bae9612']['legal_short'] == 'ООО «Ренессанс Девелопмент»'
        del comps['g5bae9612']['legal_short']
        n += 1
    cid, text = SEARCHED
    c = by[cid]
    notes = c.setdefault('accepted_notes', {})
    if notes.get('searched') != text:
        notes['searched'] = text
        n += 1
    return n


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    old, data = json.loads(raw), json.loads(raw)
    n = apply(data)
    if not n:
        print('Уже применено.')
        return 0
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    bad = fact_edit_guard.unbacked(old, data)
    assert not bad, bad
    if not write:
        print('Сухой прогон: %d правок. Запись — с ключом --write.' % n)
        return 0
    fresh_raw = open(DATA, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    apply(fresh)
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
    print('ЗАПИСАНО: %d правок.' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
