# -*- coding: utf-8 -*-
"""Показать карточку в консоли ЗАНОВО: снять отметки «черновик отправлен».

ЗАЧЕМ. `send_drafts.py` показывает карточку один раз: отметки `draft_sent` и
`post_draft_sent` защищают консоль от повторов (человек не должен решать одно
и то же дважды). Но если карточку ПЕРЕСОБРАЛИ после показа — как «Базис»/Proto
7 сентября 2026, где по замечанию владельца сменились стороны, тип и предмет —
в консоли висит старый, уже неверный черновик, и решение по нему принималось
бы вслепую. Снять отметки — единственный честный способ показать новое:
переписывать уже отправленное сообщение нельзя, кнопки под ним ведут к тем же
вердиктам, а человек не увидит, что именно изменилось.

Отметки снимаются ТОЛЬКО по явно названным id — не пачкой и не по признаку:
случайный повторный показ всей очереди означал бы десятки лишних сообщений в
группе (см. урок «консоль, куда валят всё, перестают читать»).

Запуск:
    python3 pipeline/resend_console_drafts.py <id> [<id> ...]           # сухой
    python3 pipeline/resend_console_drafts.py <id> [...] --write        # снять
    затем: python3 pipeline/ingest/send_drafts.py --write
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PENDING = ROOT / 'static' / 'data' / 'pending.json'
FLAGS = ('draft_sent', 'post_draft_sent')


def main(ids, write):
    pend = json.loads(PENDING.read_text(encoding='utf-8'))
    cards = {c['id']: c for c in pend['cards']}
    missing = [i for i in ids if i not in cards]
    assert not missing, 'в очереди предпросмотра нет карточек: %s' % ', '.join(missing)
    touched = 0
    for cid in ids:
        card = cards[cid]
        was = {f: card.get(f) for f in FLAGS}
        print(f'{cid}: «{card.get("title")}»')
        print('   отметки показа:', ', '.join(f'{f}={was[f]!r}' for f in FLAGS))
        if not any(was.values()):
            print('   карточку ещё не показывали — снимать нечего')
            continue
        touched += 1
        if write:
            for f in FLAGS:
                card.pop(f, None)
    if not write:
        print('\nСухой прогон. Снять отметки — с ключом --write.')
        return 0
    PENDING.write_text(json.dumps(pend, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'\nОтметки сняты у {touched} карточек. Теперь: '
          'python3 pipeline/ingest/send_drafts.py --write')
    return 0


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(args, '--write' in sys.argv))
