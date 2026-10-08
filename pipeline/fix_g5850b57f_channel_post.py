"""Пост о СП «Яндекс»/VK (g5850b57f, сообщение 190 основного канала): текст
по решению владельца 8 октября 2026 («можешь менять пост») — участники вместо
покупателя, доли, показатели объединяемых бизнесов (CNews), отчётность
головных компаний (ФНС, РСБУ 2025: МКПАО «ЯНДЕКС» и МКПАО «ВК»). Тот же
текст кладётся в `post_override`, чтобы следующая правка поста рутиной не
вернула старый вид. Без ключа — сухой прогон; --write — правка поста и базы.
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'publish'))
sys.path.insert(0, ROOT)
import format_post        # noqa: E402
import send_telegram      # noqa: E402

DATA = os.path.join(ROOT, 'static/data/deals_promoted.json')
DEAL, MID = 'g5850b57f', 190
TEXT = '\n'.join([
    '<b>«Яндекс» и VK объединяют корпоративные ИТ-направления Yandex B2B Tech и VK Tech</b>',
    '',
    '<b>Участники СП:</b> Яндекс и VK',
    '<b>Предмет:</b> объединение корпоративных ИТ-направлений Yandex B2B Tech и VK Tech',
    '<b>Доли:</b> как разделят доли, пока не решено; один из обсуждаемых вариантов — поровну, по 50% у каждой стороны',
    '<b>Показатели объединяемых бизнесов:</b> Yandex B2B Tech — выручка 28,9 млрд ₽ за первое полугодие 2026 года (+32% год к году), 32,2 млрд ₽ за 2024 год; VK Tech — 9 млрд ₽ за первое полугодие 2026 года (+35,3%)',
    '<b>Финансы МКПАО «ЯНДЕКС», 2025 год:</b> Выручка 88,0 млрд ₽ · Чистая прибыль 825,8 млрд ₽ · Активы 2,73 трлн ₽',
    '<b>Финансы МКПАО «ВК», 2025 год:</b> Чистый убыток 8,7 млрд ₽ · Активы 296,7 млрд ₽ · Капитал 286,0 млрд ₽',
    '<b>Сумма:</b> не раскрывается',
    '<b>Статус:</b> Обсуждается — формальности планируют завершить в первом квартале 2027 года; форма ещё не выбрана, совместное предприятие или слияние',
    '<b>Отрасль:</b> ИТ и интернет',
    '',
    '<b>Источник:</b> <a href="https://www.cnews.ru/news/top/2026-10-08_mintsifry_yandeks_i_vk_sozdadut">CNews</a>',
    'Ещё 1 источник — в карточке сделки',
    '',
    '#технологии #ИТ #СП',
])


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == DEAL)
    assert data['telegram_posts'].get(DEAL) == MID, data['telegram_posts'].get(DEAL)
    assert not deal.get('post_override') or deal['post_override'] == TEXT
    print(TEXT)
    if not write:
        print('\nСухой прогон. Правка поста и записи — с ключом --write.')
        return 0
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    chat = send_telegram.channel_address()
    assert token and chat, 'нет токена или адреса канала'
    import httpx
    with httpx.Client(timeout=20) as client:
        send_telegram.edit_message(client, token, chat, MID, TEXT, buttons=format_post.render_buttons(deal))
    fresh = json.load(open(DATA, encoding='utf-8'))
    live = next(d for d in fresh['deals'] if d['id'] == DEAL)
    live['post_override'] = TEXT
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(fresh, f, ensure_ascii=False, indent=1)
    print('\nПост 190 поправлен, post_override записан.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
