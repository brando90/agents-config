"""Deterministic tests for remote experiment mapping and honest status display."""
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import agent_board as board
import agent_board_remote_status as remote


class StatusTests(unittest.TestCase):
    def test_label_is_not_experiment_number(self):
        dirs = {'85': '/repo/experiments/85_E4_full', '4': '/repo/experiments/4_old'}
        self.assertEqual(board.remote_experiment_number('vb-e4-full896-20260914', dirs), '85')
        self.assertIsNone(board.remote_experiment_number('vb-e4-job', {}))
        dirs['86'] = '/repo/experiments/86_E4_other'
        self.assertIsNone(board.remote_experiment_number('vb-e4-job', dirs))
        self.assertEqual(board.remote_experiment_number('expt75-work', dirs), '75')

    def test_coordinator_green_does_not_claim_generation(self):
        r = dict(run_binding={'progress': True}, observed_at=time.time(), coordinator_alive=True, driver_alive=False,
                 generated=1, scored=1, planned=1792, progress_age=20,
                 watchdog_age=20, watchdog_status='BLOCKED_HANDOFF')
        state, notes, color = board.receipt_display(r)
        self.assertIn('DRIVER STOPPED', state)
        self.assertEqual(color, 'live')
        self.assertIn('reported generated 1/1792, scored 1/1792', notes)
        self.assertEqual(board.receipt_display(r, True)[2], 'stale')
        r['observed_at'] -= 700
        self.assertEqual(board.receipt_display(r)[2], 'stale')
        self.assertTrue(board.receipt_display(r)[1][0].startswith('last reported'))

    def test_malformed_timestamp_is_unknown(self):
        state, _, color = board.receipt_display({'progress_age': 0})
        self.assertEqual(color, 'stale')
        self.assertIn('UNKNOWN', state)
        self.assertIsNone(remote.process_alive({'pid': None}))
        self.assertIsNone(remote.process_alive({'pid': float('inf')}))
        self.assertIsNone(remote.process_alive({'pid': True}))
        self.assertIsNone(remote.receipt_age({'at': 'not a date'}, time.time()))

    def test_receipt_binding_and_allowlist(self):
        with tempfile.TemporaryDirectory() as d:
            cwd = str(Path(d) / 'repo')
            ack = {'session': 'job', 'cwd': cwd, 'pid': 1, 'process_start_ticks': '2',
                   'boot_id': 'boot', 'identity_environment': {'SECRET': 'must not escape'}}
            Path(d, 'acknowledgement.json').write_text(json.dumps(ack))
            Path(d, 'progress.json').write_text(json.dumps({'generated': 0, 'planned': 896}))
            with patch.object(remote, 'process_alive', return_value=True):
                result = remote.job_status('job', cwd, time.time())
            self.assertEqual(result['generated'], 0)
            self.assertFalse(result['run_binding']['progress'])
            self.assertIsNone(result['driver_alive'])
            self.assertIn('run identity missing', board.receipt_display(result)[1][0])
            ack['run_id'] = 'new-run'
            Path(d, 'acknowledgement.json').write_text(json.dumps(ack))
            Path(d, 'progress.json').write_text(json.dumps({'run_id': 'old-run', 'generated': 17, 'planned': 20}))
            Path(d, 'driver_identity.json').write_text(json.dumps({'run_id': 'old-run', 'process': {'pid': 123}}))
            with patch.object(remote, 'process_alive', return_value=True):
                mixed = remote.job_status('job', cwd, time.time())
            self.assertFalse(mixed['run_binding']['progress'])
            self.assertIsNone(mixed['driver_alive'])
            Path(d, 'progress.json').write_text(json.dumps({'run_id': 'new-run', 'generated': 2, 'planned': 20}))
            with patch.object(remote, 'process_alive', return_value=True):
                bound = remote.job_status('job', cwd, time.time())
            self.assertTrue(bound['run_binding']['progress'])
            self.assertNotIn('SECRET', json.dumps(result))
            self.assertIsNone(remote.job_status('different-job', cwd, time.time()))
            Path(d, 'progress.json').write_text('x' * 262145)
            self.assertEqual(remote.read_record(Path(d, 'progress.json')), {})

    def test_ssh_markers_inside_process_arguments_are_not_delimiters(self):
        receipt = {'job': {'observed_at': time.time(), 'coordinator_alive': True}}
        output = ('job\t1\t1\t/repo\n=PS=\n2 1 codex\n=ARGS=\n'
                  '2 codex -m astra\n3 sh -c "echo =CFG=; echo =RECEIPTS="\n'
                  '=CFG=\nmodel = "astra"\n=N=\n1\n=RECEIPTS=\n' + json.dumps(receipt))
        with tempfile.TemporaryDirectory() as d, \
             patch.object(board, 'SNAP_CACHE', str(Path(d)/'snap.json')), \
             patch.object(board, 'BOARD_DIR', d), \
             patch.object(board, 'SNAP_HOSTS', ['node']), \
             patch.object(board.subprocess, 'run', return_value=type('R', (), {'returncode': 0, 'stdout': output})()):
            hosts = board._poll_snap_now()
        self.assertEqual(hosts[0]['tmux'][0]['status_receipt'], receipt['job'])

    def test_pid_reuse_and_zombie_do_not_show_live(self):
        identity = {'pid': 123, 'boot_id': 'boot', 'start_ticks': '42'}
        fields = ['S'] + ['0'] * 18 + ['42']
        with patch.object(Path, 'read_text', side_effect=['boot\n', '123 (a space) ' + ' '.join(fields)]):
            self.assertTrue(remote.process_alive(identity))
        with patch.object(Path, 'read_text', side_effect=['boot\n', '123 (a space) ' + ' '.join(fields[:-1]+['43'])]):
            self.assertFalse(remote.process_alive(identity))
        fields[0] = 'Z'
        with patch.object(Path, 'read_text', side_effect=['boot\n', '123 (a space) ' + ' '.join(fields)]):
            self.assertFalse(remote.process_alive(identity))


if __name__ == '__main__':
    unittest.main()
