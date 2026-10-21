"""«Шереметьево»/«Библио-Глобус» (g4afd35d0) — источники и претенденты, 22 октября 2026.

Партнёр: «Добавь все источники, которые нашёл. Про WB и других претендентов
напиши в контексте сделки». Рутина «тема Клод» это сделала, но не смогла
записать в репозиторий — повторено здесь.
Цитаты (Эксперт, пересказ РБК): «Среди возможных покупателей собеседники издания
назвали Wildberries & Russ (RWB)»; «покупку доли обсуждают в том числе структуры,
связанные с Wildberries & Russ»; «Другой источник отметил, что круг претендентов не
ограничивается одним участником»; «В пресс-службе аэропорта отказались от
комментариев». AEX: «средства от возможной сделки могут направить на выкуп
блокирующего пакета акций самого аэропорта в рамках приватизации».
The Insider не добавлен: организация признана в РФ нежелательной — решение за
владельцем. Без ключа — сухой прогон.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
OLD_CTX = 'В августе аэропорт Шереметьево исключили из перечня стратегических предприятий.'
NEW_CTX = (OLD_CTX + ' По данным РБК, покупку доли обсуждают в том числе структуры, связанные с Wildberries & Russ '
           '(RWB); другой собеседник издания говорит, что претендент не один. Официально покупатель не назван, '
           'в пресс-службе аэропорта от комментариев отказались. Деньги от продажи, по данным РБК, могут пойти на '
           'выкуп блокирующего пакета акций самого аэропорта в рамках его приватизации.')
SRC = [['РБК', 'https://www.rbc.ru/business/21/10/2026/6a984fb19a794798cb018b5c'],
       ['Эксперт', 'https://expert.ru/news/rbk-uznal-o-planakh-sheremetevo-prodat-75-biblio-globusa'],
       ['БИЗНЕС Online', 'https://www.business-gazeta.ru/news/713997'],
       ['AEX.RU', 'https://www.aex.ru/news/2026/10/21/300699/']]


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    d = next(x for x in data['deals'] if x['id'] == 'g4afd35d0')
    if d['eco'].get('context') != NEW_CTX:
        assert d['eco'].get('context') == OLD_CTX, d['eco'].get('context')
        d['eco']['context'] = NEW_CTX
    have = {s[1] for s in d['src']}
    d['src'] += [s for s in SRC if s[1] not in have]
    print(d['eco']['context']); print(d['src'])
    if write:
        with open(DATA, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
            f.write('\n')


if __name__ == '__main__':
    main('--write' in sys.argv)
