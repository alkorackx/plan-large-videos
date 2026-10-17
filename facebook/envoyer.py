"""Envoie à Make les Reels Facebook arrivés à leur heure (lancé toutes les 15 min par GitHub Actions).

`facebook/file.json` : liste de {slug, quand (horodatage Unix), file_url, description}, remplie par
`programmer.py` (dépôt cliper). Make publie la vidéo sur la Page « Le Plan Large » dès réception.
Une entrée envoyée reçoit `envoye` ; après 5 échecs, elle est abandonnée (`abandon`).
"""
import json
import os
import time
import urllib.request
from pathlib import Path

FILE = Path(__file__).with_name("file.json")
PAGE_ID = "1312640408607407"
ESSAIS_MAX = 5

file = json.loads(FILE.read_text(encoding="utf-8"))
maintenant = time.time()
for e in file:
    if e.get("envoye") or e.get("abandon") or e["quand"] > maintenant:
        continue
    corps = {"page_id": PAGE_ID, "slug": e["slug"], "file_url": e["file_url"], "description": e["description"],
             "scheduled_publish_time": e["quand"]}
    req = urllib.request.Request(os.environ["MAKE_WEBHOOK"], data=json.dumps(corps).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "x-make-apikey": os.environ["MAKE_APIKEY"]})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            r.read()
        e["envoye"] = int(time.time())
        print("envoyé :", e["slug"])
    except Exception as err:                       # noqa: BLE001 — on note l'échec et on réessaie au prochain passage
        e["essais"] = e.get("essais", 0) + 1
        if e["essais"] >= ESSAIS_MAX:
            e["abandon"] = True
        print("échec :", e["slug"], err)
FILE.write_text(json.dumps(file, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
