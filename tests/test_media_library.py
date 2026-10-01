import unittest
from unittest.mock import Mock, patch

from services.media_library import MediaLibrary, mount_commands


class MediaLibraryTests(unittest.TestCase):
    def test_mount_guide_reuses_existing_files_and_chooses_free_slot(self):
        commands = mount_commands('1000', 'Storage-pool1', '/mnt/pve/Storage-pool1')
        self.assertIn('ro=1', commands)
        self.assertIn('pct set "$ctid" "-$slot"', commands)
        self.assertNotIn('mkdir', commands)
        self.assertNotIn('mkfs', commands)
        self.assertNotIn('rsync', commands)
        self.assertEqual(mount_commands('1000', 'pool', '/mnt/../etc'), '')
        self.assertEqual(mount_commands('1000', 'pool', '/mnt/$(id)'), '')
        self.assertEqual(mount_commands('1000', 'pool', '/etc'), '')

    def setUp(self):
        self.responses = {
            '/nodes/pve/storage': [
                {'storage': 'Storage-pool1', 'type': 'dir', 'active': 1},
                {'storage': 'local', 'type': 'dir', 'active': 1, 'content': 'iso'},
                {'storage': 'local-lvm', 'type': 'lvmthin', 'active': 1},
            ],
            '/storage': [{'storage': 'Storage-pool1', 'path': '/mnt/pve/Storage-pool1'},
                         {'storage': 'local', 'path': '/var/lib/vz'}],
            '/nodes/pve/lxc/1000/config': {
                'mp0': '/mnt/pve/Storage-pool1/Film,mp=/mnt/Film,ro=1',
                'mp1': 'local-lvm:vm-1000-disk-1,mp=/mnt/Serier',
                'mp2': '/dev/sde1,mp=/mnt/Disk',
            },
            '/nodes/pve/disks/list?include-partitions=1&skipsmart=1': [
                {'devpath': '/dev/sde', 'size': 1500000000000, 'used': 'partitions'},
                {'devpath': '/dev/sde1', 'parent': '/dev/sde', 'used': 'ext4', 'mounted': 1},
                {'devpath': '/dev/sdc', 'used': '', 'mounted': 0},
            ],
            '/nodes/pve/disks/directory': [],
        }
        self.pve = Mock(node_path='/nodes/pve', ctid='1000')
        self.pve.get.side_effect = self.responses.__getitem__

    def test_lists_all_pools_and_partitions_without_allocating(self):
        result = MediaLibrary(self.pve).inventory()
        self.assertEqual([s['id'] for s in result['storages']], ['Storage-pool1', 'local', 'local-lvm'])
        self.assertEqual(result['storages'][0]['paths'], ['/mnt/Film'])
        self.assertEqual(result['storages'][1]['paths'], [])
        self.assertEqual(result['storages'][2]['paths'], ['/mnt/Serier'])
        self.assertEqual(result['disks'][1]['paths'], ['/mnt/Disk'])
        self.assertEqual(result['disks'][2]['paths'], [])
        self.assertEqual(result['errors'], [])
        self.assertTrue(all(call[0] == 'get' for call in self.pve.method_calls))

    def test_offline_and_unmounted_virtual_pools_are_not_selectable(self):
        self.responses['/nodes/pve/storage'][0]['active'] = 0
        self.responses['/nodes/pve/lxc/1000/config'].pop('mp1')
        result = MediaLibrary(self.pve).inventory()
        self.assertEqual(result['storages'][0]['paths'], [])
        self.assertEqual(result['storages'][2]['paths'], [])
        self.assertIn('virtuelle diske', result['storages'][2]['reason'])

    def test_partial_api_failure_keeps_other_inventory_and_reports_error(self):
        def read(path):
            if '/disks/' in path:
                raise ValueError('denied')
            return self.responses[path]
        self.pve.get.side_effect = read
        result = MediaLibrary(self.pve).inventory()
        self.assertEqual(len(result['storages']), 3)
        self.assertEqual(result['disks'], [])
        self.assertEqual(len(result['errors']), 2)

    def test_parent_mount_maps_subdirectory_without_exposing_siblings(self):
        self.responses['/nodes/pve/lxc/1000/config'] = {'mp0': '/mnt/pve,mp=/mnt/shared'}
        result = MediaLibrary(self.pve).inventory()
        self.assertEqual(result['storages'][0]['paths'], ['/mnt/shared/Storage-pool1'])

    def test_write_guides_only_for_existing_directory_mounts(self):
        result = MediaLibrary(self.pve).inventory()
        self.assertEqual(result['mounts'][0]['write_guide']['source'], '/mnt/pve/Storage-pool1/Film')
        self.assertIn('mp0', result['mounts'][0]['write_guide']['commands'].splitlines()[0])
        self.assertTrue(result['mounts'][0]['read_only'])
        self.assertIsNone(result['mounts'][1]['write_guide'])
        self.assertIsNone(result['mounts'][2]['write_guide'])
        self.assertTrue(all(call[0] == 'get' for call in self.pve.method_calls))

    def test_mergerfs_preview_rejects_arbitrary_host_paths(self):
        library = MediaLibrary(self.pve)
        for value in ['/etc', '/mnt', '/mnt/../etc', '/mnt/$(reboot)']:
            with self.assertRaises(ValueError):
                library.mergerfs_connection(value, {'mounts': []})
        result = library.mergerfs_connection('/mnt/mediahub-storage', {'mounts': []})
        self.assertIn('fuse.mergerfs', result['commands'])
        self.assertIn('ro=1', result['commands'])


class MediaLibraryEndpointTests(unittest.TestCase):
    def test_scoped_app_key_and_active_app_admin_are_required(self):
        import app as hub
        auth = Mock()
        auth.verify_hub_key.side_effect = lambda app_id, key: key == 'test-key'
        auth.list_app_users.return_value = [{'id': 7, 'role': 'admin', 'must_change_password': False}]
        with patch.object(hub, '_auth', auth), patch.object(hub.MediaLibrary, 'inventory', return_value={'storages': []}) as inventory:
            client = hub.app.test_client()
            url = '/api/hub/apps/fjordflix/library'
            params = {'app_id': 'fjordflix', 'user_id': '7'}
            self.assertEqual(client.get(url, query_string=params).status_code, 400)
            headers = {'X-Hub-Key': 'test-key'}
            self.assertEqual(client.get(url, query_string={**params, 'app_id': 'fjordlens'}, headers=headers).status_code, 403)
            self.assertEqual(client.get(url, query_string={**params, 'user_id': '8'}, headers=headers).status_code, 403)
            self.assertEqual(client.get(url, query_string=params, headers=headers).status_code, 200)
            inventory.assert_called_once()
            auth.list_app_users.return_value[0]['must_change_password'] = True
            self.assertEqual(client.get(url, query_string=params, headers=headers).status_code, 403)
