"""Small git helpers: argv only, timeouts, never raise on git failure (return the CompletedProcess)."""
from __future__ import annotations

import os
import subprocess

ENV = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_SSH_COMMAND": os.environ.get("GIT_SSH_COMMAND", "ssh -o BatchMode=yes -o ConnectTimeout=10")}


def run(cwd, *args, timeout: float = 60) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=timeout, env=ENV)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(["git", *args], 124, "", f"timeout after {int(timeout)}s")
    except OSError as exc:
        return subprocess.CompletedProcess(["git", *args], 127, "", str(exc))


def err(proc: subprocess.CompletedProcess) -> str:
    return " ".join((proc.stderr or proc.stdout or "").split())[-200:] or f"exit {proc.returncode}"
