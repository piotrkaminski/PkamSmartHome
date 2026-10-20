# Installation

## Known-good versions

This is the last combination confirmed working on the house Pi (recorded 2026-10-20,
openHAB installed 2026-06-28). The Pi is a 32-bit Raspberry Pi 3 — newer openHAB,
Java or OS releases may drop support for it, so when reinstalling, **start from these
versions** and upgrade only after checking the openHAB release notes for 32-bit
(`armhf` / ARMv7) and Java requirements.

| Component | Version |
|-----------|---------|
| Hardware | Raspberry Pi 3 Model B Rev 1.2, 1 GB RAM |
| Architecture | `armhf` (32-bit userland), kernel `6.18.34+rpt-rpi-v7` (`armv7l`) |
| OS image | Raspberry Pi OS reference image 2025-12-04 → Raspbian GNU/Linux 13 (trixie) |
| openHABian | branch `openHAB`, commit `7abab950` (2026-02-09) |
| openHAB | `openhab` **5.1.4-1** + `openhab-addons` **5.1.4-1** (Release Build) |
| Java | OpenJDK **21.0.10** (`openjdk-21-jre-headless 21.0.10+7-1~deb13u1+rpi1`, Client VM) |
| Mosquitto | 2.0.21-1 |
| Python | 3.13.5 |
| Python packages | `paho-mqtt` 2.1.0, `gpiozero` 2.0.1 |

JVM options in `/etc/default/openhab` that work on this 1 GB Pi:

```
EXTRA_JAVA_OPTS="-Xms192m -Xmx384m -XX:-TieredCompilation -XX:TieredStopAtLevel=1 -XX:+ExitOnOutOfMemoryError -Dxtext.qn.interning=true -Duser.timezone=Europe/Warsaw"
```

**Installing this exact openHAB version** (if it is still in the openHAB apt
repository) and preventing accidental upgrades:

```bash
sudo apt install openhab=5.1.4-1 openhab-addons=5.1.4-1
sudo apt-mark hold openhab openhab-addons
# later, to allow upgrades again:
sudo apt-mark unhold openhab openhab-addons
```

Check what is actually installed:

```bash
dpkg-query -W -f='${Package} ${Version}\n' 'openhab*'
curl -s http://localhost:8080/rest/ | grep -o '"version":"[^"]*"'
java -version
```

Update this table after every successful upgrade or reinstall.

## Install openHabian with OpenHab

1. Install latest stable version of openHABian on SD card using instruction https://www.openhab.org/docs/installation/openhabian.html
    1. First boot requires to be connect to internet via cable (preferably) and can take a first long coffee break (~1 hour 15 minutes)
    1. You can watch progress on http://your-ip:81/ page.
    1. Initial login and passwords to operating system are `openhabian/openhabian`
1. Login to operating system shell as `openhabian`. Execute `sudo openhabian-config` to set following configuration:
    1. Set you host name (menu 30 -> 31)
    1. Install Mosquitto (menu 20 -> 23), use blank password for unencrypted communication despite of insisting for prividing password.
1. Change password for `openhubian` 
    1. Type in terminal `passwd`. provide current password `openhabian` and change to different one.
1. Open openHAB console on page http://your-ip:8080
    1. Create admin account
    1. Begin setup
    1. Point location or you home
    1. Skip proposed storage Add-ons
    1. Skip install discovered Add-ons, it is safer to install them manually in later phase, one by one.
    1. Install all Add-ons listed in [Required openHAB Add-ons](#required-openhab-add-ons) below.
1. Back to terminal and create `pshactor` user. This account will be used for PkamSmartHome actor service.
    1. Execute `sudo adduser pshactor`
    1. Provide additional details if would like to.
    1. Execute `sudo usermod -aG sudo pshactor`
    1. Exectue `sudo usermod -a -G gpio pshactor`
    1. Exectue `sudo chown root:gpio /dev/mem && sudo chmod g+rw /dev/mem`
1. Reboot system `sudo reboot`

## Required openHAB Add-ons

The configuration files in `openhab/` will **not** load unless every Add-on below is
installed. A missing Add-on does not always raise a visible error — Things stay
`UNINITIALIZED` and the linked Items silently remain `NULL`, so install them all before
running `install-config.sh`.

### Bindings

| Add-on | Add-on ID | Used by | Needed for |
|--------|-----------|---------|------------|
| Astro Binding | `astro` | `astro:sun:home` | Sunrise/sunset triggers for night and Xmas light rules |
| MQTT Binding | `mqtt` | `mqtt:broker:pshActor1` | All GPIO lights driven by `psh-actor` |
| NTP Binding | `ntp` | `ntp:ntp:currentTime` | Clock item on the sitemap |
| **HTTP Binding** | `http` | `http:url:openmeteo` | **Weather forecast from Open-Meteo (heat-protection rule)** |
| Shelly Binding | `shelly` | `shelly:shellyplus2pm-roller:...` | Office window blind (`Office_WindowBlind`) |
| TP-Link Smart Home Binding | `tplinksmarthome` | `tplinksmarthome:*` | Wi-Fi plugs and dimmers (lamps, Xmas lights) |

### Transformations

| Add-on | Add-on ID | Needed for |
|--------|-----------|------------|
| **JSONPATH Transformation** | `jsonpath` | **Parsing the Open-Meteo JSON response into weather Items** |

> **Note**: JSONPATH is a *transformation*, not a binding. It lives under
> Settings -> Add-ons -> **Transformations** in the UI, not under Bindings. It is easy to
> miss. Without it the HTTP Thing comes up ONLINE but every weather Item stays `NULL`,
> and `openhab.log` reports that the transformation service is not available.

### User Interfaces & Integrations

| Add-on | Add-on ID | Needed for |
|--------|-----------|------------|
| Basic UI | `basic` | Serving `orzechowa.sitemap` and `watch.sitemap` |
| HomeKit Integration | `homekit` | Exposing Items to Apple Home (`homekit="..."` metadata) |

### Installing the Add-ons

Any one of the three methods below works — pick one.

**Option 1 — Main UI**: Settings -> Add-ons, then pick the relevant tab (Bindings /
Transformations / User Interfaces) and install each entry from the tables above.

**Option 2 — Karaf console** (fastest, installs everything in one go):

```
openhab-cli console
```

then at the `openhab>` prompt:

```
addons:install openhab-binding-astro
addons:install openhab-binding-mqtt
addons:install openhab-binding-ntp
addons:install openhab-binding-http
addons:install openhab-binding-shelly
addons:install openhab-binding-tplinksmarthome
addons:install openhab-transformation-jsonpath
addons:install openhab-ui-basic
addons:install openhab-io-homekit
```

Type `logout` to leave the console. Default console credentials are `openhab/habopen`.

**Option 3 — `addons.cfg`**: edit `/etc/openhab/services/addons.cfg` and set:

```
binding = astro,mqtt,ntp,http,shelly,tplinksmarthome
transformation = jsonpath
ui = basic
misc = homekit
```

Add-ons are installed automatically a few seconds after the file is saved.

### Verifying the Add-ons are active

```
openhab-cli console
openhab> addons:list | grep -Ei 'http|jsonpath|shelly|mqtt|astro|ntp|tplink|basic|homekit'
```

Each line should read `Installed`. To confirm the weather integration specifically,
check that the Thing is online and the Item has a value:

```
curl -s http://localhost:8080/rest/things/http:url:openmeteo | grep -o '"statusInfo":{[^}]*}'
curl -s http://localhost:8080/rest/items/Weather_Temp_Max_Today | grep -o '"state":"[^"]*"'
```

A `NULL` state alongside an `ONLINE` Thing almost always means the JSONPATH
transformation is missing.

## Fix JVM Timezone

OpenHAB runs on the JVM, which has its own timezone setting independent of the OS.
Without an explicit override the JVM may use UTC or CET (UTC+1), causing:

- **`Time cron` rules to fire 1 hour late** — e.g. the 23:00 lights-off rule
  triggers at midnight local time during summer.
- **Log timestamps 1 hour behind real time** — `openhab.log` entries show 07:00
  when the wall clock reads 08:00 (CEST = UTC+2).

**Fix** — add the timezone flag to OpenHAB's JVM options:

```bash
sudo nano /etc/default/openhab
```

Find or add the `EXTRA_JAVA_OPTS` line:

```
EXTRA_JAVA_OPTS="-Duser.timezone=Europe/Warsaw"
```

Then restart OpenHAB:

```bash
sudo systemctl restart openhab
```

**Verify** — after restart, log timestamps should match local time:

```bash
sudo journalctl -u openhab -n 5
```

## PkamSmartHome Actor installation

1. Login to terminal as `pshactor`
1. Download project
    1. Add ssh key to GitHab
    1. Download project from git
   ```
   git clone git@github.com:piotrkaminski/PkamSmartHome.git
   ```
1. Initialize PSH Actor environment
   ```
   cd ~/PkamSmartHome/psh-actor
   ./install-environment.sh
   ```
1. Update OpenHab configuration
    ```
    cd ~/PkamSmartHome/openhab
    sudo ./install-config.sh
    ```
1. Install service and set to be automatically started after machine boots
    ```
    cd ~/PkamSmartHome/linux-service
    sudo ./install-service.sh
    ```
1. Service psh-actor is already started. Status can be checked by
    ```
    sudo systemctl status psh-actor
    ```

## Add auto-discovered Things
1. Login into admin console http://your-ip:8080
1. Go to Settings -> Things -> Inbox
1. Each auto discovered Thing should be added by
    1. Click on Thing name
    2. Click 'Add as Thing'

# Configuration or Executables Update

## PkamSmartHome Actor update

This step is needed when configuration or executables (python code) for switches is updated via GitHub. Initial installation does not require this step.

1. Update code
   ```
   cd ~/PkamSmartHome
   git pull
   sudo systemctl restart psh-actor
   ```

# Reset installation 

This step puts all points into standard (initial) mode. Initial installation does not require this step.

# Reset all points in PkamSmartHome Actor
   ```
   cd ~/PkamSmartHome/psh-actor
   ./reset-all-points.sh
   ```

## OpenHub configuration update

This step is needed when items, thing or configuration files are updated or added to PkamSmartHome project, but specifically openhab configuration files, not psh-actor project python code. Initial installation does not require this step.

> **Important**: `install-config.sh` only copies `.things`, `.items`, `.rules` and
> `.sitemap` files — it does **not** install openHAB Add-ons. If a `git pull` brought in
> configuration that uses a new binding or transformation, install it first (see
> [Required openHAB Add-ons](#required-openhab-add-ons)), otherwise the new Things will
> fail to initialize.

1. Update configurations
   ```
   cd ~/PkamSmartHome
   git pull
   cd ~/PkamSmartHome/openhab
   sudo ./install-config.sh
   ```
1. Check the log for unresolved bindings or transformations
   ```
   tail -f /var/log/openhab/openhab.log
   ```

# Recovery after SD card failure

Symptoms seen on 2026-10-20: `mosquitto_pub`/`mosquitto_sub` crash with
`Segmentation fault`, Python fails with `bad marshal data`, and `dpkg --verify`
lists binaries with checksum mismatches (`??5??????`) and garbled path names
(e.g. `/usr/sHare/amsa/...`). Random bit flips across unrelated packages mean the
SD card (or power supply) is failing. Services already running keep working from
memory, but **do not reboot or restart services** until the steps below are done.

## 1. Diagnose (read-only)

```bash
dpkg --verify > /tmp/dpkg-verify.txt          # no output lines = all package files intact
awk '$2!="c" && substr($1,3,1)=="5"' /tmp/dpkg-verify.txt   # changed non-config files
sudo vcgencmd get_throttled                    # anything other than 0x0 = power problem
```

Expected (harmless) entries: changed files in `/var/lib/openhab/etc/` (openHAB
rewrites them) and missing `/etc/openhab/*/readme.txt` (deleted by
`install-config.sh`). Anything in `/usr/lib`, `/usr/share/openhab`, kernel modules
or firmware is real corruption.

## 2. Back up what is not in git

Items, rules, sitemaps, MQTT Things and `config.json` are in this repo. Shelly and
TP-Link Things, users and UI pages live only in the openHAB JSON database:

```bash
ssh -t pkam-pi 'sudo tar czf /tmp/pkam-backup.tgz /var/lib/openhab/jsondb /etc/openhab /etc/default/openhab /etc/mosquitto'
scp pkam-pi:/tmp/pkam-backup.tgz ~/Desktop/
```

## 3. Replace the card (recommended)

1. Flash a new, good-quality card (A1/A2 rated or "endurance") with the image in
   [Known-good versions](#known-good-versions), and follow [Installation](#installation).
2. Install the same openHAB version and hold it (see Known-good versions).
3. Before running `install-config.sh`, restore the JSON database with openHAB stopped:
   ```bash
   sudo systemctl stop openhab
   sudo tar xzf pkam-backup.tgz -C / var/lib/openhab/jsondb
   sudo chown -R openhab:openhab /var/lib/openhab/jsondb
   sudo systemctl start openhab
   ```
4. Re-apply the JVM options from `/etc/default/openhab` in the backup.
5. Set the OS timezone: `sudo timedatectl set-timezone Europe/Warsaw`.
6. Check power: `sudo vcgencmd get_throttled` must print `throttled=0x0`. If not,
   replace the power supply before the new card gets corrupted too.

## 4. Stopgap (only if the card cannot be replaced yet)

After the backup in step 2, reinstall the damaged packages and drop corrupted
Python caches:

```bash
sudo apt install --reinstall libmosquitto1 mosquitto-clients python3-dnspython openhab openhab-addons
sudo find /usr/lib/python3/dist-packages -name '*.pyc' -delete
```

Re-run `dpkg --verify` afterwards. Expect new corruption to appear while the card
is still failing.
