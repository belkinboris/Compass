"""«Предмет» поста об этапе — общество и доля (вынесено из review.py: потолок файла)."""
import re


_LEGAL_ENTITY_IN_TEXT = re.compile(r'(?:ООО|АО|ПАО|НАО|ЗАО|ОАО|МКПАО|МКАО)\s+«')


def snapshot_subject(card, companies):
    """«Предмет» поста об этапе — юрлицо и доля, как в основном посте
    (владелец, 12 ноября 2026: «с названием общества корректным и количеством
    доли/акций»). Пост об этапе «Библио-Глобуса» вышел с «Предмет: Туроператор
    БГ» — именем профиля, а не обществом и долей. Порядок: запись доли,
    называющая общество (`eco.share`), затем `asset`, если он называет
    общество, затем имя профиля предмета, затем `asset` как есть."""
    share = str((card.get('eco') or {}).get('share') or '').strip()
    if share and len(share) <= 120 and _LEGAL_ENTITY_IN_TEXT.search(share):
        return share
    asset = str(card.get('asset') or '').strip()
    if asset and _LEGAL_ENTITY_IN_TEXT.search(asset):
        return re.sub(r'\s*\([^()]*\)\s*$', '', asset)
    cid = card.get('target')
    if cid and cid in companies:
        return companies[cid].get('name') or card.get('asset')
    return card.get('asset')
