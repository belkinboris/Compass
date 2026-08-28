# -*- coding: utf-8 -*-
"""«Алор брокер»/неназванная брокерская компания (`g6bf41023`): второй
источник (mergers.ru, со ссылкой на Forbes, 28 августа 2026) даёт причину,
почему покупка вообще понадобилась, — 26 июня ЦБ аннулировал у «Алора»
депозитарную лицензию за несоблюдение антисанкционного законодательства
(указы президента №95, №138 и №840, запрет схем перепродажи активов
иностранцев со скидкой), и описывает нынешнее состояние компании:
торговля на фондовом рынке клиентам недоступна, «Алор» сосредоточен на
переводе клиентов к другим брокерам, но продолжает работать на срочном и
валютном рынках и обслуживать институциональных инвесторов.

Цитата не лежит в тексте старого источника (Frank Media) — тот же приём,
что и в прежних правках этого поля: старое значение сохраняется,
дописывается новое предложение со ссылкой на источник.

Запуск: python3 pipeline/fix_alor_broker_license_revocation_context.py           # проверка
        python3 pipeline/fix_alor_broker_license_revocation_context.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g6bf41023'
OLD_CONTEXT = (
    'На фоне кризиса в группе сменился генеральный директор. Пост принял '
    'Александр Лужбин, уже руководивший структурой с 2011 по 2015 год. '
    'Эксперты считают назначение логичным антикризисным шагом для '
    'усиления контроля рисков и быстрого восстановления всей '
    'инфраструктуры.'
)
ADDITION = (
    '26 июня 2026 года ЦБ аннулировал депозитарную лицензию «Алора» из-за '
    'того, что брокер, по словам регулятора, не соблюдал антисанкционное '
    'законодательство — три указа президента (№95, №138 и №840), '
    'запрещающих схемы, по которым российские инвесторы покупали со '
    'скидкой активы у иностранцев, чтобы продать дороже в России. Сейчас '
    '«Алор» сосредоточен на сопровождении клиентов и переводе их активов '
    'к другим брокерам: торги на фондовом рынке клиентам недоступны, '
    'однако можно торговать на срочном и валютном рынках, а компания '
    'продолжает обслуживать институциональных инвесторов. В «Алоре» '
    'заявили, что планируют восстановить возможность торговли на '
    'фондовом рынке, но как именно — не уточнили.'
)
NEW_CONTEXT = OLD_CONTEXT + ' ' + ADDITION
NEW_SRC = ['Mergers.ru', 'https://mergers.ru/news/Alor-Broker-lishivshijsya-v-konce-iyunya-depozitarnoj-licenzii-kupil-novuyu-brokerskuyu-firmu-87445']


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card.get('eco', {}).get('context') == OLD_CONTEXT, (
        'eco.context уже другое: %r' % card.get('eco', {}).get('context'))
    src_already_present = NEW_SRC in card.get('src', [])

    print('ДОБАВЛЕНО: %r' % ADDITION)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 1

    card['eco']['context'] = NEW_CONTEXT
    if not src_already_present:
        card.setdefault('src', []).append(NEW_SRC)
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv[1:]))
