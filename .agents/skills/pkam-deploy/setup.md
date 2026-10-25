# `/pkam-deploy --setup` — set up a fresh openHABian Pi

Takes a Pi on which openHABian's first boot has finished, plus key-based SSH
access as `openhabian`, to the state the normal deploy expects (SKILL.md →
Prerequisites R1–R7, O1, O2, O4). It ends by running `/pkam-deploy --verify-only`.

Steps marked **USER** need a password, a browser or a GitHub login. Ask for them
one at a time, wait for "done", then check the result yourself. Never ask the user
to paste a password or token into the chat. They type it in their own terminal (or
after `!`) when a command prompts for it.

## Access

| Alias | User | Used for |
|-------|------|----------|
| `pkam-pi-setup` | `openhabian` | This setup: read-only checks and `sudo -n /usr/local/sbin/pkam-setup <step>` |
| `pkam-pi` | `pshactor` | The normal deploy, from Phase 4 on |

Both aliases must point to the same `HostName`. For a test Pi, point both at it,
and switch `pkam-pi` back to the production Pi when testing is over (say so in the
final report). If `ssh -o BatchMode=yes pkam-pi-setup true` fails, stop and tell the
user (Phase 0). Never try passwords, other users or other hosts.

The only root access the agent gets is `pkam-setup.sh`, installed root-owned as
`/usr/local/sbin/pkam-setup` with a sudoers rule just for that file. Its
`actor` step runs the repo's own `install-config.sh` and `install-service.sh` as
root, so for the length of the setup, root access covers whatever is on the deployed
branch. `finish` (Phase 5) removes the helper and the rule. Always run it, even after
a failed setup.

## Phase 0 — Access (USER, then check)

Ask the user to:

1. **Confirm the host key.** A reflashed card has a new key, so SSH refuses with
   `REMOTE HOST IDENTIFICATION HAS CHANGED`. Never bypass that check yourself
   (no `StrictHostKeyChecking=no`, no editing `known_hosts`). The user runs
   `ssh-keygen -R <pi-ip>`. If they want to verify the new key, they compare it with
   `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` on the Pi's own console.
2. **Copy the dev key:** `ssh-copy-id -i ~/.ssh/id_rsa.pub openhabian@<pi-ip>`. On a
   fresh image the password is `openhabian`. It gets changed in Phase 1.
3. **Add the alias** to `~/.ssh/config` on the dev machine (or let you add it):
   ```
   Host pkam-pi-setup
       HostName <pi-ip>
       User openhabian
       IdentityFile ~/.ssh/id_rsa
       IdentitiesOnly yes
   ```

Check: `ssh -o BatchMode=yes pkam-pi-setup true`. Then read the first-boot result
(read-only), because openHABian reports "successfully finished" even when Java and
openHAB failed to install:

```bash
ssh pkam-pi-setup 'grep -h "FAILED" /boot/firmware/first-boot.log /boot/first-boot.log 2>/dev/null | tail -20; java -version 2>&1 | head -1; dpkg-query -W "openhab*" 2>&1'
```

(If neither log exists, `curl -s http://<pi-ip>:81/first-boot.txt` serves the
same file until the next reboot.) Report what failed. The steps below
repair the usual failures: missing Java, missing openHAB, and dead Raspbian mirrors.

## Phase 1 — Bootstrap the helper (USER, one terminal session)

Copy the helper to the Pi and show its hash:

```bash
scp .agents/skills/pkam-deploy/pkam-setup.sh pkam-pi-setup:/tmp/pkam-setup.sh
shasum -a 256 .agents/skills/pkam-deploy/pkam-setup.sh
```

Then ask the user to run the block below in their terminal. It asks for the
`openhabian` sudo password once, then for new passwords. Tell them first:

- **`pshactor` password**: used later whenever a deploy needs `sudo`.
- **New `openhabian` password**: replaces the default `openhabian`.

```bash
ssh -t pkam-pi-setup '
  sha256sum /tmp/pkam-setup.sh &&
  sudo install -o root -g root -m 755 /tmp/pkam-setup.sh /usr/local/sbin/pkam-setup &&
  echo "openhabian ALL=(root) NOPASSWD: /usr/local/sbin/pkam-setup" | sudo tee /etc/sudoers.d/pkam-setup >/dev/null &&
  sudo chmod 440 /etc/sudoers.d/pkam-setup && sudo visudo -cf /etc/sudoers.d/pkam-setup &&
  sudo pkam-setup create-user &&
  echo "--- new password for pshactor:" && sudo passwd pshactor &&
  echo "--- change the openhabian password:" && passwd'
```

The hash printed on the Pi must equal the local `shasum`. Check:
`ssh pkam-pi-setup 'sudo -n /usr/local/sbin/pkam-setup status'`. `create-user`
must be DONE with "password set".

If `pkam-setup.sh` changes later in the setup, the user re-runs only the first
four lines of the block.

## Phase 2 — System, Java, openHAB, Mosquitto (agent)

Show the plan and get one explicit yes. The plan lists the host name (ask the user
which one they want; the default is to keep `openhabian`), the openHAB version that
will be held (known-good `5.1.4-1`, or the newer one already installed: it is
kept, never downgraded, and the plan says it is untested), `EXTRA_JAVA_OPTS` overwritten with the known-good line,
timezone `Europe/Warsaw`, I2C/SPI turned off (needs a reboot), apt switched to the fixed Raspbian mirror, and Mosquitto with no authentication on localhost. Then:

```bash
for s in mirror system java openhab mosquitto; do
  ssh pkam-pi-setup "sudo -n /usr/local/sbin/pkam-setup $s" || break
done
ssh pkam-pi-setup 'sudo -n /usr/local/sbin/pkam-setup hostname <name>'   # only if a new name was given
ssh pkam-pi-setup 'sudo -n /usr/local/sbin/pkam-setup status'
```

- `mirror` points apt at one fixed Raspbian mirror instead of the
  `raspbian.raspberrypi.com` redirector, which picks mirrors per file, including
  dead and Russian ones. **The user does not want Russian or Belarusian
  mirrors:** never add a `.ru` / `.by` mirror, and never suggest one in a manual fix.
- `java` / `openhab` / `mosquitto` lines with `got <file> from <mirror>` mean the
  dead-mirror fallback worked. Mention it in the report.
- `system` turns off I2C and SPI in `/boot/firmware/config.txt`, because
  `config.json` uses their pins (BCM 2/3 and 9–11) as plain GPIO. When it prints
  `REBOOT NEEDED`, the Pi must reboot before Phase 4 (put the reboot in the plan;
  the user runs `ssh -t pkam-pi-setup sudo reboot`). Until then `psh-actor` fails
  with `lgpio.error: 'unexpected error'`.
- `openhab` waits up to 10 minutes for REST. A Pi 3 is slow on first start.
- A `WARNING: openhab <version> is not the known-good ...` line does not stop the
  setup. Carry it into the final report and point to readme → Known-good versions
  (32-bit risk). It appears when a newer openHAB is already installed, or when
  5.1.4-1 is no longer in the repo and the newest one was installed instead.
- On any `ERROR:` line, stop, show it, and fix the cause in the repo, not on the
  Pi. Re-running a step is safe.

## Phase 3 — Accounts outside the Pi (USER)

1. **GitHub deploy key.** Show the `pshactor` public key from the `create-user`
   output (or `ssh pkam-pi 'cat ~/.ssh/id_ed25519.pub'`; `openhabian` cannot read pshactor's home). The
   user adds it under GitHub → repo → Settings → Deploy keys, with write access off.
   Check: `status` line `actor` says "GitHub access OK".
2. **openHAB admin account.** The user opens `http://<pi-ip>:8080` and creates
   the admin user. In the setup wizard they set the location, skip the proposed
   storage add-ons, and **skip installing discovered add-ons**, because add-ons
   come from `openhab/services/addons.cfg`.
3. **API token** (enables the token-only deploy checks): user name (bottom left) →
   *Create new API token*. It must be saved as `pshactor`, so this waits until the
   alias works (Phase 4). The user runs:
   ```bash
   ssh -t pkam-pi 'umask 077; read -rsp "Token: " T; printf %s "$T" > ~/.openhab-token; echo'
   ```

## Phase 4 — Repo, actor, config (agent)

Ask which branch to deploy (default `master`). Point `pkam-pi` at the Pi (Access
above). Check `ssh -o BatchMode=yes pkam-pi true`: `create-user` copied the
dev key. In the plan, list what this changes:

- `psh-actor` starts and **resets every GPIO point** on this Pi's pins.
- `install-config.sh` installs the add-ons from `addons.cfg`.

**Warning to give before adding Things from the Inbox:** on a test Pi, adding
Shelly or TP-Link Things lets its rules drive the real blinds and lamps, alongside
the production Pi. Only add them on the Pi that is meant to take over.

After a yes:

```bash
ssh pkam-pi-setup 'sudo -n /usr/local/sbin/pkam-setup actor <branch>'
ssh pkam-pi-setup 'sudo -n /usr/local/sbin/pkam-setup status'
```

Wait ~2 minutes for the add-ons to install, then do Phase 3 step 3 (token) if not
done yet.

## Phase 5 — Remove the helper, then verify

```bash
ssh pkam-pi-setup 'sudo -n /usr/local/sbin/pkam-setup status; sudo -n /usr/local/sbin/pkam-setup finish'
ssh pkam-pi-setup 'sudo -n true 2>&1; ls /etc/sudoers.d/'   # must ask for a password; no pkam-setup
```

Then run the normal readiness check (SKILL.md Step 0) and `--verify-only` against
`pkam-pi`. Report:

- every phase with DONE/FAILED
- mirror fallbacks used
- WARNs from Step 0
- the verify table
- what the user still has to do: Inbox Things, or restoring the JSON database
  from the old Pi (readme → "Recovery after SD card failure" step 2–3), and
  pointing `pkam-pi` back if this was a test Pi
