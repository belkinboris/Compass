# -*- coding: utf-8 -*-
"""Дневная очередь качества, 12 сентября 2026 — карточка `g298c1588`
(Сергей Жучков продал ProgKids компании Rocket Tech School). Полный обыск
саб-агентом нашёл немного сверх уже известного — сумма и условия сделки
по-прежнему нигде не раскрыты (это уже честно зафиксировано в
`accepted_notes`), а часть найденного оказалась НЕ ДОСТАТОЧНО проверенной,
чтобы вносить в карточку:

- WebSearch-сниппет намекал, что к моменту сделки (июль 2026) формальным
  единственным участником ООО «Прогкидс» в ЕГРЮЛ мог значиться уже не сам
  Жучков, а некто Борис Аннакурбанов — НЕ ВНЕСЕНО: это вторичный пересказ
  без прямого WebFetch первоисточника (свежей выписки ЕГРЮЛ), а не цитата;
  вносить факт о смене держателя доли на таком основании значило бы
  выдумывать бездоказательно.
- Цифры о Rocket Tech School (3000+ учеников, 170+ преподавателей и т. п.)
  — тоже только по WebSearch-сниппетам с непроверенных агрегаторов, не
  подтверждены прямым чтением; НЕ ВНЕСЕНЫ.

Внесено только то, что подтверждено ДВУМЯ независимыми регистровыми
источниками (spark-interfax.ru и rusprofile.ru сходятся) и цитатой с
собственного сайта компании-предмета:

- law.struct (было «—»): юрлицо предмета сделки — ООО «Прогкидс»,
  ИНН 7704434913, ОГРН 1177746689955, действует с 2017 года, Москва.
- eco.context (было «—»): история основания — по интервью самого Жучкова
  на сайте компании (progkids.com), ProgKids создан после того, как он
  наблюдал, как его сын изучает программирование на примере Minecraft.

ИНН ООО «Прогкидс» внесён отдельно в `pipeline/fns_registry.py`.
Rocket Tech School (покупатель) — точное юрлицо/ИНН НЕ найдено ни одним
источником, реестр не пополняется.

Запуск:
    python3 pipeline/fix_daily_queue_2026_09_12_progkids.py            # сухой прогон
    python3 pipeline/fix_daily_queue_2026_09_12_progkids.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_LAW_STRUCT = (
    'Юрлицо предмета сделки — ООО «Прогкидс» (ИНН 7704434913, '
    'ОГРН 1177746689955), Москва, действует с 2017 года.'
)

NEW_ECO_CONTEXT = (
    'ProgKids основан в 2016 году: по словам Сергея Жучкова, идея пришла, '
    'когда он наблюдал, как его сын изучает программирование на примере '
    'игры Minecraft.'
)

NEW_SRC = [
    ['spark-interfax.ru', 'https://spark-interfax.ru/moskva-arbat/'
                          'ooo-progkids-inn-7704434913-ogrn-1177746689955-'
                          '591525e914295bb9e0531c9aa8c084ba'],
    ['progkids.com', 'https://www.progkids.com/en/blog/'
                      'intervyu-s-osnovatelem-onlayn-shkoly-'
                      'programmirovaniya-progkids-sergeem-zhuchkovym'],
]


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}
    d = by_id['g298c1588']

    assert d['law']['struct'] == '—', 'law.struct уже занято: %r' % (d['law']['struct'],)
    assert d['eco']['context'] == '—', 'eco.context уже занято: %r' % (d['eco']['context'],)
    urls = {s[1] for s in d['src']}
    for name, url in NEW_SRC:
        assert url not in urls, 'источник уже добавлен: %s' % url

    print('g298c1588: заполняю law.struct (юрлицо ООО «Прогкидс», ИНН/ОГРН), '
          'eco.context (история основания), добавляю 2 источника')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d['law']['struct'] = NEW_LAW_STRUCT
    d['eco']['context'] = NEW_ECO_CONTEXT
    d['src'].extend(NEW_SRC)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
