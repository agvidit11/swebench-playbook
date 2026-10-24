"""Small git helpers: argv only, timeouts that kill the whole process group, never raise on git failure."""
from __future__ import annotations

import os
import signal
import subprocess

ENV = {**os.environ, "GIT_TERMINAL_PROMPT": "0",
       "GIT_SSH_COMMAND": os.environ.get("GIT_SSH_COMMAND", "ssh -o BatchMode=yes -o ConnectTimeout=10")}


def run(cwd, *args, timeout: float = 60, input_text: str | None = None, env: dict | None = None) -> subprocess.CompletedProcess:
    argv = ["git", *args]
    if timeout is not None and timeout <= 0:
        return subprocess.CompletedProcess(argv, 124, "", "timeout (no time left)")
    try:
        proc = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.PIPE if input_text is not None else subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env or ENV,
                                start_new_session=True)
    except OSError as exc:
        return subprocess.CompletedProcess(argv, 127, "", str(exc))
    try:
        out, err = proc.communicate(input_text, timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)        # git spawns helpers (ssh, index-pack): kill them all
        except ProcessLookupError:
            pass
        proc.communicate()
        return subprocess.CompletedProcess(argv, 124, "", f"timeout after {int(timeout)}s")
    return subprocess.CompletedProcess(argv, proc.returncode, out, err)


def err(proc: subprocess.CompletedProcess) -> str:
    return " ".join((proc.stderr or proc.stdout or "").split())[-200:] or f"exit {proc.returncode}"
