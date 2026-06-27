# PkamSmartHome — Agent Instructions

## Project Overview

PkamSmartHome is a Raspberry Pi-based home automation system that controls lights
and window blinds via GPIO pins. It communicates with OpenHAB (the central home
automation hub) through MQTT. The house name is **Orzechowa**.

## Architecture

```
Physical Button → GPIO → psh-actor (Python) → MQTT ↔ OpenHAB → HomeKit / BasicUI
                  GPIO ← psh-actor (Python) ← MQTT ↔ OpenHAB ← HomeKit / BasicUI
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
- **OpenHAB** — home automation platform (runs on openHABian)
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
- GPIO interactions are mocked in tests — never use real GPIO in test code

### OpenHAB DSL
- Thing/Item/Rule/Sitemap files are named after the house: `orzechowa.*`
- Items use `Room_Point` naming (e.g., `Office_Light`, `Livingroom_LedTV`)
- Groups use `g` prefix (e.g., `gLight`, `gNightLights`)
- Labels are in Polish
- HomeKit bindings are declared inline with items

## Configuration

The actor reads `psh-actor/config/config.json`. The JSON defines:
- `Connectivity` — MQTT broker connection (`ClientName`, `MqttIp`, `MqttPort`)
- `Rooms[]` — array of rooms, each with `Name` and `Points[]`
- **Light points** have: `Name`, `Type: "Light"`, `GpioControlPin`, `GpioButtonPin`
- **Blind points** have: `Name`, `Type: "Blind"`, `GpioControlPinUp`, `GpioControlPinDown`, `GpioButtonPinUp`, `GpioButtonPinDown`, `FullTravelTimeSec`

> **CRITICAL**: GPIO pin numbers are physical wiring assignments. Never change pin
> numbers without verifying against the actual hardware wiring.

## MQTT Topic Convention

Topics follow the pattern: `/{ActorName}/{Direction}/{Room}/{Point}`

| Direction | Usage |
|-----------|-------|
| `In` | Commands TO the actor (subscribed by psh-actor) |
| `Out` | State updates FROM the actor (published by psh-actor) |
| `Admin` | System commands: `RESET`, `NOTIFY_CURRENT_STATE` |

## Deployment Target

- **Hardware**: Raspberry Pi (runs openHABian OS)
- **Service user**: `pshactor` (with GPIO and sudo access)
- **Working directory**: `/home/pshactor/PkamSmartHome/psh-actor/`
- Code is deployed via `git pull` + `systemctl restart psh-actor`

## Safety Rules

1. **Never modify GPIO pin assignments** without explicit user confirmation
2. **Never run `systemctl` commands** in suggestions without warning
3. **Preserve the MQTT topic structure** — OpenHAB Things depend on exact topic paths
4. **Keep OpenHAB item channel bindings** in sync with MQTT thing channels
5. **Never activate both blind motor relays simultaneously** — safety interlock with 500ms delay on reversal
6. **Test changes with unit tests** before suggesting deployment
