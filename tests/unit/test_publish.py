"""publish operasyonu birim testleri."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from paketci.core import operations
from paketci.core.exceptions import PaketciError


def test_publish_no_dist_dir(tmp_path):
    with pytest.raises(PaketciError, match="Dağıtım dizini bulunamadı"):
        operations.publish_package(dist_dir=tmp_path / "nonexistent", token="dummy-token")


def test_publish_empty_dist(tmp_path):
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    with pytest.raises(PaketciError, match="Yüklenecek paket bulunamadı"):
        operations.publish_package(dist_dir=dist_dir, token="dummy-token")


def test_publish_no_token(tmp_path, monkeypatch):
    monkeypatch.delenv("PYPI_API_TOKEN", raising=False)
    monkeypatch.delenv("TWINE_PASSWORD", raising=False)
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    (dist_dir / "mypkg-0.1.0-py3-none-any.whl").write_bytes(b"dummy-wheel")

    with pytest.raises(PaketciError, match="PyPI API Token bulunamadı"):
        operations.publish_package(dist_dir=dist_dir, token=None)


def test_publish_mock_upload_success(tmp_path):
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    whl = dist_dir / "mypkg-0.1.0-py3-none-any.whl"
    whl.write_bytes(b"dummy-wheel-content")

    mock_resp = MagicMock()
    mock_resp.status_code = 200

    with patch("httpx.Client.post", return_value=mock_resp) as mock_post:
        uploaded = operations.publish_package(
            dist_dir=dist_dir,
            repository_url="https://test.pypi.org/legacy/",
            token="test-token",
        )
        assert len(uploaded) == 1
        assert uploaded[0] == "mypkg-0.1.0-py3-none-any.whl"
        assert mock_post.called
