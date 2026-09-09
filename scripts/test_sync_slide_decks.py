"""TLDR (too long; didn't read): freshness regressions using temporary repositories.

All renderer invocations are simulated; no installed presentation app is launched.
"""

import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

import sync_slide_decks as sync


SCRIPT = Path(sync.__file__).resolve()


def write_deck(path, text="first version"):
    with zipfile.ZipFile(path, "w") as deck:
        deck.writestr(
            "ppt/presentation.xml",
            f'<p:presentation xmlns:p="{sync.NS["p"]}"/>',
        )
        deck.writestr(
            "ppt/slides/slide1.xml",
            f'<p:sld xmlns:p="{sync.NS["p"]}" xmlns:a="{sync.NS["a"]}">'
            f'<p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>{text}</a:t>'
            '</a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld></p:sld>',
        )


class FreshnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="slide-gate-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.git("init", "-q")
        self.deck = self.root / "Talk — unusual (name) .pptx"
        write_deck(self.deck)
        self.pdf = sync.expected_derivatives(self.deck)["pdf"]
        self.md = sync.expected_derivatives(self.deck)["md"]
        self.pdf.write_bytes(b"%PDF-1.4\nfixture\n%%EOF\n")
        digest = sync.sha256_of(self.deck)
        self.md.write_text(sync.pptx_to_markdown(self.deck, digest), encoding="utf-8")
        sync.save_manifest(self.root, {
            "decks": {self.deck.name: {
                "source_sha256": digest,
                "derivatives": {
                    path.name: {"sha256": sync.sha256_of(path), "kind": kind}
                    for kind, path in sync.expected_derivatives(self.deck).items()
                },
            }},
        })
        self.git("add", ".")

    def git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.root), "-c", "core.hooksPath=/dev/null", *args],
            capture_output=True, text=True, check=True,
        )

    def cli(self, *args, env=None):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args], cwd=self.root,
            capture_output=True, text=True, env=env,
        )

    def run_main(self, *args):
        original = Path.cwd()
        try:
            os.chdir(self.root)
            with mock.patch.object(sys, "argv", [str(SCRIPT), *args]), \
                    contextlib.redirect_stdout(io.StringIO()), \
                    contextlib.redirect_stderr(io.StringIO()):
                return sync.main()
        finally:
            os.chdir(original)

    def test_baseline_worktree_and_index_pass(self):
        self.assertEqual(self.cli("--check").returncode, 0)
        self.assertEqual(self.cli("--check-staged").returncode, 0)

    def test_missing_or_modified_derivative_fails_both_gates(self):
        for path in (self.pdf, self.md):
            original = path.read_bytes()
            for replacement in (None, b"stale or truncated output"):
                with self.subTest(path=path.name, replacement=replacement):
                    if replacement is None:
                        path.unlink()
                    else:
                        path.write_bytes(replacement)
                    self.assertEqual(self.cli("--check").returncode, 1)
                    self.git("add", "-A")
                    self.assertEqual(self.cli("--check-staged").returncode, 1)
                    path.write_bytes(original)
                    self.git("add", "-A")

    def test_fresh_worktree_cannot_certify_different_staged_source(self):
        original = self.deck.read_bytes()
        write_deck(self.deck, "staged version")
        self.git("add", self.deck.name)
        self.deck.write_bytes(original)
        self.assertEqual(self.cli("--check").returncode, 0)
        self.assertEqual(self.cli("--check-staged").returncode, 1)

    def test_text_only_refresh_cannot_certify_old_pdf(self):
        write_deck(self.deck, "new text")
        self.assertEqual(self.cli("--md-only").returncode, 0)
        self.assertEqual(self.cli("--check").returncode, 1)
        self.git("add", "-A")
        self.assertEqual(self.cli("--check-staged").returncode, 1)

    def test_partial_or_writing_check_flags_are_rejected(self):
        for flag in ("--md-only", "--pdf-only", "--install-hook"):
            with self.subTest(flag=flag):
                self.assertEqual(self.cli("--check", flag).returncode, 2)
        self.assertFalse((self.root / ".git/hooks/pre-commit").exists())

    def test_unicode_rename_is_checked(self):
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                 "commit", "-qm", "fixture")
        self.git("mv", self.deck.name, "Renamed — deck.pptx")
        self.assertEqual(self.cli("--check-staged").returncode, 1)

    def test_source_type_change_is_checked(self):
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                 "commit", "-qm", "fixture")
        self.deck.unlink()
        self.deck.symlink_to("missing-source")
        self.git("add", self.deck.name)
        result = self.cli("--check-staged")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_corrupt_index_cannot_pass(self):
        bad_index = self.root / "bad-index"
        bad_index.write_bytes(b"not a git index")
        env = dict(os.environ, GIT_INDEX_FILE=str(bad_index))
        result = self.cli("--check-staged", env=env)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_unreadable_index_source_cannot_be_skipped(self):
        real_blob = sync.index_blob
        with mock.patch.object(sync, "index_blob", side_effect=lambda root, rel:
                               None if rel == self.deck.name else real_blob(root, rel)):
            problems, ran = sync.check_staged(self.root)
        self.assertTrue(ran)
        self.assertTrue(problems)

    def test_failed_libreoffice_output_is_not_published_or_certified(self):
        original = self.pdf.read_bytes()

        def failed_renderer(cmd, **kwargs):
            outdir = Path(cmd[cmd.index("--outdir") + 1])
            (outdir / "partial.pdf").write_bytes(b"%PDF-1.4\ntruncated")
            return subprocess.CompletedProcess(cmd, 7, "", "render failed")

        with mock.patch.object(sync, "find_soffice", return_value="soffice"), \
                mock.patch.object(sync, "repo_root", return_value=self.root), \
                mock.patch.object(sync, "soffice_version", return_value="fixture"), \
                mock.patch.object(sync.subprocess, "run", side_effect=failed_renderer):
            self.assertEqual(self.run_main("--force"), 3)
        self.assertEqual(self.pdf.read_bytes(), original)
        self.assertEqual(self.cli("--check").returncode, 1)

    def test_failed_keynote_output_is_rejected(self):
        def failed_renderer(cmd, **kwargs):
            Path(cmd[-1]).write_bytes(b"%PDF-1.4\ntruncated")
            return subprocess.CompletedProcess(cmd, 7, "", "export failed")

        original_exists = Path.exists
        with mock.patch.object(sync.sys, "platform", "darwin"), \
                mock.patch.object(Path, "exists", lambda path:
                                  True if str(path) == "/Applications/Keynote.app"
                                  else original_exists(path)), \
                mock.patch.object(sync.subprocess, "run", side_effect=failed_renderer):
            with self.assertRaises(sync.DeckError):
                sync.render_pdf_keynote(self.deck, self.root / "failed.pdf")

    def test_renderer_timeout_invalidates_prior_record(self):
        with mock.patch.object(sync, "find_soffice", return_value="soffice"), \
                mock.patch.object(sync, "render_pdf", side_effect=
                                  subprocess.TimeoutExpired("soffice", 600)):
            self.assertEqual(self.run_main("--force"), 3)
        self.assertEqual(self.cli("--check").returncode, 1)



if __name__ == "__main__":
    unittest.main()
