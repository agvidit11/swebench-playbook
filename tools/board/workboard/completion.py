"""Shell completion: `board __complete <cword> <words...>` prints candidates; reads only local caches (fast)."""
from __future__ import annotations

import json
import os
from pathlib import Path

BASH = r'''# workboard bash completion (installed by `board setup`)
_board_complete() {
    local IFS=$'\n'
    COMPREPLY=( $(board __complete "$COMP_CWORD" "${COMP_WORDS[@]}" 2>/dev/null) )
}
complete -o default -F _board_complete board workboard
'''

ZSH = r'''# workboard zsh completion (installed by `board setup`)
autoload -U +X bashcompinit && bashcompinit
_board_complete() {
    local IFS=$'\n'
    COMPREPLY=( $(board __complete "$COMP_CWORD" "${COMP_WORDS[@]}" 2>/dev/null) )
}
complete -o default -F _board_complete board workboard
'''

TASK_ARG = {"show", "explain", "claim", "release", "check", "review"}


def _cache_dir() -> Path:
    return Path(os.environ.get("WORKBOARD_CACHE", "~/.cache/workboard")).expanduser()


def task_names() -> list[str]:
    try:
        data = json.loads((_cache_dir() / "codimango-last-good.json").read_text())
        rows = data.get("rows", []) if isinstance(data, dict) else []
        return sorted({r["name"] for r in rows if isinstance(r, dict) and isinstance(r.get("name"), str)
                       and r.get("status") not in ("archived",)})
    except (OSError, ValueError):
        return []


def session_aliases() -> list[str]:
    try:
        state = json.loads((_cache_dir() / "hook-state.json").read_text())
        names = {v.get("alias", "") for v in state.get("aliases", {}).values() if isinstance(v, dict)}
        return sorted(n.split("·", 1)[-1] for n in names if n)
    except (OSError, ValueError, AttributeError):
        return []


def candidates(parser, words: list[str], cword: int) -> list[str]:
    """words[0] is the program; words[cword] is the word being completed."""
    cur = words[cword] if cword < len(words) else ""
    sub = parser._subparsers._group_actions[0] if parser._subparsers else None
    commands = sorted(c for c in (sub.choices if sub else {}) if c not in ("hook",))
    if cword <= 1:
        return [c for c in commands + ["--help", "--version"] if c.startswith(cur)]
    cmd = words[1]
    sp = sub.choices.get(cmd) if sub else None
    if sp is None:
        return []
    prev = words[cword - 1] if cword - 1 < len(words) else ""
    if prev == "--to":
        return [a for a in session_aliases() if a.lower().startswith(cur.lower())]
    if prev in ("--verdict",):
        return [v for v in ("ready", "changes", "comment") if v.startswith(cur)]
    if prev in ("--reason",) and cmd == "available":
        return [v for v in ("never-claimed", "expired", "released") if v.startswith(cur)]
    if prev in ("--group",):
        return [v for v in ("attention", "state", "owner") if v.startswith(cur)]
    if prev in ("--color", "--unicode"):
        return [v for v in ("auto", "always", "never") if v.startswith(cur)]
    if cur.startswith("-"):
        flags = sorted({o for a in sp._actions for o in a.option_strings if o.startswith("--")})
        return [f for f in flags if f.startswith(cur)]
    positional = [w for w in words[2:cword] if not w.startswith("-")]
    action_choices = {"check": ["run"], "review": ["add", "list"], "rank": ["show", "import"],
                      "config": ["show", "validate"], "plugins": ["list", "doctor"]}
    if cmd in action_choices and not positional:
        return [c for c in action_choices[cmd] if c.startswith(cur)]
    if cmd in TASK_ARG:
        return [t for t in task_names() if cur in t][:200]
    return []
