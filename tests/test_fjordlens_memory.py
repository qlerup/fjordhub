import tempfile
from pathlib import Path
import unittest

from services.compose_env import enable_fjordlens_memory_guard, FJORDLENS_MEMORY_DEFAULTS


class FjordLensMemoryTests(unittest.TestCase):
    def test_hub_migration_preserves_settings_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / '.env'
            original = 'APP_PORT=9081\nFJORDLENS_MEMORY_GUARD=0\n'
            path.write_text(original, encoding='utf-8')
            enable_fjordlens_memory_guard(root)
            first = path.read_text(encoding='utf-8')
            self.assertTrue(first.startswith(original))
            enable_fjordlens_memory_guard(root)
            self.assertEqual(path.read_text(encoding='utf-8'), first)
            self.assertEqual(first.count('FJORDLENS_MEMORY_GUARD='), 1)

    def test_hub_enables_guard_on_existing_install(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            enable_fjordlens_memory_guard(root)
            actual = dict(line.split('=', 1) for line in (root/'.env').read_text().splitlines() if line)
            self.assertEqual(actual, FJORDLENS_MEMORY_DEFAULTS)
