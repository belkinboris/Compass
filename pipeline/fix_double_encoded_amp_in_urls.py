# -*- coding: utf-8 -*-
"""Разовая чистка: 4 карточки несли в `src` ссылку с буквальным текстом
«&amp;amp;» вместо символа «&» между параметрами трекинга (двойное
HTML-экранирование при разборе притока — «&» → «&amp;» → «&amp;amp;»).
Само по себе не всегда ломает переход (браузер иногда прощает), но это
не настоящий адрес статьи, а испорченная строка — и это единственная
ссылка у каждой из четырёх карточек.

Проверено лично: базовый адрес БЕЗ параметров трекинга (utm_source и
т.п.) у всех четырёх открывается (curl, код 200) — сама статья жива,
испорчены только служебные параметры после «?». Решение — обрезать
строку до символа «?» (или до первого корректного «&», если параметры
нужны без трекинга) и убрать испорченный хвост целиком: сами параметры
utm_* не несут ничего, кроме источника перехода, и не нужны читателю.

Замер: `grep` по всей базе на `amp;` в поле `src` — 4 совпадения, все
четыре внутри этого скрипта.

Запуск: python3 pipeline/fix_double_encoded_amp_in_urls.py
        python3 pipeline/fix_double_encoded_amp_in_urls.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

FIXES = {
    'gd9c4a5eb': (
        'https://rb.ru/news/st-kapital-zerocoder/?utm_source=telegram&amp;amp;utm_medium=social&amp;amp;utm_campaign=post',
        'https://rb.ru/news/st-kapital-zerocoder/',
    ),
    'g21c5ee1e': (
        'https://rb.ru/news/nemeckij-aeroport/?utm_source=telegram&amp;amp;utm_medium=social&amp;amp;utm_campaign=post',
        'https://rb.ru/news/nemeckij-aeroport/',
    ),
    'g1a6f4fec': (
        'https://rb.ru/news/wework-prodazha-biznesa/?utm_source=telegram&amp;amp;utm_medium=social&amp;amp;utm_campaign=post',
        'https://rb.ru/news/wework-prodazha-biznesa/',
    ),
    'g5f0d5d18': (
        'https://www.vedomosti.ru/business/articles/2023/06/19/981081-trast-vistavil-na-prodazhu-bivshii-selskohozyaistvennii-aktiv-shishhanova?utm_campaign=newspaper_19_6_2023&amp;amp;utm_medium=email&amp;amp;utm_source=vedomosti',
        'https://www.vedomosti.ru/business/articles/2023/06/19/981081-trast-vistavil-na-prodazhu-bivshii-selskohozyaistvennii-aktiv-shishhanova',
    ),
}


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deals_by_id = {d['id']: d for d in data['deals']}

    for deal_id, (old_url, new_url) in FIXES.items():
        deal = deals_by_id[deal_id]
        matched = [s for s in deal['src'] if s[1] == old_url]
        assert matched, f'{deal_id}: старый URL не найден в src'
        print(f'{deal_id}: {old_url!r} -> {new_url!r}')
        if write:
            for s in deal['src']:
                if s[1] == old_url:
                    s[1] = new_url

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
