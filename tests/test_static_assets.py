"""CSS and JavaScript must change URLs together after an application update."""
import os

import pytest
from conftest import hub


@pytest.mark.parametrize('name', ['cloudflare.js', 'cloudflare.css', 'nested/new-feature.js'])
def test_every_asset_changes_version_even_when_timestamp_is_older(tmp_path, monkeypatch, name):
    dominant = tmp_path / 'styles.css'
    dominant.write_text('existing styles')
    os.utime(dominant, ns=(1000, 1000))
    changed = tmp_path / name
    changed.parent.mkdir(parents=True, exist_ok=True)
    changed.write_text('old content')
    os.utime(changed, ns=(100, 100))
    monkeypatch.setattr(hub.app, 'static_folder', str(tmp_path))
    before = hub._static_version()

    changed.write_text('new content')
    os.utime(changed, ns=(100, 100))
    after = hub._static_version()

    assert before.isdigit() and after.isdigit() and before != after
    assert hub._static_version() == after


def test_adding_and_removing_asset_invalidates_version(tmp_path, monkeypatch):
    (tmp_path / 'styles.css').write_text('styles')
    monkeypatch.setattr(hub.app, 'static_folder', str(tmp_path))
    before = hub._static_version()
    added = tmp_path / 'cloudflare.css'
    added.write_text('new style')
    assert hub._static_version() != before
    added.unlink()
    assert hub._static_version() == before
