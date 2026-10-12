"""PDF «Компас для консультантов» — условия размещения на двух страницах.

Собирает `index.html` рядом и печатает его в `../Компас_для_консультантов.pdf`
предустановленным Chromium (Playwright). Текст — тот же, что в
`02_условия_размещения.md`; меняя цену или состав там, менять и здесь.

    python3 finance/партнёры/pdf/build.py
"""
import asyncio
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
OUT_HTML = os.path.join(HERE, 'index.html')
OUT_PDF = os.path.join(HERE, '..', 'Компас_для_консультантов.pdf')
CHROMIUM = '/opt/pw-browsers/chromium'


def base_numbers():
    data = json.load(open(os.path.join(ROOT, 'static', 'data', 'deals_promoted.json'), encoding='utf-8'))
    deals, comps = len(data['deals']), len(data['companies'])
    round50 = lambda n: int(n // 50 * 50)
    return '{:,}'.format(round50(deals)).replace(',', ' '), '{:,}'.format(round50(comps)).replace(',', ' ')


FONTS = ''.join(
    "@font-face{font-family:'Manrope';src:url(fonts/manrope-%s-%d-normal.woff2) format('woff2');"
    "font-weight:%d;unicode-range:%s}" % (sub, w, w,
        'U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD'
        if sub == 'latin' else 'U+0301,U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116')
    for w in (400, 500, 600, 700) for sub in ('latin', 'cyrillic'))

CSS = """
@page{size:A4;margin:0}
*{box-sizing:border-box}
:root{--bg:#FFFCEF;--ink:#030303;--mut:#6E6A62;--line:#E5E3D1;--wine:#64181C;--sand:#F5F4E6;--bronze:#9A6B2F}
html,body{margin:0;background:#fff}
body{font-family:'Manrope',system-ui,sans-serif;color:var(--ink);font-size:11.5pt;line-height:1.5}
.page{width:210mm;height:297mm;padding:18mm 20mm 16mm;background:var(--bg);page-break-after:always;position:relative;overflow:hidden}
.page:last-child{page-break-after:auto}
.hd{display:flex;justify-content:space-between;align-items:baseline;border-bottom:1px solid var(--line);padding-bottom:8px}
.word{font-weight:700;font-size:15pt;letter-spacing:.14em;text-transform:uppercase}
.word b{color:var(--bronze)}
.hd .n{font-size:9pt;color:var(--mut)}
h1{font-size:26pt;line-height:1.1;letter-spacing:-.02em;margin:22px 0 6px;font-weight:700}
.lead{font-size:12.5pt;line-height:1.5;color:#3C3A35;margin:0 0 18px;max-width:150mm}
h2{font-size:10pt;letter-spacing:.12em;text-transform:uppercase;color:var(--wine);margin:18px 0 8px;font-weight:600}
.nums{display:flex;gap:14px;margin:0 0 6px}
.num{flex:1;background:var(--sand);border:1px solid var(--line);padding:10px 14px}
.num .v{font-size:20pt;font-weight:700;letter-spacing:-.02em;line-height:1.1}
.num .l{font-size:9pt;color:var(--mut);margin-top:3px}
ul{margin:0;padding-left:0;list-style:none}
li{position:relative;padding-left:16px;margin:0 0 6px}
li:before{content:'';position:absolute;left:0;top:.6em;width:7px;height:7px;background:var(--wine);border-radius:50%}
li b{font-weight:600}
.two{display:flex;gap:22px}
.two>div{flex:1}
.price{background:var(--ink);color:#fff;padding:16px 18px;margin:8px 0 0}
.price .big{font-size:20pt;font-weight:700;letter-spacing:-.02em;line-height:1.1}
.price .s{color:#C9C4B4;font-size:10pt;margin-top:6px}
.price .fix{color:var(--bronze);font-weight:600;margin-top:10px;font-size:10.5pt}
.ft{position:absolute;left:20mm;right:20mm;bottom:12mm;display:flex;justify-content:space-between;font-size:9pt;color:var(--mut);border-top:1px solid var(--line);padding-top:8px}
p{margin:0 0 8px}
.small{font-size:10pt;color:var(--mut)}
"""


def html(deals, comps):
    return f"""<!doctype html><html lang="ru"><head><meta charset="utf-8">
<title>Компас для консультантов</title><style>{FONTS}{CSS}</style></head><body>
<section class="page">
  <div class="hd"><span class="word">КО<b>М</b>П<b>А</b>С</span><span class="n">projectcompass.ru · для консультантов</span></div>
  <h1>Страница фирмы там, где ищут сделки</h1>
  <p class="lead">«Компас» — база сделок M&amp;A на российском рынке. Сделки, где ваша фирма названа консультантом, уже описаны; фирма-партнёр получает оформленную страницу, доступ к базе для команды и место в канале.</p>
  <div class="nums">
    <div class="num"><div class="v">{deals}</div><div class="l">сделок, основной массив с 2022 года</div></div>
    <div class="num"><div class="v">{comps}</div><div class="l">компаний с финансами из отчётности</div></div>
    <div class="num"><div class="v">каждый день</div><div class="l">новые сделки из открытых источников</div></div>
  </div>
  <h2>Что получает фирма-партнёр</h2>
  <ul>
    <li><b>Страница фирмы в каталоге консультантов.</b> Логотип и фирменные цвета, описание, сайт, контакты, по желанию — команда. Фирма подсвечена в общем списке.</li>
    <li><b>Все сделки фирмы в одном месте.</b> Сделки из открытых источников уже привязаны; сделки, которые фирма решит раскрыть, добавим в согласованном объёме. На каждой карточке фирма названа консультантом со ссылкой на её страницу.</li>
    <li><b>Материалы под именем фирмы.</b> Колонки, комментарии к сделкам, записи вебинаров — каждый подписан автором и фирмой.</li>
    <li><b>Доступ к базе для команды.</b> Фильтры по отраслям, годам, статусам и суммам; выгрузки в таблицу и PDF; подписки на компании и отрасли с уведомлениями в Telegram; ассистент, который отвечает на вопросы по базе обычным языком.</li>
    <li><b>Канал.</b> Пост о фирме при подключении; в постах о сделках фирмы она названа консультантом.</li>
    <li><b>Статистика.</b> Просмотры страницы и сделок фирмы, посещаемость сайта — раз в месяц и по запросу.</li>
  </ul>
  <h2>Зачем это консультанту</h2>
  <ul>
    <li>Видеть, кто ещё работает с вашими клиентами, и какие компании вашей отрасли выходят на сделки.</li>
    <li>Показывать свои сделки там, где их ищут: страница строится из сделок со сторонами, суммами и источниками, а не из анкеты.</li>
    <li>Готовиться к встрече с компанией за десять минут: сделки, собственники, финансы — на одном экране.</li>
  </ul>
  <div class="ft"><span>Проект «Компас» · 2026</span><span>1 / 2</span></div>
</section>
<section class="page">
  <div class="hd"><span class="word">КО<b>М</b>П<b>А</b>С</span><span class="n">условия размещения</span></div>
  <h1>Условия для первых партнёров</h1>
  <div class="two">
    <div>
      <h2>Срок и цена</h2>
      <div class="price">
        <div class="big">До 31 декабря 2026 — бесплатно</div>
        <div class="s">для фирм, подключившихся в 2026 году</div>
        <div class="big" style="margin-top:14px">2027 год — 50 000 ₽</div>
        <div class="s">всё включено, один платёж за год по счёту</div>
        <div class="fix">Цена зафиксирована для подключившихся до конца 2026 года и не меняется, если прайс 2027 года окажется выше.</div>
      </div>
      <p class="small" style="margin-top:10px">Отказаться можно в любой момент до начала платного периода. Страница тогда остаётся в базовом виде — название, сайт и сделки из открытых источников, как у любого консультанта в каталоге.</p>
    </div>
    <div>
      <h2>Что нужно от фирмы</h2>
      <ul>
        <li>Логотип (SVG или PNG) и фирменные цвета, если есть.</li>
        <li>Описание фирмы, 3–5 предложений.</li>
        <li>Сайт и контакт для связи по материалам и правкам.</li>
        <li>По желанию — команда для страницы и сделки, которые хотите показать.</li>
        <li>Согласовать макет страницы (присылаем PDF) и подписать короткое соглашение о размещении.</li>
      </ul>
      <h2>Чего не требуется</h2>
      <ul>
        <li><b>Сообщать о сделках.</b> База наполняется из открытых источников; фирма раскрывает сверх этого только то, что хочет.</li>
        <li><b>Проверять упоминания.</b> По просьбе фирмы поправим или уберём упоминание, если источник ошибся, — в тот же день.</li>
        <li><b>Эксклюзив.</b> Размещаться где-то ещё можно.</li>
      </ul>
    </div>
  </div>
  <h2>Как это происходит</h2>
  <ul>
    <li>Присылаем макет страницы фирмы: как она выглядит в списке консультантов, на компьютере и на телефоне. Вносим правки.</li>
    <li>Получаем материалы и подписанное соглашение — публикуем страницу в течение 10 рабочих дней и пишем о фирме в канале.</li>
    <li>Раз в месяц присылаем статистику. В декабре — счёт на 2027 год; решение принимается по цифрам.</li>
  </ul>
  <h2>Контакты</h2>
  <p>Сайт: projectcompass.ru · Канал: t.me/projectcompassru</p>
  <div class="ft"><span>Проект «Компас» · 2026</span><span>2 / 2</span></div>
</section>
</body></html>"""


async def render():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        br = await p.chromium.launch(executable_path=CHROMIUM if os.path.exists(CHROMIUM) else None)
        pg = await br.new_page()
        await pg.goto('file://' + OUT_HTML)
        await pg.wait_for_timeout(300)
        await pg.pdf(path=OUT_PDF, format='A4', print_background=True, prefer_css_page_size=True)
        await br.close()


if __name__ == '__main__':
    deals, comps = base_numbers()
    with open(OUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html(deals, comps))
    asyncio.run(render())
    print('PDF:', os.path.abspath(OUT_PDF))
