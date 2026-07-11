"""Codex PreToolUse hook that guards this repository's write boundary.

The hook receives one JSON object from Codex on stdin. It blocks obvious file
mutations outside the Git repository while allowing read-only access. This is a
guardrail, not an operating-system sandbox; AGENTS.md remains the primary rule.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
FALLBACK_ROOT = SCRIPT_PATH.parents[2]

PATCH_PATH_RE = re.compile(
    r"^\*\*\* (?:Add File|Update File|Delete File|Move to):\s*(.+?)\s*$",
    re.MULTILINE,
)
WINDOWS_ABSOLUTE_RE = re.compile(r"(?i)(?<![\w])([a-z]:[\\/][^\r\n\"']+)")
UNC_PATH_RE = re.compile(r"(?<![\w])(\\\\[^\r\n\"']+)")
POSIX_ABSOLUTE_RE = re.compile(r"(?<![\w.])(/[^\s\"']+)")

MUTATING_COMMAND_RE = re.compile(
    r"(?i)(?:^|[\s;|&])(?:"
    r"new-item|set-content|add-content|out-file|remove-item|move-item|"
    r"copy-item|rename-item|mkdir|md|ni|del|erase|rmdir|rd|move|copy|"
    r"touch|rm|mv|cp|install|git\s+(?:init|add|commit|checkout|switch|restore|"
    r"clean|reset|merge|rebase|cherry-pick|tag)"
    r")(?:\s|$)"
)


def git_root(cwd: Path) -> Path:
    """Return the repository root, falling back to this script's repository."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            timeout=3,
        )
        return Path(result.stdout.strip()).resolve()
    except (OSError, subprocess.SubprocessError):
        return FALLBACK_ROOT.resolve()


def is_inside(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=False))
        return True
    except ValueError:
        return False


def clean_candidate(raw: str) -> str:
    return raw.strip().strip("\"'").rstrip("),]}>")


def resolve_candidate(raw: str, cwd: Path) -> Path:
    candidate = Path(clean_candidate(raw))
    return candidate if candidate.is_absolute() else cwd / candidate


def deny(reason: str) -> int:
    print(reason, file=sys.stderr)
    return 2


def check_apply_patch(command: str, cwd: Path, root: Path) -> int:
    targets = PATCH_PATH_RE.findall(command)
    for target in targets:
        resolved = resolve_candidate(target, cwd)
        if not is_inside(resolved, root):
            return deny(
                f"Workspace guard: blocked patch target outside project root: {target}. "
                f"Allowed root: {root}"
            )
    return 0


def extract_absolute_paths(command: str) -> list[str]:
    paths: list[str] = []
    for pattern in (WINDOWS_ABSOLUTE_RE, UNC_PATH_RE, POSIX_ABSOLUTE_RE):
        paths.extend(match.group(1) for match in pattern.finditer(command))
    return paths


def check_shell(command: str, cwd: Path, root: Path) -> int:
    if not MUTATING_COMMAND_RE.search(command):
        return 0

    for raw_path in extract_absolute_paths(command):
        if not is_inside(resolve_candidate(raw_path, cwd), root):
            return deny(
                f"Workspace guard: blocked a mutating command that references an "
                f"outside path: {raw_path}. Allowed root: {root}"
            )

    traversal_re = re.compile(r"(?:^|[\s\"'])(\.\.[\\/][^\s\"']*)")
    for match in traversal_re.finditer(command):
        raw_path = match.group(1)
        if not is_inside(resolve_candidate(raw_path, cwd), root):
            return deny(
                f"Workspace guard: blocked a mutating command that escapes the "
                f"project root: {raw_path}. Allowed root: {root}"
            )
    return 0


def main() -> int:
    try:
        payload: dict[str, Any] = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return deny(f"Workspace guard: invalid hook input: {exc}")

    cwd = Path(payload.get("cwd") or Path.cwd()).resolve()
    root = git_root(cwd)
    tool_name = str(payload.get("tool_name") or "")
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}
    command = str(tool_input.get("command") or tool_input.get("cmd") or "")

    normalized_tool = tool_name.lower()
    if normalized_tool in {"apply_patch", "edit", "write"}:
        return check_apply_patch(command, cwd, root)
    if normalized_tool == "bash":
        return check_shell(command, cwd, root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
