#!/usr/bin/env python3
"""Tests for scan_setup.py. Synthetic files only. Run: python3 test_scan_setup.py"""

import importlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import scan_setup  # noqa: E402

SECRET = "SYNTHETIC_PRIVATE_CONTENT_7c1f"


class ScanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self._old_home = os.environ.get("HOME")
        os.environ["HOME"] = str(self.home)
        os.environ["USERPROFILE"] = str(self.home)
        importlib.reload(scan_setup)

    def tearDown(self):
        if self._old_home is not None:
            os.environ["HOME"] = self._old_home
        self.tmp.cleanup()

    def write(self, rel, text):
        p = self.home / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def run_scan(self, project=None):
        report = scan_setup.scan(project)
        return report, json.dumps(report)

    def test_skill_frontmatter_only(self):
        self.write(".claude/skills/acme-voice/SKILL.md",
                   "---\nname: acme-voice\ndescription: Brand voice for Acme.\n---\n\n" + SECRET)
        report, raw = self.run_scan()
        self.assertEqual(report["claude"]["skills"][0]["name"], "acme-voice")
        self.assertIn("acme-voice", report["possible_brand_or_voice_skills"])
        self.assertNotIn(SECRET, raw)

    def test_multiline_prompt_cannot_spoof_metadata(self):
        self.write(".codex/automations/job/automation.toml",
                   'name = "weekly"\nstatus = "ACTIVE"\nprompt = """\nname = "%s"\n"""\n' % SECRET)
        _, raw = self.run_scan()
        self.assertNotIn(SECRET, raw)

    def test_symlinked_skill_to_key_file_refused(self):
        key = self.write(".ssh/id_ed25519", "---\nname: " + SECRET + "\n---\n")
        d = self.home / ".claude/skills/evil"
        d.mkdir(parents=True)
        try:
            (d / "SKILL.md").symlink_to(key)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks not supported here")
        report, raw = self.run_scan()
        self.assertNotIn(SECRET, raw)
        self.assertTrue(any("refused" in n for n in report["scan_notes"]))

    def test_symlinked_skill_folder_allowed(self):
        real = self.write("elsewhere/real-skill/SKILL.md", "---\nname: real-skill\ndescription: ok\n---\n")
        (self.home / ".claude/skills").mkdir(parents=True)
        try:
            (self.home / ".claude/skills/real-skill").symlink_to(real.parent, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks not supported here")
        report, _ = self.run_scan()
        self.assertEqual(report["claude"]["skills"][0]["name"], "real-skill")

    def test_settings_env_never_reported(self):
        self.write(".claude/settings.json", json.dumps({
            "env": {"API_KEY": SECRET}, "apiKeyHelper": SECRET,
            "permissions": {"defaultMode": "default", "allow": ["Read"]},
            "hooks": {"PostToolUse": [{"command": SECRET}]}}))
        report, raw = self.run_scan()
        self.assertNotIn(SECRET, raw)
        self.assertEqual(report["claude"]["settings"]["hook_events"], ["PostToolUse"])

    def test_truncation_is_reported(self):
        for i in range(scan_setup.MAX_ITEMS + 1):
            self.write(".claude/agents/a%03d.md" % i, "---\nname: a%03d\ndescription: x\n---\n" % i)
        report, _ = self.run_scan()
        self.assertEqual(len(report["claude"]["agents"]), scan_setup.MAX_ITEMS)
        self.assertTrue(any("only the first" in n for n in report["scan_notes"]))

    def test_large_file_is_reported(self):
        self.write(".claude/CLAUDE.md", "# Rules\n" + ("x" * (scan_setup.MAX_BYTES + 10)))
        report, _ = self.run_scan()
        self.assertTrue(any("KB of" in n for n in report["scan_notes"]))

    def test_plugin_path_outside_plugins_folder_skipped(self):
        outside = self.home / "outside"
        self.write("outside/skills/x/SKILL.md", "---\nname: " + SECRET + "\n---\n")
        self.write(".claude/plugins/installed_plugins.json", json.dumps(
            {"plugins": {"p@m": [{"installPath": str(outside)}]}}))
        report, raw = self.run_scan()
        self.assertNotIn(SECRET, raw)
        self.assertEqual(report["claude"]["plugins"], [])

    def test_link_into_memory_folder_refused(self):
        mem = self.write(".claude/projects/x/memory/notes.md", "---\nname: " + SECRET + "\n---\n")
        (self.home / ".claude/agents").mkdir(parents=True)
        try:
            (self.home / ".claude/agents/helper.md").symlink_to(mem)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks not supported here")
        opened = []
        real_open = open

        def spy(path, *a, **k):
            opened.append(str(path))
            return real_open(path, *a, **k)
        scan_setup.open = spy
        try:
            report, raw = self.run_scan()
        finally:
            del scan_setup.open
        self.assertNotIn(SECRET, raw)
        self.assertFalse(any("memory" in p for p in opened))
        self.assertEqual(report["claude"]["agents"], [])

    def test_skill_md_linked_to_readme_is_listed(self):
        src = self.write("src/house-voice/README.md", "---\nname: house-voice\ndescription: Our voice.\n---\n")
        d = self.home / ".claude/skills/house-voice"
        d.mkdir(parents=True)
        try:
            (d / "SKILL.md").symlink_to(src)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks not supported here")
        report, _ = self.run_scan()
        self.assertEqual(report["claude"]["skills"][0]["description"], "Our voice.")
        self.assertIn("house-voice", report["possible_brand_or_voice_skills"])

    def test_every_plugin_install_is_scanned(self):
        a = self.home / ".claude/plugins/cache/m/p/1"
        b = self.home / ".claude/plugins/cache/m/p/2"
        self.write(".claude/plugins/cache/m/p/1/skills/one/SKILL.md", "---\nname: one\ndescription: x\n---\n")
        self.write(".claude/plugins/cache/m/p/2/skills/two/SKILL.md", "---\nname: two\ndescription: x\n---\n")
        self.write(".claude/plugins/installed_plugins.json", json.dumps({"plugins": {"p@m": [
            {"scope": "user", "installPath": str(a)}, {"scope": "project", "installPath": str(b)}]}}))
        report, _ = self.run_scan()
        names = [s["name"] for p in report["claude"]["plugins"] for s in p["skills"]]
        self.assertEqual(sorted(names), ["p:one", "p:two"])

    def test_refused_skill_is_not_listed(self):
        key = self.write(".ssh/id_ed25519", "---\nname: " + SECRET + "\n---\n")
        d = self.home / ".claude/skills/evil"
        d.mkdir(parents=True)
        try:
            (d / "SKILL.md").symlink_to(key)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks not supported here")
        report, _ = self.run_scan()
        self.assertEqual(report["claude"]["skills"], [])

    def test_plugin_cache_linked_outside_is_refused(self):
        self.write("outside/p/skills/x/SKILL.md", "---\nname: " + SECRET + "\n---\n")
        (self.home / ".claude/plugins").mkdir(parents=True)
        try:
            (self.home / ".claude/plugins/cache").symlink_to(self.home / "outside", target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks not supported here")
        self.write(".claude/plugins/installed_plugins.json", json.dumps(
            {"plugins": {"p@m": [{"installPath": str(self.home / ".claude/plugins/cache/p")}]}}))
        report, raw = self.run_scan()
        self.assertNotIn(SECRET, raw)
        self.assertTrue(any("skipped an install" in n for n in report["scan_notes"]))

    def test_plugin_with_no_installs_is_noted(self):
        self.write(".claude/plugins/installed_plugins.json", json.dumps({"plugins": {"p@m": []}}))
        report, _ = self.run_scan()
        self.assertTrue(any("no install records" in n for n in report["scan_notes"]))

    def test_skill_body_is_never_read(self):
        self.write(".claude/skills/big/SKILL.md",
                   "---\nname: big\ndescription: ok\n---\n" + ("body line\n" * 5000))
        consumed = []
        real_open = open

        class Spy:
            def __init__(self, fh):
                self.fh = fh
            def __enter__(self):
                return self
            def __exit__(self, *a):
                self.fh.close()
            def readline(self):
                line = self.fh.readline(); consumed.append(len(line)); return line
            def read(self, n=-1):
                s = self.fh.read(n); consumed.append(len(s)); return s
            def __iter__(self):
                for line in self.fh:
                    consumed.append(len(line)); yield line

        def spy(path, *a, **k):
            return Spy(real_open(path, *a, **k))
        scan_setup.open = spy
        try:
            report, _ = self.run_scan()
        finally:
            del scan_setup.open
        self.assertEqual(report["claude"]["skills"][0]["name"], "big")
        self.assertLess(sum(consumed), 200)

    def test_empty_home(self):
        report, _ = self.run_scan()
        self.assertEqual(report["claude"]["skills"], [])
        self.assertEqual(report["scan_notes"], ["complete: nothing skipped or truncated"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
