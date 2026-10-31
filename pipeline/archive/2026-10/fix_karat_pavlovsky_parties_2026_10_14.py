"""«Карат» / Павловский молочный завод (g62577a1d) — замечания владельца
14 октября 2026: «покупателем обозначен завод „Карат“… завод не может
приобрести другой завод»; «в предмете написано „с октября 2026 года
принадлежит московскому заводу «Карат»“ — тупо писать в предмете этой
карточки»; заголовок — «одна компания купила завод», без «нарастил
производство».

Покупатель по ТАСС (finance.mail.ru): сделку комментировал «генеральный
директор АО «Карат» Евгений Гребнев… Теперь в структуру компании вошел новый
завод» — то есть покупатель АО «МЗПС «Карат»» (ИНН 7736042394), 100% которого
у ООО «Карат Инвестиции» (ЕГРЮЛ, datanewton.ru). Профиль переименован на
месте из «Завод «Карат»» в «Карат» (та же компания, тот же id).
Продавец: завод — АО «Павловский молочный завод» (ИНН 5252000632), его
акционеров ЕГРЮЛ не показывает; косвенные признаки (семья гендиректора) не
доказательство — продавец остается «не раскрыт», это сказано в карточке.
Карточка снова уходит в консоль на подтверждение. Без ключа — сухой прогон."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'static', 'data', 'pending.json')
B = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
ID, BUYER, ASSET = 'g62577a1d', 'gd2c01a84', 'g2c23e12d'
OLD_TITLE = '«Карат» нарастил производство, купив нижегородский молочный завод «Эго»'
NEW_TITLE = '«Карат» купил Павловский молочный завод (бренд «Эго»)'
OLD_BUYER_DESC_HEAD = ('Московский производитель плавленых и творожных сыров (бренды «Дружба», «Янтарь», '
                       'Violette, «Карат Домашний»), работает с 1934 года.')
NEW_BUYER_DESC_HEAD = ('Московский производитель плавленых и творожных сыров (бренды «Дружба», «Янтарь», '
                       'Violette, «Карат Домашний»), работает с 1934 года. Юрлицо — АО «МЗПС «Карат»» '
                       '(ИНН 7736042394).')
ASSET_DROP = ' С октября 2026 года принадлежит московскому заводу «Карат».'
ASSET_ADD = ' Юрлицо — АО «Павловский молочный завод» (ИНН 5252000632).'
SELLER_NOTE = (' Кто продал завод, стороны не называют: это акционерное общество, а состав его '
               'акционеров в открытом реестре не виден. Гендиректор завода с 2011 года — '
               'Юлия Сергеенкова.')
NEW_SRC = [['ТАСС (через «Финансы Mail»)',
            'https://finance.mail.ru/article/moskovskij-zavod-plavlenyih-syirov-karat-kupil-pavlovskij-molochnyij-zavod-69232447/'],
           ['ЕГРЮЛ (Датаньютон): АО «Павловский молочный завод»',
            'https://datanewton.ru/contragents/1025202120240']]

braw, praw = open(B, encoding='utf-8').read(), open(P, encoding='utf-8').read()
base, pending = json.loads(braw), json.loads(praw)
co = base['companies']
card = next(c for c in pending['cards'] if c['id'] == ID)
assert card['title'] == OLD_TITLE, card['title']
assert co[BUYER]['name'] == 'Завод «Карат»', co[BUYER]['name']
assert co[BUYER]['desc'].startswith(OLD_BUYER_DESC_HEAD)
assert ASSET_DROP in co[ASSET]['desc']
card['title'] = NEW_TITLE
co[BUYER]['name'] = '«Карат»'
co[BUYER]['desc'] = NEW_BUYER_DESC_HEAD + co[BUYER]['desc'][len(OLD_BUYER_DESC_HEAD):]
d = co[ASSET]['desc'].replace(ASSET_DROP, '')
if 'ИНН 5252000632' not in d:
    d = d.replace(' Юрлицо — АО «Павловский молочный завод».', '') + ASSET_ADD
co[ASSET]['desc'] = d
ctx = card['eco'].get('context') or '—'
if 'Кто продал завод' not in ctx:
    card['eco']['context'] = (SELLER_NOTE.strip() if ctx in ('—', '') else ctx.rstrip() + SELLER_NOTE)
have = {s[1] for s in card.get('src') or [] if len(s) > 1}
for s in NEW_SRC:
    if s[1] not in have:
        card.setdefault('src', []).append(s)
for k in ('draft_sent', 'post_draft_sent', 'post_preview'):
    card.pop(k, None)
print('%s: заголовок, покупатель «Карат» (АО «МЗПС «Карат»»), предмет без «принадлежит „Карату“», '
      'оговорка о продавце, 2 источника; к повторной отправке' % ID)
print(' профиль покупателя:', co[BUYER]['desc'][:200])
print(' профиль завода:', co[ASSET]['desc'])
if '--write' in sys.argv:
    for path, obj, raw in ((B, base, braw), (P, pending, praw)):
        out = json.dumps(obj, ensure_ascii=False, indent=1)
        open(path, 'w', encoding='utf-8').write(out + ('\n' if raw.endswith('\n') else ''))
    print('записано')
