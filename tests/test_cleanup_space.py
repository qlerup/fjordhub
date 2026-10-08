import subprocess
import unittest
from unittest.mock import patch

import app as hub
import test_access_tokens as fixtures
from services.cleanup_space import reclaimed_bytes


class CleanupSpaceTests(unittest.TestCase):
    def test_docker_units_and_buildkit_summary(self):
        for text, expected in [('Total reclaimed space: 8.192kB', 8192),
                               ('Total reclaimed space: 106.8MB', 106800000),
                               ('Total:\t1.5GB', 1500000000),
                               ('Total: 2TB', 2000000000000),
                               ('Total: 1MiB', 1048576), ('Total: 0B', 0),
                               ('Deleted Networks:\nabc', 0)]:
            with self.subTest(text=text):
                self.assertEqual(reclaimed_bytes(text), expected)


class CleanupTotalRouteTests(unittest.TestCase):
    setUp = fixtures.AccessTokenTests.setUp
    tearDown = fixtures.AccessTokenTests.tearDown
    login = fixtures.AccessTokenTests.login

    def test_sum_prunes_excludes_disk_usage_and_survives_partial_failure(self):
        self.login(self.admin)
        for failed in (False, True):
            def run(command, **kwargs):
                output = {'system': 'Total: 9TB', 'builder': 'Total: 1.5GB',
                          'image': 'Total reclaimed space: 106.8MB',
                          'container': 'Total reclaimed space: 8.192kB',
                          'network': ''}[command[1]]
                return subprocess.CompletedProcess(command, int(failed and command[1] == 'network'), output, '')
            with patch.object(hub.subprocess, 'run', side_effect=run):
                response = self.client.post('/api/docker-cleanup')
            self.assertEqual(response.status_code, 500 if failed else 200)
            self.assertEqual(response.json['reclaimed_bytes'], 1606808192)
