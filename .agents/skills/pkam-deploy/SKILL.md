---
name: pkam-deploy
description: >
  Deploy PkamSmartHome changes to the Raspberry Pi over SSH and verify the
  deployment worked (psh-actor service, MQTT round trip, OpenHAB Things/Items/
  rules). Use only when the user explicitly asks to deploy, roll out, or verify
  a deployment on the Pi.
disable-model-invocation: true
argument-hint: "[git ref to deploy, default: master] [--verify-only]"
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
| OpenHAB REST | `http://localhost:8080/rest`, token in `~/.openhab-token` on the Pi (never in the repo) |
| Default ref | `master` — deploying any other branch needs explicit user OK |

Every remote command runs as `ssh pkam-pi '<cmd>'`. If `ssh pkam-pi true` fails,
stop and tell the user — never try other hosts, users or passwords.

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

- Record `PREV_SHA` (needed for rollback) and the deploy start time `T0`.
- If the Pi working tree is dirty, stop and show the user the changes.
- Capture current light states (non-invasive):

```bash
ssh pkam-pi '
  (mosquitto_sub -h localhost -t "/Pi1/Out/#" -v -W 4 > /tmp/psh-state.txt &) ;
  sleep 1 ; mosquitto_pub -h localhost -t /Pi1/In/Admin -m NOTIFY_CURRENT_STATE ;
  sleep 4 ; cat /tmp/psh-state.txt'
```

- Baseline OpenHAB Things status (see Step 5c query) — so pre-existing
  OFFLINE Things are not blamed on this deploy.

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
| `linux-service/**` | `sudo ./install-service.sh` (includes daemon-reload + restart) |
| new binding/transformation referenced in `openhab/` | **stop** — user must install the add-on first (readme "Required openHAB Add-ons") |

Present to the user: commits being deployed (`git log --oneline PREV_SHA..origin/<ref>`),
the action list, lights that will go OFF, and the rollback point `PREV_SHA`.
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
Wait ~10 s after a restart or config install before verifying.

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
| Unit tests on Pi | `cd psh-actor && python3 -m unittest discover -p 'test_*.py'` | all pass |

Count configured points without extra tools:
`python3 -c "import json;c=json.load(open('config/config.json'));print(sum(len(r['Points']) for r in c['Rooms']))"`

### 5b. MQTT round trip (non-invasive, always)

Repeat the Step 2 `NOTIFY_CURRENT_STATE` capture. Pass when one `/Pi1/Out/...`
message arrives for every configured point, each with a valid payload
(`ON`/`OFF` for lights, `0`–`100` for blinds).

**Optional active test — only with user permission, naming the light:**
send `ON` to `/Pi1/In/<Room>/<Point>`, expect `/Pi1/Out/<Room>/<Point> ON` within 2 s
and `pinctrl get <GpioControlPin>` reporting `hi` (on older OS: `raspi-gpio get <pin>`);
then send `OFF` and expect the reverse. Ask the user to confirm the lamp physically
switched — the Pi cannot observe that.

### 5c. OpenHAB (if `openhab/**` deployed)

| Check | Command | Pass when |
|-------|---------|-----------|
| Models loaded | `sudo grep -a "<T0 date>" /var/log/openhab/openhab.log \| grep -E "Loading model\|ERROR\|WARN"` | each changed `orzechowa.*` file logs `Loading model`; no `ERROR` and no new `Configuration model ... has errors` |
| Things online | `curl -s -H "Authorization: Bearer $(cat ~/.openhab-token)" localhost:8080/rest/things` → parse `UID` + `statusInfo.status` with `python3 -c` | every Thing ONLINE, or same status as the Step 2 baseline |
| Items have state | `.../rest/items?recursive=false` → every item from `orzechowa.items` exists | no item from the changed file missing; MQTT/Shelly/weather items not `NULL`/`UNDEF` |
| Rules loaded | `.../rest/rules` | every `rule "..."` name in `orzechowa.rules` present and not `UNINITIALIZED` |
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
- Things for the user to confirm physically (wall button toggles a light, HomeKit
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
Leave the Pi on detached `PREV_SHA` and tell the user to return it to `master`
once the fix is merged.
