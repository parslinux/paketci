"""PEP 517 uyumlu, sıfır bağımlılıklı saf Python paket derleme arka ucu (build-backend).

Kullanım (pyproject.toml):
    [build-system]
    requires = ["paketci"]
    build-backend = "paketci.build_backend"
"""

from __future__ import annotations

import base64
import hashlib
import os
import tarfile
import zipfile
from pathlib import Path
from typing import Any, Optional

try:
    import tomllib
except ImportError:
    import tomlkit as tomllib  # type: ignore


def _get_project_metadata(project_dir: Path) -> dict[str, Any]:
    pyproject_file = project_dir / "pyproject.toml"
    if not pyproject_file.is_file():
        raise FileNotFoundError(f"pyproject.toml bulunamadı: {pyproject_file}")

    with open(pyproject_file, "rb") as f:
        data = tomllib.load(f)

    project = data.get("project", {})
    if not project.get("name"):
        raise ValueError("pyproject.toml içinde [project.name] tanımlı olmalıdır.")
    if not project.get("version"):
        raise ValueError("pyproject.toml içinde [project.version] tanımlı olmalıdır.")

    return data


def _generate_metadata_content(data: dict[str, Any], project_dir: Path) -> str:
    project = data.get("project", {})
    name = project["name"]
    version = project["version"]

    lines = [
        "Metadata-Version: 2.1",
        f"Name: {name}",
        f"Version: {version}",
    ]

    summary = project.get("description")
    if summary:
        lines.append(f"Summary: {summary}")

    requires_python = project.get("requires-python")
    if requires_python:
        lines.append(f"Requires-Python: {requires_python}")

    license_field = project.get("license")
    if isinstance(license_field, dict) and "text" in license_field:
        lines.append(f"License: {license_field['text']}")
    elif isinstance(license_field, str):
        lines.append(f"License: {license_field}")

    # Dependencies
    for dep in project.get("dependencies", []):
        lines.append(f"Requires-Dist: {dep}")

    # Optional dependencies
    for group, group_deps in project.get("optional-dependencies", {}).items():
        lines.append(f"Provides-Extra: {group}")
        for dep in group_deps:
            lines.append(f'Requires-Dist: {dep}; extra == "{group}"')

    # Readme
    readme_file = project.get("readme")
    description_text = ""
    if readme_file:
        rf_path = project_dir / readme_file
        if rf_path.is_file():
            description_text = rf_path.read_text(encoding="utf-8")
            if readme_file.endswith(".md"):
                lines.append("Description-Content-Type: text/markdown")
            elif readme_file.endswith(".rst"):
                lines.append("Description-Content-Type: text/x-rst")

    header = "\n".join(lines)
    if description_text:
        return f"{header}\n\n{description_text}\n"
    return header + "\n"


def _generate_entry_points(data: dict[str, Any]) -> str:
    scripts = data.get("project", {}).get("scripts", {})
    if not scripts:
        return ""

    lines = ["[console_scripts]"]
    for name, target in scripts.items():
        lines.append(f"{name} = {target}")
    return "\n".join(lines) + "\n"


def _calc_record_hash(content: bytes) -> str:
    digest = hashlib.sha256(content).digest()
    b64 = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return f"sha256={b64}"


# ─────────────────────────────────────────────────────────────────────────────
# PEP 517 Kancaları (Hooks)
# ─────────────────────────────────────────────────────────────────────────────

def get_requires_for_build_wheel(config_settings: Optional[dict[str, Any]] = None) -> list[str]:
    return []


def get_requires_for_build_sdist(config_settings: Optional[dict[str, Any]] = None) -> list[str]:
    return []


def build_wheel(
    wheel_directory: str,
    config_settings: Optional[dict[str, Any]] = None,
    metadata_directory: Optional[str] = None,
) -> str:
    """Saf Python wheel (.whl) arşivi üretir."""
    cwd = Path.cwd()
    data = _get_project_metadata(cwd)
    name = data["project"]["name"].replace("-", "_")
    version = data["project"]["version"]
    wheel_filename = f"{name}-{version}-py3-none-any.whl"
    wheel_path = Path(wheel_directory) / wheel_filename

    dist_info_dir = f"{name}-{version}.dist-info"
    records: list[str] = []

    with zipfile.ZipFile(wheel_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # 1. Kaynak dosyalarını ekle (src/ veya paket klasörü)
        src_dir = cwd / "src"
        search_root = src_dir if src_dir.is_dir() else cwd

        for root, dirs, files in os.walk(search_root):
            # Gizli dizinleri ve derleme çıktılarını yoksay
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("__pycache__", "build", "dist", "tests")]
            for file in files:
                if file.endswith((".py", ".pyi", ".typed")) or not file.startswith("."):
                    file_path = Path(root) / file
                    arcname = str(file_path.relative_to(search_root))
                    content = file_path.read_bytes()
                    zf.writestr(arcname, content)
                    rec_hash = _calc_record_hash(content)
                    records.append(f"{arcname},{rec_hash},{len(content)}")

        # 2. METADATA
        meta_content = _generate_metadata_content(data, cwd).encode("utf-8")
        meta_arcname = f"{dist_info_dir}/METADATA"
        zf.writestr(meta_arcname, meta_content)
        records.append(f"{meta_arcname},{_calc_record_hash(meta_content)},{len(meta_content)}")

        # 3. WHEEL
        wheel_meta = (
            "Wheel-Version: 1.0\n"
            "Generator: paketci-build-backend\n"
            "Root-Is-Purelib: true\n"
            "Tag: py3-none-any\n"
        ).encode("utf-8")
        wheel_arcname = f"{dist_info_dir}/WHEEL"
        zf.writestr(wheel_arcname, wheel_meta)
        records.append(f"{wheel_arcname},{_calc_record_hash(wheel_meta)},{len(wheel_meta)}")

        # 4. entry_points.txt
        ep_content = _generate_entry_points(data).encode("utf-8")
        if ep_content:
            ep_arcname = f"{dist_info_dir}/entry_points.txt"
            zf.writestr(ep_arcname, ep_content)
            records.append(f"{ep_arcname},{_calc_record_hash(ep_content)},{len(ep_content)}")

        # 5. RECORD
        record_arcname = f"{dist_info_dir}/RECORD"
        records.append(f"{record_arcname},,")
        record_content = "\n".join(records) + "\n"
        zf.writestr(record_arcname, record_content.encode("utf-8"))

    return wheel_filename


def build_sdist(
    sdist_directory: str,
    config_settings: Optional[dict[str, Any]] = None,
) -> str:
    """Standart kaynak dağıtımı (.tar.gz) arşivi üretir."""
    cwd = Path.cwd()
    data = _get_project_metadata(cwd)
    name = data["project"]["name"]
    version = data["project"]["version"]
    base_name = f"{name}-{version}"
    sdist_filename = f"{base_name}.tar.gz"
    sdist_path = Path(sdist_directory) / sdist_filename

    meta_content = _generate_metadata_content(data, cwd).encode("utf-8")

    with tarfile.open(sdist_path, "w:gz") as tar:
        # PKG-INFO ekle
        ti = tarfile.TarInfo(name=f"{base_name}/PKG-INFO")
        ti.size = len(meta_content)
        import io
        tar.addfile(ti, io.BytesIO(meta_content))

        # pyproject.toml ekle
        pyproj = cwd / "pyproject.toml"
        tar.add(str(pyproj), arcname=f"{base_name}/pyproject.toml")

        # README ekle
        readme = data.get("project", {}).get("readme")
        if readme and (cwd / readme).is_file():
            tar.add(str(cwd / readme), arcname=f"{base_name}/{readme}")
        elif (cwd / "README.md").is_file():
            tar.add(str(cwd / "README.md"), arcname=f"{base_name}/README.md")

        # LICENSE ekle
        if (cwd / "LICENSE").is_file():
            tar.add(str(cwd / "LICENSE"), arcname=f"{base_name}/LICENSE")

        # src dizinini ekle
        src_dir = cwd / "src"
        if src_dir.is_dir():
            tar.add(str(src_dir), arcname=f"{base_name}/src", filter=lambda ti: None if any(p in ti.name for p in ("__pycache__", ".pytest_cache", ".pyc")) else ti)

    return sdist_filename
