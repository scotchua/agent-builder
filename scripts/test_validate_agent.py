#!/usr/bin/env python3
"""Tests for validate_agent.py. Cases and expected verdicts were written by an
independent reviewer from the spec before the script existed; do not edit an
expectation to match the code. Synthetic fixtures only. Run: python3 test_validate_agent.py"""

import importlib
import io
import re
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import validate_agent  # noqa: E402

A64 = "a" * 64
A65 = "a" * 65


# Fake credentials for test 17, assembled from pieces so no credential-shaped text
# appears in this file (hosting services block pushes that contain one).
SK = "sk" + "-ABCDEFGHIJKLMNOPQRST"
GHP = "gh" + "p_abcdefghijklmnopqrstuvwxyz012345"
PAT = "github" + "_pat_abcdefghijklmnopqrstuvwxyz012345"
XB = "xo" + "xb-1234567890-abcdefghijklmnop"
XP = "xo" + "xp-1234567890-abcdefghijklmnop"
AK = "AK" + "IAABCDEFGHIJKLMNOP"
PK = "-----BEGIN RSA PRIV" + "ATE KEY-----"


class ValidateTests(unittest.TestCase):
    def setUp(self):
        importlib.reload(validate_agent)
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def run_paths(self, *paths):
        out = io.StringIO()
        code = validate_agent.main([str(p) for p in paths], out=out)
        text = out.getvalue()
        m = re.search(r"(\d+) error\(s\), (\d+) warning\(s\)", text.strip().splitlines()[-1])
        self.assertIsNotNone(m, "summary line missing")
        return code, text, int(m.group(1)), int(m.group(2))

    def lines(self, text, prefix):
        return [l for l in text.splitlines() if l.startswith(prefix)]

    def needs_toml(self):
        if validate_agent.tomllib is None:
            self.skipTest("TOML checks need Python 3.11 or later")

    # 1
    def test_valid_skill_quoted_and_folded(self):
        p = self.write("agents/research/SKILL.md",
                       '---\nname: "research"\ndescription: >-\n  Builds research\n  agents.\n---\n# Instructions\nDo careful work.\n')
        code, text, e, w = self.run_paths(p)
        self.assertEqual((code, e, w), (0, 0, 0))
        self.assertIn("looks fine", text)

    # 2
    def test_valid_skill_folder_argument_max_name(self):
        self.write("agents/%s/SKILL.md" % A64, "---\nname: %s\ndescription: |-\n  Plans work.\n---\nUse the plan.\n" % A64)
        code, text, e, w = self.run_paths(str(self.root / "agents" / A64) + "/")
        self.assertEqual((code, e, w), (0, 0, 0))
        self.assertIn("looks fine", text)

    # Author-added regression (not from the independent oracle): a relative "." path.
    def test_current_folder_argument(self):
        import os
        self.write("my-skill/SKILL.md", "---\nname: my-skill\ndescription: Fixture\n---\nDo it.\n")
        old = os.getcwd()
        os.chdir(str(self.root / "my-skill"))
        try:
            code, text, e, w = self.run_paths(".")
        finally:
            os.chdir(old)
        self.assertEqual((code, e, w), (0, 0, 0))

    # 3
    def test_missing_and_unclosed_frontmatter(self):
        a = self.write("agents/missing/SKILL.md", "# Instructions\nDo work.\n")
        b = self.write("agents/unclosed/SKILL.md", "---\nname: unclosed\ndescription: Test fixture\n# Instructions\n")
        code, text, e, w = self.run_paths(a, b)
        self.assertEqual((code, e), (1, 2))
        errs = self.lines(text, "ERROR:")
        self.assertTrue(any("missing" in l and "frontmatter" in l for l in errs))
        self.assertTrue(any("unclosed" in l and "never closed" in l for l in errs))

    # 4
    def test_missing_name_and_empty_description(self):
        p = self.write("agents/incomplete/SKILL.md", '---\ndescription: ""\n---\nInstructions.\n')
        code, text, e, w = self.run_paths(p)
        self.assertEqual((code, e), (1, 2))
        self.assertIn("`name` is missing", text)
        self.assertIn("`description` is missing or empty", text)

    # 5
    def test_name_shape_rules(self):
        a = self.write("agents/-Bad--/SKILL.md", "---\nname: -Bad--\ndescription: Fixture\n---\nInstructions.\n")
        b = self.write("agents/%s.md" % A65, "---\nname: %s\ndescription: Fixture\ntools: Read\n---\nInstructions.\n" % A65)
        code, text, e, w = self.run_paths(a, b)
        self.assertEqual(code, 1)
        self.assertEqual(e, 5)
        for phrase in ("lowercase letters", "start with a hyphen", "end with a hyphen", "two hyphens", "the limit is 64"):
            self.assertIn(phrase, text)
        self.assertNotIn("matching them avoids confusion", text)

    # 6
    def test_folder_mismatch_and_long_description(self):
        p = self.write("agents/skill-folder/SKILL.md", "---\nname: other\ndescription: " + "d" * 1025 + "\n---\nInstructions.\n")
        code, text, e, w = self.run_paths(p)
        self.assertEqual((code, e), (1, 2))
        self.assertIn("skill-folder", text)
        self.assertIn("1025 characters", text)

    # 7
    def test_long_skill_body_warns(self):
        p = self.write("agents/long-body/SKILL.md", "---\nname: long-body\ndescription: Fixture\n---\n" + "x\n" * 501)
        code, text, e, w = self.run_paths(p)
        self.assertEqual((code, e, w), (0, 0, 1))
        self.assertIn("over 500", text)

    # 8
    def test_valid_subagent_yaml_list_tools(self):
        p = self.write("agents/reviewer.md",
                       "---\nname: reviewer\ndescription: |-\n  Reviews changes carefully.\nmodel: claude-3-7-sonnet\n"
                       "effort: max\npermissionMode: plan\ntools:\n  - Read\n  - Grep\n---\nReview the supplied changes.\n")
        code, text, e, w = self.run_paths(p)
        self.assertEqual((code, e, w), (0, 0, 0))
        self.assertIn("looks fine", text)

    # 9
    def test_subagent_combined_warnings(self):
        p = self.write("agents/file-name.md",
                       "---\nname: internal-name\ndescription: Fixture\nmodel: mystery-model\neffort: extreme\n"
                       "permissionMode: unrestricted\n---\n")
        code, text, e, w = self.run_paths(p)
        self.assertEqual((code, e, w), (0, 0, 6))
        for phrase in ("matching them", "mystery-model", "extreme", "unrestricted", "every tool", "no instructions"):
            self.assertIn(phrase, text)

    # 10 (spec changed 2026-09-24 after review job 6c208e finding 4: bypassPermissions is now an ERROR;
    # recorded as a deliberate spec change, not an expectation edited to match code)
    def test_bypass_error_and_comma_tools(self):
        p = self.write("agents/operator.md",
                       "---\nname: operator\ndescription: Fixture\npermissionMode: bypassPermissions\ntools: Read, Grep\n---\nOperate carefully.\n")
        code, text, e, w = self.run_paths(p)
        self.assertEqual((code, e, w), (1, 1, 0))
        self.assertIn("safety prompts", text)
        self.assertNotIn("every tool", text)

    # 11
    def test_valid_codex_toml(self):
        self.needs_toml()
        p = self.write("agents/coder.toml", 'name = "coder"\ndescription = "Writes code."\n'
                       'developer_instructions = "Make focused changes."\nmodel_reasoning_effort = "ultra"\nsandbox_mode = "workspace-write"\n')
        code, text, e, w = self.run_paths(p)
        self.assertEqual((code, e, w), (0, 0, 0))
        self.assertIn("looks fine", text)

    # 12
    def test_malformed_toml(self):
        self.needs_toml()
        p = self.write("agents/broken.toml", 'name = "broken\ndescription = "Fixture"\ndeveloper_instructions = "Work."\n')
        code, text, e, w = self.run_paths(p)
        self.assertEqual((code, e), (1, 1))
        self.assertIn("not valid TOML", text)

    # 13
    def test_toml_required_fields(self):
        self.needs_toml()
        a = self.write("agents/no-name.toml", 'description = "Fixture"\ndeveloper_instructions = "Work."\n')
        b = self.write("agents/empty-desc.toml", 'name = "empty-desc"\ndescription = ""\ndeveloper_instructions = "Work."\n')
        c = self.write("agents/bad-instructions.toml", 'name = "bad-instructions"\ndescription = "Fixture"\ndeveloper_instructions = 7\n')
        code, text, e, w = self.run_paths(a, b, c)
        self.assertEqual((code, e), (1, 3))
        errs = self.lines(text, "ERROR:")
        self.assertTrue(any("no-name.toml" in l and "`name`" in l for l in errs))
        self.assertTrue(any("empty-desc.toml" in l and "`description`" in l for l in errs))
        self.assertTrue(any("bad-instructions.toml" in l and "`developer_instructions`" in l for l in errs))

    # 14
    def test_toml_mismatch_and_unknown_values(self):
        self.needs_toml()
        p = self.write("agents/custom.toml", 'name = "other"\ndescription = "Fixture"\ndeveloper_instructions = "Work."\n'
                       'model_reasoning_effort = "extreme"\nsandbox_mode = "container"\n')
        code, text, e, w = self.run_paths(p)
        self.assertEqual((code, e, w), (0, 0, 3))
        for phrase in ("matching them", "extreme", "container"):
            self.assertIn(phrase, text)

    # 15 (spec changed 2026-09-24 with finding 4: danger-full-access is now an ERROR)
    def test_toml_full_access_is_error(self):
        self.needs_toml()
        p = self.write("agents/admin.toml", 'name = "admin"\ndescription = "Fixture"\ndeveloper_instructions = "Work carefully."\n'
                       'sandbox_mode = "danger-full-access"\n')
        code, text, e, w = self.run_paths(p)
        self.assertEqual((code, e, w), (1, 1, 0))
        self.assertIn("full access", text)
        self.assertNotIn("not one this checker knows", text)

    # 16
    def test_toml_without_tomllib(self):
        validate_agent.tomllib = None
        p = self.write("agents/legacy.toml", 'name = "legacy"\ndescription = "Fixture"\ndeveloper_instructions = "Work."\n')
        code, text, e, w = self.run_paths(p)
        self.assertEqual((code, e, w), (0, 0, 1))
        self.assertIn("could not be checked", text)

    # 17
    def test_secrets_redacted_with_line_numbers(self):
        self.needs_toml()
        values = ["" + SK + "", "" + GHP + "",
                  "" + PAT + "", "abcdefgh", "ijklmnop",
                  "" + XB + "", "" + XP + "", "qrstuvwx", "yzabcdef",
                  "" + AK + "", "" + PK + "", "ghijklmn", "opqrstuv"]
        a = self.write("agents/secure/SKILL.md", "---\nname: secure\ndescription: Scanner fixture\n---\n"
                       "" + SK + "\n" + GHP + "\n"
                       "" + PAT + "\npassword: abcdefgh\npasswd=ijklmnop\n")
        b = self.write("agents/scanner.md", "---\nname: scanner\ndescription: Scanner fixture\ntools: Read, Grep\n---\n"
                       "Check credentials safely.\n" + XB + "\n" + XP + "\n"
                       "api_key: qrstuvwx\napikey=yzabcdef\n")
        c = self.write("agents/vault.toml", 'name = "vault"\ndescription = "Scanner fixture"\ndeveloper_instructions = "Inspect safely."\n'
                       "# " + AK + "\n# " + PK + "\n# secret=ghijklmn\n# token: opqrstuv\n")
        code, text, e, w = self.run_paths(a, b, c)
        self.assertEqual((code, e), (1, 13))
        errs = self.lines(text, "ERROR:")
        expected = [("SKILL.md", n) for n in range(5, 10)] + [("scanner.md", n) for n in range(7, 11)] + \
                   [("vault.toml", n) for n in range(4, 8)]
        for fname, n in expected:
            self.assertTrue(any(fname in l and "line %d " % n in l for l in errs), (fname, n))
        for v in values:
            self.assertNotIn(v, text)

    # Author-added from review job 6c208e findings 1, 3, 7 (not from the independent oracle).
    def test_prose_about_secrets_is_not_flagged(self):
        p = self.write("agents/careful.md", "---\nname: careful\ndescription: Fixture\ntools: Read\n---\n"
                       "- Never set api_key: placeholder-value; use the app's credential setup.\n"
                       "token: <your token goes in the app, not here>\napi_key: ${API_KEY_FROM_ENV}\n")
        code, text, e, w = self.run_paths(p)
        self.assertEqual((code, e, w), (0, 0, 0))

    def test_indented_and_json_secrets_are_flagged(self):
        p = self.write("agents/leaky.md", "---\nname: leaky\ndescription: Fixture\ntools: Read\n---\nDo it.\n"
                       "  api_key: abcd1234efgh5678\n  - api_key: abcd1234efgh5678\n"
                       '    "token": "abcd1234efgh5678ijkl"\n{"token": "abcd1234efgh5678ijkl"}\n')
        code, text, e, w = self.run_paths(p)
        self.assertEqual((code, e), (1, 4))
        for n in (7, 8, 9, 10):
            self.assertIn("line %d " % n, text)
        self.assertNotIn("abcd1234efgh5678", text)

    # Author-added from review jobs 397b90 findings 1 and 2 and b2d375 finding 1 (not from the independent oracle).
    def test_unquoted_inline_mapping_is_flagged(self):
        p = self.write("agents/inline.md", "---\nname: inline\ndescription: Fixture\ntools: Read\n---\nDo it.\n"
                       "{token: abcdefgh12}\n{name: x, api_key: abcdefgh12}\n")
        code, text, e, w = self.run_paths(p)
        self.assertEqual((code, e), (1, 2))
        self.assertNotIn("abcdefgh12", text)

    def test_quoted_syntax_in_docs_is_not_flagged(self):
        p = self.write("agents/docs.md", "---\nname: docs\ndescription: Fixture\ntools: Read\n---\n"
                       'Never write `"token": "placeholder-value"` in a file.\n'
                       '| Setting | Example |\n| auth | "api_key": "placeholder-value" |\n'
                       'A line like "secret": "placeholder-value" is what to avoid.\n'
                       'When finished, token: abcdefgh12 is recorded.\n')
        code, text, e, w = self.run_paths(p)
        self.assertEqual((code, e, w), (0, 0, 0))

    def test_agent_and_bash_tools_warn(self):
        p = self.write("agents/broad.md", "---\nname: broad\ndescription: Fixture\ntools: Read, Grep, Glob, Agent, Bash\n---\nDo it.\n")
        code, text, e, w = self.run_paths(p)
        self.assertEqual((code, e, w), (0, 0, 2))
        self.assertIn("start other helpers", text)
        self.assertIn("run any command", text)

    def test_duplicate_key_and_unclosed_quote(self):
        p = self.write("agents/messy.md", '---\nname: messy\nname: messy\ndescription: "unterminated\ntools: Read\n---\nDo it.\n')
        code, text, e, w = self.run_paths(p)
        self.assertEqual(code, 1)
        self.assertIn("appears twice", text)
        self.assertIn("never closed", text)

    # 18
    def test_unsupported_and_missing_paths(self):
        a = self.write("agents/notes.txt", "ordinary text\n")
        b = self.root / "agents" / "does-not-exist.md"
        code, text, e, w = self.run_paths(a, b)
        self.assertEqual((code, e), (1, 2))
        self.assertIn("unsupported", text)
        self.assertIn("does not exist", text)


if __name__ == "__main__":
    unittest.main(verbosity=1)
