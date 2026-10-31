# -*- coding: utf-8 -*-
"""Месячная очередь качества, 11 сентября 2026 — карточка `c1aa8b20d`
(«Fesco получила в управление Петропавловск-Камчатский морской торговый
порт и «Камчатское морское пароходство»», октябрь 2025) уже несла
контекст и оценку 16,7 млрд ₽, но не называла ЮРИДИЧЕСКУЮ ПРИРОДУ
сделки (это передача в управление конфискованного госимущества, не
покупка) и финансовые показатели предмета.

Личный WebFetch подтвердил дословно:
- ПРАЙМ (https://www.alta.ru/logistics_news/122591/): «Сейчас
  учредитель ООО «ПКМТП» и ООО «КМП» - Российская Федерация, а
  оперативное управление этими активами находится под контролем группы
  FESCO».
- Собственный пресс-релиз FESCO
  (https://paluba.media/news/203116): «Транспортная группа FESCO...
  приняла полномочия единоличного исполнительного органа ООО «ПКМТП» и
  ООО «КМП»».
- Морвести (https://morvesti.ru/news/1679/116091/): «За 2024 год чистая
  прибыль ПКМТП составила 253,4 млн руб.», годовой грузооборот —
  «около 1 млн тонн в год».
- АиФ.Камчатка
  (https://kamchatka.aif.ru/society/gosudarstvo-zabralo-u-ivancheya-kamchatskoe-morskoe-parohodstvo):
  «Годовая выручка пароходства в последние годы составляла около 5-7
  млрд рублей».
- TAdviser (https://www.tadviser.ru/index.php/Компания:Петропавловск-Камчатский_морской_торговый_порт):
  «Судовой состав пароходства включает восемь единиц плавсредств».

Запуск:
    python3 pipeline/fix_fesco_kamchatka_port_structure_fin.py            # сухой прогон
    python3 pipeline/fix_fesco_kamchatka_port_structure_fin.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_LAW_STRUCT = (
    'Собственник ООО «ПКМТП» и ООО «Камчатское морское пароходство» — '
    'Российская Федерация; FESCO получила только полномочия '
    'единоличного исполнительного органа (управление) по распоряжению '
    'Росимущества, доли в капитале этих компаний FESCO не приобретает. '
    'До передачи самого порта и пароходства (сентябрь 2025 года) FESCO '
    'уже управляла рядом смежных камчатских компаний того же '
    'конфискованного имущественного комплекса.'
)

NEW_ECO_TARGET_FIN = (
    'Чистая прибыль ПКМТП за 2024 год — 253,4 млн ₽ при грузообороте '
    'около 1 млн тонн в год. Выручка «Камчатского морского пароходства» '
    'в последние годы составляла около 5–7 млрд ₽, в составе флота — '
    'восемь судов.'
)

NEW_SRC = [
    ['ПРАЙМ', 'https://www.alta.ru/logistics_news/122591/'],
    ['Морвести', 'https://morvesti.ru/news/1679/116091/'],
    ['АиФ.Камчатка', 'https://kamchatka.aif.ru/society/gosudarstvo-zabralo-u-ivancheya-kamchatskoe-morskoe-parohodstvo'],
    ['TAdviser', 'https://www.tadviser.ru/index.php/Компания:Петропавловск-Камчатский_морской_торговый_порт'],
]


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['c1aa8b20d']

    assert d.get('law', {}).get('struct') in (None, '—'), 'law.struct уже занят: %r' % (d.get('law', {}).get('struct'),)
    assert d['eco'].get('target_fin') in (None, '—'), 'eco.target_fin уже занят: %r' % (d['eco'].get('target_fin'),)
    urls = {s[1] for s in d['src']}
    for src in NEW_SRC:
        assert src[1] not in urls, 'источник уже добавлен: %s' % src[1]

    print('c1aa8b20d: law.struct и eco.target_fin заполнены (природа '
          'сделки — управление, не покупка; финансы предмета); добавлено '
          '4 источника')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d.setdefault('law', {})['struct'] = NEW_LAW_STRUCT
    d['eco']['target_fin'] = NEW_ECO_TARGET_FIN
    d['src'].extend(NEW_SRC)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
