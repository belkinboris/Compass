"""Готовая карточка — в консоль сразу, одной командой (28 октября 2026).

Владелец: «почему нельзя по нахождении новости… сделать черновик карты,
пост и отправить создателям?» До этого показ в консоль был последним шагом
длинного прогона притока — и его не делали четыре прогона подряд
(«Ломбард 888» ждал сутки, KNOWN_ISSUES 28 октября 2026). Команда делает
все, что нужно для показа одной карточки, и ничего не оставляет памяти
агента:

  1. `git pull --rebase origin main`;
  2. проверяет, что карточка в очереди прочитана, принята и прочитана второй
     раз (без этого консоль ее не покажет — те же ворота, что в send_drafts);
  3. коммитит очередь и таблицу правок (`static/data/pending.json`,
     `pipeline/ingest/fixes/`) и пушит — очередь не база, полный pytest
     для нее не нужен, хватает быстрых проверок очереди;
  4. ждет, пока сайт подтянет очередь (ссылка на предпросмотр в сообщении
     должна открываться), до WAIT_MIN минут;
  5. `send_drafts.main(write=True, only=<id>)` — 🗂 карточка и 📣 проект
     поста в консоль, затем коммит отметок показа и push.

    python3 pipeline/ingest/ship_card.py <id>            # сухой прогон: что сделает
    python3 pipeline/ingest/ship_card.py <id> --write
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
WAIT_MIN = 12
POLL_S = 30
# Быстрые проверки очереди — те же, что в полном прогоне смотрят на pending.json:
# все инварианты базы (test_data: в том числе pending_since, типы, роли) и
# проверки очереди из test_ingest (таблица правок применена, ворота видят
# очередь, заглушки в посте). Полный pytest остается для записи в базу (шаг 11).
QUICK_TESTS = [
    ['test_data.py', '-q', '-p', 'no:cacheprovider'],
    ['test_ingest.py', '-q', '-p', 'no:cacheprovider', '-k', 'pending or review_table or placeholder or gate_sees or send_plan'],
]


def git(*args, check=True):
    r = subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True)
    if check and r.returncode:
        raise SystemExit('git %s: %s' % (' '.join(args), (r.stderr or r.stdout).strip()[-400:]))
    return r.stdout.strip()


def push_with_retry(tries=4):
    for i in range(tries):
        git('pull', '--rebase', '--autostash', 'origin', 'main')
        r = subprocess.run(['git', 'push', '-u', 'origin', 'main'], cwd=ROOT, capture_output=True, text=True)
        if r.returncode == 0:
            return True
        time.sleep(2 ** (i + 1))
    return False


def card_state(card_id):
    pending = json.load(open(PENDING, encoding='utf-8'))
    card = next((c for c in pending.get('cards') or [] if c['id'] == card_id), None)
    if not card:
        return None, ['карточки %s нет в очереди (pending.json)' % card_id]
    missing = [k for k in ('reviewed', 'accepted', 'second_read') if not card.get(k)]
    return card, (['нет отметки %s' % k for k in missing])


def commit_queue(message):
    git('add', 'static/data/pending.json', 'pipeline/ingest/fixes')
    if not git('status', '--porcelain', '--', 'static/data/pending.json', 'pipeline/ingest/fixes'):
        return False
    git('commit', '-q', '-m', message)
    return True


def wait_for_site(card_id):
    import send_drafts
    deadline = time.time() + WAIT_MIN * 60
    while time.time() < deadline:
        live = send_drafts.site_pending_ids()
        if live is not None and card_id in live:
            return True
        time.sleep(POLL_S)
    return False


def main(argv):
    if not argv or argv[0].startswith('-'):
        print(__doc__)
        return 2
    card_id, write = argv[0], '--write' in argv
    git('pull', '--rebase', '--autostash', 'origin', 'main')   # чужие правки прогона остаются в рабочей копии
    card, problems = card_state(card_id)
    if problems:
        print('НЕ ГОТОВА: ' + '; '.join(problems))
        return 1
    print('Карточка %s «%s» — прочитана, принята, прочитана второй раз.' % (card_id, str(card.get('title') or '')[:70]))
    if card.get('draft_sent') and card.get('post_draft_sent', card.get('draft_sent')):
        print('Уже показана в консоли (draft_sent) — делать нечего.')
        return 0
    if not write:
        print('Сухой прогон: закоммитил бы очередь, запушил, дождался сайта и отправил 🗂/📣 в консоль. Запись — с ключом --write.')
        return 0
    for args in QUICK_TESTS:
        r = subprocess.run([sys.executable, '-m', 'pytest', *args], cwd=ROOT, capture_output=True, text=True)
        if r.returncode:
            print('Быстрые проверки очереди не прошли — не отправляю:\n' + r.stdout[-1500:])
            return 1
    print('Быстрые проверки очереди прошли.')
    if commit_queue('Очередь: карточка %s готова к показу в консоли' % card_id):
        if not push_with_retry():
            print('push не прошел после четырех попыток — консоль не получит ссылку на предпросмотр, стоп.')
            return 1
        print('Очередь запушена.')
    print('Жду, пока сайт подтянет очередь (до %d минут)…' % WAIT_MIN)
    if not wait_for_site(card_id):
        print('Сайт за %d минут карточку не подтянул — отправка отложена; повторите команду позже.' % WAIT_MIN)
        return 1
    import send_drafts
    rc = send_drafts.main(write=True, only=card_id)
    if rc:
        return rc
    if commit_queue('Очередь: карточка %s показана в консоли' % card_id):
        push_with_retry()
    print('ГОТОВО: %s показана в консоли.' % card_id)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
