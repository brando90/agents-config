#!/usr/bin/env python3
"""Enroll this Pi profile and install its native background sync service."""
import argparse
import json
import os
from pathlib import Path
import plistlib
import shlex
import subprocess
import sys

import auto_sync
import sync_runtime

LABEL = 'com.brando.pi-config-sync'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile',type=Path,default=Path.home()/'.pi/agent')
    p.add_argument('--hub',required=True)
    p.add_argument('--ssh-host')
    p.add_argument('--remote-script')
    p.add_argument('--seed',action='store_true')
    args=p.parse_args()
    root=Path(__file__).resolve().parent
    profile=args.profile.expanduser().resolve()
    folder=profile/'auto-sync'
    folder.mkdir(parents=True,exist_ok=True,mode=0o700)
    config={'root':str(root),'profile':str(profile),'hub':args.hub,'interval':60}
    if args.ssh_host:
        if not args.remote_script: p.error('--remote-script is required with --ssh-host')
        config.update(sshHost=args.ssh_host,remoteScript=args.remote_script)
    config_path=folder/'config.json'
    stable_path=':'.join([str(Path.home()/'.local/bin'),'/dfs/scratch0/brando9/bin','/opt/homebrew/bin','/usr/local/bin','/usr/bin','/bin','/usr/sbin','/sbin'])
    auto_sync.save(config_path,config)
    if not (folder/'baseline.json').exists():
        # Earlier rollout saved even redundant defaults as host overrides.
        # Keep intentional differences; let identical portable values sync.
        path=profile/'agents-config-host.json'
        if path.exists():
            host=sync_runtime.read_json(path)
            shared=sync_runtime.expand(sync_runtime.read_json(root/'runtime.json').get('settings',{}),root,profile)
            host['settings']={k:v for k,v in host.get('settings',{}).items() if shared.get(k)!=v}
            sync_runtime.write_json(path,host)
    command=[sys.executable,str(root/'auto_sync.py'),'watch','--config',str(config_path)]
    if sys.platform=='darwin':
        target=Path.home()/'Library/LaunchAgents'/f'{LABEL}.plist'
        target.parent.mkdir(parents=True,exist_ok=True)
        domain=f'gui/{os.getuid()}'
        subprocess.run(['launchctl','bootout',domain+'/'+LABEL],capture_output=True)
    else:
        subprocess.run(['systemctl','--user','stop','pi-config-sync.service'],capture_output=True)
    # Existing baseline must never be discarded by reinstalling the service.
    enrolled=(folder/'baseline.json').exists()
    for _ in range(3):
        result=auto_sync.once(config,seed=args.seed and not enrolled,enroll=not args.seed and not enrolled)
        if result==0: break
    if result: raise SystemExit('Enrollment failed; service not started. Inspect auto-sync/status.json.')
    if sys.platform=='darwin':
        data={'Label':LABEL,'ProgramArguments':command,'RunAtLoad':True,'KeepAlive':True,
              'ThrottleInterval':60,'ProcessType':'Background',
              'EnvironmentVariables':{'PATH':stable_path,'HOME':str(Path.home())},
              'StandardOutPath':str(folder/'service.log'),'StandardErrorPath':str(folder/'service.log')}
        target.write_bytes(plistlib.dumps(data));target.chmod(0o600)
        subprocess.run(['launchctl','bootstrap',domain,str(target)],check=True)
        subprocess.run(['launchctl','print',domain+'/'+LABEL],check=True,capture_output=True)
    else:
        target=Path.home()/'.config/systemd/user/pi-config-sync.service'
        target.parent.mkdir(parents=True,exist_ok=True)
        # systemd uses its own quoting; JSON strings supply compatible quoting for these paths.
        quote=lambda s: json.dumps(str(s)).replace('%','%%')
        text='\n'.join(['[Unit]','Description=Private automatic Pi configuration sync','After=network-online.target',
             '[Service]','Type=simple','ExecStart='+' '.join(quote(s) for s in command),
             'Environment='+quote('HOME='+str(Path.home())),
             'Environment='+quote('PATH='+stable_path),
             'Restart=always','RestartSec=60','UMask=0077',
             '[Install]','WantedBy=default.target',''])
        target.write_text(text)
        subprocess.run(['systemctl','--user','daemon-reload'],check=True)
        subprocess.run(['systemctl','--user','enable','--now','pi-config-sync.service'],check=True)
        subprocess.run(['systemctl','--user','is-active','pi-config-sync.service'],check=True)
        linger=subprocess.run(['loginctl','enable-linger',str(os.getuid())],capture_output=True)
        if linger.returncode:
            print('Linger unavailable: user service persistence after logout must be verified separately.')
    print('Installed automatic Pi sync: every 60 seconds; offline retry up to 30 minutes; no model requests.')
    print('Status: '+str(folder/'status.json'))
    return 0


if __name__=='__main__': raise SystemExit(main())
