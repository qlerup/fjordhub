import json
from pathlib import Path
from unittest.mock import Mock
import pytest
from services.app_storage import fields, seed_worker


def test_manifest_uses_standard_storage_picker():
    app=json.loads((Path(__file__).parents[1]/'app_registry/fjordseed.json').read_text(encoding='utf-8'))
    assert {f['key'] for f in fields(app)}=={'DATA_DIR','DOWNLOADS_DIR'}


def test_managed_worker_recognition_rejects_foreign_or_stale_mounts():
    config={'services':{'app':{'volumes':[{'target':'/data','source':'/opt/seed'}, {'target':'/downloads','source':'/mnt/downloads'}]}}}
    c=Mock(labels={'com.docker.compose.service':'qbittorrent','dk.fjordseed.owner':'a'*32},attrs={'Mounts':[
        {'Type':'bind','Destination':'/config','Source':'/opt/seed/qbit'},
        {'Type':'bind','Destination':'/downloads','Source':'/mnt/downloads'}]})
    c.name='fjordseed-'+'a'*32+'-qbittorrent'
    assert seed_worker('fjordseed',c,config)
    assert not seed_worker('other',c,config)
    c.attrs['Mounts'][1]['Source']='/old/downloads'
    with pytest.raises(ValueError):seed_worker('fjordseed',c,config)
