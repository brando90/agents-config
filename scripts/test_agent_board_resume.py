"""TLDR: unit tests for agent_board's one-shot classification and --resume-dead (mocked tmux, synthetic transcripts)."""

import io
import json
import os
import tempfile
import threading
import time
import unittest
from unittest import mock

import agent_board as board

UUID = "{}-aaaa-4bbb-8ccc-{:012d}"


def _records(entrypoint, cwd="/Users/me/proj", model="claude-fable-5-1"):
    return [
        {"type": "mode", "entrypoint": entrypoint, "cwd": cwd},
        {"type": "user", "cwd": cwd, "gitBranch": "main", "entrypoint": entrypoint,
         "message": {"role": "user", "content": "Review the private board forwarding fix"}},
        {"type": "assistant", "entrypoint": entrypoint,
         "message": {"role": "assistant", "model": model,
                     "content": [{"type": "text", "text": "VERDICT: PASS"}]}},
    ]


def _write(path, recs):
    with open(path, "w") as fh:
        # compact separators: Claude Code writes its records without spaces
        fh.write("\n".join(json.dumps(r, separators=(",", ":")) for r in recs) + "\n")
    return path


def _row(sid, tag="cc", proc=False, oneshot=False, cwd="/", age=3600.0, cell="—"):
    return {"sid": sid, "tag": tag, "proc": proc, "alive": proc, "oneshot": oneshot,
            "cwd": cwd, "age": age, "last": 1.0, "topic": "t", "tmux_cell": cell,
            "seats": [], "state": "stale"}


class TranscriptScanTests(unittest.TestCase):
    def test_head_scan_reads_the_entrypoint(self):
        with tempfile.TemporaryDirectory() as d:
            for entry in ("sdk-cli", "cli", "claude-desktop"):
                got = board.scan_transcript(_write(os.path.join(d, entry + ".jsonl"),
                                                   _records(entry)))
                topic, cwd, branch, model, effort, seen = got
                self.assertEqual(seen, entry)
                self.assertEqual((cwd, model), ("/Users/me/proj", "claude-fable-5-1"))
                self.assertTrue(topic.startswith("Review the private board"))
            self.assertIn("sdk-cli", board.ONESHOT_ENTRYPOINTS)
            self.assertNotIn("cli", board.ONESHOT_ENTRYPOINTS)

    def test_missing_entrypoint_is_empty_not_a_guess(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(os.path.join(d, "old.jsonl"),
                       [{"type": "user", "cwd": "/x", "message": {"role": "user", "content": "hi"}}])
            self.assertEqual(board.scan_transcript(p)[5], "")
            self.assertEqual(board.current_model(p, "m", "e", "")[2], "")

    def test_tail_wins_when_a_print_run_was_continued_interactively(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(os.path.join(d, "t.jsonl"), _records("sdk-cli") + _records("cli"))
            self.assertEqual(board.scan_transcript(p)[5], "sdk-cli")           # head
            self.assertEqual(board.current_model(p, "", "", "sdk-cli")[2], "cli")  # newest


class ClassificationTests(unittest.TestCase):
    """Rows as collect_sessions() builds them, with the process registry mocked."""

    def rows_for(self, procs):
        with tempfile.TemporaryDirectory() as cfg:
            proj = os.path.join(cfg, "projects", "-tmp-proj")
            os.makedirs(proj)
            sids = {k: UUID.format(k * 8, i) for i, k in enumerate("abcd", 1)}
            _write(os.path.join(proj, sids["a"] + ".jsonl"), _records("sdk-cli"))
            _write(os.path.join(proj, sids["b"] + ".jsonl"), _records("sdk-cli"))
            _write(os.path.join(proj, sids["c"] + ".jsonl"), _records("cli"))
            _write(os.path.join(proj, sids["d"] + ".jsonl"), _records("sdk-cli") + _records("cli"))
            reg = {sids[k]: [{"pid": "1", "tmux": "2", "app": None, "updated": 0}] for k in procs}
            fake_expt = lambda path, kind, cache, dirs, model="", effort="", entry="": (
                ("-", "") + board.current_model(path, model, effort, entry))
            with mock.patch.object(board, "CONFIGS", {cfg: "cc"}), \
                 mock.patch.object(board, "claude_registry", lambda tab, panes: reg), \
                 mock.patch.object(board, "load_registry", lambda: {}), \
                 mock.patch.object(board, "load_expt_cache", lambda: {}), \
                 mock.patch.object(board, "save_expt_cache", lambda c: None), \
                 mock.patch.object(board, "local_experiment_dirs", lambda: []), \
                 mock.patch.object(board, "load_summaries", lambda: {}), \
                 mock.patch.object(board, "session_expt", fake_expt):
                rows = board.collect_sessions(1, True, tab={}, panes={}, collapse=False)
            return sids, {r["sid"]: r for r in rows}

    def test_finished_running_interactive_and_continued_print_runs(self):
        sids, rows = self.rows_for(procs="b")
        a, b, c, d = (rows[sids[k]] for k in "abcd")
        self.assertEqual((a["tmux_cell"], a["tmux_how"], a["state"], a["oneshot"]),
                         ("one-shot", "finished", "stale", True))      # exited claude -p
        self.assertEqual((b["tmux_cell"], b["tmux_how"], b["state"], b["proc"]),
                         ("tmux 2", "live", "live", True))             # claude -p still running
        self.assertEqual((c["tmux_cell"], c["tmux_how"], c["oneshot"]), ("—", "exited", False))
        self.assertEqual((d["tmux_cell"], d["oneshot"]), ("—", False))  # continued interactively

    def test_finished_oneshot_stays_listed_while_fresh_then_drops(self):
        fresh = _row("a" * 36, oneshot=True, age=60.0, cell="one-shot")
        old = _row("b" * 36, oneshot=True, age=board.IDLE_S + 1, cell="one-shot")
        self.assertEqual([r["sid"] for r in board.one_per_seat([fresh, old])], [fresh["sid"]])

    def test_live_and_seated_rows_are_always_kept(self):
        live = _row("c" * 36, proc=True, age=99999.0, cell="tmux 2")
        seated = dict(_row("d" * 36, age=99999.0), seats=["2"])
        self.assertEqual(len(board.one_per_seat([live, seated])), 2)


class AgentBinaryTests(unittest.TestCase):
    """Trigger Rule 46 runs a worker from a private per-node COPY of the binary
    (`claude-pinned`). If the board does not recognise it, the live session reads as
    having no process -- and `--resume-dead all` forks a session that is still running,
    the exact outcome the liveness guard exists to prevent."""

    def registry_for(self, command):
        with tempfile.TemporaryDirectory() as cfg:
            os.makedirs(os.path.join(cfg, "sessions"))
            sid = UUID.format("11111111", 7)
            start = 1788983319.0
            with open(os.path.join(cfg, "sessions", "4242.json"), "w") as fh:
                json.dump({"pid": 4242, "sessionId": sid, "tmux": "vb-fix:@1.%1",
                           "startedAt": int(start * 1000)}, fh)
            tab = {"4242": ("1", start, command, "??")}
            with mock.patch.object(board, "CONFIGS", {cfg: "cc"}):
                return sid, board.claude_registry(tab, {})

    def test_a_pinned_copy_of_the_binary_counts_as_a_live_process(self):
        for command in ["/lfs/h/0/u/bin/claude-pinned --dangerously-skip-permissions",
                        "/lfs/h/0/u/bin/claude-pinned -p reply OK",
                        "/opt/claude.exe --model claude-fable-5-1",
                        "claude --remote-control vb-fix --model claude-fable-5-1",
                        "node /usr/lib/node_modules/@anthropic-ai/claude-code/cli.js"]:
            sid, reg = self.registry_for(command)
            self.assertEqual([p["pid"] for p in reg.get(sid, [])], ["4242"], command)
            self.assertEqual(reg[sid][0]["tmux"], "vb-fix", command)

    def test_a_merely_similar_command_is_still_not_an_agent(self):
        for command in ["/opt/claudette --model claude-fable-5-1", "vim /tmp/claude.md",
                        "less /var/log/codex.log", "python3 claude_helper.py",
                        "less /tmp/codex-pinned", "python3 /tmp/claude-helper.py",
                        "bash -c echo Claude Code",
                        "vim /usr/lib/node_modules/@anthropic-ai/claude-code/cli.js",
                        "node /tmp/helper.js /usr/lib/node_modules/@openai/codex/bin/codex.js"]:
            sid, reg = self.registry_for(command)
            self.assertEqual(reg, {}, command)

    def test_codex_detection_matches_a_pinned_copy_too(self):
        for command in ["/home/u/bin/codex-pinned -m gpt-6-astra", "codex exec -m gpt-6-astra",
                        "/opt/codex.exe -m gpt-6-astra",
                        "node /usr/lib/node_modules/@openai/codex/bin/codex.js exec"]:
            self.assertTrue(board.CODEX_RE.search(command), command)
        for command in ["/opt/codexicon run", "/opt/claude --model x", "less /tmp/codex-pinned",
                        "vim /usr/lib/node_modules/@openai/codex/bin/codex.js"]:
            self.assertFalse(board.CODEX_RE.search(command), command)

    def test_helper_executables_cannot_claim_a_matching_registry_entry(self):
        for command in ["/opt/claude-monitor --model claude-fable-5-1",
                        "/opt/claude_helper -p task", "/opt/codex-helper exec -m gpt-6-astra",
                        "/opt/codex-monitor -m gpt-6-astra"]:
            with self.subTest(command=command):
                sid, registry = self.registry_for(command)
                self.assertEqual(registry, {})
                self.assertFalse(board.CODEX_RE.search(command))

    def test_remote_panes_recognize_pinned_and_packaged_agents(self):
        for command, expected in [
            ("/home/u/bin/claude-pinned --model claude-fable-5-1 -p review", ("cc", "fable5.1")),
            ("/home/u/bin/codex-pinned -m gpt-6-astra -c model_reasoning_effort=ultra",
             ("cxd", "gpt-6-astra+ultra")),
            ("node /usr/lib/node_modules/@anthropic-ai/claude-code/cli.js --model claude-sonnet-5",
             ("cc", "sonnet5")),
            ("node /usr/local/bin/codex -m gpt-6-astra", ("cxd", "gpt-6-astra")),
            ("less /tmp/claude-pinned", ("—", "")),
        ]:
            with self.subTest(command=command):
                self.assertEqual(board.snap_agent([command], {}), expected)


class ProcessTableTests(unittest.TestCase):
    def test_failed_registry_read_refuses_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            sessions = os.path.join(directory, "sessions")
            os.mkdir(sessions)
            with open(os.path.join(sessions, "4242.json"), "w") as fh:
                fh.write('{"pid":4242,')  # interrupted or still-in-progress registry write
            row = _row(UUID.format("11111111", 1), cwd=directory)
            out = io.StringIO()
            with mock.patch.object(board, "BOARD_DIR", directory), \
                 mock.patch.object(board, "CONFIGS", {directory: "cc"}), \
                 mock.patch.object(board, "process_table", return_value={"4242": ("1", 1, "claude")}), \
                 mock.patch.object(board.subprocess, "run") as run:
                rc = board.resume_dead([row], [row["sid"]], target=("$9", "9"), out=out)
            self.assertEqual(rc, 1)
            self.assertIn("cannot read the process registry entry", out.getvalue())
            run.assert_not_called()

    def test_failed_ps_with_partial_output_refuses_resume(self):
        partial = mock.Mock(returncode=1,
                            stdout="99999 1 Wed Sep  9 12:00:00 2026 ? /bin/bash\n")
        row = _row(UUID.format("11111111", 1), cwd="/")
        output = io.StringIO()
        with mock.patch.object(board.subprocess, "run", return_value=partial) as run, \
             mock.patch.object(board, "tmux_panes", return_value={}), \
             mock.patch.object(board, "collect_sessions", return_value=[row]), \
             mock.patch.object(board.sys, "argv", ["agent_board.py", "--resume-dead", "all"]), \
             mock.patch.object(board.sys, "stdout", output):
            self.assertEqual(board.main(), 1)
        self.assertIn("refusing to resume anything", output.getvalue())
        self.assertEqual(len(run.call_args_list), 1)
        self.assertEqual(run.call_args.args[0][0], "ps")


class CodexResumeTests(unittest.TestCase):
    old_sid = UUID.format("aaaaaaaa", 1)
    fresh_sid = UUID.format("bbbbbbbb", 2)

    def rows_for(self, command):
        now = int(time.time())
        stamp = lambda epoch: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch))
        with tempfile.TemporaryDirectory() as directory:
            rollouts = os.path.join(directory, "sessions", "2026", "09", "09")
            os.makedirs(rollouts)
            entries = []
            # Put the new thread first: a resumed process must not accidentally claim it
            # just because this different thread was created at the same time.
            for sid, started in [(self.fresh_sid, now), (self.old_sid, now - 86400)]:
                entries.append({"id": sid, "updated_at": stamp(now), "thread_name": "fixture"})
                _write(os.path.join(rollouts, f"rollout-fixture-{sid}.jsonl"), [
                    {"type": "session_meta", "payload": {"timestamp": stamp(started), "cwd": directory}},
                    {"type": "turn_context", "payload": {"model": "gpt-6-astra"}},
                ])
            _write(os.path.join(directory, "session_index.jsonl"), entries)
            with mock.patch.object(board, "CODEX_DIR", directory), \
                 mock.patch.object(board, "load_expt_cache", return_value={}), \
                 mock.patch.object(board, "save_expt_cache"), \
                 mock.patch.object(board, "local_experiment_dirs", return_value={}):
                rows = board.collect_codex(6, {"4242": ("1", now, command, "?")},
                                          {"4242": ("fixture", "codex")})
            return {row["sid"]: row for row in rows}

    def test_explicit_resume_claims_its_old_thread_and_never_a_same_time_new_thread(self):
        for prefix in ["codex resume", "codex exec resume", "/tmp/codex-pinned resume",
                       "codex --approve-for-me -c model_reasoning_effort=ultra exec --json resume -m gpt-6-astra",
                       "node /usr/lib/node_modules/@openai/codex/bin/codex.js resume"]:
            with self.subTest(prefix=prefix):
                rows = self.rows_for(prefix + " " + self.old_sid)
                self.assertTrue(rows[self.old_sid]["proc"])
                self.assertEqual(rows[self.old_sid]["tmux_cell"], "fixture")
                self.assertFalse(rows[self.fresh_sid]["proc"])

    def test_new_thread_matching_ignores_a_resume_command_buried_in_its_prompt(self):
        for command in ["codex exec finish the fixture",
                        "codex exec -m gpt-6-astra explain codex resume " + self.old_sid,
                        "codex exec Explain the app-server and sandbox setup",
                        "codex Explain the app-server",
                        "codex -- explain resume " + self.old_sid]:
            with self.subTest(command=command):
                rows = self.rows_for(command)
                self.assertFalse(rows[self.old_sid]["proc"])
                self.assertTrue(rows[self.fresh_sid]["proc"])

    def test_actual_app_servers_and_sandbox_commands_do_not_claim_threads(self):
        for command in ["codex app-server", "codex -m gpt-6-astra app-server",
                        "codex sandbox linux true", "codex --strict-config mcp-server"]:
            with self.subTest(command=command):
                self.assertTrue(all(row["proc"] is False for row in self.rows_for(command).values()))

    def test_last_picker_and_named_resumes_report_unknown_identity(self):
        for command in ["codex resume --last", "codex exec resume --last continue",
                        "codex resume", "codex resume my-thread-name"]:
            with self.subTest(command=command):
                for row in self.rows_for(command).values():
                    self.assertIsNone(row["proc"])
                    self.assertEqual(row["tmux_cell"], "? (resume)")
                    self.assertIn("cannot be established", row["note"])


class TmuxTargetTests(unittest.TestCase):
    @staticmethod
    def fake_run(table):
        def run(args, **kw):
            r = mock.Mock()
            out = table.get(args[1])
            r.returncode, r.stdout, r.stderr = (1, "", "") if out is None else (0, out, "")
            return r
        return run

    def test_first_session_by_id_even_when_names_have_spaces(self):
        with mock.patch.object(board.subprocess, "run",
                               self.fake_run({"ls": "$4\tresearch work\n$5\tmain\n"})), \
             mock.patch.dict(os.environ, {"TMUX_PANE": ""}):
            self.assertEqual(board.tmux_target(dry_run=True), ("$4", "research work"))

    def test_the_callers_own_pane_wins(self):
        with mock.patch.object(board.subprocess, "run",
                               self.fake_run({"display-message": "$5\tmain\n", "ls": "$4\tx\n"})), \
             mock.patch.dict(os.environ, {"TMUX_PANE": "%3"}):
            self.assertEqual(board.tmux_target(dry_run=True), ("$5", "main"))

    def test_no_server_and_no_binary(self):
        with mock.patch.object(board.subprocess, "run", self.fake_run({})), \
             mock.patch.dict(os.environ, {"TMUX_PANE": ""}):
            self.assertEqual(board.tmux_target(dry_run=True), ("$recovered", "recovered"))

        def boom(*a, **k):
            raise FileNotFoundError("tmux")
        with mock.patch.object(board.subprocess, "run", boom):
            self.assertEqual(board.tmux_target(dry_run=True), (None, None))


class ResumeDeadTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.cwd = temporary.name
        for patch in [mock.patch.object(board, "BOARD_DIR", self.cwd),
                      mock.patch.object(board, "process_table", return_value={"1": ("0", 1, "sh")}),
                      mock.patch.object(board, "claude_registry", return_value={})]:
            patch.start()
            self.addCleanup(patch.stop)
        self.dead_cc = _row(UUID.format("11111111", 1), cwd=self.cwd)
        self.dead_ccv = _row(UUID.format("22222222", 2), tag="ccv", cwd=self.cwd)
        self.live = _row(UUID.format("33333333", 3), proc=True, cell="tmux 2")
        self.oneshot = _row(UUID.format("44444444", 4), oneshot=True, cell="one-shot")
        self.gone = _row(UUID.format("55555555", 5), cwd="/nonexistent/dir")
        self.rows = [self.dead_cc, self.dead_ccv, self.live, self.oneshot, self.gone]

    def run_it(self, wanted, **kw):
        out = io.StringIO()
        kw.setdefault("target", ("$9", "9"))
        rc = board.resume_dead(self.rows, wanted, dry_run=True, out=out, **kw)
        return rc, out.getvalue()

    def test_listing_shows_only_dead_interactive_sessions(self):
        rc, text = self.run_it([])
        self.assertEqual(rc, 0)
        for sid8 in ("11111111", "22222222", "55555555"):
            self.assertIn(sid8, text)
        self.assertNotIn("33333333", text)   # live
        self.assertNotIn("44444444", text)   # finished one-shot
        self.assertIn("--resume-dead", text)

    def test_dry_run_uses_each_configs_wrapper_and_the_session_id_target(self):
        rc, text = self.run_it(["11111111", "22222222"])
        self.assertEqual(rc, 0)
        self.assertIn("clauded --resume " + self.dead_cc["sid"], text)
        self.assertIn("clauded-vals --resume " + self.dead_ccv["sid"], text)
        self.assertIn("-t '$9:' -n cc-11111111 -c " + self.cwd, text)
        self.assertIn("-t '$9:' -n ccv-22222222", text)
        self.assertNotIn("--fork-session", text)
        self.assertIn("2 window(s) in tmux session 9", text)

    def test_all_with_fork_reports_the_skipped_row_and_exits_nonzero(self):
        rc, text = self.run_it(["all"], fork=True)
        self.assertEqual(rc, 1)
        self.assertEqual(text.count("--fork-session"), 2)
        self.assertIn("55555555: skipped, cwd missing", text)
        self.assertIn("2 window(s), 1 NOT opened", text)

    def test_a_session_named_twice_opens_once(self):
        rc, text = self.run_it(["11111111", self.dead_cc["sid"]])
        self.assertEqual(rc, 0)
        self.assertEqual(text.count("send-keys"), 1)
        self.assertIn("1 window(s)", text)

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

    def test_only_uuids_are_typed_into_a_shell(self):
        for bad in ("--continue", "66666666; rm -rf ~", "66666666-aaaa-4bbb-8ccc-00000000000g",
                    "66666666aaaa4bbb8ccc000000000006"):
            self.rows.append(_row(bad, cwd=self.cwd))
            rc, text = self.run_it([bad[:4]])
            self.assertEqual(rc, 1, bad)
            self.assertIn("not a UUID", text)
            self.assertNotIn("send-keys", text)
            self.rows.pop()

    def test_unreadable_process_table_refuses_everything(self):
        rc, text = self.run_it(["all"], liveness=False)
        self.assertEqual(rc, 1)
        self.assertIn("refusing", text)
        self.assertNotIn("send-keys", text)

    def test_no_tmux_is_reported_not_raised(self):
        rc, text = self.run_it(["11111111"], target=(None, None))
        self.assertEqual(rc, 1)
        self.assertIn("tmux is not available", text)

    def test_real_launch_failures_are_reported_and_counted(self):
        def run(args, **kw):
            r = mock.Mock()
            if args[1] == "new-window":
                r.returncode, r.stdout, r.stderr = 1, "", "can't find session"
            return r
        out = io.StringIO()
        with mock.patch.object(board.subprocess, "run", run):
            rc = board.resume_dead(self.rows, ["11111111"], target=("$9", "9"), out=out)
        self.assertEqual(rc, 1)
        self.assertIn("recovery failed (can't find session)", out.getvalue())
        self.assertIn("1 NOT opened", out.getvalue())

    def recovery_runner(self):
        windows = []
        calls = []

        def run(args, **kw):
            calls.append(args)
            if args[1] == "new-window":
                token = f"11:1234:@{len(windows) + 1}"
                windows.append(token)
                return mock.Mock(returncode=0, stdout=token + "\n", stderr="")
            if args[1] == "list-windows":
                return mock.Mock(returncode=0, stdout="\n".join(["11:1234:@0"] + windows), stderr="")
            return mock.Mock(returncode=0, stdout="", stderr="")

        return run, windows, calls

    def launch_one(self):
        out = io.StringIO()
        rc = board.resume_dead(self.rows, ["11111111"], target=("$9", "9"), out=out)
        return rc, out.getvalue()

    def test_a_second_startup_is_refused_until_its_recovery_window_is_closed(self):
        run, windows, calls = self.recovery_runner()
        with mock.patch.object(board.subprocess, "run", run):
            self.assertEqual(self.launch_one()[0], 0)
            rc, text = self.launch_one()
            self.assertEqual(rc, 1)
            self.assertIn("recovery window @1 still exists", text)
            self.assertNotIn("clauded --resume", text)
            self.assertEqual(sum(c[1] == "new-window" for c in calls), 1)
            windows.clear()  # the user inspected and closed the failed startup window
            self.assertEqual(self.launch_one()[0], 0)
            self.assertEqual(sum(c[1] == "new-window" for c in calls), 2)

    def test_overlapping_recoveries_cannot_both_create_a_window(self):
        run, windows, calls = self.recovery_runner()
        entered, release = threading.Event(), threading.Event()
        first = []

        def delayed(args, **kw):
            if args[1] == "new-window":
                entered.set()
                self.assertTrue(release.wait(5))
            return run(args, **kw)

        with mock.patch.object(board.subprocess, "run", delayed):
            thread = threading.Thread(target=lambda: first.append(self.launch_one()))
            thread.start()
            try:
                self.assertTrue(entered.wait(5))
                rc, text = self.launch_one()
                self.assertEqual(rc, 1)
                self.assertIn("another recovery attempt holds", text)
            finally:
                release.set()
                thread.join(5)
        self.assertEqual(first[0][0], 0)
        self.assertEqual(len(windows), 1)

    def test_fresh_liveness_and_failed_refresh_both_refuse_a_launch(self):
        for table, registry, message in [
            ({}, {}, "cannot refresh the process table"),
            ({"1": ("0", 1, "sh")}, {self.dead_cc["sid"]: [{}]}, "already running"),
        ]:
            with mock.patch.object(board, "process_table", return_value=table), \
                 mock.patch.object(board, "claude_registry", return_value=registry), \
                 mock.patch.object(board.subprocess, "run") as run:
                rc, text = self.launch_one()
            self.assertEqual(rc, 1)
            self.assertIn(message, text)
            run.assert_not_called()

    def test_unknown_window_state_does_not_expire_a_reservation(self):
        run, windows, calls = self.recovery_runner()
        with mock.patch.object(board.subprocess, "run", run):
            self.assertEqual(self.launch_one()[0], 0)
        with mock.patch.object(board.subprocess, "run", return_value=mock.Mock(
                returncode=1, stdout="", stderr="tmux unavailable")):
            rc, text = self.launch_one()
        self.assertEqual(rc, 1)
        self.assertIn("cannot check the previous recovery window", text)

    def test_a_timed_out_launch_cannot_be_retried_without_inspection(self):
        with mock.patch.object(board.subprocess, "run", side_effect=board.subprocess.TimeoutExpired(
                "tmux new-window", 10)):
            self.assertEqual(self.launch_one()[0], 1)
        with mock.patch.object(board.subprocess, "run") as run:
            rc, text = self.launch_one()
        self.assertEqual(rc, 1)
        self.assertIn("recovery outcome is uncertain", text)
        run.assert_not_called()

    def test_a_new_server_can_reuse_a_window_number_without_claiming_an_old_reservation(self):
        run, windows, calls = self.recovery_runner()
        with mock.patch.object(board.subprocess, "run", run):
            self.assertEqual(self.launch_one()[0], 0)
            windows[:] = ["22:5678:@1"]
            self.assertEqual(self.launch_one()[0], 0)
        self.assertEqual(sum(c[1] == "new-window" for c in calls), 2)

    def test_switching_sockets_does_not_release_a_running_servers_reservation(self):
        run, windows, calls = self.recovery_runner()
        with mock.patch.object(board.subprocess, "run", run):
            self.assertEqual(self.launch_one()[0], 0)
        with mock.patch.object(board, "process_table", return_value={"11": ("1", 1234, "tmux")}), \
             mock.patch.object(board.subprocess, "run", return_value=mock.Mock(
                 returncode=0, stdout="22:5678:@0\n", stderr="")):
            rc, text = self.launch_one()
        self.assertEqual(rc, 1)
        self.assertIn("another tmux socket", text)


if __name__ == "__main__":
    unittest.main()
