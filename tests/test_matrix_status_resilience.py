"""A broken Matrix runtime must never break the FjordHub integrations menu."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import app as fjordhub

from services.auth import AuthService
from services.install_state import InstallState
from services.matrix_hub import MatrixHub, managed_docker


def test_packages_page_does_not_call_matrix_status():
    with TemporaryDirectory() as temp:
        auth = AuthService(Path(temp) / "hub.db")
        uid = auth.create_user("matrix-regression-admin", "password", role="admin")
        with patch.object(fjordhub, "_auth", auth), patch.object(
            fjordhub, "_install_state", InstallState(Path(temp))
        ), patch.object(fjordhub._package_catalog, "refresh_if_stale"), patch.object(
            fjordhub, "_get_package_defs", return_value=[]
        ), patch.object(fjordhub._matrix_hub, "status", side_effect=RuntimeError("Docker API down")):
            client = fjordhub.app.test_client()
            with client.session_transaction() as session:
                session["_user_id"] = auth.get_by_id(uid).get_id()
                session["_fresh"] = True
            response = client.get("/packages")
            assert response.status_code == 200
            assert "Matrix / Element X" in response.get_data(as_text=True)


def test_uninstalled_matrix_status_does_not_access_docker():
    with TemporaryDirectory() as temp, patch(
        "services.matrix_hub.docker.from_env",
        side_effect=RuntimeError("Should never connect for uninstalled Matrix")
    ) as connect:
        result = MatrixHub(Path(temp)).status()
        assert result["phase"] == "not_installed"
        connect.assert_not_called()


def test_installed_matrix_status_survives_failed_docker_probe():
    with TemporaryDirectory() as temp:
        hub = MatrixHub(Path(temp))
        hub._save_state(domain="matrix.example.dk", phase="ready")
        with patch("services.matrix_hub.docker.from_env",
                   side_effect=RuntimeError("Docker unavailable")):
            result = hub.status()
        assert result["phase"] == "ready"
        assert result["server"] == "unavailable"
        assert result["bot"] == "unavailable"


def test_docker_adapter_explicitly_closes_plain_client():
    class PlainDocker:
        closed = False

        def close(self):
            self.closed = True

    docker_client = PlainDocker()
    with patch("services.matrix_hub.docker.from_env", return_value=docker_client):
        with managed_docker(timeout=5) as client:
            assert client is docker_client
        assert docker_client.closed
