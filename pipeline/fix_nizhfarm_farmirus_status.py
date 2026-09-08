# -*- coding: utf-8 -*-
"""Месячная очередь, 8 сентября 2026 — карточка `c43cb8f80` (Президент РФ
передал АО «Нижфарм» в управление ООО «Фармирус», 4 апреля 2025) не
несла `status` вовсе (`null`) — на экране это рендерилось бы как
UNDEFINED (уже описанный класс дефекта, см. CLAUDE.md). Указ подписан и
опубликован, и по устоявшейся в базе конвенции для указов о временном
управлении (`g9c4b80a7` CanPack, `c7fd83d05` Danone Россия — обе
«Закрыта») это уже свершившийся правовой факт, а не обсуждаемый план.

Личный WebFetch (kommersant.ru/doc/7638104) подтвердил нюанс: «В
"Нижфарме" сообщили, что не получали официальных уведомлений о передаче
акций компании "Фармирусу"» — компания «ожидает официальных разъяснений
и продолжает работать». Это не отменяет статус (указ президента вступает
в силу подписанием/публикацией, а не корпоративным уведомлением), но
добавлено честной оговоркой в `eco.context`.

Поле `eco.context` уже прошло вычитку — за основу слияния взят ТЕКУЩИЙ
текст с диска.

Запуск:
    python3 pipeline/fix_nizhfarm_farmirus_status.py            # сухой прогон
    python3 pipeline/fix_nizhfarm_farmirus_status.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'
CARD_ID = 'c43cb8f80'

NEW_STATUS = 'Закрыта'

OLD_CONTEXT = (
    'По данным СПАРК, «Фармирус» создана в 2020 году Анной Залогиной для '
    'торговли лекарствами. Выручка компании за 2024 год — 1,1 млрд ₽, '
    'чистая прибыль — 18 млн ₽.'
)
NEW_CONTEXT = OLD_CONTEXT + (
    ' На момент публикации указа в «Нижфарме» заявляли, что не получали '
    'официальных уведомлений о передаче акций компании «Фармирусу», и '
    'ожидали разъяснений, продолжая работать в обычном режиме.'
)


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}
    card = by_id[CARD_ID]

    assert card.get('status') is None, 'status уже занят: %r' % (card.get('status'),)
    assert card['eco']['context'] == OLD_CONTEXT, \
        'eco.context уже другой: %r' % (card['eco']['context'],)

    print('status: None -> %r' % NEW_STATUS)
    print('eco.context: добавляется оговорка об уведомлении (Коммерсантъ)')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    card['status'] = NEW_STATUS
    card['eco']['context'] = NEW_CONTEXT

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
