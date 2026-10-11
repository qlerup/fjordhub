"""Remove an app's Compose runtime without deleting persistent files or volumes."""
import json
import re
import subprocess
from pathlib import Path

from services.compose_env import build_compose_env


def remove_runtime(app_def, directory, *, required_service=None, protected_containers=()):
    if not directory or not Path(directory).is_dir():
        raise RuntimeError('Appens Compose-mappe mangler. Registreringen bevares til reparation.')

    def run(args, timeout=30):
        result = subprocess.run(args, cwd=str(directory), env=build_compose_env(),
                                capture_output=True, text=True, timeout=timeout)
        if result.returncode:
            # Compose output can contain interpolated settings; do not return it.
            raise RuntimeError('Docker-oprydningen fejlede. Data og registrering er bevaret. Kontrollér Docker og prøv igen.')
        return result.stdout.strip()

    config = json.loads(run(['docker', 'compose', 'config', '--format', 'json']))
    project = config.get('name')
    if not isinstance(project, str) or not re.fullmatch(r'[a-z0-9][a-z0-9_-]*', project):
        raise RuntimeError('Appens Docker Compose-projekt kunne ikke identificeres.')
    container = app_def.get('container_name')
    legacy = app_def.get('legacy_container_names', [])
    if not isinstance(legacy,list):
        raise RuntimeError('Ugyldige tidligere containernavne i app-definitionen.')
    names = [n for n in [container, *legacy] if n]
    if any(not isinstance(n,str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]*',n) for n in names):
        raise RuntimeError('Ugyldigt containernavn i app-definitionen.')
    names = list(dict.fromkeys(names))
    if names and not any(service.get('container_name') in names for service in config.get('services',{}).values()):
        raise RuntimeError('Compose-mappen tilhører ikke den forventede app. Intet er fjernet.')
    if required_service and config.get('services', {}).get(required_service, {}).get('container_name') != container:
        raise RuntimeError('Compose-mappen tilhører ikke den forventede installation. Intet er fjernet.')
    for container in names:
        existing = run(['docker', 'ps', '-a', '--filter', f'name=^/{container}$',
                        '--format', '{{.ID}} {{.Label "com.docker.compose.project"}}'])
        for line in existing.splitlines():
            parts = line.split()
            if len(parts) != 2 or parts[1] != project:
                raise RuntimeError('Containernavnet tilhører en anden eller ukendt installation. Intet slettes automatisk; kontrollér dens datamapper og Compose-projekt.')

    # No --volumes, --rmi or filesystem deletion. Data can be located inside
    # the checkout as well as in external bind mounts or Docker volumes.
    if protected_containers:
        members=set(run(['docker','ps','-a','--filter',f'label=com.docker.compose.project={project}',
                         '--format','{{.Names}}']).splitlines())
        if members.intersection(set(protected_containers)-set(names)):
            raise RuntimeError('Compose-projektet deles med en anden app. Intet er fjernet; ret projektopsætningen før afinstallation.')
    run(['docker', 'compose', 'down', '--remove-orphans', '--timeout', '20'], timeout=90)
    remaining = run(['docker', 'ps', '-a', '--filter', f'label=com.docker.compose.project={project}',
                     '--format', '{{.ID}}'])
    if remaining:
        raise RuntimeError('Der findes stadig app-containere. Data og registrering er bevaret; prøv igen.')
    for container in names:
        if run(['docker', 'ps', '-a', '--filter', f'name=^/{container}$', '--format', '{{.ID}}']):
            raise RuntimeError('Appens container findes stadig efter oprydningen. Registreringen bevares; prøv igen.')
    if run(['docker','network','ls','--filter',f'label=com.docker.compose.project={project}','--format','{{.ID}}']):
        raise RuntimeError('Appens Docker-netværk er stadig i brug. Registreringen bevares; kontrollér tilsluttede containere og prøv igen.')
