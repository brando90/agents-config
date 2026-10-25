import base64
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import auto_sync as auto
import sync_runtime as runtime


class AutoSyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.top = Path(self.tmp.name).resolve()
        self.hub = self.top/'hub'
        self.clients = []
        for name in ('a','b'):
            root = self.top/name/'config'
            profile = self.top/name/'profile'
            (root/'skills/demo').mkdir(parents=True)
            profile.mkdir()
            (root/'skills/demo/SKILL.md').write_text('original')
            (root/'runtime.json').write_text(json.dumps({'version':1,'settings':{'skills':['${CONFIG_DIR}/skills'],'theme':'dark'},'trackedDirectories':['skills']}))
            with contextlib.redirect_stdout(io.StringIO()):
                runtime.sync(root/'runtime.json', profile)
            self.clients.append({'root':str(root),'profile':str(profile),'hub':str(self.hub)})
        self.a,self.b = self.clients

    def value(self, client, name='theme'):
        return runtime.read_json(Path(client['profile'])/'settings.json').get(name)

    def edit(self, client, name, value):
        p = Path(client['profile'])/'settings.json'
        s = runtime.read_json(p)
        if value is None: s.pop(name,None)
        else: s[name]=value
        p.write_text(json.dumps(s))

    def setup_pair(self):
        self.assertEqual(auto.once(self.a,seed=True),0)
        self.assertEqual(auto.once(self.b,enroll=True),0)

    def test_two_way_settings_and_skill_edits(self):
        self.setup_pair()
        self.edit(self.a,'theme','light')
        self.assertEqual(auto.once(self.a),0)
        self.assertEqual(auto.once(self.b),0)
        self.assertEqual(self.value(self.b),'light')
        p = Path(self.b['root'])/'skills/demo/SKILL.md'
        p.write_text('edited on b')
        self.assertEqual(auto.once(self.b),0)
        self.assertEqual(auto.once(self.a),0)
        self.assertEqual((Path(self.a['root'])/'skills/demo/SKILL.md').read_text(),'edited on b')

    def test_conflict_preserves_both_and_does_not_advance_baseline(self):
        self.setup_pair()
        before=(Path(self.b['profile'])/'auto-sync/baseline.json').read_bytes()
        self.edit(self.a,'theme','a');self.edit(self.b,'theme','b')
        auto.once(self.a)
        self.assertEqual(auto.once(self.b),1)
        self.assertEqual(self.value(self.b),'b')
        self.assertEqual((Path(self.b['profile'])/'auto-sync/baseline.json').read_bytes(),before)
        self.edit(self.b,'theme','a')
        self.assertEqual(auto.once(self.b),0)

    def test_nonoverlapping_changes_merge(self):
        self.setup_pair()
        self.edit(self.a,'theme','light');self.edit(self.b,'hideThinkingBlock',True)
        auto.once(self.a);auto.once(self.b);auto.once(self.a)
        self.assertEqual(self.value(self.b),'light')
        self.assertTrue(self.value(self.a,'hideThinkingBlock'))

    def test_deletion_and_private_files(self):
        self.setup_pair()
        root=Path(self.a['root'])
        (root/'private-skills/private').mkdir(parents=True)
        (root/'private-skills/private/SKILL.md').write_text('private fixture')
        auto.once(self.a);auto.once(self.b)
        self.assertEqual((Path(self.b['root'])/'private-skills/private/SKILL.md').read_text(),'private fixture')
        self.edit(self.a,'theme',None)
        (root/'skills/demo/SKILL.md').unlink()
        auto.once(self.a);auto.once(self.b)
        self.assertIsNone(self.value(self.b))
        self.assertFalse((Path(self.b['root'])/'skills/demo/SKILL.md').exists())
        self.assertTrue(list((Path(self.b['profile'])/'auto-sync/backups').rglob('SKILL.md')))

    def test_host_override_and_identity_stay_local(self):
        profile=Path(self.b['profile'])
        (profile/'agents-config-host.json').write_text(json.dumps({'settings':{'defaultModel':'host-model'}}))
        self.edit(self.b,'defaultModel','host-model');self.edit(self.b,'deviceId','only-b')
        self.edit(self.a,'defaultModel','shared-model')
        self.setup_pair()
        self.assertEqual(self.value(self.b,'defaultModel'),'host-model')
        self.assertEqual(self.value(self.b,'deviceId'),'only-b')
        self.assertNotIn('setting/deviceId',runtime.read_json(self.hub/'state.json')['values'])

    def test_offline_and_concurrent_edit_preserved(self):
        self.setup_pair()
        self.edit(self.a,'theme','local')
        with patch.object(auto,'transport',side_effect=RuntimeError('offline')):
            with self.assertRaises(RuntimeError): auto.once(self.a)
        self.assertEqual(self.value(self.a),'local')
        original=auto.transport
        def racing(config,request):
            result=original(config,request)
            self.edit(self.a,'theme','newer')
            return result
        with patch.object(auto,'transport',side_effect=racing):
            with self.assertRaisesRegex(ValueError,'changed during sync'): auto.once(self.a)
        self.assertEqual(self.value(self.a),'newer')
        self.assertEqual(auto.once(self.a),0)
        self.assertEqual(auto.once(self.b),0)
        self.assertEqual(self.value(self.b),'newer')

    def test_mutable_npm_reference_pinned_to_installed_version(self):
        profile=Path(self.a['profile'])
        package=profile/'npm/node_modules/@example/tool'
        package.mkdir(parents=True)
        (package/'package.json').write_text('{"version":"1.2.3"}')
        self.assertEqual(auto.pin_packages(['npm:@example/tool'],profile),['npm:@example/tool@1.2.3'])
        self.assertEqual(auto.pin_packages(['npm:@example/tool@2.0.0'],profile),['npm:@example/tool@2.0.0'])

    def test_deletion_vs_edit_conflicts_and_roundtrip_modes(self):
        self.setup_pair()
        first=Path(self.a['root'])/'skills/demo/SKILL.md'
        second=Path(self.b['root'])/'skills/demo/SKILL.md'
        first.unlink();second.write_text('concurrent edit')
        auto.once(self.a)
        self.assertEqual(auto.once(self.b),1)
        self.assertEqual(second.read_text(),'concurrent edit')

    def test_hub_lock_and_idempotency(self):
        self.setup_pair()
        before=runtime.read_json(self.hub/'state.json')['revision']
        auto.once(self.a);auto.once(self.b)
        self.assertEqual(runtime.read_json(self.hub/'state.json')['revision'],before)
        with auto.lock(self.hub/'lock'):
            with self.assertRaises(BlockingIOError): auto.once(self.a)

    def test_manifest_edit_becomes_shared(self):
        self.setup_pair()
        path=Path(self.a['root'])/'runtime.json'
        spec=json.loads(path.read_text());spec['settings']['theme']='light';path.write_text(json.dumps(spec))
        self.assertEqual(auto.once(self.a),0)
        self.assertEqual(auto.once(self.b),0)
        self.assertEqual(self.value(self.b),'light')

    def test_malicious_paths_symlinks_and_unknown_settings_rejected(self):
        for key in ('file/skills/../../auth.json','file/skills/.env','setting/apiKey'):
            with self.assertRaises(ValueError): auto.validate({key:None})
        root=Path(self.a['root']);(root/'skills/link').symlink_to(self.top)
        with self.assertRaises(ValueError): auto.snapshot(root,Path(self.a['profile']),{})

    def test_bootstrap_requires_explicit_choice_and_lock_respected(self):
        with self.assertRaises(ValueError): auto.once(self.a)
        profile=Path(self.a['profile']);(profile/'settings.json.lock').mkdir()
        with self.assertRaises(FileExistsError): auto.once(self.a,seed=True)


if __name__=='__main__': unittest.main()
