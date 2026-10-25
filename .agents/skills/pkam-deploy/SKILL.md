---
name: pkam-deploy
description: >
  Deploy PkamSmartHome changes to the Raspberry Pi over SSH and verify the
  deployment worked (psh-actor service, MQTT round trip, OpenHAB Things/Items/
  rules), or set up a freshly installed openHABian Pi (--setup). Use only when
  the user explicitly asks to deploy, roll out, verify a deployment, or set up
  the Pi.
disable-model-invocation: true
argument-hint: "[branch to deploy, default: the Pi's current branch] [--verify-only | --setup]"
---

# PkamSmartHome — Deploy & Verify

Deploys a git ref to the Pi, applies only the steps the change needs, then proves
each affected component works. Ends with a pass/fail report and, on failure, a
rollback offer.

## Settings

| Setting | Value |
|---------|-------|
| SSH host alias | `pkam-pi` (user `pshactor`, key auth, defined in `~/.ssh/config`) |
| Repo on Pi | `/home/pshactor/PkamSmartHome` |
| Actor name / topic root | `Pi1` → `/Pi1/In/...`, `/Pi1/Out/...` |
| OpenHAB REST | `http://localhost:8080/rest`, token in `~/.openhab-token` on the Pi (never in the repo). Sitemaps and item states work without it; Things and rules return 401 without it |
| Default ref | The branch currently checked out on the Pi (`PREV_BRANCH`, any branch is fine). If the Pi is detached, the user must name a branch. Deploying a branch other than `PREV_BRANCH` switches the Pi to it — call that out in the Step 3 plan |

Every remote command runs as `ssh pkam-pi '<cmd>'`. If `ssh pkam-pi true` fails,
stop and tell the user — never try other hosts, users or passwords.

## Prerequisites

A normal deploy expects a Pi set up by `--setup` (see `setup.md`), or by hand
following `readme.md` → Installation and → "Prepare the Pi for /pkam-deploy".
Step 0 checks all of this read-only.

**Required** (if any is missing, stop and point the user to the readme):

| # | Where | Must be true |
|---|-------|--------------|
| R1 | dev machine | `ssh -o BatchMode=yes pkam-pi true` works: `Host pkam-pi` in `~/.ssh/config` (user `pshactor`), dev public key in the Pi's `~pshactor/.ssh/authorized_keys`, Pi host key already accepted |
| R2 | dev machine | Repo cloned with push access to `origin`; `psh-actor/.venv` built from `requirements.txt` (for Step 1 tests) |
| R3 | Pi | Base install done: openHABian, openHAB 5.1.4 or newer (5.1.4 is the known-good version, see readme; add-ons come from `openhab/services/addons.cfg`, see Step 3), Mosquitto on `localhost:1883` without auth, `mosquitto-clients`, `curl`, `pinctrl` |
| R4 | Pi | User `pshactor` in groups `sudo` and `gpio` |
| R5 | Pi | Repo at `/home/pshactor/PkamSmartHome`, `origin` = `git@github.com:piotrkaminski/PkamSmartHome.git`, `pshactor` can fetch without prompts (SSH key on GitHub, `github.com` in `known_hosts`), clean working tree. Any branch is fine if it tracks an `origin` branch and has no commits that are not on origin; a detached HEAD must be a commit that exists on origin |
| R6 | Pi | `install-environment.sh` run once (`paho-mqtt` + `gpiozero` importable by system `python3`, `psh-actor/logs/` exists) |
| R7 | Pi | `install-service.sh` and `install-config.sh` run once; `psh-actor` enabled + active; `openhab`, `mosquitto` active; `/rest/sitemaps/orzechowa` returns 200 |

**Optional** (if missing, the deploy still runs, with less coverage):

| # | Must be true | If missing |
|---|--------------|-----------|
| O1 | `~/.openhab-token` on the Pi, mode 600, valid API token | "Things online" and "Rules loaded" checks are SKIPPED |
| O2 | `pshactor` can read `/var/log/openhab/openhab.log` | "Models loaded" check is SKIPPED |
| O3 | Passwordless `sudo` | User runs each `sudo` line themselves with `! ssh -t pkam-pi ...` (this is the normal case and the safer one) |
| O4 | OS timezone and the single JVM `-Duser.timezone` are both `Europe/Warsaw` | `T0` and openHAB log timestamps disagree; log windows may be off by an hour |

## Modes

- `/pkam-deploy <ref>` — full flow, Steps 0–7.
- `/pkam-deploy --setup` — fresh openHABian Pi to deploy-ready, over SSH as
  `openhabian` (alias `pkam-pi-setup`). Follow `setup.md` in this directory; it
  ends with `--verify-only`. It needs the user for passwords, the GitHub deploy key
  and the openHAB admin account, and it never takes them through the chat.
- `/pkam-deploy --verify-only` — no deploy: Step 0, Step 2 (snapshot + integrity), then
  every check in Step 5 against what is running now, then Step 6. Checks that only
  make sense right after a deploy (e.g. `Started cleanly` when the actor has been
  up for weeks and its startup log has rotated) are SKIPPED with the reason.

## Ground rules

1. **Read-only commands run freely** (status, logs, `git log`, REST GETs,
   `mosquitto_sub`, `NOTIFY_CURRENT_STATE`).
2. **Everything that changes state needs one explicit confirmation** of the full
   plan (step 3). If the plan changes midway, confirm again.
3. **Restarting `psh-actor` turns OFF every GPIO light** (`Main` calls
   `rooms_service.reset()` on startup). Say so in the plan, with the list of lights
   currently ON, and suggest a better time if it is evening.
4. **`install-config.sh` wipes `/etc/openhab/{items,things,rules,sitemaps}`** and
   overwrites `openhab/backup/` (only one backup generation). It does not touch
   Shelly/TP-Link Things (JSONDB).
5. Never edit files on the Pi by hand, never `git push` from the Pi, never change
   `config.json` pins (see AGENTS.md safety rules).
6. Never switch a light or move a blind for testing without asking first.

## Step 0 — Readiness check (read-only)

```bash
ssh -o BatchMode=yes pkam-pi 'bash -s' < .agents/skills/pkam-deploy/check-pi-ready.sh
```

- Exit code 0 / `READY` = all required checks passed. Any `FAIL` = **stop**, list
  the failed checks, and point to the matching R-row above and readme →
  "Prepare the Pi for /pkam-deploy". Do not try to fix the Pi yourself.
- `add-ons missing` / `add-ons not in list` WARNs are deploy work, not readiness
  failures: they mean the Pi's add-ons differ from `openhab/services/addons.cfg`,
  and Step 3 must plan `install-config.sh` (see the add-ons row there).
- Carry each `WARN` into the plan (Step 3) and the report (Step 6) so the user
  knows which checks will be SKIPPED and why.
- If `ssh` itself fails (R1), stop and tell the user. Never try other hosts,
  users or passwords.

## Step 1 — Local preflight (on this machine)

- `git status` clean, target ref pushed to `origin`.
- Unit tests pass:
  `cd psh-actor && .venv/bin/python -m unittest discover -p 'test_*.py'`
- Stop on any failure.

## Step 2 — Remote snapshot (read-only)

```bash
ssh pkam-pi '
  cd ~/PkamSmartHome &&
  git rev-parse HEAD && git status --porcelain && git branch --show-current &&
  systemctl is-active psh-actor openhab mosquitto &&
  date "+%F %T %Z"'
```

- Record `PREV_SHA` and `PREV_BRANCH` (empty if detached; both needed for
  rollback) and the deploy start time `T0`. With no ref given, `<ref>` =
  `PREV_BRANCH`.
- If the Pi working tree is dirty, stop and show the user the changes.
- Capture current light states (non-invasive):

```bash
ssh pkam-pi '
  (mosquitto_sub -h localhost -t "/Pi1/Out/#" -v -W 4 > /tmp/psh-state.txt &) ;
  sleep 1 ; mosquitto_pub -h localhost -t /Pi1/In/Admin -m NOTIFY_CURRENT_STATE ;
  sleep 4 ; cat /tmp/psh-state.txt'
```

- Baseline OpenHAB Things status (see Step 5c query) — so pre-existing
  OFFLINE Things are not blamed on this deploy. Without a token, record it as
  SKIPPED and continue.
- **Quick integrity check** — catches a failing SD card before a deploy makes it
  worse:

```bash
ssh pkam-pi 'dpkg --verify libmosquitto1 mosquitto-clients python3-dnspython openhab openhab-addons 2>&1 \
  | awk "\$2!=\"c\" && substr(\$1,3,1)==\"5\"" | grep -v "^..5.* /var/lib/openhab/etc/"'
```

  No output = OK. Any line (a changed binary, jar or `.kar`) = **stop**: do not
  deploy or restart anything, report it, and point the user to
  "Recovery after SD card failure" in `readme.md`. Changed files under
  `/var/lib/openhab/etc/` are normal (openHAB rewrites them).

## Step 3 — Plan the deploy and confirm

```bash
ssh pkam-pi 'cd ~/PkamSmartHome && git fetch -q origin && git diff --name-only PREV_SHA origin/<ref>'
```

Map changed paths to actions:

| Changed path | Action |
|--------------|--------|
| only `*.md`, `.agents/`, `.claude/`, `test_*.py` | pull only, no restart |
| `psh-actor/requirements.txt` | run `install-environment.sh` |
| `psh-actor/*.py` (non-test), `psh-actor/config/*`, `psh-actor/logging.conf` | restart `psh-actor` |
| `openhab/**` | `sudo ./install-config.sh` (OpenHAB hot-reloads files; no restart) |
| `openhab/services/addons.cfg`, or Step 0 warned `add-ons missing` / `add-ons not in list` | `sudo ./install-config.sh` — it installs every listed add-on and **uninstalls** unlisted ones of the listed types (bindings, transformations, UIs, misc). Name both sets in the plan |
| `linux-service/**` | `sudo ./install-service.sh` (includes daemon-reload + restart) |
| new binding/transformation referenced in `openhab/` but not in `openhab/services/addons.cfg` | **stop** — the add-on must be added to `addons.cfg` in the repo first |

Present to the user: commits being deployed (`git log --oneline PREV_SHA..origin/<ref>`),
the action list, lights that will go OFF, and the rollback point `PREV_SHA`.
If `<ref>` ≠ `PREV_BRANCH`, say plainly: "the Pi switches from `PREV_BRANCH` to
`<ref>`".
Wait for an explicit yes.

## Step 4 — Deploy

Run only the actions selected in Step 3, in this order, stopping at the first error:

```bash
ssh pkam-pi 'cd ~/PkamSmartHome && git checkout -q <ref> && git pull --ff-only'
ssh pkam-pi 'cd ~/PkamSmartHome/psh-actor && ./install-environment.sh'        # if needed
ssh -t pkam-pi 'cd ~/PkamSmartHome/openhab && sudo ./install-config.sh'       # if needed
ssh -t pkam-pi 'cd ~/PkamSmartHome/linux-service && sudo ./install-service.sh' # if needed
ssh -t pkam-pi 'sudo systemctl restart psh-actor'                             # if needed
```

If `sudo` needs a password, ask the user to run that line themselves with `! ssh -t pkam-pi ...`.
Wait ~10 s after a restart or config install before verifying — or ~2 min when
add-ons are being installed (a Pi 3 is slow to start bundles; Things whose binding
is not up yet stay `UNINITIALIZED` meanwhile).

## Step 5 — Verify

Run every check for each deployed component. A check is PASS, FAIL, or SKIPPED
(with reason).

### 5a. psh-actor (if restarted or code changed)

| Check | Command | Pass when |
|-------|---------|-----------|
| Service active | `systemctl is-active psh-actor` | `active` |
| No crash | `journalctl -u psh-actor --since "<T0>" --no-pager` | no `Traceback`, `FATAL`, `CRITICAL` |
| Started cleanly | `grep -a "" logs/psh-actor.log \| tail -200` | contains `System initialized` after `T0` |
| MQTT subscribed | same log | `Subscribing to topic /Pi1/In/#` |
| All points loaded | count `Light point ... initialized` / `Blind point ... initialized` lines vs. points in `config/config.json` | counts equal |
| Unit tests on Pi | `cd psh-actor && python3 -m unittest discover -p 'test_*.py'` | all pass — **only run if** `grep -l MockFactory test_point_factory.py test_room.py` lists both files; otherwise SKIPPED (those tests would create real gpiozero devices on the Pi's pins and could switch relays) |

Count configured points without extra tools:
`python3 -c "import json;c=json.load(open('config/config.json'));print(sum(len(r['Points']) for r in c['Rooms']))"`

### 5b. MQTT round trip (non-invasive, always)

Repeat the Step 2 `NOTIFY_CURRENT_STATE` capture. Pass when one `/Pi1/Out/...`
message arrives for every configured point, each with a valid payload
(`ON`/`OFF` for lights, `0`–`100` for blinds).

If `mosquitto_pub`/`mosquitto_sub` fail (e.g. exit 139 `Segmentation fault`),
retry the same round trip with paho, which `psh-actor` already depends on:

```bash
ssh pkam-pi 'cd ~/PkamSmartHome/psh-actor && timeout 15 python3 - <<"EOF"
import paho.mqtt.client as mqtt, time
got = []
c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "verify-%d" % time.time())
c.on_message = lambda cl, u, m: got.append((m.topic, m.payload.decode()))
c.connect("localhost", 1883); c.loop_start()
c.subscribe("/Pi1/Out/#"); time.sleep(1)
c.publish("/Pi1/In/Admin", "NOTIFY_CURRENT_STATE"); time.sleep(3)
c.loop_stop(); c.disconnect()
for t, p in got: print(t, p)
print("count:", len(got))
EOF'
```

Report the mosquitto client failure as FAIL either way (the user's
`reset-all-points.sh` / `notify-current-status.sh` depend on it). If paho also
fails to import (`bad marshal data`, `ImportError`), that is FAIL **and** a sign of
file corruption — run the Step 2 integrity check and warn that restarting
`psh-actor` would likely fail.

When no round trip works, still compare pin levels with OpenHAB item states
(read-only): `pinctrl get <GpioControlPin>` (`hi` = ON) vs.
`curl -s localhost:8080/rest/items/<Item>/state`.

**Optional active test — only with user permission, naming the light:**
send `ON` to `/Pi1/In/<Room>/<Point>`, expect `/Pi1/Out/<Room>/<Point> ON` within 2 s
and `pinctrl get <GpioControlPin>` reporting `hi` (on older OS: `raspi-gpio get <pin>`);
then send `OFF` and expect the reverse. Ask the user to confirm the lamp physically
switched — the Pi cannot observe that.

### 5c. OpenHAB (if `openhab/**` deployed, and always in `--verify-only`)

If `~/.openhab-token` is missing, run the anonymous checks (sitemaps, item
states) and mark the token-only checks SKIPPED — never treat a missing token as a
failure, and never ask the user to paste the token into the chat.

| Check | Command | Pass when |
|-------|---------|-----------|
| Add-ons match | re-run Step 0's script and read its `add-ons` lines | `add-ons installed` PASS. Without a token it only proves the config was applied, so say so in the report; `openhab.log` lines like `Failed installing` are FAIL |
| Models loaded | `grep -a` without sudo first; if the log is unreadable for `pshactor`, mark SKIPPED (not PASS) — `sudo grep -a "<T0 date>" /var/log/openhab/openhab.log \| grep -E "Loading model\|ERROR\|WARN"` | each changed `orzechowa.*` file logs `Loading model`; no `ERROR` and no new `Configuration model ... has errors` |
| Things online | `curl -s -H "Authorization: Bearer $(cat ~/.openhab-token)" localhost:8080/rest/things` → parse `UID` + `statusInfo.status` with `python3 -c` | every Thing ONLINE, or same status as the Step 2 baseline. No token → SKIPPED |
| Items have state | `curl -s localhost:8080/rest/items/<Item>/state` for each item in `orzechowa.items` (works without token) | no item from the changed file missing; MQTT/Shelly/weather items not `NULL`/`UNDEF` |
| Rules loaded | `.../rest/rules` (needs token) | every `rule "..."` name in `orzechowa.rules` present and not `UNINITIALIZED`. No token → SKIPPED |
| Sitemaps serve | `curl -s -o /dev/null -w "%{http_code}" localhost:8080/rest/sitemaps/orzechowa` and `/watch` | `200` |
| MQTT ↔ items in sync | for each light point in `config.json` with a channel in `orzechowa.things`, item state equals the 5b reported state | all match |

Points in `config.json` with no channel in `orzechowa.things` (currently the two
Marysia lights) are reported as **INFO**, not FAIL.

### 5d. systemd unit (if `linux-service/**` deployed)

`systemctl is-enabled psh-actor` → `enabled`; `systemctl cat psh-actor` matches
`linux-service/psh-actor.service`.

## Step 6 — Report

Reply with:

- Deployed `PREV_SHA` → `NEW_SHA` (ref name), actions run.
- A table of every check: component, check, PASS/FAIL/SKIPPED/INFO, evidence (one line).
- Things for the user to confirm physically (wall button toggles a light, BasicUI
  shows the change, blinds respond).
- Overall verdict: **SUCCESS** only if no FAIL.

## Step 7 — Rollback (on FAIL, only after user agrees)

```bash
ssh pkam-pi 'cd ~/PkamSmartHome && git checkout -q PREV_SHA'
ssh -t pkam-pi 'cd ~/PkamSmartHome/openhab && sudo ./install-config.sh'   # if openhab was deployed
ssh -t pkam-pi 'sudo systemctl restart psh-actor'                         # if actor was restarted
```

Re-installing from the checked-out `PREV_SHA` is safer than restoring
`openhab/backup/`, which was just overwritten. Afterwards re-run Step 5 and report.
Leave the Pi on detached `PREV_SHA`. Tell the user to check out a branch again
once the fix is merged (`PREV_BRANCH`, or whichever branch they want running).
