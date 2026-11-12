# -*- coding: utf-8 -*-
"""Вычитка, партия m037 (часть c): правовая форма продавца карточки gfcfba8c9 (ТЦ «Аура» в Ярославле).

Реестр (party_legal_names.py gfcfba8c9, 12 ноября 2026): профиль Renaissance Development сопоставлен с ООО
«Ренессанс Девелопмент», ИНН 7701306504; при записи партии реестр не ответил, и legal_short не встал.

    python3 pipeline/archive/2026-11/reread_m037_c.py [--write]
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reread_m037_engine as engine  # noqa: E402

BY = 'reread_m037'

OPS = []

PROFILES = [{'pid': 'g5bae9612', 'key': 'legal_short', 'old': None, 'new': 'ООО «Ренессанс Девелопмент»'}]

EVENTS = []

RETRACT = []

NOTES = []

ADD_SRC = []

REMOVE_SRC = []

MATCH_KEYS = []

GOLD = []


if __name__ == '__main__':
    sys.exit(engine.run(globals()))
