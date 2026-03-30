#!/bin/sh
uid=$(python3 -c 'import os; print(os.getuid())')
pid_file="/tmp/beepboop-${uid}.pid"
socket_path="/tmp/beepboop-${uid}.sock"
[ -f "$pid_file" ] || exit 0
pid=$(cat "$pid_file")
kill -TERM "$pid" 2>/dev/null || true
# Wait for daemon to exit (it removes PID file in its own cleanup)
i=0
while [ $i -lt 20 ] && [ -f "$pid_file" ]; do
    sleep 0.05; i=$((i+1))
done
# Fallback: remove PID file if daemon didn't clean up
rm -f "$pid_file"
