"""Shared test helpers: temp git remotes and configs."""
import subprocess, tempfile
from pathlib import Path
from workboard.config import load_config, Server


def git(cwd, *args, check=True):
    return subprocess.run(["git", *args], cwd=cwd, check=check, capture_output=True, text=True)


def bare_remote(tmp: Path, name="ledger.git") -> Path:
    remote = tmp / name
    git(tmp, "init", "-q", "--bare", "-b", "main", str(remote))
    seed = tmp / f"seed-{name}"
    git(tmp, "init", "-q", "-b", "main", str(seed))
    git(seed, "config", "user.email", "t@example.com"); git(seed, "config", "user.name", "t")
    (seed / "README").write_text("ledger\n")
    git(seed, "add", "README"); git(seed, "commit", "-q", "-m", "seed")
    git(seed, "push", "-q", str(remote), "main")
    return remote


def cfg_for(tmp: Path, host: str, remote: Path):
    cfg = load_config(Path("/nonexistent"))
    cfg.servers = [Server(id="h1", host_alias="h1"), Server(id="h2", host_alias="h2")]
    cfg.ledger.path = str(tmp / f"ledger-{host}")
    cfg.ledger.remote = str(remote)
    return cfg
