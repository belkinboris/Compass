"""ВТБ/«Лабинский» (g97679d43), веха closed — выпуск по прямому слову владельца, 20 октября 2026.

Владелец в чате с агентом: «опубликуй уже скорее». Текст — тот, что прислали
партнёр и владелец (pipeline/fix_labinsky_milestone_2026_10_20.py, TEXT).
Пост уходит в основной канал тем же post_to_channels, что у рутины публикации,
и записывается в telegram_milestones — второй раз его не выпустит ни рутина, ни
кнопка на сайте (_milestone_already_out). Без ключа — сухой прогон.
"""
import json, os, sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in ('pipeline/publish', 'pipeline/ingest', 'pipeline'):
    sys.path.insert(0, os.path.join(ROOT, p))
import send_telegram, format_post, channels  # noqa: E402
from fix_labinsky_milestone_2026_10_20 import TEXT  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
EVENT = 'g97679d43-closed'


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    ms = data.setdefault('telegram_milestones', {})
    assert EVENT not in ms, ms.get(EVENT)
    deal = next(d for d in data['deals'] if d['id'] == 'g97679d43')
    print(TEXT)
    if not write:
        print('сухой прогон'); return
    import httpx
    token = os.environ['TELEGRAM_BOT_TOKEN']
    addr = {channels.MAIN: send_telegram.channel_address()}
    assert addr[channels.MAIN]
    with httpx.Client(timeout=30) as client:
        mids, error = send_telegram.post_to_channels(client, token, addr, [channels.MAIN], TEXT,
                                                     format_post.render_buttons(deal))
    print('вышло:', mids, 'ошибка:', error)
    if mids:
        data = json.load(open(DATA, encoding='utf-8'))
        now = datetime.now(timezone.utc).isoformat(timespec='seconds')
        data.setdefault('telegram_milestones', {})[EVENT] = {'at': now, 'message_id': mids[channels.MAIN],
                                                             'by': 'owner_in_chat'}
        data['telegram_last_post_at'] = now
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        with open(DATA, 'a', encoding='utf-8') as f:
            f.write('\n')


if __name__ == '__main__':
    main('--write' in sys.argv)
