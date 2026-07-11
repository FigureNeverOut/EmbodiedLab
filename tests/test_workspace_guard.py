"""Tests for the project-local Codex workspace guard hook."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = ROOT / ".codex" / "hooks" / "enforce_workspace.py"
SPEC = importlib.util.spec_from_file_location("enforce_workspace", HOOK_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load hook module from {HOOK_PATH}")
HOOK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HOOK)


class WorkspaceGuardTests(unittest.TestCase):
    def test_patch_inside_root_is_allowed(self) -> None:
        command = (
            "*** Begin Patch\n"
            "*** Add File: docs/example.md\n"
            "+example\n"
            "*** End Patch"
        )
        self.assertEqual(HOOK.check_apply_patch(command, ROOT, ROOT), 0)

    def test_patch_outside_root_is_denied(self) -> None:
        outside = ROOT.parent / "outside.txt"
        command = (
            "*** Begin Patch\n"
            f"*** Add File: {outside}\n"
            "+outside\n"
            "*** End Patch"
        )
        self.assertEqual(HOOK.check_apply_patch(command, ROOT, ROOT), 2)

    def test_mutating_shell_command_inside_root_is_allowed(self) -> None:
        target = ROOT / "tmp" / "inside.txt"
        command = f"New-Item -ItemType File -Path '{target}'"
        self.assertEqual(HOOK.check_shell(command, ROOT, ROOT), 0)

    def test_mutating_shell_command_outside_root_is_denied(self) -> None:
        target = ROOT.parent / "outside.txt"
        command = f"New-Item -ItemType File -Path '{target}'"
        self.assertEqual(HOOK.check_shell(command, ROOT, ROOT), 2)

    def test_read_only_external_path_is_allowed(self) -> None:
        command = "Get-Content -LiteralPath 'C:\\Users\\example\\resume.pdf'"
        self.assertEqual(HOOK.check_shell(command, ROOT, ROOT), 0)


if __name__ == "__main__":
    unittest.main()
