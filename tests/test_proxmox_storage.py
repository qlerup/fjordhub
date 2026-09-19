import os
import unittest
from unittest.mock import Mock, patch

from services.proxmox_storage import ProxmoxStorage
from services.storage_mount import volume_commands
from services.app_storage import AppStorage


class ProxmoxStorageTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'PROXMOX_NODE':'pve', 'PROXMOX_VMID':'1000', 'PROXMOX_TOKEN_ID':'hub@pve!monitor'})
        self.env.start(); self.addCleanup(self.env.stop)
        self.service = ProxmoxStorage()
        self.rows = [dict(storage='Storage-pool1', type='dir', content='rootdir,images', active=1, avail=500*1024**3),
                     dict(storage='local-lvm', type='lvmthin', content='rootdir,images', active=1, avail=150*1024**3),
                     dict(storage='local', type='dir', content='iso', active=1)]
        self.config = {'rootfs':'local-lvm:vm-1000-disk-0,size=200G'}
        self.service.get = Mock(side_effect=lambda path: self.rows if path.endswith('/storage') else self.config if path.endswith('/config') else {'path':'/mnt/pve/Storage-pool1'})

    def test_inventory_includes_unattached_pools_and_excludes_iso_only(self):
        data = self.service.inventory()
        self.assertEqual([s['id'] for s in data['storages']], ['Storage-pool1','local-lvm'])
        self.assertFalse(data['storages'][0]['system_pool'])
        self.assertTrue(data['storages'][1]['system_pool'])

    def test_empty_inventory_provides_read_only_scoped_access_commands(self):
        self.rows.clear()
        data = self.service.inventory()
        self.assertTrue(data['needs_access'])
        self.assertIn('/storage --users hub@pve --roles PVEAuditor', data['access_commands'])
        self.assertIn("--tokens 'hub@pve!monitor'", data['access_commands'])
        self.assertNotIn('pct ', data['access_commands'])

    def test_directory_path_is_derived_and_existing_mount_reused(self):
        plan = self.service.selection('Storage-pool1','films','')
        self.assertEqual(plan['destination'], '/mnt/fjordhub/Storage-pool1/films')
        self.assertFalse(plan['configured'])
        self.config['mp0'] = '/mnt/pve/Storage-pool1/fjordhub,mp=/mnt/library'
        self.assertEqual(self.service.selection('Storage-pool1','films','')['destination'], '/mnt/library/films')

    def test_invalid_folder_or_unavailable_storage_rejected(self):
        for folder in ['../films','/films','a/b','..','a;b','a\nb']:
            with self.subTest(folder=folder), self.assertRaises(ValueError):
                self.service.selection('Storage-pool1',folder,'')
        self.rows[0]['active'] = 0
        with self.assertRaises(ValueError): self.service.selection('Storage-pool1','films','')

    def test_new_block_volume_requires_size_and_checks_capacity(self):
        for size in ['',0,-1,True,151,'1;exit']:
            with self.subTest(size=size), self.assertRaises(ValueError):
                self.service.selection('local-lvm','films',size)
        self.assertEqual(self.service.selection('local-lvm','films',100)['size_gib'],100)

    def test_existing_block_mount_does_not_require_new_capacity(self):
        self.config['mp1'] = 'local-lvm:vm-1000-disk-1,mp=/mnt/data,size=100G,backup=1'
        self.rows[1]['avail'] = 0
        plan = self.service.selection('local-lvm','films','')
        self.assertTrue(plan['configured'])
        self.assertEqual(plan['destination'],'/mnt/data/films')

    def test_unprivileged_container_uses_managed_volume(self):
        self.config['unprivileged'] = 1
        self.assertTrue(self.service.selection('Storage-pool1','films',100)['needs_size'])

    def test_parent_mount_is_not_enough(self):
        service = AppStorage(Mock(),Mock())
        service.proxmox = self.service
        self.config['mp0'] = '/mnt/pve/Storage-pool1/fjordhub,mp=/mnt/fjordhub/Storage-pool1'
        service.folders = Mock(return_value={'ready':True,'mount_target':'/mnt'})
        self.assertFalse(service.storage_plan('Storage-pool1','films','')['ready'])
        service.folders.return_value['mount_target'] = '/mnt/fjordhub/Storage-pool1'
        self.assertTrue(service.storage_plan('Storage-pool1','films','')['ready'])

    def test_volume_commands_preserve_existing_mount_options(self):
        script = volume_commands('1000','local-lvm','/mnt/fjordhub/local-lvm',100)
        self.assertIn('source="$storage_id:100"',script)
        self.assertIn('if [ "$reuse" = 0 ]; then pct set',script)
        self.assertNotIn('mkdir -p',script)
        self.assertIn('pct reboot',script)
