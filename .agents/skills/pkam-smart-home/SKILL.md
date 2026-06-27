---
name: pkam-smart-home
description: >
  PkamSmartHome IoT automation system running on Raspberry Pi with OpenHAB.
  Use this skill when working with GPIO pin control, MQTT messaging,
  OpenHAB configuration (Things, Items, Rules, Sitemaps), psh-actor Python
  service, systemd service management, or home automation workflows.
  Trigger on: 'smart home', 'GPIO', 'MQTT', 'OpenHAB', 'psh-actor',
  'light point', 'room configuration', 'openHABian', 'HomeKit',
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
| `RESET` | `RESET` | Turns OFF all points and sends state update |
| `NOTIFY_CURRENT_STATE` | `NOTIFY_CURRENT_STATE` | Publishes current state of all points |

### Point Commands

| Command | Payload |
|---------|---------|
| Turn ON | `ON` |
| Turn OFF | `OFF` |

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
          "Name": "<point name, used in MQTT topics>",
          "Type": "Light",
          "GpioControlPin": "<BCM pin number for relay output (integer)>",
          "GpioButtonPin": "<BCM pin number for button input (integer)>"
        }
      ]
    }
  ]
}
```

### Current Room/Point Layout

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

> [!CAUTION]
> GPIO pin numbers are BCM (Broadcom) numbering. They map to physical wiring.
> Changing a pin number without rewiring will either break control or potentially
> damage hardware. **Always confirm with the user before modifying pin assignments.**

---

## Point System Architecture

### Class Hierarchy

```
Point (base class)
  └── LightPoint (GPIO relay + button)
      └── (future: DimmerPoint, ShutterPoint, etc.)
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

### Point Factory (`point_factory.py`)

Creates points from JSON configuration. Point ID format: `/{RoomName}/{PointName}`

### Adding a New Point Type

1. Create a new class inheriting from `Point`
2. Add a new `CONFIG_POINT_TYPE_*` constant
3. Add a new `elif` branch in `PointFactory.createPoint()`
4. Add corresponding OpenHAB Thing channel, Item, and Sitemap entry

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

### Thing Definition Pattern

MQTT-controlled points follow this pattern in `orzechowa.things`:

```
Type switch : channelId [
  stateTopic="/{ActorName}/Out/{Room}/{Point}",
  commandTopic="/{ActorName}/In/{Room}/{Point}",
  on="ON", off="OFF"
]
```

### Item Definition Pattern

Items in `orzechowa.items` follow:

```
Switch  ItemName  "Label"  <icon>  (Groups)  {channel="mqtt:topic:bridgeId:thingId:channelId", homekit="Lighting"}
```

### Light Groups

Groups with aggregation functions allow controlling multiple lights:
- `Group:Switch:AND(ON, OFF)` — all-on / all-off semantics
- `Group:Switch:OR(ON, OFF)` — any-on semantics (used for ceiling light groups)

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
| `point_factory.py` | `test_point_factory.py` | Point creation, validation errors |
| `room.py` | `test_room.py` | Room init, point delegation |
| `rooms_service.py` | `test_rooms_service.py` | Room lookup, status routing |

> [!NOTE]
> The test file for hub communication has a typo in its name:
> `test_hub_comminication_service.py` (double `i` missing). Do NOT rename it
> without user approval as it may be referenced in CI or scripts.

---

## Adding a New Room or Light Point

### Workflow: Add a New GPIO-Controlled Light

1. **Wire the hardware** — connect relay to a free GPIO output pin, button to a free GPIO input pin
2. **Update `config.json`** — add a point entry under the appropriate room (or create a new room)
3. **Update `orzechowa.things`** — add a new `Type switch` channel with matching MQTT topics
4. **Update `orzechowa.items`** — add a new `Switch` item linked to the thing channel, with HomeKit tag
5. **Update `orzechowa.sitemap`** — add the item to the appropriate frame
6. **Deploy** — `git push`, then on the Pi: `git pull` + restart actor + reinstall OpenHAB config

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
> - **MQTT topics must be consistent** across `config.json`, `orzechowa.things`, and `orzechowa.rules`
> - **The actor uses `signal.pause()`** — it blocks the main thread and relies on MQTT callbacks and GPIO interrupts
> - **No authentication on MQTT** — Mosquitto runs without passwords (local network only)
> - **Labels are in Polish** — OpenHAB UI labels use Polish language; maintain this convention
> - **The `install-config.sh` script is destructive** — it deletes all existing OpenHAB config before copying new files
> - **Service depends on `mosquitto.service`** — MQTT broker must start before psh-actor
