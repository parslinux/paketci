"""Paralel asenkron wheel/sdist indirici."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from typing import Optional

import httpx
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from paketci.cli.ui import console
from paketci.core.exceptions import FetchError, OfflineModeError
from paketci.fetcher.cache import WheelStore
from paketci.fetcher.hasher import verify
from paketci.lockfile.models import LockedFile
from paketci.utils.logging import get_logger

logger = get_logger(__name__)

DEFAULT_CONCURRENCY = 8
DEFAULT_TIMEOUT = 60.0


class Downloader:
    """
    Paralel wheel/sdist indirici.

    - asyncio.Semaphore ile eş zamanlı indirme sayısını sınırlar.
    - Her indirme sonrası SHA-256 doğrulaması yapar.
    - Content-addressable WheelStore üzerinden önbellek kullanır.
    - Rich progress bar ile anlık indirme hızı ve boyutunu gösterir.
    """

    def __init__(
        self,
        store: Optional[WheelStore] = None,
        concurrency: int = DEFAULT_CONCURRENCY,
        timeout: float = DEFAULT_TIMEOUT,
        offline: bool = False,
        show_progress: bool = True,
    ) -> None:
        self._store = store or WheelStore()
        self._concurrency = concurrency
        self._timeout = timeout
        self._offline = offline
        self._show_progress = show_progress

    async def download_all(
        self,
        files: list[LockedFile],
        dest_dir: Path,
    ) -> dict[str, Path]:
        """
        Birden fazla dosyayı paralel indirir.

        Returns:
            {filename: local_path} eşlemesi.
        """
        dest_dir.mkdir(parents=True, exist_ok=True)
        if not files:
            return {}

        semaphore = asyncio.Semaphore(self._concurrency)

        progress: Optional[Progress] = None
        if self._show_progress and console.is_terminal:
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.fields[filename]}"),
                BarColumn(bar_width=30),
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
                console=console,
                transient=True,
            )
            progress.start()

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                tasks = [
                    self._download_one(f, dest_dir, semaphore, client, progress)
                    for f in files
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            if progress:
                progress.stop()

        output: dict[str, Path] = {}
        errors: list[Exception] = []
        for f, result in zip(files, results):
            if isinstance(result, Exception):
                errors.append(result)
                logger.error("İndirme hatası %s: %s", f.filename, result)
            else:
                output[f.filename] = result  # type: ignore[assignment]

        if errors:
            raise FetchError(
                f"{len(errors)} dosya indirilemedi. İlk hata: {errors[0]}"
            )
        return output

    async def _download_one(
        self,
        file: LockedFile,
        dest_dir: Path,
        semaphore: asyncio.Semaphore,
        client: httpx.AsyncClient,
        progress: Optional[Progress] = None,
    ) -> Path:
        """Tek bir dosyayı indirir; önce önbellekte arar."""
        # 1. Önbellekte var mı?
        cached = self._store.get(file.sha256, file.filename)
        if cached:
            logger.debug("Önbellekten: %s", file.filename)
            dst = dest_dir / file.filename
            from paketci.utils.paths import link_or_copy
            link_or_copy(cached, dst)
            return dst

        # 2. Offline modda → hata
        if self._offline:
            raise OfflineModeError(
                f"Offline mod: '{file.filename}' önbellekte yok, indirilemez."
            )

        # 3. İndir
        async with semaphore:
            return await self._fetch(file, dest_dir, client, progress)

    async def _fetch(
        self,
        file: LockedFile,
        dest_dir: Path,
        client: httpx.AsyncClient,
        progress: Optional[Progress] = None,
    ) -> Path:
        tmp_path: Optional[Path] = None
        task_id = None
        if progress:
            task_id = progress.add_task(
                "download",
                filename=file.filename,
                total=None,
            )

        try:
            with tempfile.NamedTemporaryFile(
                dir=dest_dir, delete=False, suffix=".tmp"
            ) as tmp:
                tmp_path = Path(tmp.name)
                async with client.stream("GET", file.url) as resp:
                    resp.raise_for_status()
                    total = resp.headers.get("Content-Length")
                    if progress and task_id is not None and total and total.isdigit():
                        progress.update(task_id, total=int(total))

                    async for chunk in resp.aiter_bytes(chunk_size=65536):
                        tmp.write(chunk)
                        if progress and task_id is not None:
                            progress.update(task_id, advance=len(chunk))

            # Hash doğrula
            verify(tmp_path, file.sha256)

            # Önbelleğe koy ve son hedefe hardlink/kopya
            store_path = self._store.put(tmp_path, file.sha256)
            dest = dest_dir / file.filename
            from paketci.utils.paths import link_or_copy
            link_or_copy(store_path, dest)

            tmp_path.unlink(missing_ok=True)
            if progress and task_id is not None:
                progress.update(task_id, visible=False)
            return dest

        except Exception:
            if progress and task_id is not None:
                progress.update(task_id, visible=False)
            if tmp_path and tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            raise

