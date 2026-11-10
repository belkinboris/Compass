"""«Медприбор» (gb89d3a84): первоисточник — «Коммерсантъ» (kommersant.ru/doc/9092327),
на него ссылается заметка mergers.ru. Ставим его первым в src, а в посте вместо
«Источник: Mergers.ru» — «Коммерсантъ» (сообщение в канале правится editMessageText,
подписчиков не будит; кнопка передается заново).

Владелец, 10 ноября 2026: «статья mergers отсылает на статью коммерсанта».
Без ключей — сухой прогон; --write — база; --edit — вышедшее сообщение."""
import json, os, sys
sys.path.insert(0, 'pipeline/publish'); sys.path.insert(0, 'pipeline')
import format_post, send_telegram  # noqa: E402
DATA, ID = 'static/data/deals_promoted.json', 'gb89d3a84'
KOM = ['Коммерсантъ', 'https://www.kommersant.ru/doc/9092327']
MRG = 'https://mergers.ru/news/Kompaniya-Medpribor-priobrela-krupnogo-postavschika-medicinskogo-oborudovaniya-VTS-87755'
OLD_SRC = '<b>Источник:</b> <a href="%s">Mergers.ru</a>' % MRG
NEW_SRC = '<b>Источник:</b> <a href="%s">Коммерсантъ</a>' % KOM[1]


def apply(deal):
    assert [s[1] for s in deal['src']] == ['https://vademec.ru/news/2026/11/09/svyazannaya-s-iclinic-kompaniya-'
                                           'priobrela-rossiyskogo-partnera-siemens-healthineers/'], deal['src']
    assert OLD_SRC in deal['post_override']
    deal['src'] = [KOM] + deal['src']
    deal['post_override'] = deal['post_override'].replace(OLD_SRC, NEW_SRC)


data = json.load(open(DATA, encoding='utf-8'))
deal = next(d for d in data['deals'] if d['id'] == ID)
msg = data['telegram_posts'].get(ID)
probe = json.loads(json.dumps(deal)); apply(probe)
print(probe['post_override']); print('сообщение в канале:', msg)
if '--write' in sys.argv:
    data = json.load(open(DATA, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == ID)
    apply(deal)
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1); f.write('\n')
    print('записано')
if '--edit' in sys.argv:
    import httpx
    data = json.load(open(DATA, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == ID)
    assert NEW_SRC in deal['post_override']
    with httpx.Client(timeout=30) as client:
        send_telegram.edit_message(client, os.environ['TELEGRAM_BOT_TOKEN'], send_telegram.channel_address(),
                                   msg, deal['post_override'], format_post.render_buttons(deal))
    print('сообщение', msg, 'исправлено')
