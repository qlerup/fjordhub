"""Deleting a Hub identity must revoke membership just like removing app access."""
import tempfile
import unittest
from pathlib import Path

from services.auth import AuthService


class DeletedUserMembershipTests(unittest.TestCase):
    def test_deleted_user_disappears_from_every_app_membership(self):
        apps = ('fjordlens', 'fjordflix', 'fjord3d', 'fjordparcel',
                'fjordbudget', 'fjordvpn', 'orbitmap', 'urban-explorer')
        with tempfile.TemporaryDirectory() as directory:
            auth = AuthService(Path(directory)/'hub.db')
            user = auth.create_user('deleted-user', 'test-password')
            for app in apps:
                auth.set_user_app_access(user, app)
                self.assertIn(user, [item['id'] for item in auth.list_app_users(app)])
            auth.delete_user(user)
            for app in apps:
                self.assertNotIn(user, [item['id'] for item in auth.list_app_users(app)])
