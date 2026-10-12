"""Два PDF на одну страницу в стиле сайта: для консультантов и для компаний.

    python3 finance/партнёры/pdf/build.py

Текст — тот же, что в `консультанты.md` и `компании.md`; цена и срок — в
TERMS ниже, одной строкой.
"""
import asyncio
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(HERE, '..')
CHROMIUM = '/opt/pw-browsers/chromium'

TERMS = ('До 31 декабря 2026 — бесплатно', '2027 год — 50 000 ₽ за всё',
         'цена зафиксирована для подключившихся в 2026 году')

AUDIENCES = {
    'консультантов': dict(
        nav='Консультанты',
        h1='Страница фирмы в «Компасе»',
        lead='Сделки, где фирма названа консультантом, уже описаны. Партнёр получает оформленную страницу, доступ к базе для команды и место в канале.',
        cols=[
            ('Что получает фирма', [
                'Страница: логотип, описание, контакты, команда. Подсветка в каталоге.',
                'Все сделки фирмы на одной странице — и те, что она раскроет сама.',
                'Материалы под именем фирмы: колонки, комментарии, вебинары.',
                'Доступ к базе для команды: фильтры, выгрузки, подписки, ассистент.',
                'Пост о фирме в канале. Статистика раз в месяц.',
            ]),
            ('Что нужно от фирмы', [
                'Логотип, описание в 3–5 предложений, сайт и контакт.',
                'Согласовать макет страницы — присылаем PDF.',
                'Подписать соглашение о размещении, две страницы.',
            ]),
            ('Чего не нужно', [
                'Сообщать о сделках. База собирается из открытых источников; фирма раскрывает сверх этого только то, что хочет.',
                'Проверять упоминания: по просьбе фирмы поправим или уберём в тот же день.',
            ]),
        ],
    ),
    'компаний': dict(
        nav='Компании',
        h1='Страница компании в «Компасе»',
        lead='По странице компании к встрече с ней готовятся консультанты, инвесторы и покупатели. Лучше, когда на ней то, что компания хочет о себе сказать.',
        cols=[
            ('Что получает компания', [
                'Страница: логотип, описание, сайт, контакт для инвесторов и партнёров.',
                'Все сделки компании с её ролью — и те, что она раскроет сама.',
                'Финансы из отчётности с комментарием компании.',
                'Новости компании — как источник её сделок.',
                'Пост в канале. Видно, кто следит за компанией.',
            ]),
            ('Что нужно от компании', [
                'Логотип, описание в 3–5 предложений, сайт и контакт.',
                'Согласовать макет страницы — присылаем PDF.',
                'Подписать соглашение о размещении, две страницы.',
            ]),
            ('Для команды', [
                'Кто покупает и продаёт в вашей отрасли — с суммами и источниками.',
                'Кто консультирует конкурентов и партнёров.',
                'Подписки на компании и отрасли, выгрузки, ассистент.',
            ]),
        ],
    ),
}

FONTS = """
@font-face{font-family:'Commissioner';src:url(fonts/commissioner-cyrillic.woff2) format('woff2');font-weight:100 900;unicode-range:U+0301,U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116}
@font-face{font-family:'Commissioner';src:url(fonts/commissioner-latin.woff2) format('woff2');font-weight:100 900}
@font-face{font-family:'PT Serif Compass';src:url(fonts/PTSerif-Bold.ttf) format('truetype');font-weight:700}
"""

CSS = """
@page{size:A4;margin:0}
*{box-sizing:border-box}
:root{--paper:#F5F5F1;--card:#fff;--ink:#15191D;--muted:#66707A;--line:#E2E5DF;--accent:#1D5A44;--accent-deep:#0F2B21;--accent-soft:#E9F0EC;--ivory:#F3F1E9;--bronze:#A3814E;--bronze-light:#C9AE7C}
html,body{margin:0}
body{font-family:'Commissioner',system-ui,sans-serif;color:var(--ink);font-size:11pt;line-height:1.5;background:#fff}
.page{width:210mm;height:297mm;background:var(--paper);position:relative;overflow:hidden;display:flex;flex-direction:column}
.top{background:#fff;border-bottom:1px solid var(--line);padding:14px 18mm;display:flex;align-items:center;gap:30px}
.logo{display:inline-flex;align-items:center;gap:9px;font-family:'PT Serif Compass',Georgia,serif;font-weight:700;font-size:20px;letter-spacing:.02em}
.logo b{color:var(--bronze)}
.nav{display:flex;gap:22px;font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.nav .on{color:var(--ink);border-bottom:2px solid var(--accent);padding-bottom:3px}
.body{padding:16mm 18mm 0;flex:1}
.kicker{font-size:10px;font-weight:600;letter-spacing:.2em;text-transform:uppercase;color:var(--accent)}
h1{font-family:'PT Serif Compass',Georgia,serif;font-weight:700;font-size:30pt;line-height:1.12;margin:10px 0 12px;max-width:150mm}
.lead{font-size:12.5pt;line-height:1.5;color:#3C434A;margin:0;max-width:150mm}
.cols{display:grid;grid-template-columns:1.25fr 1fr 1fr;gap:12px;margin-top:22px}
.card{background:var(--card);border:1px solid var(--line);border-radius:4px;padding:18px 18px 14px;position:relative;overflow:hidden}
.card:before{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--accent)}
.label{display:block;font-size:9.5px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin-bottom:10px}
ul{margin:0;padding:0;list-style:none}
li{padding:6px 0;border-top:1px solid var(--line);font-size:10.5pt;line-height:1.42}
li:first-child{border-top:0;padding-top:0}
.terms{margin:22px 0 0;background:linear-gradient(160deg,#0A1210 0%,#0F2B21 100%);color:var(--ivory);border-radius:4px;padding:20px 24px;display:grid;grid-template-columns:1fr 1fr 1.3fr;gap:18px}
.terms .label{color:var(--bronze-light);margin-bottom:6px}
.terms b{font-family:'PT Serif Compass',Georgia,serif;font-size:16pt;line-height:1.2;display:block}
.terms span{font-size:10.5pt;color:#C9C4B4;line-height:1.4;display:block}
.foot{padding:12px 18mm 14mm;display:flex;justify-content:space-between;font-size:10pt;color:var(--muted);border-top:1px solid var(--line)}
"""

MARK = ('<svg viewBox="0 0 48 48" width="22" height="22" fill="none" aria-hidden="true"><circle cx="24" cy="24" r="21" stroke="#15191D" stroke-width="2.6"/>'
        '<g transform="rotate(-38 24 24)"><polygon points="24,5 28.5,24 19.5,24" fill="#A3814E"/><polygon points="24,43 28.5,24 19.5,24" fill="#15191D"/></g>'
        '<circle cx="24" cy="24" r="3.2" fill="#fff" stroke="#15191D" stroke-width="1.6"/></svg>')
NAV = ['Сделки', 'Компании', 'Консультанты', 'Материалы', 'Аналитика', 'Ассистент']


def numbers():
    d = json.load(open(os.path.join(ROOT, 'static', 'data', 'deals_promoted.json'), encoding='utf-8'))
    r = lambda n: '{:,}'.format(int(n // 50 * 50)).replace(',', ' ')
    return r(len(d['deals'])), r(len(d['companies']))


def page(a, deals, comps):
    nav = ''.join(f'<span class="{"on" if x == a["nav"] else ""}">{x}</span>' for x in NAV)
    cols = ''.join(f'<div class="card"><span class="label">{t}</span><ul>' + ''.join(f'<li>{x}</li>' for x in items) + '</ul></div>'
                   for t, items in a['cols'])
    return f"""<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>{a['h1']}</title><style>{FONTS}{CSS}</style></head><body>
<section class="page">
  <header class="top"><span class="logo">{MARK}<span>КО<b>М</b>П<b>А</b>С</span></span><nav class="nav">{nav}</nav></header>
  <div class="body">
    <span class="kicker">Для партнёров · {deals} сделок · {comps} компаний</span>
    <h1>{a['h1']}</h1>
    <p class="lead">{a['lead']}</p>
    <div class="cols">{cols}</div>
    <div class="terms">
      <div><span class="label">Срок</span><b>{TERMS[0]}</b></div>
      <div><span class="label">Дальше</span><b>{TERMS[1]}</b></div>
      <div><span class="label">Условие</span><span style="padding-top:4px">{TERMS[2][0].upper() + TERMS[2][1:]}. Отказаться можно в любой момент до начала платного периода.</span></div>
    </div>
  </div>
  <footer class="foot"><span>projectcompass.ru · t.me/projectcompassru</span><span>Проект «Компас» · 2026</span></footer>
</section></body></html>"""


async def main():
    from playwright.async_api import async_playwright
    deals, comps = numbers()
    async with async_playwright() as p:
        br = await p.chromium.launch(executable_path=CHROMIUM if os.path.exists(CHROMIUM) else None)
        for key, a in AUDIENCES.items():
            src = os.path.join(HERE, f'{key}.html')
            open(src, 'w', encoding='utf-8').write(page(a, deals, comps))
            pg = await br.new_page()
            await pg.goto('file://' + src)
            await pg.evaluate('document.fonts.ready'); await pg.wait_for_timeout(300)
            out = os.path.join(OUT, f'Компас_для_{key}.pdf')
            await pg.pdf(path=out, format='A4', print_background=True, prefer_css_page_size=True)
            await pg.screenshot(path=os.path.join(HERE, f'{key}.png'), full_page=True)
            print(out, os.path.getsize(out) // 1024, 'KB')
            await pg.close()
        await br.close()


if __name__ == '__main__':
    asyncio.run(main())
