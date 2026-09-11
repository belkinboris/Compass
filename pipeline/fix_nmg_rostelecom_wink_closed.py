# -*- coding: utf-8 -*-
"""Месячная очередь качества, 11 сентября 2026 — карточка `ca71a7545`
(«НМГ и Ростелеком объединяют видеосервисы more.tv и Wink в совместное
предприятие») несла настоящее время в заголовке и `status: None`, хотя
второй источник, уже стоящий в `src` (VC.ru), прямо сообщает, что
сделка ЗАКРЫТА: «НМГ и «Ростелеком» закрыли сделку по объединению
more.tv и Wink в один видеосервис» — эта дословная цитата не была
внесена в структурные поля, только ссылка попала в `src`. Год карточки
(«2024») тоже неверен: статья датирована 15.06.2023 — тот же класс
ошибки, что уже чинился для «Эльдако» в этом прогоне (год определён по
дате публикации источника закрытия, не выдуман).

Личный WebFetch подтвердил дословно
(https://vc.ru/media/728626-nmg-i-rostelekom-zakryli-sdelku-po-obedineniyu-more-tv-i-wink-v-odin-videoservis,
дата публикации 15.06.2023): «НМГ и «Ростелеком» закрыли сделку по
объединению more.tv и Wink в один видеосервис»; «Компании учредят
совместное предприятие, «Ростелеком» получит в нём 70%, НМГ – 30%»
(структура уже верно стояла в `eco.share`); «Онлайн-кинотеатры more.tv
и Wink объединят под брендом последнего» (Wink). Точного дня закрытия
(отличного от дня публикации) в статье нет — используется дата
публикации как известная точка отсчёта, без точности до конкретного
календарного события, отдельно не проверенного.

Запуск:
    python3 pipeline/fix_nmg_rostelecom_wink_closed.py            # сухой прогон
    python3 pipeline/fix_nmg_rostelecom_wink_closed.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

OLD_TITLE = 'НМГ и Ростелеком объединяют видеосервисы more.tv и Wink в совместное предприятие'
NEW_TITLE = 'НМГ и Ростелеком закрыли сделку по объединению видеосервисов more.tv и Wink'

OLD_DATE = '2024'
NEW_DATE = '2023-06-15'


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['ca71a7545']

    assert d['title'] == OLD_TITLE, 'title уже другой: %r' % (d['title'],)
    assert d['date'] == OLD_DATE, 'date уже другая: %r' % (d['date'],)
    assert d.get('status') is None, 'status уже занят: %r' % (d.get('status'),)

    print('ca71a7545: title переписан в прошедшее время (сделка закрыта), '
          'status -> Закрыта, date исправлена с 2024 на 2023-06-15')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d['title'] = NEW_TITLE
    d['date'] = NEW_DATE
    d['status'] = 'Закрыта'

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
