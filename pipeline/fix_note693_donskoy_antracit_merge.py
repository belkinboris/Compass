# -*- coding: utf-8 -*-
"""Приток 19.09.2026, часовой прогон 10:20 МСК — ответ на заметку владельца
№693. Источник самой карточки gef939ff4 (Коммерсантъ) прямо говорит: торги
2 июня 2026 года по продаже прав требования и контроля над «Донским
антрацитом»/«Обуховской» НЕ СОСТОЯЛИСЬ (заявок не поступило) — то есть
активы по-прежнему у АО «Лучшее решение», а не проданы дальше. Владелец:
«убрал бы эту карту и в карту с АО «Лучшее решение» дописал дополнительную
информацию, что они пытаются продать этот актив». Факт о сорвавшихся
торгах 2 июня уже стоит в контексте карточки-продолжения (g87443ed1) —
переносим только НОВЫЕ факты gef939ff4 (происхождение актива: продажа
Сбербанком кипрской Valleyton в 2021 году, $230 млн + $446,8 млн долга по
кредиту; предполагаемый бенефициар Fabcell — Искендер Халилов, что
оспаривается его представителем; финансовые показатели «Обуховской»), а
саму gef939ff4 удаляем с редиректом на g87443ed1.
"""
import json
import sys

DATA_PATH = 'static/data/deals_promoted.json'

ADDED_CONTEXT = (
    ' До перехода к структурам, связанным с Fabcell Limited, в ноябре 2021 '
    'года Сбербанк на торгах продал акции обоих предприятий и права '
    'требования по выданным им кредитам кипрской Valleyton Investments — '
    'сумма сделки составила $230 млн, а задолженность по синдицированному '
    'кредиту, по документации к торгам, — $446,8 млн. Бенефициаром Fabcell '
    'Limited в марте 2022 года называли Искендера Халилова, что оспаривает '
    'его представитель; прямой связи между Valleyton и Fabcell не установлено.'
)


def main(write):
    data = json.load(open(DATA_PATH, encoding='utf-8'))
    deals = data['deals']
    old_card = next(d for d in deals if d['id'] == 'gef939ff4')
    assert old_card['title'] == 'СБК Премьер приобрела угольные активы «Донской антрацит» и «Обуховская»'

    survivor = next(d for d in deals if d['id'] == 'g87443ed1')
    old_context = survivor['eco']['context']
    assert 'Valleyton' not in old_context
    survivor['eco']['context'] = old_context + ADDED_CONTEXT

    data['deals'] = [d for d in deals if d['id'] != 'gef939ff4']
    data.setdefault('merged', {})['gef939ff4'] = 'g87443ed1'

    tp = data.get('telegram_posts', {})
    assert tp.get('gef939ff4') is None and tp.get('g87443ed1') is None

    if write:
        json.dump(data, open(DATA_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('gef939ff4 удалена, факты перенесены в g87443ed1. ЗАПИСАНО.')
    else:
        print('Сухой прогон. Повторите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
