"""Core operasyonlar — CLI komutlarının çağırdığı pipeline fonksiyonları.

Bağımlılık yönü:
  cli → core.operations → {config, resolver, index, fetcher, installer, lockfile} → utils
"""

from __future__ import annotations

import asyncio
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from paketci import __version__
from paketci.config.loader import ConfigLoader
from paketci.config.models import Dependency
from paketci.core.exceptions import FrozenLockfileError, LockfileError
from paketci.fetcher.downloader import Downloader
from paketci.index.cache import MetadataCache
from paketci.index.client import PyPIClient
from paketci.installer.env import TargetEnv, detect_env
from paketci.installer.sdist import build_sdist_to_wheel
from paketci.installer.wheel import install_wheel
from paketci.lockfile import io as lockfile_io
from paketci.lockfile.models import LockedFile, LockedGraph, LockedPackage
from paketci.resolver.solver import solve
from paketci.utils.logging import get_logger
from paketci.utils.paths import find_project_root

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Yardımcılar
# ─────────────────────────────────────────────────────────────────────────────

def _make_client_and_cache(index_url: str) -> tuple[PyPIClient, MetadataCache]:
    from urllib.parse import urlparse
    parsed = urlparse(index_url)
    if "pypi.org" in (parsed.netloc or ""):
        base = "https://pypi.org/pypi"
    else:
        base = index_url.rstrip("/")
        if base.endswith("/simple"):
            base = base[:-7]
    client = PyPIClient(base_url=base)
    cache = MetadataCache()
    return client, cache


def _load_config_and_lock(project_root: Path) -> tuple[ConfigLoader, Optional[LockedGraph]]:
    loader = ConfigLoader(project_root)
    config = loader.load()
    lock_path = project_root / config.lockfile_path
    graph: Optional[LockedGraph] = None
    if lock_path.is_file():
        try:
            graph = lockfile_io.read(lock_path)
        except LockfileError as exc:
            logger.warning("Lockfile okunamadı: %s", exc)
    return loader, graph


def _build_locked_graph(
    resolve_result,
    client: PyPIClient,
    cache: MetadataCache,
    requires_python: str,
) -> LockedGraph:
    """Çözümleme sonucundan LockedGraph oluşturur."""
    packages: dict[str, LockedPackage] = {}

    for norm_name, (name, version) in resolve_result.mapping.items():
        meta = cache.get(name, version)
        if meta is None:
            meta = client.get_metadata(name, version)
            cache.set(meta)

        best = meta.best_wheel() or meta.best_sdist()
        files = (
            [LockedFile(filename=best.filename, url=best.url, sha256=best.sha256)]
            if best else []
        )
        packages[norm_name] = LockedPackage(
            name=name,
            version=version,
            files=files,
            dependencies=meta.requires_dist or [],
        )

    return LockedGraph(
        lockfile_version=1,
        generated_by=f"paketci {__version__}",
        python=requires_python,
        packages=packages,
    )


def _install_packages_batch(
    packages: list[LockedPackage],
    downloader: Downloader,
    env: TargetEnv,
    force: bool = False,
) -> None:
    """
    Paketleri paralel indirip kurar. Zaten kurulu olan sürümleri atlar (idempotent).
    """
    to_install: list[LockedPackage] = []
    for pkg in packages:
        if not force and env.is_installed(pkg.name, pkg.version):
            logger.info("  ✔ %s==%s zaten kurulu (atlandı)", pkg.name, pkg.version)
            continue
        if not pkg.files:
            logger.warning("Kurulacak dosya yok: %s", pkg.name)
            continue
        to_install.append(pkg)

    if not to_install:
        logger.info("Tüm paketler zaten güncel ve kurulu.")
        return

    logger.info("📦 %d paket indiriliyor ve kuruluyor...", len(to_install))

    all_files: list[LockedFile] = []
    for pkg in to_install:
        all_files.extend(pkg.files)

    with tempfile.TemporaryDirectory(prefix="paketci_") as tmpdir:
        tmp_path = Path(tmpdir)
        downloaded = asyncio.run(downloader.download_all(all_files, tmp_path))

        for filename, local_path in downloaded.items():
            if local_path.suffix == ".whl":
                install_wheel(local_path, env)
            else:
                # sdist → wheel → kur
                wheel = build_sdist_to_wheel(local_path, tmp_path / "build")
                install_wheel(wheel, env)


def _install_package(
    pkg: LockedPackage,
    downloader: Downloader,
    env: TargetEnv,
) -> None:
    """Tek paketi kurar."""
    _install_packages_batch([pkg], downloader, env)


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline Operasyonlar
# ─────────────────────────────────────────────────────────────────────────────

def add(
    packages: list[str],
    dev: bool = False,
    optional_group: Optional[str] = None,
    offline: bool = False,
    editable: bool = False,
    project_root: Optional[Path] = None,
) -> None:
    """
    `paketci add <paket>` akışı:
    git/yerel dizin veya PyPI paketlerini çözer, kurar ve pyproject.toml'a kaydeder.
    """
    from paketci.fetcher.vcs import is_git_url, clone_git_repo, install_editable

    root = project_root or find_project_root()
    loader = ConfigLoader(root)
    config = loader.load()
    env = detect_env()
    group = optional_group or ("dev" if dev else None)

    # 1. Yerel dizin veya Git deposu kontrolü
    standard_packages: list[str] = []

    for pkg_spec in packages:
        pkg_path = Path(pkg_spec)
        if editable or pkg_path.is_dir():
            target_path = pkg_path if pkg_path.is_dir() else root / pkg_path
            name = install_editable(target_path, env)
            dep = Dependency(name=name, constraint=f"@ file://{target_path.resolve()}")
            loader.add_dependency(dep, optional_group=group)
            logger.info("🔗 Yerel paket bağlandı (editable): %s (%s)", name, target_path)
        elif is_git_url(pkg_spec):
            cloned = clone_git_repo(pkg_spec)
            name = install_editable(cloned, env)
            dep = Dependency(name=name, constraint=f"@ {pkg_spec}")
            loader.add_dependency(dep, optional_group=group)
            logger.info("📦 Git deposu klonlandı ve bağlandı: %s (%s)", name, pkg_spec)
        else:
            standard_packages.append(pkg_spec)

    if not standard_packages:
        return

    client, cache = _make_client_and_cache(config.index_url)
    downloader = Downloader(offline=offline)

    # Mevcut bağımlılıklarla birlikte çözümle
    existing = [d.pep508() for d in config.dependencies if not d.constraint.startswith("@")]
    all_reqs = existing + standard_packages

    logger.info("🔍 Bağımlılıklar çözümleniyor...")

    with client:
        result = solve(all_reqs, client, cache)
        # Lockfile güncelle (client açıkken metadata çekebilir)
        lock_path = root / config.lockfile_path
        graph = _build_locked_graph(result, client, cache, config.requires_python)
        lockfile_io.write(graph, lock_path)
    logger.info("🔒 Lockfile güncellendi: %s", lock_path.name)

    # İlgili paketleri kur (ana paket ve bağımlılıkları - idempotent)
    _install_packages_batch(graph.all_packages(), downloader, env)

    # pyproject.toml'a yaz
    for pkg_spec in standard_packages:
        from paketci.config.loader import _parse_dep
        dep = _parse_dep(pkg_spec)
        loader.add_dependency(dep, optional_group=group)

    logger.info("✅ Tamamlandı: %s paket eklendi.", len(packages))


def remove(
    packages: list[str],
    optional_group: Optional[str] = None,
    project_root: Optional[Path] = None,
) -> None:
    """`paketci remove <paket>` — pyproject.toml'dan siler, lockfile günceller."""
    root = project_root or find_project_root()
    loader = ConfigLoader(root)
    config = loader.load()

    removed = []
    for name in packages:
        ok = loader.remove_dependency(name, optional_group=optional_group)
        if ok:
            removed.append(name)
            logger.info("  ➖ Kaldırıldı: %s", name)
        else:
            logger.warning("Bulunamadı: %s", name)

    if removed:
        # Lockfile'ı yeniden çözümle
        config = loader.load()
        remaining = [d.pep508() for d in config.dependencies]
        if remaining:
            lock(project_root=root)
        else:
            # Hiç bağımlılık kalmadıysa boş lockfile
            lock_path = root / config.lockfile_path
            lockfile_io.write(
                LockedGraph(python=config.requires_python), lock_path
            )


def lock(
    project_root: Optional[Path] = None,
    offline: bool = False,
    solver: str = "resolvelib",
) -> None:
    """`paketci lock` — pyproject.toml'dan lockfile oluşturur/günceller."""
    root = project_root or find_project_root()
    loader = ConfigLoader(root)
    config = loader.load()

    reqs = [d.pep508() for d in config.dependencies]
    if not reqs:
        logger.info("Bağımlılık yok, lockfile boş bırakıldı.")
        return

    client, cache = _make_client_and_cache(config.index_url)

    logger.info("🔍 Çözümleniyor (%s)...", solver)

    with client:
        result = solve(reqs, client, cache, solver_type=solver)
        graph = _build_locked_graph(result, client, cache, config.requires_python)

    lock_path = root / config.lockfile_path
    lockfile_io.write(graph, lock_path)
    logger.info("🔒 Lockfile oluşturuldu: %s (%d paket)", lock_path.name, len(graph.packages))


def install(
    frozen: bool = False,
    offline: bool = False,
    target: Optional[Path] = None,
    project_root: Optional[Path] = None,
) -> None:
    """`paketci install` — lockfile'dan kurar, resolver çalıştırmaz."""
    root = project_root or find_project_root()
    loader = ConfigLoader(root)
    config = loader.load()

    lock_path = root / config.lockfile_path
    graph = lockfile_io.read(lock_path)

    env = detect_env(target)
    downloader = Downloader(offline=offline)

    logger.info("📦 Lockfile paketleri kontrol ediliyor (%d paket)...", len(graph.packages))
    _install_packages_batch(graph.all_packages(), downloader, env)
    logger.info("✅ Kurulum tamamlandı.")


def sync(
    frozen: bool = False,
    offline: bool = False,
    project_root: Optional[Path] = None,
) -> None:
    """`paketci sync` — lockfile ile mevcut ortamı eşitler."""
    # Önce lock'u güncelle (frozen değilse), sonra install
    root = project_root or find_project_root()
    if not frozen:
        lock(project_root=root, offline=offline)
    install(frozen=frozen, offline=offline, project_root=root)


def update(
    packages: Optional[list[str]] = None,
    project_root: Optional[Path] = None,
) -> None:
    """`paketci update` — lockfile'ı en yeni versiyonlarla yeniler."""
    root = project_root or find_project_root()
    # Şimdilik: tüm lockfile'ı yeniden çözümle
    lock(project_root=root)
    logger.info("✅ Tüm paketler güncellendi.")


def list_packages(project_root: Optional[Path] = None) -> list[LockedPackage]:
    """`paketci list` — kurulu paket listesini döndürür."""
    root = project_root or find_project_root()
    loader = ConfigLoader(root)
    config = loader.load()
    lock_path = root / config.lockfile_path

    if not lock_path.is_file():
        return []

    graph = lockfile_io.read(lock_path)
    return sorted(graph.all_packages(), key=lambda p: p.name.lower())


def why(
    package: str,
    project_root: Optional[Path] = None,
) -> dict[str, list[str]]:
    """
    `paketci why <paket>` — paketin neden bağımlılık ağacında olduğunu açıklar.

    Returns:
        {depender_name: [req_strings]} — hangi paket bu paketi istemiş.
    """
    root = project_root or find_project_root()
    loader = ConfigLoader(root)
    config = loader.load()
    lock_path = root / config.lockfile_path

    if not lock_path.is_file():
        return {}

    graph = lockfile_io.read(lock_path)
    target = package.lower().replace("-", "_")
    dependents: dict[str, list[str]] = {}

    # Kök bağımlılıkları kontrol et
    root_deps = [d.name.lower().replace("-", "_") for d in config.dependencies]
    if target in root_deps:
        dependents["<proje>"] = [package]

    for pkg in graph.all_packages():
        for dep_str in pkg.dependencies:
            dep_name = dep_str.split(">")[0].split("<")[0].split("=")[0].split("!")[0].split("[")[0].strip()
            if dep_name.lower().replace("-", "_") == target:
                dependents.setdefault(pkg.name, []).append(dep_str)

    return dependents


def init(
    name: Optional[str] = None,
    directory: Optional[Path] = None,
    requires_python: str = ">=3.10",
    create_venv: bool = False,
) -> Path:
    """
    Yeni bir proje başlatır: pyproject.toml, README.md, .gitignore oluşturur.
    """
    target_dir = (directory or Path.cwd()).resolve()
    pyproject = target_dir / "pyproject.toml"
    if pyproject.exists():
        from paketci.core.exceptions import ConfigError
        raise ConfigError(f"Bu dizinde zaten bir pyproject.toml mevcut: {pyproject}")

    proj_name = name or target_dir.name.lower().replace(" ", "-")

    content = f"""[project]
name = "{proj_name}"
version = "0.1.0"
description = ""
readme = "README.md"
requires-python = "{requires_python}"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.paketci]
lockfile-path = "paketci.lock"
index-url = "https://pypi.org/simple"
"""
    target_dir.mkdir(parents=True, exist_ok=True)
    pyproject.write_text(content, encoding="utf-8")

    readme = target_dir / "README.md"
    if not readme.exists():
        readme.write_text(f"# {proj_name}\n\nPaketci ile oluşturuldu.\n", encoding="utf-8")

    gitignore = target_dir / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(".venv/\n__pycache__/\n*.py[cod]\ndist/\nbuild/\n", encoding="utf-8")

    if create_venv:
        venv_dir = target_dir / ".venv"
        if not venv_dir.exists():
            import venv
            logger.info("🔧 Sanal ortam (.venv) oluşturuluyor...")
            venv.create(venv_dir, with_pip=True)

    return pyproject


@dataclass
class CheckReport:
    """Proje sağlık kontrolü raporu."""
    pyproject_exists: bool = False
    lockfile_exists: bool = False
    missing_in_lock: list[str] = field(default_factory=list)
    missing_in_env: list[tuple[str, str]] = field(default_factory=list)
    installed_ok: list[tuple[str, str]] = field(default_factory=list)
    peer_warnings: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)

    @property
    def is_healthy(self) -> bool:
        return (
            self.pyproject_exists
            and self.lockfile_exists
            and not self.missing_in_lock
            and not self.missing_in_env
        )


def check(project_root: Optional[Path] = None) -> CheckReport:
    """
    Proje sağlığını kontrol eder: pyproject.toml, lockfile senkronizasyonu, venv durumu ve peer dependency'ler.
    """
    from packaging.requirements import Requirement
    from packaging.specifiers import SpecifierSet
    from packaging.utils import canonicalize_name

    root = project_root or find_project_root()
    report = CheckReport()

    pyproject_path = root / "pyproject.toml"
    if not pyproject_path.is_file():
        report.messages.append("pyproject.toml bulunamadı.")
        return report
    report.pyproject_exists = True

    loader = ConfigLoader(root)
    config = loader.load()

    lock_path = root / config.lockfile_path
    if not lock_path.is_file():
        report.messages.append(f"Lockfile bulunamadı: {config.lockfile_path} ('paketci lock' çalıştırın)")
        return report
    report.lockfile_exists = True

    graph = lockfile_io.read(lock_path)
    locked_names = {canonicalize_name(name) for name in graph.packages}

    # 1. Config'deki doğrudan bağımlılıklar lockfile'da var mı?
    for dep in config.dependencies:
        norm = canonicalize_name(dep.name)
        if norm not in locked_names:
            report.missing_in_lock.append(dep.name)

    # 2. Lockfile'daki paketler hedef ortamda kurulu mu?
    env = detect_env()
    for pkg in graph.all_packages():
        if env.is_installed(pkg.name, pkg.version):
            report.installed_ok.append((pkg.name, pkg.version))
        else:
            report.missing_in_env.append((pkg.name, pkg.version))

    # 3. Peer dependency denetimi
    for pkg_name, peer_spec in config.peer_dependencies.items():
        norm_pkg = canonicalize_name(pkg_name)
        if norm_pkg in locked_names:
            try:
                req = Requirement(peer_spec)
                peer_norm = canonicalize_name(req.name)
                if peer_norm not in locked_names:
                    report.peer_warnings.append(
                        f"'{pkg_name}' için gerekli olan peer dependency '{peer_spec}' kilitli değil!"
                    )
                else:
                    peer_pkg = graph.get(peer_norm)
                    if peer_pkg and req.specifier and not req.specifier.contains(peer_pkg.version, prereleases=True):
                        report.peer_warnings.append(
                            f"'{pkg_name}' peer dependency olarak '{peer_spec}' bekliyor, fakat kilitli sürüm '{peer_pkg.version}'"
                        )
            except Exception:
                pass

    plugin_prefixes = ["pytest-", "sphinx-", "flask-", "django-", "celery-", "mypy-"]
    for pkg in graph.all_packages():
        norm = canonicalize_name(pkg.name)
        for prefix in plugin_prefixes:
            if norm.startswith(prefix):
                host_pkg = prefix.rstrip("-")
                if host_pkg not in locked_names:
                    report.peer_warnings.append(
                        f"'{pkg.name}' bir eklenti paketi fakat ana paket '{host_pkg}' kilitli değil (peer dependency uyarısı)."
                    )

    return report


def run_cmd(
    command: list[str],
    project_root: Optional[Path] = None,
) -> int:
    """
    Proje sanal ortamı bağlamında bir komut çalıştırır.

    Args:
        command: Çalıştırılacak komut ve argümanları listesi (örn. ['pytest', '-v']).
        project_root: Proje kök dizini.

    Returns:
        Komutun çıkış kodu (exit code).
    """
    import os
    import subprocess

    root = project_root or find_project_root()
    env = detect_env()

    run_env = os.environ.copy()
    scripts_dir_str = str(env.scripts_dir)
    current_path = run_env.get("PATH", "")
    run_env["PATH"] = f"{scripts_dir_str}{os.pathsep}{current_path}"
    run_env["VIRTUAL_ENV"] = str(env.scripts_dir.parent)

    cmd_name = command[0]
    local_binary = env.scripts_dir / cmd_name
    exec_cmd = list(command)
    if local_binary.is_file() and os.access(local_binary, os.X_OK):
        exec_cmd[0] = str(local_binary)

    result = subprocess.run(exec_cmd, env=run_env, cwd=root)
    return result.returncode


@dataclass
class TreeNode:
    """Bağımlılık ağacı düğümü."""
    name: str
    version: str
    constraint: str = ""
    dependencies: list[TreeNode] = field(default_factory=list)


def dependency_tree(project_root: Optional[Path] = None) -> list[TreeNode]:
    """Hiyerarşik bağımlılık ağacını üretir."""
    from packaging.utils import canonicalize_name
    from packaging.requirements import Requirement
    root = project_root or find_project_root()
    loader, graph = _load_config_and_lock(root)
    if not graph:
        return []

    config = loader.load()
    pkg_map = {canonicalize_name(pkg.name): pkg for pkg in graph.all_packages()}

    def _build_node(name: str, constraint: str, visited: set[str]) -> TreeNode:
        norm = canonicalize_name(name)
        pkg = pkg_map.get(norm)
        version = pkg.version if pkg else "?"
        node = TreeNode(name=name, version=version, constraint=constraint)

        if norm in visited:
            return node
        new_visited = visited | {norm}

        if pkg:
            for dep_str in pkg.dependencies:
                try:
                    req = Requirement(dep_str)
                    if req.marker is None or req.marker.evaluate():
                        child = _build_node(req.name, str(req.specifier), new_visited)
                        node.dependencies.append(child)
                except Exception:
                    pass
        return node

    roots: list[TreeNode] = []
    for dep in config.dependencies:
        roots.append(_build_node(dep.name, dep.constraint, set()))
    return roots


@dataclass
class CacheReport:
    """Önbellek kullanım raporu."""
    wheel_cache_dir: Path
    wheel_count: int
    wheel_size_bytes: int
    metadata_cache_dir: Path
    metadata_count: int
    metadata_size_bytes: int

    @property
    def total_size_bytes(self) -> int:
        return self.wheel_size_bytes + self.metadata_size_bytes


def cache_info() -> CacheReport:
    """Önbellek boyutu ve dosya istatistiklerini raporlar."""
    from paketci.fetcher.cache import WheelStore
    from paketci.index.cache import MetadataCache

    ws = WheelStore()
    mc = MetadataCache()

    def _dir_stats(p: Path) -> tuple[int, int]:
        count = 0
        total_size = 0
        if p.is_dir():
            for f in p.rglob("*"):
                if f.is_file():
                    count += 1
                    total_size += f.stat().st_size
        return count, total_size

    w_count, w_size = _dir_stats(ws.cache_dir)
    m_count, m_size = _dir_stats(mc.cache_dir)

    return CacheReport(
        wheel_cache_dir=ws.cache_dir,
        wheel_count=w_count,
        wheel_size_bytes=w_size,
        metadata_cache_dir=mc.cache_dir,
        metadata_count=m_count,
        metadata_size_bytes=m_size,
    )


def cache_clean() -> tuple[int, int]:
    """Tüm önbellekleri temizler. (silinen_dosya_sayisi, temizlenen_bayt) döndürür."""
    import shutil
    report = cache_info()
    files_deleted = report.wheel_count + report.metadata_count
    bytes_freed = report.total_size_bytes

    if report.wheel_cache_dir.is_dir():
        shutil.rmtree(report.wheel_cache_dir, ignore_errors=True)
    if report.metadata_cache_dir.is_dir():
        shutil.rmtree(report.metadata_cache_dir, ignore_errors=True)

    return files_deleted, bytes_freed


def build_package(
    project_root: Optional[Path] = None,
    sdist: bool = True,
    wheel: bool = True,
    dest_dir: Optional[Path] = None,
    isolation: bool = True,
) -> list[Path]:
    """
    Projeyi sdist (.tar.gz) ve wheel (.whl) paketlerine derler (PEP 517).
    """
    import subprocess
    import sys

    root = project_root or find_project_root()
    out = (dest_dir or (root / "dist")).resolve()
    out.mkdir(parents=True, exist_ok=True)

    before_files = set(out.glob("*"))

    cmd = [sys.executable, "-m", "build", str(root), "--outdir", str(out)]
    if sdist and not wheel:
        cmd.append("--sdist")
    elif wheel and not sdist:
        cmd.append("--wheel")
    if not isolation:
        cmd.append("--no-isolation")

    logger.info("📦 Proje derleniyor (PEP 517 / build)...")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        from paketci.core.exceptions import PaketciError
        raise PaketciError(f"Derleme başarısız oldu (çıkış kodu: {exc.returncode})") from exc

    after_files = set(out.glob("*"))
    new_files = [p for p in (after_files - before_files) if p.is_file()]
    return sorted(new_files)


@dataclass
class OutdatedPackage:
    """Eski kalmış paket bilgisi."""
    name: str
    current_version: str
    latest_version: str
    update_type: str  # "major", "minor", "patch"


@dataclass
class LicenseInfo:
    """Paket lisans bilgisi."""
    name: str
    version: str
    license_name: str


def find_outdated(
    include_prereleases: bool = False,
    project_root: Optional[Path] = None,
) -> list[OutdatedPackage]:
    """Kilitli paketlerin PyPI'daki en yeni sürümlerini sorgular."""
    from packaging.version import Version, InvalidVersion
    root = project_root or find_project_root()
    loader, graph = _load_config_and_lock(root)
    if not graph:
        return []

    config = loader.load()
    client, cache = _make_client_and_cache(config.index_url)

    outdated: list[OutdatedPackage] = []
    with client:
        for pkg in graph.all_packages():
            try:
                raw_versions = client.get_versions(pkg.name)
                if not raw_versions:
                    continue

                parsed_versions = []
                for v in raw_versions:
                    try:
                        pv = Version(v)
                        if include_prereleases or not pv.is_prerelease:
                            parsed_versions.append(pv)
                    except InvalidVersion:
                        pass

                if not parsed_versions:
                    continue

                latest_ver = sorted(parsed_versions, reverse=True)[0]
                cur_v = Version(pkg.version)

                if latest_ver > cur_v:
                    update_type = "patch"
                    if latest_ver.major > cur_v.major:
                        update_type = "major"
                    elif latest_ver.minor > cur_v.minor:
                        update_type = "minor"

                    outdated.append(
                        OutdatedPackage(
                            name=pkg.name,
                            current_version=pkg.version,
                            latest_version=str(latest_ver),
                            update_type=update_type,
                        )
                    )
            except Exception as exc:
                logger.debug("Versiyon kontrolü yapılamadı '%s': %s", pkg.name, exc)

    return sorted(outdated, key=lambda x: x.name.lower())


def get_licenses(project_root: Optional[Path] = None) -> list[LicenseInfo]:
    """Kilitli veya kurulu paketlerin lisans bilgilerini derler."""
    import importlib.metadata
    from packaging.utils import canonicalize_name
    root = project_root or find_project_root()
    loader, graph = _load_config_and_lock(root)
    if not graph:
        return []

    env = detect_env()
    results: list[LicenseInfo] = []

    try:
        dists = list(importlib.metadata.distributions(path=[str(env.site_packages)]))
    except Exception:
        dists = []

    dist_map = {}
    for d in dists:
        raw = d.metadata.get("Name")
        if raw:
            dist_map[canonicalize_name(raw)] = d

    for pkg in graph.all_packages():
        norm = canonicalize_name(pkg.name)
        lic_name = "Bilinmiyor"
        d = dist_map.get(norm)
        if d:
            lic = d.metadata.get("License") or d.metadata.get("License-Expression")
            if not lic or lic.strip() in ("", "UNKNOWN"):
                classifiers = d.metadata.get_all("Classifier") or []
                lic_classifiers = [c.split(" :: ")[-1] for c in classifiers if c.startswith("License ::")]
                if lic_classifiers:
                    lic = ", ".join(lic_classifiers)
            if lic:
                lic_name = lic.strip()

        results.append(LicenseInfo(name=pkg.name, version=pkg.version, license_name=lic_name))

    return sorted(results, key=lambda x: x.name.lower())


def publish_package(
    dist_dir: Optional[Path] = None,
    repository_url: str = "https://upload.pypi.org/legacy/",
    token: Optional[str] = None,
    project_root: Optional[Path] = None,
    skip_existing: bool = False,
) -> list[str]:
    """
    dist/ dizinindeki derlenmiş paketleri PyPI / TestPyPI deposuna yükler.
    """
    import os
    import hashlib
    import httpx

    root = project_root or find_project_root()
    d_dir = (dist_dir or (root / "dist")).resolve()

    if not d_dir.is_dir():
        from paketci.core.exceptions import PaketciError
        raise PaketciError(f"Dağıtım dizini bulunamadı: {d_dir}. Önce 'paketci build' çalıştırın.")

    files = [p for p in d_dir.glob("*") if p.is_file() and (p.suffix == ".whl" or p.name.endswith(".tar.gz"))]
    if not files:
        from paketci.core.exceptions import PaketciError
        raise PaketciError(f"Yüklenecek paket bulunamadı: {d_dir}. Önce 'paketci build' çalıştırın.")

    auth_token = token or os.environ.get("PYPI_API_TOKEN") or os.environ.get("TWINE_PASSWORD")
    if not auth_token:
        from paketci.core.exceptions import PaketciError
        raise PaketciError(
            "PyPI API Token bulunamadı. Lütfen --token argümanı sağlayın veya PYPI_API_TOKEN ortam değişkenini ayarlayın."
        )

    uploaded: list[str] = []
    auth = ("__token__", auth_token)

    for file_path in sorted(files):
        logger.info("📤 Yükleniyor: %s ➔ %s", file_path.name, repository_url)
        content = file_path.read_bytes()
        sha256 = hashlib.sha256(content).hexdigest()
        md5 = hashlib.md5(content).hexdigest()

        filetype = "bdist_wheel" if file_path.suffix == ".whl" else "sdist"

        data = {
            ":action": "file_upload",
            "protocol_version": "1",
            "filetype": filetype,
            "sha256_digest": sha256,
            "md5_digest": md5,
        }

        files_payload = {
            "content": (file_path.name, content, "application/octet-stream")
        }

        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                repository_url,
                data=data,
                files=files_payload,
                auth=auth,
            )

            if skip_existing and resp.status_code == 400 and "already exists" in resp.text.lower():
                logger.warning("  ⚠ Paket zaten mevcut (atlandı): %s", file_path.name)
                continue

            if resp.status_code not in (200, 201):
                from paketci.core.exceptions import PaketciError
                raise PaketciError(f"Yükleme başarısız ({resp.status_code}): {resp.text}")

        logger.info("  ✔ Yüklendi: %s", file_path.name)
        uploaded.append(file_path.name)

    return uploaded


# ─────────────────────────────────────────────────────────────────────────────
# Dedupe Operasyonu (Tek Sürüm Zorlama & Çakışma Denetimi)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class DedupePackageReport:
    package: str
    locked_version: str
    dependents: list[tuple[str, str]]
    is_compatible: bool
    conflicts: list[str] = field(default_factory=list)


@dataclass
class DedupeResult:
    packages_checked: int
    compatible_count: int
    conflict_count: int
    reports: list[DedupePackageReport]


def dedupe(project_root: Optional[Path] = None, check_only: bool = False) -> DedupeResult:
    """Lockfile'daki tüm paketlerin bağımlılık kısıtlamalarını denetler,
    tek bir uyumlu sürüme indirgenebilirliğini (deduplication) doğrular."""
    from packaging.requirements import Requirement
    from packaging.specifiers import SpecifierSet
    from packaging.utils import canonicalize_name

    root = project_root or find_project_root()
    try:
        loader, graph = _load_config_and_lock(root)
    except Exception:
        return DedupeResult(packages_checked=0, compatible_count=0, conflict_count=0, reports=[])

    if not graph or not graph.packages:
        return DedupeResult(packages_checked=0, compatible_count=0, conflict_count=0, reports=[])

    config = loader.load()

    # dep_map: canonical_name -> list of (source, constraint_str)
    dep_map: dict[str, list[tuple[str, str]]] = {
        canonicalize_name(pkg_name): [] for pkg_name in graph.packages
    }

    # Doğrudan proje bağımlılıkları
    for direct_dep in config.dependencies:
        c_name = canonicalize_name(direct_dep.name)
        if c_name in dep_map:
            dep_map[c_name].append(("project (direct)", direct_dep.constraint or "*"))

    for group, group_deps in config.optional_dependencies.items():
        for opt_dep in group_deps:
            c_name = canonicalize_name(opt_dep.name)
            if c_name in dep_map:
                dep_map[c_name].append((f"project ({group})", opt_dep.constraint or "*"))

    # Transitif paketlerin gereksinimleri
    for parent_pkg in graph.packages.values():
        for req_str in parent_pkg.dependencies:
            try:
                req = Requirement(req_str)
                if req.marker and not req.marker.evaluate({"extra": ""}):
                    continue
                c_name = canonicalize_name(req.name)
                if c_name in dep_map:
                    constraint_str = str(req.specifier) if req.specifier else "*"
                    dep_map[c_name].append((parent_pkg.name, constraint_str))
            except Exception:
                continue

    reports: list[DedupePackageReport] = []
    conflict_count = 0
    compatible_count = 0

    for pkg_name, pkg in sorted(graph.packages.items()):
        c_name = canonicalize_name(pkg_name)
        dependents = dep_map.get(c_name, [])
        conflicts: list[str] = []

        for source, spec_str in dependents:
            if spec_str and spec_str != "*":
                try:
                    spec = SpecifierSet(spec_str)
                    if not spec.contains(pkg.version, prereleases=True):
                        conflicts.append(f"{source} bunu istiyor: '{spec_str}' fakat kilitli sürüm '{pkg.version}'")
                except Exception:
                    pass

        is_compatible = len(conflicts) == 0
        if is_compatible:
            compatible_count += 1
        else:
            conflict_count += 1

        reports.append(
            DedupePackageReport(
                package=pkg.name,
                locked_version=pkg.version,
                dependents=dependents,
                is_compatible=is_compatible,
                conflicts=conflicts,
            )
        )

    return DedupeResult(
        packages_checked=len(reports),
        compatible_count=compatible_count,
        conflict_count=conflict_count,
        reports=reports,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Workspace (Monorepo) Operasyonları
# ─────────────────────────────────────────────────────────────────────────────

def list_workspace(project_root: Optional[Path] = None):
    """Çalışma alanındaki (workspace) tüm üyeleri listeler."""
    from paketci.core.exceptions import ConfigError
    from paketci.workspace import find_workspace

    root = project_root or find_project_root()
    ws = find_workspace(root)
    if not ws:
        raise ConfigError(
            f"Çalışma alanı (workspace) bulunamadı: {root}\n"
            "pyproject.toml dosyasında [tool.paketci.workspace] members tanımlı olmalıdır."
        )
    return ws


def run_workspace_cmd(
    project_root: Optional[Path] = None,
    command: list[str] = [],
    member_name: Optional[str] = None,
) -> dict[str, int]:
    """Workspace içindeki üye projelerde komut çalıştırır."""
    import subprocess
    from paketci.core.exceptions import PaketciError

    ws = list_workspace(project_root)
    members_to_run = ws.members
    if member_name:
        member = ws.get_member(member_name)
        if not member:
            raise PaketciError(f"Workspace üyesi bulunamadı: '{member_name}'")
        members_to_run = [member]

    if not command:
        raise PaketciError("Çalıştırılacak bir komut belirtilmedi.")

    results: dict[str, int] = {}
    for member in members_to_run:
        logger.info("📦 Workspace Üyesi: %s (%s)", member.name, member.path)
        res = subprocess.run(command, cwd=member.path)
        results[member.name] = res.returncode

    return results






