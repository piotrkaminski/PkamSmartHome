#!/bin/bash
# Root helper for `/pkam-deploy --setup` on a freshly installed openHABian Pi.
# Installed by the user (bootstrap in setup.md) as root-owned /usr/local/sbin/pkam-setup,
# with a sudoers rule that lets `openhabian` run only this file without a password.
# `pkam-setup finish` removes both.
#
# Usage: sudo pkam-setup <step> [arg]
#   status              read-only: one DONE/TODO line per step
#   create-user         create pshactor (no password yet), groups, SSH keys
#   mirror              point apt at RASPBIAN_MIRROR instead of the redirector
#   system              timezone, base packages, group memberships
#   java                OpenJDK 21 (with dead-mirror fallback)
#   openhab             openHAB (known-good 5.1.4, or a newer one already installed) held, JVM options, service enabled
#   mosquitto           Mosquitto broker on localhost:1883, no auth
#   hostname <name>     set the host name
#   actor <branch>      clone repo as pshactor, install env, config, service
#   finish              remove this helper and its sudoers rule
# Every step is idempotent: re-running a DONE step changes nothing.

set -u
export DEBIAN_FRONTEND=noninteractive

# Last version confirmed on the house Pi (readme: Known-good versions). A newer installed
# version is kept with a WARNING, never downgraded.
OPENHAB_KNOWN_GOOD=5.1.4-1
JAVA_PKG=openjdk-21-jre-headless
TZ_NAME=Europe/Warsaw
JAVA_OPTS='EXTRA_JAVA_OPTS="-Xms192m -Xmx384m -XX:-TieredCompilation -XX:TieredStopAtLevel=1 -XX:+ExitOnOutOfMemoryError -Dxtext.qn.interning=true -Duser.timezone=Europe/Warsaw"'
REPO_URL=git@github.com:piotrkaminski/PkamSmartHome.git
ACTOR=pshactor
ACTOR_HOME=/home/$ACTOR
REPO=$ACTOR_HOME/PkamSmartHome
# GitHub's published ed25519 host key fingerprint (docs.github.com, "GitHub's SSH key fingerprints").
GITHUB_ED25519_FP=SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU
# The user does not want Russian or Belarusian mirrors. raspbian.raspberrypi.com
# is a redirector that picks a mirror per file (it used mirror.truenetwork.ru and a
# dead ftp.icm.edu.pl), so apt is pointed at one fixed mirror and the fallbacks are
# fixed too. Never add a .ru / .by mirror or the redirector here.
RASPBIAN_MIRROR=http://ftp.halifax.rwth-aachen.de/raspbian/raspbian
FALLBACK_MIRRORS="${PKAM_FALLBACK_MIRRORS:-http://mirror.netcologne.de/raspbian/raspbian http://mirror.init7.net/raspbian/raspbian http://mirrors.ocf.berkeley.edu/raspbian/raspbian}"
APT_SOURCES="/etc/apt/sources.list /etc/apt/sources.list.d/*.list /etc/apt/sources.list.d/*.sources"
UNWANTED_SOURCES='raspbian\.raspberrypi\.com|https?://[^/ ]*\.(ru|by)/'

die() { echo "ERROR: $*" >&2; exit 1; }
log() { echo "== $*"; }

[ "$(id -u)" = 0 ] || die "run with sudo"

# apt-get install with a retry for .debs that failed to download: each missing
# file is fetched from FALLBACK_MIRRORS, checked against the SHA256 from the
# signed apt index (apt prints MD5Sum, SHA256 or SHA512 there), and put in
# apt's cache. apt re-checks cached files against the index itself.
apt_install() {
    apt-get install -y -o DPkg::Lock::Timeout=120 "$@" && return 0
    log "apt failed — retrying missing .debs from fallback mirrors"
    apt-get install -y --print-uris -qq "$@" | tr -d "'" | while read -r url file _size hash; do
        case $url in */pool/*) ;; *) continue ;; esac
        [ -f "/var/cache/apt/archives/$file" ] && continue
        path=pool/${url#*/pool/}
        case ${hash%%:*} in
            MD5Sum) sum=md5sum ;; SHA256) sum=sha256sum ;; SHA512) sum=sha512sum ;;
            *) echo "   unknown hash type for $file: $hash"; continue ;;
        esac
        for m in $FALLBACK_MIRRORS; do
            tmp=/var/cache/apt/archives/partial/$file
            if curl -fsSL -m 300 -o "$tmp" "$m/$path" && [ "$($sum < "$tmp" | cut -d' ' -f1)" = "${hash#*:}" ]; then
                mv "$tmp" "/var/cache/apt/archives/$file"; echo "   got $file from $m"; break
            fi
            rm -f "$tmp"; echo "   $m: failed for $file"
        done
    done
    apt-get install -y -o DPkg::Lock::Timeout=120 "$@"
}

# db:Status-Status, not Status: a held package reads "hold ok installed".
is_installed() { [ "$(dpkg-query -W -f='${db:Status-Status}' "$1" 2>/dev/null)" = installed ]; }
installed_version() { is_installed "$1" && dpkg-query -W -f='${Version}' "$1"; }
in_group() { id -nG "$1" 2>/dev/null | tr ' ' '\n' | grep -qx "$2"; }
line() { printf '%-5s %-12s %s\n' "$1" "$2" "${3:-}"; }

step_status() {
    bad=$(grep -lE "$UNWANTED_SOURCES" $APT_SOURCES 2>/dev/null | tr '\n' ' ')
    [ -z "$bad" ] && line DONE mirror "$RASPBIAN_MIRROR" || line TODO mirror "redirector or .ru/.by mirror in: $bad"
    id "$ACTOR" >/dev/null 2>&1 && [ -s "$ACTOR_HOME/.ssh/authorized_keys" ] && [ -s "$ACTOR_HOME/.ssh/id_ed25519.pub" ] \
        && line DONE create-user "$(passwd -S "$ACTOR" | awk '{print ($2=="P") ? "password set" : "NO PASSWORD (user must run: sudo passwd pshactor)"}')" \
        || line TODO create-user
    [ "$(timedatectl show -p Timezone --value)" = "$TZ_NAME" ] && in_group "$ACTOR" openhab && command -v pip3 >/dev/null \
        && line DONE system || line TODO system
    is_installed "$JAVA_PKG" && line DONE java "$(java -version 2>&1 | head -1)" || line TODO java
    v=$(installed_version openhab)
    if [ -n "$v" ] && dpkg --compare-versions "$v" ge "$OPENHAB_KNOWN_GOOD" \
        && [ "$(installed_version openhab-addons)" = "$v" ] && grep -qxF "$JAVA_OPTS" /etc/default/openhab 2>/dev/null; then
        newer=; [ "$v" != "$OPENHAB_KNOWN_GOOD" ] && newer=" (WARNING: newer than known-good $OPENHAB_KNOWN_GOOD)"
        line DONE openhab "$v$newer, $(apt-mark showhold | grep -c '^openhab') packages held, service $(systemctl is-active openhab)"
    else
        line TODO openhab "${v:-not installed}"
    fi
    is_installed mosquitto && is_installed mosquitto-clients && ss -ltn | grep -q '127.0.0.1:1883\|\[::1\]:1883' \
        && line DONE mosquitto "$(dpkg-query -W -f='${Version}' mosquitto)" || line TODO mosquitto
    line INFO hostname "$(hostname)"
    if [ -d "$REPO/.git" ] && systemctl is-enabled psh-actor >/dev/null 2>&1; then
        line DONE actor "$(sudo -u "$ACTOR" git -C "$REPO" branch --show-current), psh-actor $(systemctl is-active psh-actor)"
    else
        sudo -u "$ACTOR" GIT_SSH_COMMAND="ssh -o BatchMode=yes" timeout 20 git ls-remote -q "$REPO_URL" HEAD >/dev/null 2>&1 \
            && line TODO actor "GitHub access OK" \
            || line TODO actor "GitHub access missing — add $ACTOR_HOME/.ssh/id_ed25519.pub as a read-only deploy key"
    fi
    [ -s "$ACTOR_HOME/.openhab-token" ] && line DONE token || line TODO token "user stores an openHAB API token (setup.md)"
}

step_create_user() {
    id "$ACTOR" >/dev/null 2>&1 || adduser --disabled-password --gecos "" "$ACTOR"
    for g in sudo gpio; do usermod -aG "$g" "$ACTOR"; done
    install -d -m 700 -o "$ACTOR" -g "$ACTOR" "$ACTOR_HOME/.ssh"
    # Same dev-machine key that already logs in as openhabian.
    src=/home/openhabian/.ssh/authorized_keys
    [ -s "$src" ] || die "$src is empty — run ssh-copy-id for openhabian first"
    touch "$ACTOR_HOME/.ssh/authorized_keys"
    while read -r k; do grep -qxF "$k" "$ACTOR_HOME/.ssh/authorized_keys" || echo "$k" >> "$ACTOR_HOME/.ssh/authorized_keys"; done < "$src"
    [ -f "$ACTOR_HOME/.ssh/id_ed25519" ] || sudo -u "$ACTOR" ssh-keygen -q -t ed25519 -N "" -C "$ACTOR@$(hostname)" -f "$ACTOR_HOME/.ssh/id_ed25519"
    if ! sudo -u "$ACTOR" ssh-keygen -F github.com -f "$ACTOR_HOME/.ssh/known_hosts" >/dev/null 2>&1; then
        key=$(ssh-keyscan -t ed25519 github.com 2>/dev/null | grep -v '^#')
        fp=$(echo "$key" | ssh-keygen -lf - | awk '{print $2}')
        [ "$fp" = "$GITHUB_ED25519_FP" ] || die "github.com host key fingerprint $fp does not match $GITHUB_ED25519_FP"
        echo "$key" >> "$ACTOR_HOME/.ssh/known_hosts"
    fi
    chown -R "$ACTOR:$ACTOR" "$ACTOR_HOME/.ssh"; chmod 600 "$ACTOR_HOME/.ssh/authorized_keys"
    log "GitHub deploy key for $ACTOR (read-only):"; cat "$ACTOR_HOME/.ssh/id_ed25519.pub"
}

step_mirror() {
    bad=$(grep -lE "$UNWANTED_SOURCES" $APT_SOURCES 2>/dev/null)
    for f in $bad; do
        install -d -m 700 /root/pkam-setup-backup
        cp -a "$f" "/root/pkam-setup-backup/$(basename "$f")"
        sed -i -E "s#https?://raspbian\.raspberrypi\.com/raspbian/?#$RASPBIAN_MIRROR/#g" "$f"
        grep -qE "$UNWANTED_SOURCES" "$f" && die "$f still has an unwanted source — fix it by hand: $(grep -E "$UNWANTED_SOURCES" "$f")"
        echo "   $f -> $RASPBIAN_MIRROR (backup in /root/pkam-setup-backup)"
    done
    apt-get update -o DPkg::Lock::Timeout=120 || die "apt-get update failed with $RASPBIAN_MIRROR"
}

step_system() {
    timedatectl set-timezone "$TZ_NAME"
    apt_install git curl python3-pip
    getent group openhab >/dev/null || groupadd --system openhab
    # pshactor reads openhab.log (deploy check "Models loaded"); openhabian edits /etc/openhab.
    for u in "$ACTOR" openhabian; do usermod -aG openhab "$u"; done
}

step_java() {
    is_installed "$JAVA_PKG" || apt_install "$JAVA_PKG"
    java -version
}

step_openhab() {
    is_installed "$JAVA_PKG" || die "run the java step first"
    apt-get update -o DPkg::Lock::Timeout=120 >/dev/null
    # Keep an installed version at or above known-good (never downgrade); otherwise install
    # known-good, or the newest available one if known-good is gone from the repo.
    v=$(installed_version openhab)
    if [ -z "$v" ] || dpkg --compare-versions "$v" lt "$OPENHAB_KNOWN_GOOD"; then
        if apt-cache madison openhab | grep -q " $OPENHAB_KNOWN_GOOD "; then
            v=$OPENHAB_KNOWN_GOOD
        else
            v=$(apt-cache madison openhab | awk '{print $3}' | sort -V | tail -1)
            [ -n "$v" ] || die "no openhab package in the configured apt repos"
        fi
    fi
    if [ "$v" != "$OPENHAB_KNOWN_GOOD" ]; then
        echo "WARNING: openhab $v is not the known-good $OPENHAB_KNOWN_GOOD — check its release notes for 32-bit (armhf) and Java support (readme: Known-good versions). Continuing."
    fi
    apt-mark unhold openhab openhab-addons >/dev/null 2>&1
    if [ "$(installed_version openhab)" != "$v" ] || [ "$(installed_version openhab-addons)" != "$v" ]; then
        apt_install "openhab=$v" "openhab-addons=$v"
    fi
    apt-mark hold openhab openhab-addons
    log "openhab $v held"
    f=/etc/default/openhab
    if ! grep -qxF "$JAVA_OPTS" "$f"; then
        cp -a "$f" "$f.pkam-setup.bak"
        sed -i '/^[[:space:]]*EXTRA_JAVA_OPTS=/d' "$f"
        echo "$JAVA_OPTS" >> "$f"
    fi
    systemctl daemon-reload
    systemctl enable openhab
    systemctl restart openhab
    log "waiting for openHAB REST (a Pi 3 needs several minutes on first start)"
    # Jetty answers 404 before the REST bundle is up, so wait for the version, not any reply.
    for _ in $(seq 60); do curl -s localhost:8080/rest/ | grep -q '"version"' && break; sleep 10; done
    curl -s localhost:8080/rest/ | grep -o '"version":"[^"]*"' || die "openHAB REST not up after 10 min — check /var/log/openhab/openhab.log"
}

step_mosquitto() {
    apt_install mosquitto mosquitto-clients
    systemctl enable --now mosquitto
    # Mosquitto 2 with no listener configured = localhost:1883, anonymous allowed.
    sleep 2; ss -ltn | grep ':1883' || die "mosquitto is not listening on 1883"
}

step_hostname() {
    name=${1:-}
    [[ $name =~ ^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$ ]] || die "invalid host name '$name'"
    hostnamectl set-hostname "$name"
    sed -i "s/^127\.0\.1\.1[[:space:]].*/127.0.1.1\t$name/" /etc/hosts
    grep -q '^127\.0\.1\.1' /etc/hosts || printf '127.0.1.1\t%s\n' "$name" >> /etc/hosts
    hostname
}

step_actor() {
    branch=${1:-}
    [[ $branch =~ ^[A-Za-z0-9._/-]+$ ]] || die "invalid branch '$branch'"
    as_actor() { sudo -u "$ACTOR" -H GIT_SSH_COMMAND="ssh -o BatchMode=yes" "$@"; }
    [ -d "$REPO/.git" ] || as_actor git clone -q "$REPO_URL" "$REPO" || die "clone failed — is the deploy key added on GitHub?"
    as_actor git -C "$REPO" fetch -q origin
    as_actor git -C "$REPO" checkout -q "$branch"
    as_actor git -C "$REPO" pull -q --ff-only
    # Same as psh-actor/install-environment.sh, split by user: pip and logs as pshactor, /dev/mem as root.
    (cd "$REPO/psh-actor" && as_actor pip3 install -q -r requirements.txt --break-system-packages && as_actor mkdir -p logs) || die "install-environment failed"
    chown root:gpio /dev/mem && chmod g+rw /dev/mem
    (cd "$REPO/openhab" && ./install-config.sh) || die "install-config.sh failed"
    (cd "$REPO/linux-service" && ./install-service.sh) || die "install-service.sh failed"
    sleep 5; systemctl is-active psh-actor
}

step_finish() {
    rm -f /etc/sudoers.d/pkam-setup /usr/local/sbin/pkam-setup || die "could not remove the helper — remove it by hand"
    echo "pkam-setup helper and its sudoers rule removed"
}

case "${1:-}" in
    status)      step_status ;;
    mirror)      step_mirror ;;
    create-user) step_create_user ;;
    system)      step_system ;;
    java)        step_java ;;
    openhab)     step_openhab ;;
    mosquitto)   step_mosquitto ;;
    hostname)    step_hostname "${2:-}" ;;
    actor)       step_actor "${2:-}" ;;
    finish)      step_finish ;;
    *) die "unknown step '${1:-}' — see the header of this file" ;;
esac
