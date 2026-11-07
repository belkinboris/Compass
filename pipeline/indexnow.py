# -*- coding: utf-8 -*-
"""Отправить адреса сайта в Яндекс по протоколу IndexNow (7 ноября 2026).

ЗАЧЕМ. В Яндекс Вебмастере раздел «Файлы Sitemap» у Яндекса переведен в режим «только
для чтения» — добавить карту сайта или отправить ее на переобход владелец не может.
IndexNow — открытый протокол, который Яндекс принимает напрямую: сайт подтверждает
право ключом в корне сайта (/<KEY>.txt, маршрут в app/site.py),
и адреса уходят на переобход без Вебмастера. За раз — до 10 000 адресов.

    python3 pipeline/indexnow.py            # сухой прогон: сколько адресов уйдет
    python3 pipeline/indexnow.py --write    # отправить все адреса из живого sitemap.xml
"""
import json
import re
import sys
import urllib.request

HOST = 'projectcompass.ru'
KEY = 'eb72eb6f35d87d366278454f3772a60d'
KEY_LOCATION = 'https://%s/%s.txt' % (HOST, KEY)   # только корень: ключ в подпапке Яндекс отвергает (422)
ENDPOINT = 'https://yandex.com/indexnow'
UA = 'Mozilla/5.0 (compatible; KompasIndexNow/1.0)'


def sitemap_urls():
    req = urllib.request.Request('https://%s/sitemap.xml' % HOST, headers={'User-Agent': UA})
    xml = urllib.request.urlopen(req, timeout=60).read().decode('utf-8')
    return re.findall(r'<loc>([^<]+)</loc>', xml)


def submit(urls):
    body = json.dumps({'host': HOST, 'key': KEY, 'keyLocation': KEY_LOCATION, 'urlList': urls}).encode()
    req = urllib.request.Request(ENDPOINT, data=body, method='POST',
                                 headers={'Content-Type': 'application/json; charset=utf-8', 'User-Agent': UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode('utf-8', 'replace')[:300]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')[:300]


def main(argv):
    urls = sitemap_urls()
    print('адресов в sitemap.xml: %d' % len(urls))
    if '--write' not in argv:
        print('Сухой прогон. Отправка — с ключом --write.')
        return 0
    for i in range(0, len(urls), 10000):
        status, text = submit(urls[i:i + 10000])
        print('пачка %d: ответ %s %s' % (i // 10000 + 1, status, text))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
