"""ВТБ/«Лабинский» (g97679d43), веха closed — текст поста от владельца и партнера, 20 октября 2026.

Партнер переписал пост этапа (ответ текстом на «[веха g97679d43~closed]»
сайт тогда не разбирал, правка пропала — починено в main.py), владелец
прислал тот же текст в чат: «Только не забудь все шрифты и линки сделать».
1) В базе: заголовок этапа и предмет в снимке — их словами (без имени
   Очкаласова: правило «без имен людей в постах», docs/card_parties.md).
2) На сайт: готовый пост этапа их текстом, с жирными подписями и ссылками —
   по кнопке «Пост в канал» сайт публикует именно его.
Без ключа — сухой прогон.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'publish'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import format_post, channels  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
DEAL, KIND = 'g97679d43', 'closed'
HEADLINE = 'ВТБ продал агрохолдинг «Лабинский» за 50 млрд рублей'
ASSET = 'агрокомплекс «Лабинский», включая земельные участки'
OLD_HEADLINE = 'ВТБ продал агрохолдинг «Лабинский» структурам «Просторов» за 50 млрд рублей'
OLD_ASSET = 'агрокомплекс «Лабинский» и земли Виталия Очкаласова'
TEXT = ('<b>ВТБ продал агрохолдинг «Лабинский» за 50 млрд рублей</b>\n\n'
        '<b>Покупатель:</b> агрохолдинг «Просторы»\n'
        '<b>Продавец:</b> ВТБ\n'
        '<b>Предмет:</b> агрокомплекс «Лабинский», включая земельные участки\n'
        '<b>Сумма:</b> 50 млрд ₽\n'
        '<b>Статус:</b> Закрыта · октябрь 2026\n'
        '<b>Отрасль:</b> Агро\n\n'
        '<b>Источник:</b> <a href="https://frankmedia.ru/310918">Frank Media</a>\n\n'
        'Подробнее в <a href="https://projectcompass.ru/#/deal/g97679d43">карточке сделки</a>')


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == DEAL)
    event = next(e for e in deal['events'] if e.get('kind') == KIND)
    assert event['id'] == 'g97679d43-closed'
    if event.get('headline') != HEADLINE:
        assert event.get('headline') == OLD_HEADLINE, event.get('headline')
        assert event['snapshot'].get('asset') == OLD_ASSET, event['snapshot'].get('asset')
        event['headline'] = HEADLINE
        event['snapshot']['asset'] = ASSET
        print('веха: заголовок и предмет заменены')
    draft = {'combo': '%s~%s' % (DEAL, KIND), 'event_id': event['id'], 'text': TEXT,
             'buttons': format_post.render_buttons(deal), 'route': list(channels.channels_for(deal))}
    print(json.dumps(draft, ensure_ascii=False, indent=1))
    if not write:
        print('сухой прогон'); return
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    import httpx
    site = os.environ.get('APP_BASE_URL', 'https://projectcompass.ru').rstrip('/')
    token = os.environ.get('MODERATION_TOKEN') or os.environ.get('TELEGRAM_WEBHOOK_SECRET') or ''
    r = httpx.post('%s/api/ops/milestone-draft' % site, json={'token': token, **draft}, timeout=20)
    print('сайт:', r.status_code, r.text[:200])


if __name__ == '__main__':
    main('--write' in sys.argv)
