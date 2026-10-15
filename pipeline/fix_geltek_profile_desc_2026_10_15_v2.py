# -*- coding: utf-8 -*-
"""Второй дефект того же класса на той же карточке: `accept_card.py`
дописал в `desc` профиля «Гельтек» (`g7666e3f4`) предложение «Юрлицо —
ООО «Гельтек РНД».» — короче первого, но с именем в кавычках, и
`_pick_novel_sentences` в `format_post.py` ставит предложения с
кавычками первым кандидатом независимо от их места в тексте. Выбранное
предложение содержит слово «Гельтек» (внутри «Гельтек РНД»), поэтому
`has_novelty(name="Гельтек", detail)` не находит новизны у самого
ИМЕНИ — и строка «Покупатель:» печатает деталь без имени перед ней:
«Покупатель: Юрлицо — ООО «Гельтек РНД».» без слова «Гельтек» спереди.

Это не точечная правка кода (нужен замер — сколько профилей вообще
попадают под комбинацию «имя-подстрока юрлица + кавычки», отдельная
запись в KNOWN_ISSUES.md), а практическое обходное решение для ЭТОЙ
карточки: оба предложения `desc` слиты в одно — тогда выбранный текст
сам по себе осмыслен без имени-подлежащего перед ним.

Запуск:
    python3 pipeline/fix_geltek_profile_desc_2026_10_15_v2.py            # сухой прогон
    python3 pipeline/fix_geltek_profile_desc_2026_10_15_v2.py --write    # применить
"""
import json
import sys

DATA = '/home/user/Compass/static/data/deals_promoted.json'
COMPANY_ID = 'g7666e3f4'

OLD = ('Российский производитель косметики, владелец — Сергей Кирш; бренды Geltek Baby '
       '(уход за детской кожей) и молодёжная косметика The U. Юрлицо — ООО «Гельтек РНД».')
NEW = ('Российский производитель косметики (владелец — Сергей Кирш, бренды Geltek Baby и '
       'The U), юрлицо — ООО «Гельтек РНД».')


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    company = data['companies'][COMPANY_ID]
    assert company['desc'] == OLD, company['desc']

    print('ПРАВКА %s: desc' % COMPANY_ID)
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(DATA, encoding='utf-8'))
    assert fresh['companies'][COMPANY_ID]['desc'] == OLD, 'кто-то уже поправил — перечитайте'
    fresh['companies'][COMPANY_ID]['desc'] = NEW
    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
