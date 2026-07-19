---
name: pkam-smart-home
description: >
  PkamSmartHome IoT automation system running on Raspberry Pi with OpenHAB.
  Use this skill when working with GPIO pin control, MQTT messaging,
  OpenHAB configuration (Things, Items, Rules, Sitemaps), psh-actor Python
  service, systemd service management, or home automation workflows.
  Trigger on: 'smart home', 'GPIO', 'MQTT', 'OpenHAB', 'psh-actor',
  'light point', 'blind point', 'window blind', 'rollershutter',
  'room configuration', 'openHABian', 'HomeKit', 'WindowCovering',
  'TP-Link', 'Mosquitto', 'Astro binding', 'systemd service'.
---

# PkamSmartHome — Domain Knowledge

## System Architecture

### Communication Flow

```
┌─────────────┐     GPIO      ┌───────────┐    MQTT     ┌──────────┐
│  Physical   │──────────────▶│           │────────────▶│          │──▶ HomeKit
│  Buttons    │               │ psh-actor │             │ OpenHAB  │──▶ BasicUI
│             │◀──────────────│ (Python)  │◀────────────│          │──▶ Watch UI
│  Relays     │     GPIO      │           │    MQTT     │          │
└─────────────┘               └───────────┘             └──────────┘
                                   │                         │
                              config.json              orzechowa.*
                              logging.conf             (things/items/
                                                        rules/sitemaps)
```

### Component Responsibilities

| Component | Runs On | Manages |
|-----------|---------|---------|
| **psh-actor** | Raspberry Pi (systemd) | GPIO read/write, MQTT pub/sub, button debounce |
| **OpenHAB** | Raspberry Pi (openHABian) | Automation rules, UI, HomeKit bridge, device discovery |
| **Mosquitto** | Raspberry Pi (systemd) | MQTT message broker (localhost:1883) |
| **TP-Link Smart Home Binding** | OpenHAB | Wi-Fi smart plugs and dimmers (HS100, HS110, KL110) |
| **Astro Binding** | OpenHAB | Sunrise/sunset times for automation triggers |

---

## MQTT Topic Convention

All MQTT topics follow this structure:

```
/{ActorName}/{Direction}/{Room}/{PointName}
```

### Topic Directions

| Direction | Purpose | Example |
|-----------|---------|---------|
| `In` | Commands sent TO the actor | `/Pi1/In/Office/Ceiling` |
| `Out` | Status updates FROM the actor | `/Pi1/Out/Office/Ceiling` |
| `Admin` | System-level commands | `/Pi1/In/Admin` |

### Admin Commands

| Command | Payload | Effect |
|---------|---------|--------|
| `RESET` | `RESET` | Turns OFF all lights, fully opens all blinds, sends state update |
| `NOTIFY_CURRENT_STATE` | `NOTIFY_CURRENT_STATE` | Publishes current state of all points |

### Light Point Commands

| Command | Payload |
|---------|---------|
| Turn ON | `ON` |
| Turn OFF | `OFF` |

### Blind Point Commands

| Command | Payload | Effect |
|---------|---------|--------|
| Move up | `UP` | Start opening (continuous until STOP) |
| Move down | `DOWN` | Start closing (continuous until STOP) |
| Stop | `STOP` | Stop any movement |
| Go to position | `0`–`100` | Move to target percentage (0=fully open, 100=fully closed) |

Predefined positions: `0` (fully open), `50` (half), `67` (2/3 closed), `100` (fully closed).
State is published as an integer percentage (e.g., `0`, `50`, `67`, `100`).

### Wildcard Subscription

The actor subscribes to `/{ActorName}/In/#` — this captures both point-specific
and admin messages. Point IDs are extracted by parsing everything after `/In/`.

---

## Configuration Schema

The actor configuration lives at `psh-actor/config/config.json`:

```json
{
  "General": {
    "Name": "<actor display name>"
  },
  "Connectivity": {
    "ClientName": "<MQTT client ID, used in topic paths>",
    "MqttIp": "<broker hostname>",
    "MqttPort": "<broker port (integer)>"
  },
  "Rooms": [
    {
      "Name": "<room name, used in MQTT topics and point IDs>",
      "Points": [
        {
          "Name": "<point name>",
          "Type": "Light",
          "GpioControlPin": "<BCM pin for relay output (integer)>",
          "GpioButtonPin": "<BCM pin for button input (integer)>"
        },
        {
          "Name": "<point name>",
          "Type": "Blind",
          "GpioControlPinUp": "<BCM pin for UP relay (integer)>",
          "GpioControlPinDown": "<BCM pin for DOWN relay (integer)>",
          "GpioButtonPinUp": "<BCM pin for UP button (integer)>",
          "GpioButtonPinDown": "<BCM pin for DOWN button (integer)>",
          "FullTravelTimeSec": "<seconds for full open→close travel (float)>"
        }
      ]
    }
  ]
}
```

### Current Room/Point Layout — Lights

| Room | Point | Control Pin | Button Pin | MQTT Topic Suffix |
|------|-------|------------|------------|-------------------|
| Office | Ceiling | 2 | 3 | `/Office/Ceiling` |
| Livingroom | LedTV | 4 | 17 | `/Livingroom/LedTV` |
| Livingroom | Ceiling13 | 11 | 5 | `/Livingroom/Ceiling13` |
| Livingroom | Ceiling23 | 0 | 6 | `/Livingroom/Ceiling23` |
| Diningroom | Ceiling23 | 10 | 27 | `/Diningroom/Ceiling23` |
| Diningroom | Ceiling13 | 9 | 22 | `/Diningroom/Ceiling13` |
| Marysia | Ceiling13 | 12 | 16 | `/Marysia/Ceiling13` |
| Marysia | Ceiling23 | 20 | 21 | `/Marysia/Ceiling23` |

### Current Room/Point Layout — Blinds

| Room | Point | CtlUp | CtlDown | BtnUp | BtnDown | Travel (s) | MQTT Topic Suffix |
|------|-------|-------|---------|-------|---------|------------|-------------------|
| Office | WindowBlind | TBD | TBD | TBD | TBD | 25.0 | `/Office/WindowBlind` |

> [!WARNING]
> The Office WindowBlind GPIO pins are set to `0` (placeholder). They must be
> updated with actual BCM pin numbers matching the physical wiring before deployment.

> [!CAUTION]
> GPIO pin numbers are BCM (Broadcom) numbering. They map to physical wiring.
> Changing a pin number without rewiring will either break control or potentially
> damage hardware. **Always confirm with the user before modifying pin assignments.**

---

## Point System Architecture

### Class Hierarchy

```
Point (base class)
  ├── LightPoint  (1 relay + 1 button, binary ON/OFF)
  └── BlindPoint   (2 relays + 2 buttons, position 0–100%)
```

### Point Base Class (`point.py`)

Abstract base with four lifecycle methods:
- `initialize()` — set up hardware resources
- `updateStatus(message)` — handle incoming MQTT command
- `reset()` — return to default state
- `notifyCurrentState()` — publish current state to MQTT

### LightPoint (`light_point.py`)

- Uses `gpiozero.DigitalOutputDevice` for relay control
- Uses `gpiozero.Button` with `hold_time=0.1` for debounce
- Button press triggers `toggle()` → changes state + notifies hub
- Reset turns OFF and notifies

### BlindPoint (`blind_point.py`)

- Uses two `gpiozero.DigitalOutputDevice` for UP and DOWN relay control
- Uses two `gpiozero.Button` for physical UP and DOWN buttons (hold-to-move)
- **Position model**: 0.0 (fully open) to 100.0 (fully closed), tracked via elapsed time
- **Time-based movement**: position delta = `elapsed / FullTravelTimeSec * 100%`
- **Safety interlock**: both relays never active simultaneously; 500ms delay on direction reversal
- **Timed go-to-position**: uses `threading.Timer` to auto-stop at target position
- **Button behavior**: press = start moving, release = stop (direction-aware)
- Reset fully opens (position = 0) and notifies
- Position does not persist across restarts (resets to 0 = fully open)

### Point Factory (`point_factory.py`)

Creates points from JSON configuration. Point ID format: `/{RoomName}/{PointName}`

The factory delegates to type-specific creation methods:
- `_createLightPoint()` — validates `GpioControlPin`, `GpioButtonPin`
- `_createBlindPoint()` — validates `GpioControlPinUp`, `GpioControlPinDown`, `GpioButtonPinUp`, `GpioButtonPinDown`, `FullTravelTimeSec`

### Adding a New Point Type

1. Create a new class inheriting from `Point`
2. Add a new `CONFIG_POINT_TYPE_*` constant in `constants.py`
3. Add a new `_create*Point()` method and `elif` branch in `PointFactory.createPoint()`
4. Add corresponding OpenHAB Thing channel, Item, and Sitemap entry
5. Create `test_{module}.py` with mocked GPIO

---

## OpenHAB Configuration

### File Structure

```
openhab/
├── install-config.sh     # Backs up existing + deploys new config
├── things/
│   └── orzechowa.things  # MQTT bridge, NTP, Astro bindings
├── items/
│   └── orzechowa.items   # All controllable items with HomeKit tags
├── rules/
│   └── orzechowa.rules   # Automation rules (sunset, sunrise, Xmas)
└── sitemaps/
    ├── orzechowa.sitemap  # Full home control UI
    └── watch.sitemap      # Simplified watch/mobile UI
```

### Thing Definition Patterns

MQTT-controlled **lights** use `Type switch` in `orzechowa.things`:

```
Type switch : channelId [
  stateTopic="/{ActorName}/Out/{Room}/{Point}",
  commandTopic="/{ActorName}/In/{Room}/{Point}",
  on="ON", off="OFF"
]
```

MQTT-controlled **blinds** use `Type rollershutter`:

```
Type rollershutter : channelId [
  stateTopic="/{ActorName}/Out/{Room}/{Point}",
  commandTopic="/{ActorName}/In/{Room}/{Point}",
  up="UP", down="DOWN", stop="STOP"
]
```

### Item Definition Patterns

Light items in `orzechowa.items`:

```
Switch  ItemName  "Label"  <icon>  (Groups)  {channel="mqtt:topic:bridgeId:thingId:channelId", homekit="Lighting"}
```

Blind items:

```
Rollershutter  ItemName  "Label"  <rollershutter>  (Groups)  {channel="mqtt:topic:bridgeId:thingId:channelId", homekit="WindowCovering"}
```

Blind sitemap controls (slider + preset buttons):

```
Slider item=Room_Blind
Switch item=Room_Blind mappings=[0="Otwórz", 50="1/2", 67="2/3", 100="Zamknij"]
```

### Groups

Groups with aggregation functions:
- `Group:Switch:AND(ON, OFF)` — all-on / all-off semantics (lights)
- `Group:Switch:OR(ON, OFF)` — any-on semantics (ceiling light groups)
- `Group gBlind` — all blinds group (no aggregation function)

### Automation Rules

| Rule | Trigger | Action |
|------|---------|--------|
| Startup | System started | Sends `NOTIFY_CURRENT_STATE` to actor via MQTT |
| Night lights ON | Sunset + 30 min | Turns on `gNightLights`; also `gAwayLights` if Away mode is ON |
| Xmas lights ON | 16:00 daily (Dec 6–31, Jan 1–15) | Turns off night lights, turns on `gXmasLights` |
| Lights OFF | 23:00 daily | Turns off all night, Xmas, and away lights |
| Sunrise OFF | Sunrise event | Turns off night and Xmas lights |

### Non-MQTT Devices

These are controlled directly by OpenHAB via TP-Link binding (Wi-Fi):

| Item | Device | Type |
|------|--------|------|
| `Office_Biurko` | KL110 dimmer | Desk lamp |
| `Office_Lamp` | HS100 plug | Desk lamp |
| `Livingroom_Lampa` | HS100 plug | Floor lamp |
| `Outdoor_Front_Xmas` | HS110 plug | Christmas lights |
| `Outdoor_Front` | KL110 dimmer | Front wall lamp |
| `Taras_Xmas` | HS110 plug | Terrace Christmas lights |
| `Taras_1` | KL110 dimmer | Terrace wall lamp |

---

## Deployment Workflows

### Fresh Installation

1. Flash openHABian → configure OS → install Mosquitto
2. Create `pshactor` user with GPIO + sudo access
3. Clone repo → run `psh-actor/install-environment.sh` (installs pip packages, creates logs dir, sets GPIO permissions)
4. Deploy OpenHAB config → run `openhab/install-config.sh` (backs up existing, copies new)
5. Install systemd service → run `linux-service/install-service.sh`
6. Reboot → service starts automatically

### Actor Code Update

```bash
cd ~/PkamSmartHome
git pull
sudo systemctl restart psh-actor
```

### OpenHAB Config Update

```bash
cd ~/PkamSmartHome
git pull
cd openhab
sudo ./install-config.sh
```

### Reset All Points

```bash
cd ~/PkamSmartHome/psh-actor
./reset-all-points.sh
```

This publishes `RESET` to `/{ActorName}/In/Admin` via `mosquitto_pub`.

---

## Testing Conventions

### Test Structure

- Tests live alongside source files in `psh-actor/`
- Pattern: `test_{module}.py` (e.g., `test_light_point.py`)
- Framework: `unittest.TestCase`
- Mocking: `unittest.mock.Mock` (GPIO is always mocked)

### Running Tests

```bash
cd psh-actor
python3 -m pytest test_*.py
# or
python3 -m unittest discover -p 'test_*.py'
```

### Test Coverage

| Module | Test File | Covered |
|--------|-----------|---------|
| `hub_communication_service.py` | `test_hub_comminication_service.py` | Topic parsing, message routing, admin commands |
| `light_point.py` | `test_light_point.py` | ON/OFF, toggle, reset, notify state |
| `blind_point.py` | `test_blind_point.py` | UP/DOWN/STOP, position tracking, timer, interlock, buttons, reset |
| `point_factory.py` | `test_point_factory.py` | Light + Blind creation, validation errors |
| `room.py` | `test_room.py` | Room init, point delegation |
| `rooms_service.py` | `test_rooms_service.py` | Room lookup, status routing |

> [!NOTE]
> The test file for hub communication has a typo in its name:
> `test_hub_comminication_service.py` (double `i` missing). Do NOT rename it
> without user approval as it may be referenced in CI or scripts.

---

## Adding New Points

### Workflow: Add a New GPIO-Controlled Light

1. **Wire the hardware** — connect relay to a free GPIO output pin, button to a free GPIO input pin
2. **Update `config.json`** — add a point with `"Type": "Light"` under the appropriate room
3. **Update `orzechowa.things`** — add a new `Type switch` channel with matching MQTT topics
4. **Update `orzechowa.items`** — add a new `Switch` item linked to the thing channel, with `homekit="Lighting"`
5. **Update `orzechowa.sitemap`** — add the item to the appropriate frame
6. **Deploy** — `git push`, then on the Pi: `git pull` + restart actor + reinstall OpenHAB config

### Workflow: Add a New GPIO-Controlled Blind

1. **Wire the hardware** — connect UP relay, DOWN relay, UP button, DOWN button to 4 free GPIO pins
2. **Update `config.json`** — add a point with `"Type": "Blind"` including all 4 pin numbers and `FullTravelTimeSec`
3. **Measure travel time** — time the blind from fully open to fully closed and set `FullTravelTimeSec`
4. **Update `orzechowa.things`** — add a `Type rollershutter` channel with `up="UP", down="DOWN", stop="STOP"`
5. **Update `orzechowa.items`** — add a `Rollershutter` item with `homekit="WindowCovering"`, add to `gBlind` group
6. **Update `orzechowa.sitemap`** — add `Slider` + `Switch` with preset `mappings=[0="Otwórz", 50="1/2", 67="2/3", 100="Zamknij"]`
7. **Deploy** — `git push`, then on the Pi: `git pull` + restart actor + reinstall OpenHAB config

### Workflow: Add a New TP-Link Wi-Fi Device

1. **Plug in the device** — it will be auto-discovered by OpenHAB
2. **Add as Thing** via OpenHAB admin UI (Settings → Things → Inbox)
3. **Update `orzechowa.items`** — add item with `channel="tplinksmarthome:..."`
4. **Update `orzechowa.sitemap`** — add to appropriate frame
5. **Deploy OpenHAB config**

---

## Important Constraints

> [!WARNING]
> - **GPIO pins are hardware-mapped** — never change pin numbers without physical verification
> - **Blind motors have safety interlocks** — both relays must NEVER be active simultaneously; 500ms delay on direction reversal
> - **MQTT topics must be consistent** across `config.json`, `orzechowa.things`, and `orzechowa.rules`
> - **The actor uses `signal.pause()`** — it blocks the main thread and relies on MQTT callbacks and GPIO interrupts
> - **No authentication on MQTT** — Mosquitto runs without passwords (local network only)
> - **Labels are in Polish** — OpenHAB UI labels use Polish language; maintain this convention
> - **The `install-config.sh` script is destructive** — it deletes all existing OpenHAB config before copying new files
> - **Service depends on `mosquitto.service`** — MQTT broker must start before psh-actor
> - **Blind position does not persist** — on restart, position resets to 0% (fully open)
