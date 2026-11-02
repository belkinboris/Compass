# -*- coding: utf-8 -*-
"""Сводка за октябрь 2026: новый черновик в консоль по правкам владельца.

Владелец, 2 ноября 2026, о своем тексте сводки в консоли: «Убери особенности
месяца и вместо 115 укажи цифру именно закрытых сделок. И в каких отраслях
больше всего тоже — только закрытых. И где цену пишем — надо сказать, что это
по раскрытой сумме». Правило теперь в `monthly_digest.render` (его текст —
образец формата); здесь — пересобрать текст октября, положить его в
`owner_text` (им выйдет сводка) и заново отправить черновик в консоль: отсчет
суток молчания начинается заново.

    python3 pipeline/fix_digest_closed_2026_11_02.py           # показать текст
    python3 pipeline/fix_digest_closed_2026_11_02.py --write   # записать и отправить черновик
"""
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'publish'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import monthly_digest  # noqa: E402
import send_telegram  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
KEY = '2026-10'


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    text = monthly_digest.render(data, 2026, 10)
    assert text and 'закрытых' in text and 'Особенности' not in text
    state = data['telegram_digests'][KEY]
    assert not state.get('message_id'), 'сводка уже вышла'
    print(text)
    if not write:
        print('\nСухой прогон. Запись и отправка — с ключом --write.')
        return 0
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    assert token, 'нет токена бота в окружении'
    data = json.load(open(DATA, encoding='utf-8'))          # перечитать прямо перед записью
    digests = data['telegram_digests']
    digests[KEY]['owner_text'] = text
    digests[KEY].pop('drafted_at', None)
    changed, err = send_telegram.deliver_digest('draft', KEY, text, token, None, digests,
                                                datetime.now(timezone.utc))
    assert changed and not err, err
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано, черновик в консоли.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
