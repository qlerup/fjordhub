from unittest.mock import Mock, patch
import app as hub


def test_installed_gpu_page_is_admin_only():
    with hub.app.test_request_context('/apps/fjordflix/gpu'), patch.object(hub, 'current_user', Mock(is_admin=False)):
        assert hub.app_gpu_setup.__wrapped__('fjordflix')[1] == 403


def test_gpu_page_reuses_helper_without_install_controls():
    definition = {'id':'fjordflix','name':'FjordFlix','description':'Film','gpu_service':'app','gpu_video':True}
    with hub.app.test_request_context('/apps/fjordflix/gpu'), \
         patch.object(hub, 'current_user', Mock(is_admin=True)), \
         patch.object(hub, '_get_app', return_value=definition), \
         patch.object(hub, '_nfs_runtime_info', return_value={'vmid':'101'}):
        html = hub.app_gpu_setup.__wrapped__('fjordflix')
    assert 'id="gpu-modal"' in html
    assert 'id="gpu-sync-script"' in html
    assert 'id="gpu-auto-container-btn"' in html
    assert 'id="btn-install"' not in html
    assert 'id="gpu-use-btn"' not in html


def test_non_gpu_app_has_no_setup_page():
    with hub.app.test_request_context('/apps/other/gpu'), \
         patch.object(hub, 'current_user', Mock(is_admin=True)), \
         patch.object(hub, '_get_app', return_value={'id':'other'}):
        assert hub.app_gpu_setup.__wrapped__('other')[1] == 404
