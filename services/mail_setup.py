"""Provision FjordMail on its Docker host after the normal build/start step."""
import os
import re
from pathlib import Path, PurePosixPath
import docker
from services.installer import _container_path_to_host_path


def prepare_mail(install_dir, log):
    directory = Path(install_dir)
    script = directory / 'scripts' / 'enable-basic-mail.sh'
    if not script.is_file():
        raise RuntimeError('FjordMail-versionen mangler automatisk lageropsætning. Opdatér FjordMail først.')
    values = {}
    for line in (directory / '.env').read_text(encoding='utf-8').splitlines():
        key, separator, value = line.partition('=')
        if separator and not line.lstrip().startswith('#'):
            values[key.strip()] = value.strip().strip('\"\'')
    app = _container_path_to_host_path(directory)
    origin = values.get('MAIL_STORAGE_ORIGIN') or values.get('DATA_DIR')
    for value in (app, origin):
        if not value or not re.fullmatch(r'/[A-Za-z0-9_./-]+', value) or len(PurePosixPath(value).parts) < 3 or '..' in PurePosixPath(value).parts:
            raise RuntimeError('FjordMails installations- og lagerstier kunne ikke valideres på Docker-værten.')
    log('FjordHub klargør automatisk krypteret lager og mailmotor. Eksisterende data bevares.')
    client = docker.from_env(timeout=1200)
    helper = None
    try:
        image = client.containers.get(os.environ['HOSTNAME']).attrs['Image']
        args = ['--automatic', app, origin + '.cipher', origin + '.secure', origin + '.keys/storage.key']
        # The helper is short-lived; the mail application never receives host access.
        # Enter the actual Docker host mount namespace, rather than mounting FUSE
        # inside the management container where sibling containers cannot see it.
        code = "import os,sys;os.chroot('/host');os.chdir('/');os.execv('/usr/bin/nsenter',['nsenter','--target','1','--mount','--net','--uts','--ipc','--pid','--','/bin/bash',sys.argv[1],*sys.argv[2:]])"
        helper = client.containers.run(image, ['python', '-c', code, app + '/scripts/enable-basic-mail.sh', *args],
            entrypoint=[], privileged=True, pid_mode='host', network_mode='host',
            volumes={'/': {'bind': '/host', 'mode': 'rw'}}, detach=True,
            labels={'dk.fjordhub.setup': 'fjordmail'}, environment={'FJORDMAIL_AUTOMATIC_SETUP': '1'})
        for raw in helper.logs(stream=True, follow=True):
            for line in raw.decode('utf-8', errors='replace').splitlines():
                if line.startswith('FJORDMAIL_SETUP: '):
                    log(line[len('FJORDMAIL_SETUP: '):])
        result = helper.wait(timeout=1200)
        if result.get('StatusCode') != 0:
            raise RuntimeError('Automatisk FjordMail-klargøring fejlede. Tidligere data og konfiguration er bevaret. Kontrollér Docker-værtens FUSE-adgang og prøv opdateringen igen.')
        log('FjordMail: krypteret lager og mailmotor er klar. Eksisterende pausevalg bevares.')
    except docker.errors.DockerException:
        raise RuntimeError('FjordHub kunne ikke gennemføre automatisk FjordMail-klargøring på Docker-værten.') from None
    finally:
        if helper is not None:
            helper.remove(force=True)
        client.close()
