#!/usr/bin/env python3
"""Process supervisor for the Plen Dev agents container (Railway).

  audit        audit-agent/server.py  on $PORT       (Railway domain #1, target port 8080)
  alex-web     alex/server.py         on $ALEX_PORT  (Railway domain #2, target port 8081)
  alex-worker  alex/alex.py work      (self-schedules on ET weekdays: inbox, sends, prospecting, WhatsApp report)

A crashed process is restarted with backoff. If any process crashes 5 times within 10 minutes,
the whole container exits so Railway restarts it (restartPolicy ON_FAILURE).
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = sys.executable
PORT = os.environ.get("PORT", "8080")
ALEX_PORT = os.environ.get("ALEX_PORT", "8081")

PROCS = {
    "audit": ([PY, "server.py"], HERE / "audit-agent", {"PORT": PORT}),
    "alex-web": ([PY, "server.py"], HERE / "alex", {"PORT": ALEX_PORT, "ALEX_PORT": ALEX_PORT}),
    "alex-worker": ([PY, "alex.py", "work"], HERE / "alex", {}),
}
if os.environ.get("DISABLE_ALEX", "false").lower() == "true":
    PROCS = {"audit": PROCS["audit"]}


def log(*a):
    print("[run]", time.strftime("%Y-%m-%d %H:%M:%S"), *a, flush=True)


def start(name):
    cmd, cwd, env = PROCS[name]
    log(f"starting {name}: {' '.join(cmd[1:])}")
    return subprocess.Popen(cmd, cwd=cwd, env=os.environ | env)


def main():
    for d in (os.environ.get("OUTBOX_DIR"), os.environ.get("ALEX_DATA_DIR")):
        if d:
            Path(d).mkdir(parents=True, exist_ok=True)
    procs = {n: start(n) for n in PROCS}
    crashes = {n: [] for n in PROCS}

    def stop(*_):
        log("stopping")
        for p in procs.values():
            p.terminate()
        sys.exit(0)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    while True:
        time.sleep(5)
        for n, p in list(procs.items()):
            if p.poll() is None:
                continue
            now = time.time()
            crashes[n] = [t for t in crashes[n] if now - t < 600] + [now]
            if len(crashes[n]) >= 5:
                log(f"{n} crashed 5 times in 10 minutes; exiting so Railway restarts the container")
                for q in procs.values():
                    q.terminate()
                sys.exit(1)
            wait = 2 ** len(crashes[n])
            log(f"{n} exited with {p.returncode}; restarting in {wait}s")
            time.sleep(wait)
            procs[n] = start(n)


if __name__ == "__main__":
    main()
