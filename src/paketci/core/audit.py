"""Güvenlik denetimi modülü — OSV.dev (Open Source Vulnerabilities) API entegrasyonu."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import httpx

from paketci.core.exceptions import PaketciError
from paketci.lockfile import io as lockfile_io
from paketci.utils.paths import find_project_root


@dataclass
class Vulnerability:
    """Tek bir güvenlik zafiyeti kaydı."""

    id: str
    package: str
    version: str
    summary: str
    severity: str
    fixed_in: list[str] = field(default_factory=list)
    reference_url: str = ""


@dataclass
class AuditResult:
    """Güvenlik denetimi sonuç raporu."""

    packages_scanned: int
    vulnerabilities: list[Vulnerability] = field(default_factory=list)

    @property
    def has_vulnerabilities(self) -> bool:
        return len(self.vulnerabilities) > 0


def _parse_severity(vuln_data: dict) -> str:
    # CVSS veya database_specific severity bul
    sev_list = vuln_data.get("severity", [])
    if sev_list and isinstance(sev_list, list):
        for s in sev_list:
            score = s.get("score", "")
            if score.startswith("CVSS:3"):
                return "HIGH"  # Varsayılan standart gösterge

    db_specific = vuln_data.get("database_specific", {})
    sev = db_specific.get("severity")
    if sev:
        return str(sev).upper()

    return "MODERATE"


def _extract_fixed_versions(vuln_data: dict, pkg_name: str) -> list[str]:
    fixed = []
    for affected in vuln_data.get("affected", []):
        pkg = affected.get("package", {})
        if pkg.get("name", "").lower() == pkg_name.lower():
            for r in affected.get("ranges", []):
                for event in r.get("events", []):
                    if "fixed" in event:
                        fixed.append(event["fixed"])
    return fixed


async def _scan_single_package(
    client: httpx.AsyncClient,
    pkg_name: str,
    pkg_version: str,
    semaphore: asyncio.Semaphore,
) -> list[Vulnerability]:
    async with semaphore:
        url = "https://api.osv.dev/v1/query"
        payload = {
            "package": {
                "name": pkg_name,
                "ecosystem": "PyPI",
            },
            "version": pkg_version,
        }
        try:
            resp = await client.post(url, json=payload, timeout=15.0)
            if resp.status_code != 200:
                return []
            data = resp.json()
            vulns_raw = data.get("vulns", [])
            results = []
            for v in vulns_raw:
                vuln_id = v.get("id", "UNKNOWN")
                summary = v.get("summary") or v.get("details", "")[:80] or "Açıklama belirtilmemiş"
                severity = _parse_severity(v)
                fixed = _extract_fixed_versions(v, pkg_name)
                refs = v.get("references", [])
                ref_url = refs[0].get("url", "") if refs else f"https://osv.dev/vulnerability/{vuln_id}"

                results.append(
                    Vulnerability(
                        id=vuln_id,
                        package=pkg_name,
                        version=pkg_version,
                        summary=summary.strip().replace("\n", " "),
                        severity=severity,
                        fixed_in=fixed,
                        reference_url=ref_url,
                    )
                )
            return results
        except Exception:
            return []


async def audit_async(project_root: Path) -> AuditResult:
    lock_path = project_root / "paketci.lock"
    if not lock_path.is_file():
        raise PaketciError("paketci.lock bulunamadı. Önce 'paketci lock' çalıştırın.")

    graph = lockfile_io.read(lock_path)
    packages = list(graph.packages.values())

    if not packages:
        return AuditResult(packages_scanned=0, vulnerabilities=[])

    semaphore = asyncio.Semaphore(10)
    async with httpx.AsyncClient() as client:
        tasks = [
            _scan_single_package(client, pkg.name, pkg.version, semaphore)
            for pkg in packages
        ]
        all_vulns_lists = await asyncio.gather(*tasks)

    flat_vulns = [vuln for sublist in all_vulns_lists for vuln in sublist]
    return AuditResult(
        packages_scanned=len(packages),
        vulnerabilities=flat_vulns,
    )


def audit(project_root: Optional[Path] = None) -> AuditResult:
    """Kilitli paketlerin güvenlik zafiyetlerini (CVE/GHSA) tarar."""
    root = project_root or find_project_root()
    return asyncio.run(audit_async(root))
