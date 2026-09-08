"""TLDR: unit tests for agent_board's one-shot detection and --resume-dead (no tmux, no real transcripts)."""

import io
import json
import os
import tempfile
import unittest

import agent_board as board


def _transcript(tmpdir, name, entrypoint, cwd="/Users/me/proj"):
    path = os.path.join(tmpdir, name + ".jsonl")
    recs = [
        {"type": "mode", "sessionId": name, "entrypoint": entrypoint, "cwd": cwd},
        {"type": "user", "cwd": cwd, "gitBranch": "main", "entrypoint": entrypoint,
         "message": {"role": "user", "content": "Review the private board forwarding fix"}},
        {"type": "assistant", "entrypoint": entrypoint,
         "message": {"role": "assistant", "model": "claude-fable-5-1",
                     "content": [{"type": "text", "text": "VERDICT: PASS"}]}},
    ]
    with open(path, "w") as fh:
        # compact separators: Claude Code writes its records without spaces
        fh.write("\n".join(json.dumps(r, separators=(",", ":")) for r in recs) + "\n")
    return path


def _row(sid, tag="cc", proc=False, oneshot=False, cwd="/", age=3600.0, cell="—"):
    return {"sid": sid, "tag": tag, "proc": proc, "alive": proc, "oneshot": oneshot,
            "cwd": cwd, "age": age, "last": 1.0, "topic": "t", "tmux_cell": cell,
            "seats": [], "state": "stale"}


class ScanTranscriptTests(unittest.TestCase):
    def test_entrypoint_is_read_for_print_and_interactive_runs(self):
        with tempfile.TemporaryDirectory() as d:
            for entry in ("sdk-cli", "cli", "claude-desktop"):
                topic, cwd, branch, model, effort, got = board.scan_transcript(
                    _transcript(d, entry, entry))
                self.assertEqual(got, entry)
                self.assertEqual(cwd, "/Users/me/proj")
                self.assertEqual(model, "claude-fable-5-1")
                self.assertTrue(topic.startswith("Review the private board"))
            self.assertIn("sdk-cli", board.ONESHOT_ENTRYPOINTS)
            self.assertNotIn("cli", board.ONESHOT_ENTRYPOINTS)

    def test_missing_entrypoint_is_empty_not_a_guess(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "old.jsonl")
            with open(path, "w") as fh:
                fh.write(json.dumps({"type": "user", "cwd": "/x",
                                     "message": {"role": "user", "content": "hi"}}) + "\n")
            self.assertEqual(board.scan_transcript(path)[5], "")


class OnePerSeatTests(unittest.TestCase):
    def test_finished_oneshot_stays_listed_while_fresh_then_drops(self):
        fresh = _row("a" * 36, oneshot=True, age=60.0, cell="one-shot")
        old = _row("b" * 36, oneshot=True, age=board.IDLE_S + 1, cell="one-shot")
        kept = board.one_per_seat([fresh, old])
        self.assertEqual([r["sid"] for r in kept], [fresh["sid"]])

    def test_live_and_seated_rows_are_always_kept(self):
        live = _row("c" * 36, proc=True, age=99999.0, cell="tmux 2")
        seated = dict(_row("d" * 36, age=99999.0), seats=["2"])
        self.assertEqual(len(board.one_per_seat([live, seated])), 2)


class ResumeDeadTests(unittest.TestCase):
    def setUp(self):
        self.cwd = tempfile.mkdtemp()
        self.dead_cc = _row("11111111-aaaa-4bbb-8ccc-000000000001", cwd=self.cwd)
        self.dead_ccv = _row("22222222-aaaa-4bbb-8ccc-000000000002", tag="ccv", cwd=self.cwd)
        self.live = _row("33333333-aaaa-4bbb-8ccc-000000000003", proc=True, cell="tmux 2")
        self.oneshot = _row("44444444-aaaa-4bbb-8ccc-000000000004", oneshot=True,
                            cell="one-shot")
        self.gone = _row("55555555-aaaa-4bbb-8ccc-000000000005", cwd="/nonexistent/dir")
        self.rows = [self.dead_cc, self.dead_ccv, self.live, self.oneshot, self.gone]

    def run_it(self, wanted, **kw):
        out = io.StringIO()
        rc = board.resume_dead(self.rows, wanted, dry_run=True, target="9", out=out, **kw)
        return rc, out.getvalue()

    def test_listing_shows_only_dead_interactive_sessions(self):
        rc, text = self.run_it([])
        self.assertEqual(rc, 0)
        self.assertIn("11111111", text)
        self.assertIn("22222222", text)
        self.assertIn("55555555", text)
        self.assertNotIn("33333333", text)   # live
        self.assertNotIn("44444444", text)   # finished one-shot
        self.assertIn("--resume-dead", text)

    def test_dry_run_uses_the_wrapper_for_each_config_and_the_session_colon_target(self):
        rc, text = self.run_it(["11111111", "22222222"])
        self.assertEqual(rc, 0)
        self.assertIn("clauded --resume 11111111-aaaa-4bbb-8ccc-000000000001", text)
        self.assertIn("clauded-vals --resume 22222222-aaaa-4bbb-8ccc-000000000002", text)
        self.assertIn("-t 9: -n cc-11111111 -c " + self.cwd, text)
        self.assertIn("-t 9: -n ccv-22222222", text)
        self.assertNotIn("--fork-session", text)

    def test_fork_flag_and_all(self):
        rc, text = self.run_it(["all"], fork=True)
        self.assertEqual(rc, 0)
        self.assertEqual(text.count("--fork-session"), 2)   # the two resumable rows
        self.assertIn("55555555: skipped, cwd missing", text)
        self.assertIn("2 window(s)", text)

    def test_live_oneshot_ambiguous_and_unknown_ids_are_refused(self):
        for prefix, why in (("33333333", "already running"), ("44444444", "finished"),
                            ("deadbeef", "no transcript")):
            rc, text = self.run_it([prefix])
            self.assertEqual(rc, 1, prefix)
            self.assertIn(why, text)
        self.rows.append(_row("11111111-bbbb-4bbb-8ccc-000000000009", cwd=self.cwd))
        rc, text = self.run_it(["11111111"])
        self.assertEqual(rc, 1)
        self.assertIn("ambiguous", text)

    def test_only_uuid_shaped_ids_are_typed_into_a_shell(self):
        self.rows.append(_row("66666666; rm -rf ~", cwd=self.cwd))
        rc, text = self.run_it(["66666666"])
        self.assertEqual(rc, 1)
        self.assertIn("not UUID-shaped", text)
        self.assertNotIn("rm -rf", text.split("skipped")[1].split("\n")[1] if "\n" in text.split("skipped")[1] else "")
        self.assertNotIn("send-keys", text)


if __name__ == "__main__":
    unittest.main()
