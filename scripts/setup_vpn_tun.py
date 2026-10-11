#!/usr/bin/python3
"""Identify the exact Hub LXC from its container ID, then configure TUN."""
import argparse
import ipaddress
import json
import os
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def run(args):
    result=subprocess.run(args,capture_output=True,text=True,timeout=20)
    if result.returncode:
        raise ValueError('Kommandoen fejlede: '+args[0]+'. Kontrollér værtens opsætning.')
    return result.stdout


def discover(hub_id):
    matches=[]
    for line in run(['pct','list']).splitlines()[1:]:
        parts=line.split()
        if len(parts)<2 or not parts[0].isdigit() or parts[1]!='running':continue
        ctid=parts[0]
        try:
            items=json.loads(run(['pct','exec',ctid,'--','docker','inspect',hub_id]))
        except (ValueError,subprocess.TimeoutExpired):continue
        if len(items)!=1 or items[0].get('Id')!=hub_id or items[0].get('Name')!='/fjordhub':continue
        container=items[0]
        directory=next((m.get('Source') for m in container.get('Mounts',[])
                        if m.get('Destination')=='/fjordhub-src' and m.get('Type')=='bind'),None)
        if not directory:
            directory=(container.get('Config',{}).get('Labels') or {}).get('com.docker.compose.project.working_dir')
        if not isinstance(directory,str) or not re.fullmatch(r'/[A-Za-z0-9_./-]+',directory) or '..' in Path(directory).parts:
            raise ValueError('FjordHubs installationsmappe kunne ikke identificeres sikkert.')
        route=json.loads(run(['pct','exec',ctid,'--','ip','-j','-4','route','get','1.1.1.1']))
        guest=str(ipaddress.IPv4Address(route[0]['prefsrc']))
        host_route=json.loads(run(['ip','-j','-4','route','get',guest]))
        host=str(ipaddress.IPv4Address(host_route[0]['prefsrc']))
        matches.append({'ctid':ctid,'host':host,'directory':directory})
    if len(matches)!=1:
        raise ValueError('Denne FjordHub blev ikke fundet entydigt i en kørende LXC. Kør kommandoen på den rigtige Proxmox-vært, eller kopier en ny kommando fra guiden.')
    return matches[0]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--hub-container',required=True)
    parser.add_argument('--detect-only',action='store_true')
    args=parser.parse_args()
    if os.geteuid()!=0 or not Path('/etc/pve').is_dir():
        raise SystemExit('Kør kommandoen som root i Proxmox-værtens Shell.')
    if not re.fullmatch('[a-f0-9]{64}',args.hub_container):
        raise SystemExit('Ugyldigt FjordHub-container-ID.')
    try:
        target=discover(args.hub_container)
    except (ValueError,KeyError,IndexError,OSError,subprocess.TimeoutExpired) as exc:
        raise SystemExit(str(exc) if isinstance(exc,ValueError) else 'Proxmox-oplysningerne kunne ikke identificeres. Kontrollér værtens netværk.') from None
    if args.detect_only:
        print(json.dumps(target));return
    print('Opsætter TUN for FjordHub i LXC '+target['ctid']+'.',flush=True)
    from host_agent.storage import Agent
    Agent(target['ctid']).ensure_vpn_tun()
    from scripts import configure_proxmox
    sys.argv=['configure_proxmox.py',target['ctid'],'--host',target['host'],'--directory',target['directory']]
    configure_proxmox.main()
    run(['pct','exec',target['ctid'],'--','docker','exec','fjordhub','python','-c',
         'from services.vpn_setup import ensure_vpn_tun; ensure_vpn_tun(print)'])
    print('TUN er klar. Genindlæs FjordVPN-guiden og fortsæt installationen.')


if __name__=='__main__':main()
