# -*- coding: utf-8 -*-
"""Шерегеш (g03475792), 3 ноября 2026, по прямому «да» владельца: пост 253
(ушел без его кнопки, с текстом консоли) владелец удалил; публикуем его текст —
ответ на новый проект поста — новым постом в основном канале и записываем номер.

    python3 pipeline/archive/2026-11/post_sheregesh_owner_text_2026_11_03.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path[:0] = [os.path.join(ROOT, 'pipeline', 'publish'), os.path.join(ROOT, 'pipeline'), ROOT]
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
OWNER = ('<b>Компания из ОАЭ получила контроль над ООО «Каскад восток»</b>\n\n'
         '<b>Покупатель:</b> «Рокет Фандс Инвестмент Ин Коммершиал Энтерпрайзис Энд Менеджмент Л.Л.К» — '
         'компания, зарегистрированная в ОАЭ.\n'
         '<b>Продавец:</b> Татьяна Прокудина\n'
         '<b>Предмет:</b> ООО «Каскад восток» — оператор большинства горнолыжных подъемников и трасс '
         'курорта Шерегеш в Кузбассе.\n'
         '<b>Статус:</b> Закрыта · ноябрь 2026\n'
         '<b>Отрасль:</b> Гостиницы и туризм\n\n'
         '<b>Источник:</b> <a href="https://ngs24.ru/text/business/2026/11/03/76741240/">Ngs24.ru</a>\n\n'
         '#недвижимость #гостиницы #MA')


def main(argv):
    import send_telegram as st, format_post, check_post, httpx
    data = json.load(open(BASE, encoding='utf-8'))
    c = [d for d in data['deals'] if d['id'] == 'g03475792'][0]
    assert data['telegram_posts'].get('g03475792') == 253
    text = format_post.with_card_link(OWNER, c)
    assert not check_post.check(text), check_post.check(text)
    print(text)
    if '--write' not in argv:
        print('\nСухой прогон. Публикация — с ключом --write.')
        return
    token = os.environ['TELEGRAM_BOT_TOKEN'].strip()
    main_chat = st.channel_address(st.site_channels())
    with httpx.Client(timeout=30) as cl:
        r = st.post_message(cl, token, main_chat, text, format_post.render_buttons(c))
    mid = (r or {}).get('result', {}).get('message_id') if isinstance(r, dict) else r
    assert mid, r
    fresh = json.load(open(BASE, encoding='utf-8'))
    fc = [d for d in fresh['deals'] if d['id'] == 'g03475792'][0]
    fc['post_override'] = OWNER
    fc['post_approved'] = True
    fresh['telegram_posts']['g03475792'] = mid
    open(BASE, 'w', encoding='utf-8').write(json.dumps(fresh, ensure_ascii=False, indent=1) + '\n')
    print('\nопубликовано: сообщение %s' % mid)


if __name__ == '__main__':
    main(sys.argv[1:])
