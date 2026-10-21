#!/bin/bash
# Read-only readiness check for /pkam-deploy. Changes nothing on the Pi.
# Run from the dev machine:
#   ssh -o BatchMode=yes pkam-pi 'bash -s' < .agents/skills/pkam-deploy/check-pi-ready.sh
# Output: one line per check — PASS / FAIL (required, deploy must stop) /
# WARN (optional, some checks get SKIPPED or the user runs sudo lines).

REPO=/home/pshactor/PkamSmartHome
fails=0

pass() { echo "PASS  $1${2:+ — $2}"; }
fail() { echo "FAIL  $1${2:+ — $2}"; fails=$((fails + 1)); }
warn() { echo "WARN  $1${2:+ — $2}"; }

# --- Required -------------------------------------------------------------

[ "$(id -un)" = pshactor ] && pass "user" "pshactor" || fail "user" "logged in as $(id -un), expected pshactor"
for g in sudo gpio; do
    id -nG | grep -qw "$g" && pass "group $g" || fail "group $g" "pshactor not in group $g"
done

if [ -d "$REPO/.git" ]; then
    pass "repo" "$REPO"
    cd "$REPO"
    branch=$(git branch --show-current)
    if [ -n "$branch" ]; then
        pass "branch" "$branch"
        upstream=$(git rev-parse --abbrev-ref '@{u}' 2>/dev/null)
        if [ -z "$upstream" ]; then
            fail "upstream" "branch $branch does not track an origin branch — git pull would fail"
        elif [ "$(git rev-list --count '@{u}..HEAD')" -ne 0 ]; then
            fail "upstream" "$branch has commits not on $upstream (made on the Pi?)"
        else
            pass "upstream" "$upstream"
        fi
    else
        warn "branch" "detached at $(git rev-parse --short HEAD) (e.g. after a rollback) — name the ref to deploy explicitly"
        [ -n "$(git branch -r --contains HEAD)" ] \
            && pass "HEAD on origin" \
            || fail "HEAD on origin" "detached commit is not on any origin branch"
    fi
    [ -z "$(git status --porcelain)" ] && pass "working tree clean" || fail "working tree clean" "local changes on the Pi"
    url=$(git remote get-url origin 2>/dev/null)
    [ "$url" = git@github.com:piotrkaminski/PkamSmartHome.git ] && pass "origin" "$url" || fail "origin" "got '${url:-none}'"
    GIT_SSH_COMMAND="ssh -o BatchMode=yes" timeout 20 git ls-remote -q origin HEAD >/dev/null 2>&1 \
        && pass "GitHub access" "fetch works without prompts" \
        || fail "GitHub access" "pshactor cannot fetch from GitHub non-interactively"
else
    fail "repo" "$REPO not cloned"
fi

for s in psh-actor openhab mosquitto; do
    st=$(systemctl is-active "$s" 2>/dev/null)
    [ "$st" = active ] && pass "service $s" "active" || fail "service $s" "${st:-unknown}"
done
[ "$(systemctl is-enabled psh-actor 2>/dev/null)" = enabled ] && pass "psh-actor enabled" || fail "psh-actor enabled" "run install-service.sh"

for t in git python3 curl dpkg mosquitto_pub mosquitto_sub pinctrl; do
    command -v "$t" >/dev/null && pass "tool $t" || fail "tool $t" "missing"
done
python3 -c 'import paho.mqtt, gpiozero' 2>/dev/null \
    && pass "python packages" "paho-mqtt, gpiozero" \
    || fail "python packages" "run psh-actor/install-environment.sh"
[ -d "$REPO/psh-actor/logs" ] && pass "actor logs dir" || fail "actor logs dir" "run psh-actor/install-environment.sh"

code=$(curl -s -o /dev/null -w '%{http_code}' localhost:8080/rest/sitemaps/orzechowa)
[ "$code" = 200 ] && pass "OpenHAB REST" "sitemap orzechowa 200" || fail "OpenHAB REST" "sitemap orzechowa returned $code"

# --- Optional -------------------------------------------------------------

if [ -s ~/.openhab-token ]; then
    perm=$(stat -c %a ~/.openhab-token)
    [ "$perm" = 600 ] || warn "token permissions" "~/.openhab-token is $perm, should be 600"
    code=$(curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $(cat ~/.openhab-token)" localhost:8080/rest/things)
    [ "$code" = 200 ] && pass "OpenHAB token" "works" || warn "OpenHAB token" "/rest/things returned $code — token invalid or revoked"
else
    warn "OpenHAB token" "~/.openhab-token missing — Things/rules checks will be SKIPPED"
fi

sudo -n true 2>/dev/null && pass "sudo" "passwordless" || warn "sudo" "asks for a password — user runs sudo lines via '! ssh -t pkam-pi ...'"
[ -r /var/log/openhab/openhab.log ] && pass "openhab.log readable" || warn "openhab.log readable" "'Models loaded' check will be SKIPPED"

tz=$(timedatectl show -p Timezone --value 2>/dev/null)
[ "$tz" = Europe/Warsaw ] && pass "OS timezone" "$tz" || warn "OS timezone" "$tz, expected Europe/Warsaw"
jvm=$(grep -o 'user.timezone=[^ "]*' /etc/default/openhab 2>/dev/null | sort -u)
[ "$jvm" = user.timezone=Europe/Warsaw ] && pass "JVM timezone" "Europe/Warsaw" \
    || warn "JVM timezone" "/etc/default/openhab has: $(echo ${jvm:-none} | tr '\n' ' ')— expected one user.timezone=Europe/Warsaw"

echo
[ "$fails" -eq 0 ] && echo "READY (required checks passed)" || echo "NOT READY: $fails required check(s) failed"
exit "$fails"
