# -*- coding: utf-8 -*-
"""Месячная очередь качества, 11 сентября 2026 — карточка `ce6b8c447`
(«Carlsberg требует у России компенсацию за срыв продажи «Балтики»»,
статус уже «Не состоялась» — сделка с «Арнестом» сорвалась). Роль
«Арнеста» проверена и подтверждена независимо (три источника со
ссылкой на «Интерфакс»): «покупателем "Балтики" должна была выступить
группа "Арнест"», рамочное соглашение расторгнуто после введения
временного управления Росимущества.

Итоговая судьба «Балтики» — уже задокументирована в ОТДЕЛЬНОЙ карточке
`baltika` («Carlsberg продал «Балтику»: management buy-out через
«ВГ Инвест»», декабрь 2024, 34 млрд ₽) — здесь добавляется только
краткая ссылка на неё, без пересказа деталей. Личный WebFetch
подтвердил дословно (Interfax,
https://interfax.com/newsroom/top-stories/109619/): «Balthika had
come under the ownership of VG Invest», «the parties settled all
outstanding legal disputes» — формулировка не уточняет явно, поглощает
ли урегулирование именно международно-правовое требование о
компенсации 71 млрд ₽ (три уведомления о споре по инвестдоговорам,
поданы 13 октября 2023 года). Статус самого этого международного
требования (продолжается ли оно, отозвано ли) НЕ подтверждён и НЕ
опровергнут ни одним найденным источником — честно оставлено как
открытый вопрос, а не приравнено к урегулированию сделки по продаже.

Запуск:
    python3 pipeline/fix_carlsberg_baltika_arnest_outcome.py            # сухой прогон
    python3 pipeline/fix_carlsberg_baltika_arnest_outcome.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

OLD_ECO_CONTEXT = (
    'Carlsberg направил властям письмо, в котором назвал действия РФ '
    'нарушением обязательств по двустороннему инвестиционному '
    'соглашению. В Минфине оснований для компенсации убытков датчанам '
    'не нашли.'
)

NEW_ECO_CONTEXT = OLD_ECO_CONTEXT + (
    ' В итоге «Балтику» вывели из-под временного управления и продали '
    'менеджменту компании в декабре 2024 года (карточка «Carlsberg '
    'продал «Балтику»: management buy-out через «ВГ Инвест»») — '
    'стороны заявили, что урегулировали споры, но продолжается ли '
    'именно это международное требование о компенсации, ни один '
    'источник не уточняет.'
)

NEW_SRC = [['Interfax', 'https://interfax.com/newsroom/top-stories/109619/']]


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['ce6b8c447']

    assert d['eco'].get('context') == OLD_ECO_CONTEXT, 'eco.context изменился: %r' % (d['eco'].get('context'),)
    urls = {s[1] for s in d['src']}
    assert NEW_SRC[0][1] not in urls, 'источник уже добавлен'

    print('ce6b8c447: eco.context дополнен перекрёстной ссылкой на '
          'исход (карточка baltika); добавлен источник')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d['eco']['context'] = NEW_ECO_CONTEXT
    d['src'].append(NEW_SRC[0])

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
