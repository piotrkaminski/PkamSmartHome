# Read-only: matches every channel binding in orzechowa.items to the Things that
# exist in openHAB, and lists Things no item uses. Changes nothing on the Pi.
# Run from the dev machine (needs ~/.openhab-token on the Pi):
#   ssh pkam-pi 'python3 -' < .agents/skills/pkam-deploy/check-item-things.py
# Output: OK / MISSING (no Thing or channel) / NULL (Thing there, no state yet)
# per item, then INFO lines for unused Things.
import json, os, re, urllib.request

REPO = os.path.expanduser("~/PkamSmartHome")
TOKEN = open(os.path.expanduser("~/.openhab-token")).read().strip()


def get(path):
    req = urllib.request.Request("http://localhost:8080/rest/" + path,
                                 headers={"Authorization": "Bearer " + TOKEN})
    return json.load(urllib.request.urlopen(req, timeout=30))


things = {t["UID"]: t for t in get("things")}
channels = {c["uid"] for t in things.values() for c in t.get("channels", [])}
states = {i["name"]: i["state"] for i in get("items")}
used = set()
for line in open(REPO + "/openhab/items/orzechowa.items"):
    m = re.match(r'\s*\w+\s+(\w+)\s.*?channel="([^"]+)"', line)
    if not m:
        continue
    name, ch = m.groups()
    uid = max((u for u in things if ch.startswith(u + ":")), key=len, default=None)
    state = states.get(name, "MISSING")
    if uid:
        used.add(uid)
    if not uid or ch not in channels:
        result = "MISSING"
    elif state in ("NULL", "UNDEF"):
        result = "NULL"
    else:
        result = "OK"
    status = things[uid]["statusInfo"]["status"] if uid else "no Thing"
    print(f"{result:8} {name:30} {state[:24]:24} {status:13} {ch}")
used |= {things[u].get("bridgeUID") for u in used}  # e.g. the MQTT broker
for uid in sorted(set(things) - used):
    t = things[uid]
    print(f"INFO     unused Thing {uid} ({t.get('label', '')}) {t['statusInfo']['status']}")
