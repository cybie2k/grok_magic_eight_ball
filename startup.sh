#!/bin/sh
set -eu
cd /workspace

VENDOR=/workspace/vendor
export LD_LIBRARY_PATH="$VENDOR/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export TCL_LIBRARY="$VENDOR/tcltk/tcl8.6"
export TK_LIBRARY="$VENDOR/tcltk/tk8.6"
export PYTHONPATH="$VENDOR/py${PYTHONPATH:+:$PYTHONPATH}"
export DISPLAY=:99
export EIGHT_BALL_FILL=1

alive() {
  pidfile=$1
  [ -f "$pidfile" ] || return 1
  pid=$(cat "$pidfile")
  [ -n "$pid" ] && [ -d "/proc/$pid" ]
}

port_in_use() {
  python3 - "$1" << 'PY'
import socket, sys
s = socket.socket()
try:
    s.bind(("127.0.0.1", int(sys.argv[1])))
except OSError:
    raise SystemExit(0)
s.close()
raise SystemExit(1)
PY
}

free_port() {
  python3 - "$1" << 'PY'
import os, signal, sys
port = int(sys.argv[1])
hexport = f"{port:04X}"
for path in ("/proc/net/tcp", "/proc/net/tcp6"):
    try:
        fh = open(path)
    except OSError:
        continue
    for line in fh:
        parts = line.split()
        if len(parts) < 10:
            continue
        if not parts[1].upper().endswith(":" + hexport):
            continue
        inode = parts[9]
        for pid in os.listdir("/proc"):
            if not pid.isdigit():
                continue
            fd_dir = f"/proc/{pid}/fd"
            try:
                names = os.listdir(fd_dir)
            except OSError:
                continue
            for fd in names:
                try:
                    target = os.readlink(f"{fd_dir}/{fd}")
                except OSError:
                    continue
                if inode and inode in target:
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                    except OSError:
                        pass
PY
}

if curl -sf -o /dev/null --max-time 2 http://127.0.0.1:8080/vnc.html && alive /tmp/eight-ball.pid; then
  exit 0
fi

if port_in_use 8080 && ! alive /tmp/websockify.pid; then
  free_port 8080
  sleep 1
fi

if ! alive /tmp/xvfb.pid; then
  Xvfb :99 -screen 0 560x820x24 -ac +extension RANDR >>/tmp/xvfb.log 2>&1 &
  echo $! > /tmp/xvfb.pid
  sleep 0.5
fi

if ! alive /tmp/eight-ball.pid; then
  python3 /workspace/artifacts/eight_ball.py >>/tmp/eight-ball.log 2>&1 &
  echo $! > /tmp/eight-ball.pid
  sleep 0.8
fi

if ! alive /tmp/x11vnc.pid; then
  "$VENDOR/bin/x11vnc" \
    -display :99 \
    -forever \
    -shared \
    -nopw \
    -listen 127.0.0.1 \
    -rfbport 5900 \
    -noxdamage \
    -repeat \
    >>/tmp/x11vnc.log 2>&1 &
  echo $! > /tmp/x11vnc.pid
  sleep 0.5
fi

if ! alive /tmp/websockify.pid; then
  python3 -m websockify --web="$VENDOR/novnc" 0.0.0.0:8080 127.0.0.1:5900 >>/tmp/websockify.log 2>&1 &
  echo $! > /tmp/websockify.pid
fi
