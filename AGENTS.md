# PkamSmartHome — Agent Instructions

## Project Overview

PkamSmartHome is a Raspberry Pi-based home automation system for the house
**Orzechowa**. OpenHAB is the central hub. Devices reach it in three ways:

- **GPIO lights** — wall buttons and relays wired to the Pi, driven by `psh-actor`
  over MQTT
- **Window blinds** — Shelly Plus 2PM roller controllers, controlled by OpenHAB
  directly through the Shelly binding (not by `psh-actor`)
- **Wi-Fi lamps/plugs** — TP-Link Kasa devices, controlled by OpenHAB through the
  TP-Link binding

`psh-actor` still supports GPIO-wired blinds (`BlindPoint`), but none are deployed
right now — `config.json` defines lights only.

## Architecture

```
Physical Button → GPIO → psh-actor (Python) → MQTT ↔ OpenHAB → BasicUI
                  GPIO ← psh-actor (Python) ← MQTT ↔ OpenHAB ← BasicUI
                         Shelly roller (Wi-Fi) ←──────→ OpenHAB
                         TP-Link plug/dimmer (Wi-Fi) ←→ OpenHAB
                         Open-Meteo (HTTP + JSONPATH) → OpenHAB  (weather for blind rules)
```

The system has three components:

| Component | Purpose | Path |
|-----------|---------|------|
| **psh-actor** | Python daemon reading GPIO buttons and controlling GPIO relays via MQTT | `psh-actor/` |
| **OpenHAB config** | Things, Items, Rules, Sitemaps for the OpenHAB instance | `openhab/` |
| **Linux service** | systemd unit to auto-start psh-actor on boot | `linux-service/` |

## Technology Stack

- **Python 3** — main language for `psh-actor`
- **paho-mqtt** — MQTT client library
- **gpiozero** — GPIO abstraction (`LED`, `Button`, `DigitalOutputDevice`)
- **OpenHAB** — home automation platform (runs on openHABian) in version openHAB 5.1.4
  (known-good; newer versions are allowed but untested, see readme → Known-good versions).
  Required add-ons: astro, km200, mqtt, ntp, http, shelly, tplinksmarthome, jsonpath
  transformation, basic UI — listed in `openhab/services/addons.cfg`
- **Mosquitto** — MQTT broker (local, unencrypted, port 1883)
- **systemd** — service management for the actor daemon

## Code Conventions

### Python (psh-actor)
- Classes use `PascalCase`, methods use `camelCase` (existing pattern — do NOT change to `snake_case`)
- Constants defined in `constants.py` using `UPPER_SNAKE_CASE`
- Configuration keys map to JSON property names and are defined as constants
- All classes have a flat structure — no package/module nesting
- Tests use `unittest.TestCase` with `unittest.mock.Mock`
- Test files follow the pattern `test_{module_name}.py`
- GPIO interactions are mocked in tests — never use real GPIO in test code. Tests
  that build real gpiozero devices (e.g. via `PointFactory`) must set
  `Device.pin_factory = MockFactory()` in `setUp`

### Running tests

Run from `psh-actor/` (modules import each other by flat name):

```bash
cd psh-actor
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # once
.venv/bin/python -m unittest discover -p 'test_*.py'
```

All tests must pass before suggesting deployment. Setting
`GPIOZERO_PIN_FACTORY=mock` is optional — tests that need it install a mock factory.

### OpenHAB DSL
- Thing/Item/Rule/Sitemap files are named after the house: `orzechowa.*`
- Items use `Room_Point` naming (e.g., `Office_Light`, `Livingroom_LedTV`)
- Groups use `g` prefix (e.g., `gLight`, `gNightLights`)
- Labels are in Polish
- HomeKit is no longer used — do not add `homekit="..."` metadata to items
- There is no local validator for OpenHAB DSL — review syntax carefully and tell
  the user to check `/var/log/openhab/openhab.log` after deployment
- Things in `orzechowa.things` cover MQTT, NTP, Astro and Open-Meteo only. Shelly
  and TP-Link Things were added through the OpenHAB UI (Inbox), so they are not
  in this repo — items just reference their channel UIDs

## Configuration

The actor reads `psh-actor/config/config.json`. The JSON defines:
- `Connectivity` — MQTT broker connection (`ClientName`, `MqttIp`, `MqttPort`)
- `Rooms[]` — array of rooms, each with `Name` and `Points[]`
- **Light points** have: `Name`, `Type: "Light"`, `GpioControlPin`, `GpioButtonPin`
- **Blind points** have: `Name`, `Type: "Blind"`, `GpioControlPinUp`, `GpioControlPinDown`, `GpioButtonPinUp`, `GpioButtonPinDown`, `FullTravelTimeSec`

Pin numbers use **BCM** (Broadcom) numbering.

> **CRITICAL**: GPIO pin numbers are physical wiring assignments. Never change pin
> numbers without verifying against the actual hardware wiring.

## MQTT Topic Convention

Topics follow the pattern: `/{ActorName}/{Direction}/{Room}/{Point}`

| Direction | Usage |
|-----------|-------|
| `In` | Commands TO the actor (subscribed by psh-actor) |
| `Out` | State updates FROM the actor (published by psh-actor) |
| `Admin` | System commands: `RESET`, `NOTIFY_CURRENT_STATE` (published to `/{ActorName}/In/Admin`) |

`{ActorName}` is `Connectivity.ClientName` (currently `Pi1`). It is hardcoded in
`orzechowa.things` and in the `Startup` rule — renaming it requires updating both.

## Deployment Target

- **Hardware**: Raspberry Pi (runs openHABian OS)
- **Service user**: `pshactor` (with GPIO and sudo access)
- **Working directory**: `/home/pshactor/PkamSmartHome/psh-actor/`
- Code is deployed via `git pull` + `systemctl restart psh-actor`
- OpenHAB config is deployed via `openhab/install-config.sh`, which **deletes**
  everything in `/etc/openhab/{items,things,rules,sitemaps}` before copying (it
  backs them up to `openhab/backup/` first). It also copies
  `openhab/services/addons.cfg`, which installs the listed add-ons and
  **uninstalls** unlisted ones of the same types — add new add-ons there
- Logs: `psh-actor/logs/psh-actor.log` (actor), `/var/log/openhab/openhab.log` (OpenHAB)

## Access to the Pi

- **SSH**: `ssh pkam-pi` — host alias in `~/.ssh/config` on the dev machine, user
  `pshactor`, key auth only. If `ssh pkam-pi true` fails, stop and tell the user;
  never try other hosts, users or passwords.
- **Setup SSH**: `ssh pkam-pi-setup` — same Pi, user `openhabian`, key auth only.
  Used only by `/pkam-deploy --setup` (`.agents/skills/pkam-deploy/setup.md`).
  There, root is limited to `sudo -n /usr/local/sbin/pkam-setup <step>`, which the
  setup removes at the end. Never bypass a changed SSH host key; the user confirms it.
- **OpenHAB REST**: `http://localhost:8080/rest` from the Pi; API token in
  `~/.openhab-token` on the Pi. Never copy the token into the repo or into logs.
- **Deploying**: only through the `/pkam-deploy` skill
  (`.agents/skills/pkam-deploy/SKILL.md`), and only when the user asks. What
  the Pi must have first is under "Prerequisites" in that skill; check it with
  `.agents/skills/pkam-deploy/check-pi-ready.sh` (read-only).
- **`sudo`**: if it prompts for a password, ask the user to run that line
  themselves with `! ssh -t pkam-pi sudo ...`.

| Allowed without asking (read-only) | Needs explicit user confirmation |
|------------------------------------|----------------------------------|
| `systemctl status` / `is-active`, `journalctl` | `git pull` / `git checkout` on the Pi |
| Reading `psh-actor/logs/` and `/var/log/openhab/openhab.log` | `systemctl restart` / `stop` / `start` of any service |
| `git log`, `git status`, `git diff` on the Pi | `install-environment.sh`, `install-config.sh`, `install-service.sh` |
| REST `GET` requests to OpenHAB | REST `POST` / `PUT` / `DELETE` (commands to items, rule changes) |
| `mosquitto_sub`; `NOTIFY_CURRENT_STATE` to `/Pi1/In/Admin` | Any other `mosquitto_pub` (switches lights, moves blinds, `RESET`) |
| `pinctrl get` / `raspi-gpio get` | `reboot`, package installs, any change to files on the Pi |
| `sudo -n /usr/local/sbin/pkam-setup status` (setup only) | Every other `pkam-setup` step (one confirmation of the setup plan per phase) |

> **Restarting `psh-actor` turns OFF every GPIO light** — `Main` calls
> `rooms_service.reset()` on startup. Before asking to restart, tell the user
> which lights are currently ON (get them with `NOTIFY_CURRENT_STATE`).

Never edit files on the Pi by hand and never `git push` from the Pi — all changes
go through this repo.

## Domain Reference

Detailed domain knowledge (current points, groups, rules, devices, workflows for
adding lights/blinds) is in `.agents/skills/pkam-smart-home/SKILL.md`.

## Safety Rules

1. **Never modify GPIO pin assignments** without explicit user confirmation
2. **Never run `systemctl` commands** in suggestions without warning
3. **Preserve the MQTT topic structure** — OpenHAB Things depend on exact topic paths
4. **Keep OpenHAB item channel bindings** in sync with MQTT thing channels
5. **Never activate both blind motor relays simultaneously** — safety interlock with 500ms delay on reversal
6. **Test changes with unit tests** before suggesting deployment
