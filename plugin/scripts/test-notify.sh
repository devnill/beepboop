#!/bin/sh
# Tests for notify.sh. Stubs uname/tmux/osascript/terminal-notifier on a temp
# PATH; the tty is redirected to a temp file via BEEPBOOP_TTY.
DIR="$(cd "$(dirname "$0")" && pwd)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
BIN="$T/bin"; mkdir "$BIN"
LOG="$T/log"; TTYF="$T/tty"

mkstub() { printf '#!/bin/sh\n%s\n' "$2" > "$BIN/$1"; chmod +x "$BIN/$1"; }
mkstub osascript 'echo osascript >> "$STUBLOG"'
mkstub terminal-notifier 'echo terminal-notifier >> "$STUBLOG"'
mkstub uname 'echo "${FAKE_UNAME:-Darwin}"'
mkstub tmux 'if [ "$FAKE_TMUX_FAIL" = 1 ]; then exit 1; fi; echo "$FAKE_TMUX_PT"'

FAILS=0
# run_case name expect(fallback|nofallback) ttyfile [env assignments...]
run_case() {
    name="$1"; expect="$2"; ttyp="$3"; shift 3
    : > "$LOG"; : > "$TTYF"
    err="$(env -i PATH="$BIN:/usr/bin:/bin" HOME="$T" STUBLOG="$LOG" \
        BEEPBOOP_TTY="$ttyp" CLAUDE_PLUGIN_ROOT="$T" "$@" \
        /bin/sh "$DIR/notify.sh" T B 2>&1 >/dev/null)"
    rc=$?
    got=nofallback; [ -s "$LOG" ] && got=fallback
    if [ "$got" = "$expect" ] && [ "$rc" -eq 0 ] && [ -z "$err" ]; then
        echo "PASS: $name"
    else
        echo "FAIL: $name (expected $expect got $got, rc=$rc, stderr='$err')"
        FAILS=$((FAILS+1))
    fi
}
assert_tty() {
    name="$1"; want="$2"
    if grep -aq "$want" "$TTYF"; then echo "PASS: $name"
    else echo "FAIL: $name (tty lacks '$want')"; FAILS=$((FAILS+1)); fi
}

run_case "ghostty plain: no fallback" nofallback "$TTYF" GHOSTTY_RESOURCES_DIR=/x
assert_tty "ghostty plain: OSC 777 written" '777;notify;T;B'
run_case "TERM_PROGRAM=ghostty: no fallback" nofallback "$TTYF" TERM_PROGRAM=ghostty
assert_tty "TERM_PROGRAM=ghostty: OSC 777 written" '777;notify;T;B'
run_case "iTerm2: no fallback" nofallback "$TTYF" TERM_PROGRAM=iTerm.app
assert_tty "iTerm2: OSC 9 written" ']9;T: B'
run_case "ghostty in tmux passthrough off: fallback" fallback "$TTYF" GHOSTTY_RESOURCES_DIR=/x TMUX=/s FAKE_TMUX_PT=off
run_case "ghostty in tmux passthrough unset: fallback" fallback "$TTYF" GHOSTTY_RESOURCES_DIR=/x TMUX=/s FAKE_TMUX_PT=
run_case "ghostty in tmux tmux fails: fallback" fallback "$TTYF" GHOSTTY_RESOURCES_DIR=/x TMUX=/s FAKE_TMUX_FAIL=1
run_case "ghostty in tmux passthrough on: no fallback" nofallback "$TTYF" GHOSTTY_RESOURCES_DIR=/x TMUX=/s FAKE_TMUX_PT=on
assert_tty "tmux wrapped sequence written" 'Ptmux;'
run_case "ghostty in tmux passthrough all: no fallback" nofallback "$TTYF" GHOSTTY_RESOURCES_DIR=/x TMUX=/s FAKE_TMUX_PT=all
run_case "ghostty in screen: no fallback" nofallback "$TTYF" GHOSTTY_RESOURCES_DIR=/x STY=1
run_case "Terminal.app (no OSC): fallback" fallback "$TTYF" TERM_PROGRAM=Apple_Terminal
run_case "tty unwritable: fallback, silent" fallback "$T/nodir/tty" GHOSTTY_RESOURCES_DIR=/x
run_case "linux ghostty: no fallback" nofallback "$TTYF" GHOSTTY_RESOURCES_DIR=/x FAKE_UNAME=Linux
run_case "linux no OSC: no fallback" nofallback "$TTYF" FAKE_UNAME=Linux

# No controlling tty, default /dev/tty path (BEEPBOOP_TTY empty -> /dev/tty)
if command -v python3 >/dev/null 2>&1; then
    : > "$LOG"
    err="$(env -i PATH="$BIN:/usr/bin:/bin" HOME="$T" STUBLOG="$LOG" CLAUDE_PLUGIN_ROOT="$T" \
        GHOSTTY_RESOURCES_DIR=/x /usr/bin/python3 -c 'import os,sys; os.setsid(); os.execvp(sys.argv[1], sys.argv[1:])' \
        /bin/sh "$DIR/notify.sh" T B 2>&1 >/dev/null </dev/null)"
    rc=$?
    if [ -s "$LOG" ] && [ "$rc" -eq 0 ] && [ -z "$err" ]; then echo "PASS: no controlling tty: fallback, silent"
    else echo "FAIL: no controlling tty (rc=$rc, stderr='$err', log='$(cat "$LOG")')"; FAILS=$((FAILS+1)); fi
else
    echo "SKIP: no controlling tty (python3 unavailable)"
fi

[ "$FAILS" -eq 0 ] || { echo "$FAILS failure(s)"; exit 1; }
echo "all passed"
