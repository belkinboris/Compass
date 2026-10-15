# -*- coding: utf-8 -*-
"""Профиль g5f73fcaf («Русская промышленная компания»): после привязки ИНН
к карточке gbe13372d `accept_card.py` дописал в конец `desc` короткое
предложение «Юрлицо — АО «РПК».» — единственное с кавычками, поэтому
`format_post._pick_novel_sentences` в посте карточки стало показывать ТОЛЬКО
его, а не содержательное описание холдинга (KNOWN_ISSUES.md, «Пост теряет
имя покупателя…», второй случай). Склеено в одно предложение — кандидат для
выбора остался один, содержит всё.

Запуск:
    python3 pipeline/fix_rpk_profile_desc_2026_10_15.py            # сухой прогон
    python3 pipeline/fix_rpk_profile_desc_2026_10_15.py --write    # применить
"""
import json
import sys

DATA = '/home/user/Compass/static/data/deals_promoted.json'
CID = 'g5f73fcaf'
OLD = ('Угледобывающий холдинг; управляет активами в сфере добычи и обогащения угля и '
       'антрацита. Зарегистрирован в мае 2026 года, гендиректор — Феликс Нахшунов. '
       'Юрлицо — АО «РПК».')
NEW = ('Угледобывающий холдинг; управляет активами в сфере добычи и обогащения угля и '
       'антрацита, зарегистрирован в мае 2026 года, гендиректор — Феликс Нахшунов; '
       'юрлицо — АО «РПК».')


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    comp = data['companies'][CID]
    assert comp['desc'] == OLD, 'desc уже не тот, что ожидался: %r' % comp['desc']
    print('%s\n-> %s' % (OLD, NEW))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(DATA, encoding='utf-8'))
    fresh_comp = fresh['companies'][CID]
    assert fresh_comp['desc'] == OLD, 'desc поменяли параллельно — перечитайте'
    fresh_comp['desc'] = NEW
    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
