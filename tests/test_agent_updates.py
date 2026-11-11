"""Deterministic agent-update tests; no downloads, installed apps, or model calls."""
import hashlib
import io
import json
import os
from pathlib import Path
import plistlib
import re
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import auto_update_agent_apps as updates
import install_agent_updates as install
from install_dotfiles import parse_jsonc


class SettingsTests(unittest.TestCase):
    def test_only_update_mode_changes(self):
        original = '{\n  // Keep this comment\n  "model": "keep-me",\n  "nested": {"update.mode": "manual"},\n  "update.mode": "manual", // keep this too\n}\n'
        expected = original.replace('"update.mode": "manual", //', '"update.mode": "default", //')
        result = install.setting(original, "update.mode", "default")
        self.assertEqual(result, expected)
        self.assertEqual(install.setting(result, "update.mode", "default"), result)

    def test_insert_preserves_comments_crlf_and_strings(self):
        original = '{\r\n  "url": "https://example.test/a,}", // hello\r\n}\r\n'
        result = install.setting(original, "auto_update", True)
        self.assertEqual(parse_jsonc(result), {"url": "https://example.test/a,}", "auto_update": True})
        self.assertIn('// hello', result)
        self.assertNotIn('\n', result.replace('\r\n', ''))

    def test_bad_settings_fail_instead_of_replacing(self):
        with self.assertRaises((ValueError, IndexError)):
            install.setting('{"model": BROKEN}', "auto_update", True)

    def test_empty_settings(self):
        self.assertEqual(parse_jsonc(install.setting('', 'auto_update', True)), {'auto_update': True})

    def test_native_antigravity_uses_its_documented_string_boolean(self):
        _, key, value = install.SETTINGS['Antigravity']
        self.assertEqual(parse_jsonc(install.setting('{}', key, value)), {'autoCheckForUpdates': 'true'})

    def test_schedule_preserves_other_settings(self):
        data = install.agent_plist(Path('/Users/test'), {'Nice': 5})
        self.assertEqual(data['Nice'], 5)
        self.assertTrue(data['RunAtLoad'])
        self.assertEqual(data['StartInterval'], 3600)
        self.assertEqual(data['StartCalendarInterval'], {'Hour': 10, 'Minute': 17})
        self.assertEqual(plistlib.loads(plistlib.dumps(data)), data)
        self.assertNotIn('KeepAlive', data)

    def test_private_backups_and_idempotent_files(self):
        with tempfile.TemporaryDirectory() as root:
            home = Path(root)
            path = home / 'settings.json'
            path.write_text('{"model":"keep"}\n')
            old = path.read_bytes()
            installer = install.Installer(home, home / 'Applications', True)
            installer.file(path, b'{"model":"keep","auto_update":true}\n')
            self.assertEqual((installer.backup / 'settings.json').read_bytes(), old)
            self.assertEqual((installer.backup / 'settings.json').stat().st_mode & 0o777, 0o600)
            installer.file(path, path.read_bytes())
            self.assertEqual(len(installer.changes), 1)

    def test_existing_symlink_is_preserved(self):
        with tempfile.TemporaryDirectory() as root:
            home = Path(root)
            target = home / 'actual.json'
            target.write_text('{}')
            path = home / 'settings.json'
            path.symlink_to(target)
            installer = install.Installer(home, home / 'Applications', True)
            installer.file(path, b'{"auto_update":true}\n')
            self.assertTrue(path.is_symlink())
            self.assertEqual(target.read_bytes(), b'{"auto_update":true}\n')
            self.assertEqual((installer.backup / 'actual.json').read_text(), '{}')

    def test_reload_waits_for_the_shared_update_lock(self):
        with tempfile.TemporaryDirectory() as root:
            home = Path(root)
            with updates.update_lock(updates.lock_path(home)), patch.object(install.Path, 'home', return_value=home), \
                    patch.object(install.time, 'sleep'), patch.object(install.subprocess, 'run') as run:
                with self.assertRaisesRegex(RuntimeError, 'reload deferred'):
                    install.reload_job(home / 'agent.plist')
                run.assert_not_called()

    def test_reload_holds_the_lock_across_scheduler_changes(self):
        with tempfile.TemporaryDirectory() as root:
            home, plist = Path(root), Path(root) / 'agent.plist'
            def run(command, **kwargs):
                if command[1] in ('bootout', 'enable', 'bootstrap', 'kickstart'):
                    with updates.update_lock(updates.lock_path(home)) as acquired:
                        self.assertEqual(acquired, command[1] == 'kickstart')
                    self.assertNotIn('-k', command)
                return subprocess.CompletedProcess(command, 0, stdout=str(plist))
            with patch.object(install.Path, 'home', return_value=home), \
                    patch.object(install.subprocess, 'run', side_effect=run):
                install.reload_job(plist)

    def test_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as root:
            home = Path(root)
            installer = install.Installer(home, home / 'Applications', False)
            installer.file(home / 'not-created', b'hello')
            self.assertFalse((home / 'not-created').exists())
            self.assertFalse(installer.state.exists())


class UpdaterTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name)
        self.state = self.home / 'state'
        self.state.mkdir()
        self.updater = updates.Updater(self.home, self.state, io.StringIO(), time.monotonic() + 60)

    def test_actual_npm_prefix_not_default(self):
        root = self.home / 'custom/lib/node_modules/@openai/codex'
        (root / 'bin').mkdir(parents=True)
        (root / 'package.json').write_text('{"name":"@openai/codex","version":"1.0.0"}')
        entry = root / 'bin/codex.js'
        entry.write_text('')
        link = self.home / 'codex'
        link.symlink_to(entry)
        self.assertEqual(updates.npm_installation(str(link), '@openai/codex'),
                         (str((self.home / 'custom').resolve()), str(root.resolve())))
        self.assertIsNone(updates.npm_installation(str(link), '@other/codex'))

    def test_non_global_node_modules_not_adopted(self):
        root = self.home / 'project/node_modules/opencode-ai'
        (root / 'bin').mkdir(parents=True)
        (root / 'package.json').write_text('{"name":"opencode-ai"}')
        entry = root / 'bin/opencode'
        entry.touch()
        self.assertIsNone(updates.npm_installation(str(entry), 'opencode-ai'))

    def test_shared_lock_excludes_another_caller(self):
        path = self.state / 'lock'
        with updates.update_lock(path) as first:
            self.assertTrue(first)
            with updates.update_lock(path) as second:
                self.assertFalse(second)
        with updates.update_lock(path) as third:
            self.assertTrue(third)

    def test_custom_receipt_directory_does_not_create_a_competing_lock(self):
        with patch.object(updates.Path, 'home', return_value=self.home), \
                patch.object(updates.sys, 'platform', 'darwin'), \
                patch.dict(os.environ, {'XDG_STATE_HOME': str(self.home / 'custom-state'), 'AGENT_CLI_UPDATE_SKIP': '0'}), \
                patch.object(updates, 'discover', return_value=[]), \
                patch.object(updates, 'update_lock', wraps=updates.update_lock) as lock:
            self.assertEqual(updates.main([]), 0)
        lock.assert_called_once_with(self.home / '.local/state/agent-cli-updates/update.flock')

    def test_freshness_and_failure_retry(self):
        now = 100000
        self.assertFalse(updates.due({'status': 'updated', 'attempted_at': now - 3700}, now, 86400))
        self.assertTrue(updates.due({'status': 'failed', 'attempted_at': now - 3700}, now, 86400))
        self.assertFalse(updates.due({'status': 'deferred', 'attempted_at': now - 10}, now, 86400))
        self.assertTrue(updates.due({'status': 'checked', 'attempted_at': now}, now, 86400, True))

    def test_native_routes_do_not_restart_or_update_plugins(self):
        self.assertEqual(updates.NATIVE['pi'], ('update', '--self', '--no-approve'))
        self.assertNotIn('--handoff', updates.NATIVE['herdr'])
        self.assertIn('--no-gateway-restart', updates.NATIVE['hermes'])
        self.assertIn('--no-restart', updates.NATIVE['openclaw'])
        self.assertNotIn('--yes', updates.NATIVE['openclaw'])
        self.assertNotIn('agent', updates.NATIVE)  # Cursor retains the shared command name.
        self.assertFalse(any('--all' in args or '--plugins' in args for args in updates.NATIVE.values()))
        self.assertNotIn('gemini', updates.NATIVE)
        self.assertNotIn('harbor', updates.UV)
        self.assertNotIn('valkyrie', updates.UV)

    def test_unknown_subcommand_cannot_become_a_model_prompt(self):
        target = updates.Target('pi', 'native', '/bin/pi', ['/bin/pi', 'update', '--self'])
        with patch.object(self.updater, 'run', return_value='Usage: pi [prompt]\n') as run:
            with self.assertRaisesRegex(RuntimeError, 'no prompt was submitted'):
                self.updater.update(target)
        run.assert_called_once_with(['/bin/pi', '--help'], 30)

    def test_native_guard_accepts_both_help_layouts(self):
        target = updates.Target('pi', 'native', '/bin/pi', ['/bin/pi', 'update', '--self'])
        for help_text in ('  update  Update the CLI\n', '  pi update [source]\n', '  upgrade|update  Update the CLI\n'):
            with self.subTest(help_text=help_text), patch.object(self.updater, 'run', return_value=help_text):
                self.updater.guard(target)

    def test_cli_inventory_does_not_adopt_desktop_bundles(self):
        with patch.object(updates.shutil, 'which', side_effect=lambda name: '/opt/homebrew/bin/brew' if name == 'brew' else None):
            self.assertEqual(updates.discover(self.home), [])

    def test_dirty_hermes_is_never_stashed(self):
        repo = self.home / '.hermes/hermes-agent'
        (repo / '.git').mkdir(parents=True)
        target = updates.Target('hermes', 'native', '/bin/hermes', ['/bin/hermes', 'update'])
        with patch.object(self.updater, 'run', side_effect=['  update  Update Hermes\n', ' M local.py\n']) as run:
            with self.assertRaisesRegex(updates.Deferred, 'local work'):
                self.updater.update(target)
        self.assertEqual(run.call_count, 2)

    def test_patched_and_vendor_startup_clients_not_falsely_reported_updated(self):
        self.assertEqual(self.updater.update(updates.Target('patched', 'preserved'))['status'], 'preserved')
        self.assertEqual(self.updater.update(updates.Target('native', 'on-launch'))['status'], 'on-launch')

    def test_junie_requires_the_managed_vendor_shim(self):
        executable = self.home / 'junie'
        target = updates.Target('junie', 'on-launch', str(executable))
        executable.write_bytes(b'standalone binary')
        with self.assertRaisesRegex(updates.Deferred, 'shim is absent'):
            self.updater.update(target)
        executable.write_text('#!/bin/bash\n# JUNIE_MANAGED_SHIM\n')
        self.assertEqual(self.updater.update(target)['status'], 'on-launch')

    def test_fast_agent_uses_the_official_main_distribution(self):
        self.assertEqual(updates.UV['fast-agent-acp'], 'fast-agent-mcp')

    def test_broken_uv_client_can_be_repaired_by_its_manager(self):
        target = updates.Target('minion-code', 'uv', '/bin/minion-code', ['uv', 'tool', 'upgrade', 'minion-code'],
                                package='minion-code', prefix='/tools/minion-code')
        with patch.object(self.updater, 'version', side_effect=[RuntimeError('broken import'), '0.1.45']), \
                patch.object(self.updater, 'run', return_value='') as run:
            result = self.updater.update(target)
        run.assert_called_once_with(['/usr/bin/env', 'UV_TOOL_DIR=/tools', 'UV_TOOL_BIN_DIR=/bin', *target.command])
        self.assertEqual(result['before'], 'unavailable')
        self.assertEqual(result['after'], '0.1.45')

    def test_uv_does_not_export_commands_inside_its_virtual_environment(self):
        target = updates.Target('minion-code', 'uv', '/tools/minion-code/bin/minion-code',
                                ['uv', 'tool', 'upgrade', 'minion-code'], prefix='/tools/minion-code')
        with patch.object(self.updater, 'version', return_value='0.1.45'), \
                patch.object(self.updater, 'run') as run:
            with self.assertRaisesRegex(updates.Deferred, 'export directory'):
                self.updater.update(target)
        run.assert_not_called()

    def test_stakpak_autopilot_is_not_restarted(self):
        target = updates.Target('stakpak', 'native', '/bin/stakpak', ['/bin/stakpak', 'update'])
        with patch.object(self.updater, 'run', side_effect=['  update  Update binary\n', '/opt/bin/stakpak\n']):
            with self.assertRaisesRegex(updates.Deferred, 'restart autopilot'):
                self.updater.update(target)

    def test_failed_command_is_not_success(self):
        with self.assertRaisesRegex(RuntimeError, 'exited 7'):
            updates.run_command([sys.executable, '-c', 'raise SystemExit(7)'],
                                cwd=self.home, log=io.StringIO(), timeout=5)

    def test_timeout_is_bounded(self):
        start = time.monotonic()
        with self.assertRaisesRegex(RuntimeError, 'timed out'):
            updates.run_command([sys.executable, '-c', 'import time; time.sleep(30)'],
                                cwd=self.home, log=io.StringIO(), timeout=0.1)
        self.assertLess(time.monotonic() - start, 6)

    def test_version_prefix_is_not_lost(self):
        self.assertEqual(updates.VERSION.search('Hermes v0.22.5').group(0), '0.22.5')
        self.assertEqual(updates.VERSION.search('v1.2.41+abc123').group(0), '1.2.41+abc123')

    def test_unrecognized_version_is_not_reported_as_checked(self):
        target = updates.Target('tool', 'native', '/bin/tool')
        with patch.object(self.updater, 'run', return_value='unrecognized output'):
            with self.assertRaisesRegex(RuntimeError, 'version could not be verified'):
                self.updater.version(target)

    def test_mastra_metadata_and_help_not_unknown_version_flag(self):
        root = self.home / 'mastra'
        root.mkdir()
        (root / 'package.json').write_text('{"version":"0.48.1"}')
        target = updates.Target('mastracode', 'npm', '/bin/mastracode', package_dir=str(root))
        with patch.object(self.updater, 'run', return_value='Usage: mastracode --help') as run:
            self.assertEqual(self.updater.version(target), '0.48.1')
        run.assert_called_once_with(['/bin/mastracode', '--help'], 30)

    def test_uv_uses_its_own_distribution_metadata(self):
        target = updates.Target('minion-code', 'uv', '/bin/minion-code', package='minion-code', prefix='/tools/minion-code')
        with patch.object(self.updater, 'run', side_effect=['Usage: minion-code', '0.1.45\n']) as run:
            self.assertEqual(self.updater.version(target), '0.1.45')
        self.assertEqual(run.call_args_list[1].args[0][0], '/tools/minion-code/bin/python')
        self.assertNotIn('--version', str(run.call_args_list))

    def test_terminal_answers_only_known_install_prompt(self):
        program = "import os; assert os.isatty(0); print('Install TEST now?', flush=True); assert input() == 'y'; print('installed')"
        log = io.StringIO()
        output = updates.run_confirmed_command([sys.executable, '-c', program], cwd=self.home,
                                              log=log, timeout=5, env=os.environ.copy(),
                                              pattern=r'Install TEST now\?')
        self.assertIn('installed', output)

    def test_unexpected_terminal_prompt_is_not_accepted(self):
        program = "print('Unrelated operation?', flush=True); input()"
        with self.assertRaisesRegex(TimeoutError, 'unexpected confirmation'):
            updates.run_confirmed_command([sys.executable, '-c', program], cwd=self.home,
                                          log=io.StringIO(), timeout=0.2, env=os.environ.copy(),
                                          pattern=r'Install TEST now\?')

    def test_terminal_timeout_cleans_up_child_after_parent_exits(self):
        child_program = "import signal,time; signal.signal(signal.SIGHUP,signal.SIG_IGN); print('ready',flush=True); time.sleep(30)"
        program = (f"import subprocess,sys; child=subprocess.Popen([sys.executable,'-c',{child_program!r}],stdout=subprocess.PIPE); "
                   "assert child.stdout.readline().strip()==b'ready'; print('CHILD_PID='+str(child.pid),flush=True)")
        log = io.StringIO()
        with self.assertRaisesRegex(TimeoutError, 'timed out'):
            updates.run_confirmed_command([sys.executable, '-c', program], cwd=self.home,
                                          log=log, timeout=1, env=os.environ.copy(), pattern=r'Install TEST now\?')
        child = re.search(r'CHILD_PID=(\d+)', log.getvalue()).group(1)
        for _ in range(20):
            status = subprocess.run(['/bin/ps', '-p', child, '-o', 'stat='], capture_output=True, text=True)
            if status.returncode or status.stdout.strip().startswith('Z'):
                break
            time.sleep(0.02)
        else:
            self.fail('owned terminal child survived updater timeout')

    def test_old_openclaw_requires_bridge_before_native_update(self):
        target = updates.Target('openclaw', 'native', '/bin/openclaw', ['/bin/openclaw', 'update', '--no-restart'])
        with patch.object(self.updater, 'run', return_value='  update *  Update OpenClaw'), \
                patch.object(self.updater, 'version', return_value='2026.4.24'):
            with self.assertRaisesRegex(updates.Deferred, 'bridge migration'):
                self.updater.guard(target)
        with patch.object(self.updater, 'run', return_value='  update *  Update OpenClaw'), \
                patch.object(self.updater, 'version', return_value='2026.11.3'):
            self.updater.guard(target)

    def test_vtcode_does_not_offer_an_unrequested_desktop_install(self):
        target = updates.Target('vtcode', 'native', '/bin/vtcode', ['/bin/vtcode', 'update'])
        for help_text in ('update options', 'update --without-desktop'):
            with self.subTest(help_text=help_text), patch.object(self.updater, 'guard'), \
                    patch.object(self.updater, 'version', return_value='0.182.0'), \
                    patch.object(self.updater, 'run', side_effect=[help_text, 'already current']) as run:
                self.assertEqual(self.updater.update(target)['status'], 'checked')
                command = run.call_args_list[-1].args[0]
                self.assertEqual('--without-desktop' in command, '--without-desktop' in help_text)
                self.assertNotIn('--with-desktop', command)

    def test_vtcode_pin_is_retained(self):
        target = updates.Target('vtcode', 'native', '/bin/vtcode', ['/bin/vtcode', 'update'])
        with patch.object(self.updater, 'run', side_effect=['  update  Update binary\n', 'Pinned: 0.180.5 (test)\n']):
            with self.assertRaisesRegex(updates.Deferred, 'version pin'):
                self.updater.update(target)

    def test_stakpak_release_fallback_cannot_hide_failed_install(self):
        target = updates.Target('stakpak', 'native', '/bin/stakpak', ['/bin/stakpak', 'update'])
        for latest in ('v0.3.88', 'v0.3.89'):
            def run(command, timeout=300):
                if command == target.command:
                    raise RuntimeError('vendor endpoint unavailable')
                if command[0] == 'curl':
                    return json.dumps({'tag_name': latest})
                if command[0] == '/bin/ps':
                    return ''
                if '--help' in command:
                    return '  update  Update Stakpak\n'
                return 'stakpak 0.3.88\n'
            with self.subTest(latest=latest), patch.object(self.updater, 'run', side_effect=run), \
                    patch.object(self.updater, 'install_stakpak_release', side_effect=RuntimeError('download failed')) as install_release:
                if latest == 'v0.3.88':
                    self.assertEqual(self.updater.update(target)['status'], 'checked')
                    install_release.assert_not_called()
                else:
                    with self.assertRaisesRegex(RuntimeError, 'download failed'):
                        self.updater.update(target)
                    install_release.assert_called_once()

    def stakpak_fixture(self):
        executable = self.home / 'stakpak'
        executable.write_text('#!/bin/sh\necho stakpak 0.3.88\n')
        executable.chmod(0o700)
        buffer = io.BytesIO()
        binary = b'#!/bin/sh\necho stakpak 0.3.89\n'
        with tarfile.open(fileobj=buffer, mode='w:gz') as archive:
            for name, data in [('stakpak', binary), ('../outside', b'must not be extracted')]:
                member = tarfile.TarInfo(name)
                member.size = len(data)
                archive.addfile(member, io.BytesIO(data))
        data = buffer.getvalue()
        name = 'stakpak-darwin-aarch64.tar.gz'
        release = {'tag_name': 'v0.3.89', 'assets': [{'name': name,
                   'browser_download_url': 'https://github.com/stakpak/agent/releases/download/v0.3.89/' + name,
                   'digest': 'sha256:' + hashlib.sha256(data).hexdigest()}]}
        target = updates.Target('stakpak', 'native', str(executable), [str(executable), 'update'])
        actual_run = self.updater.run
        def run(command, timeout=300):
            if command[0] == 'curl':
                Path(command[command.index('-o') + 1]).write_bytes(data)
                return ''
            return actual_run(command, timeout)
        return target, release, run

    def test_official_binary_update_is_verified_and_does_not_extract_paths(self):
        target, release, run = self.stakpak_fixture()
        with patch.object(self.updater, 'run', side_effect=run), patch.object(self.updater, 'guard'), \
                patch.object(updates.platform, 'machine', return_value='arm64'):
            self.updater.install_stakpak_release(target, release)
        self.assertIn('0.3.89', Path(target.executable).read_text())
        self.assertFalse((self.home / 'outside').exists())
        self.assertEqual(list(self.home.glob('.stakpak-update-*')), [])

    def test_bad_release_checksum_keeps_original_binary(self):
        target, release, run = self.stakpak_fixture()
        original = Path(target.executable).read_bytes()
        release['assets'][0]['digest'] = 'sha256:' + '0' * 64
        with patch.object(self.updater, 'run', side_effect=run), patch.object(self.updater, 'guard'), \
                patch.object(updates.platform, 'machine', return_value='arm64'):
            with self.assertRaisesRegex(RuntimeError, 'checksum mismatch'):
                self.updater.install_stakpak_release(target, release)
        self.assertEqual(Path(target.executable).read_bytes(), original)

    def test_failed_active_binary_verification_rolls_back(self):
        target, release, run = self.stakpak_fixture()
        original = Path(target.executable).read_bytes()
        with patch.object(self.updater, 'run', side_effect=run), patch.object(self.updater, 'guard'), \
                patch.object(self.updater, 'version', side_effect=RuntimeError('active probe failed')), \
                patch.object(updates.platform, 'machine', return_value='arm64'):
            with self.assertRaisesRegex(RuntimeError, 'active probe failed'):
                self.updater.install_stakpak_release(target, release)
        self.assertEqual(Path(target.executable).read_bytes(), original)

    def test_atomic_receipt_is_private(self):
        path = self.state / 'status.json'
        updates.atomic_json(path, {'pi': {'status': 'updated', 'after': '1.5.2'}})
        self.assertEqual(json.loads(path.read_text())['pi']['after'], '1.5.2')
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(list(self.state.glob('*.tmp')), [])

    def test_npm_updates_exact_active_prefix_and_verifies(self):
        root = self.home / 'custom/lib/node_modules/tool'
        root.mkdir(parents=True)
        manifest = root / 'package.json'
        manifest.write_text('{"version":"1.0.0"}')
        target = updates.Target('tool', 'npm', '/bin/tool', ['npm'], 'tool',
                                str(self.home / 'custom'), str(root))
        calls = []
        def run(command, timeout=300):
            calls.append(command)
            if command[1] == 'view':
                return '"1.1.0"'
            if command[1] == 'install':
                manifest.write_text('{"version":"1.1.0"}')
                return ''
            return 'tool ' + json.loads(manifest.read_text())['version']
        with patch.object(self.updater, 'run', side_effect=run):
            result = self.updater.update(target)
        self.assertEqual(result, {'status': 'updated', 'before': '1.0.0', 'after': '1.1.0'})
        command = next(command for command in calls if command[1] == 'install')
        self.assertEqual(command[command.index('--prefix') + 1], str(self.home / 'custom'))
        self.assertEqual(command[-1], 'tool@1.1.0')


if __name__ == '__main__':
    unittest.main()
