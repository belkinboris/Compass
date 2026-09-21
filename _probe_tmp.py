# -*- coding: utf-8 -*-
"""Проверка: останется ли строка читателя применённой после нашей правки."""
import json, sys
ROOT="/home/user/Compass"
sys.path.insert(0, ROOT); sys.path.insert(0, ROOT+"/pipeline/ingest")
import review
from pipeline.fix_audit_move_utils import get_field, set_field
data=json.loads(open(ROOT+"/static/data/deals_promoted.json",encoding="utf-8").read())
cards={d["id"]:d for d in data["deals"]}; companies=data["companies"]

def probe(cid, field, new):
    card=cards[cid]
    old=get_field(card, field) if "." in field else card.get(field)
    if "." in field: set_field(card, field, new)
    else: card[field]=new
    bad=[]
    for row in review.FIXES:
        if row["id"]!=cid or row.get("field")!=field: continue
        if not review.already_applied(row, card, companies):
            bad.append(row.get("new"))
    if "." in field: set_field(card, field, old)
    else: card[field]=old
    print(("OK  " if not bad else "БЛОК"), cid, field, "| строк-блокеров:", len(bad))
    for b in bad: print("      ", json.dumps(b, ensure_ascii=False)[:160])

for args in [
  ("g7ea48d66","eco.sum","XX"),
  ("g0431fc51","eco.sum","1–1,5 млрд ₽ (по оценке)"),
  ("gmru-kolomenskoe-peko","eco.sum","800–900 млн ₽ (по оценке)"),
  ("gdfce7e3d","eco.sum","4,3–4,8 млрд ₽ (по оценке)"),
  ("gf6be51a1","law.terms","XX"),
  ("ge3bc7c98","law.terms","—"),
  ("ge3bc7c98","eco.context","XX"),
  ("ce1b2321f","asset","XX"),
  ("gb70b4830","law.struct","XX"),
  ("g8ff9bdf8","eco.context","XX"),
  ("g8ff9bdf8","eco.val","XX"),
  ("g39527843","eco.target_fin","—"),
  ("g39527843","eco.context","XX"),
  ("gadbed4b9","law.terms","XX"),
  ("g0a0d451a","eco.rationale","—"),
  ("g0a0d451a","law.appr","XX"),
  ("ga58cd8e7","eco.context","XX"),
  ("ge8f111a2","law.struct","XX"),
  ("gb1b7478f","law.appr","—"),
  ("gb1b7478f","law.struct","XX"),
  ("g1f098415","eco.share","—"),
  ("g1f098415","eco.target_fin","XX"),
  ("g1f098415","eco.context","XX"),
  ("gmru-dobroflot-ikorny","eco.share","—"),
  ("gcface540","eco.target_fin","XX"),
  ("gcface540","extra","XX"),
]:
    probe(*args)
