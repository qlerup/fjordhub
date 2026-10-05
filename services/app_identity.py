"""Canonical app identity and aliases for installations made before a rename."""


def canonical_app_id(app_id: str) -> str:
    return 'fjord3d' if app_id == 'fjordshare' else app_id
