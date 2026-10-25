"""Native SAT / DPLL Bağımlılık Çözücü (Pure-Python SAT Solver).

Bağımlılık çözümlemesini Boolean Satisfiability (CNF SAT) problemine dönüştürür
ve DPLL (Davis–Putnam–Logemann–Loveland) algoritması ile çözer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name
from packaging.version import Version, parse as parse_version

from paketci.core.exceptions import ResolveError
from paketci.index.cache import MetadataCache
from paketci.index.client import PyPIClient
from paketci.resolver.solver import SolveResult


# ─────────────────────────────────────────────────────────────────────────────
# SAT Çekirdeği (DPLL Engine)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Literal:
    """Tek bir SAT literali (değişken ve polarite)."""
    var: str  # Örn: "requests:2.31.0"
    positive: bool = True

    def __neg__(self) -> Literal:
        return Literal(self.var, not self.positive)

    def __repr__(self) -> str:
        return self.var if self.positive else f"¬{self.var}"


class DPLLSolver:
    """CNF (Conjunctive Normal Form) için DPLL SAT çözücüsü."""

    def __init__(self, clauses: List[List[Literal]], var_priority: Optional[List[str]] = None):
        self.clauses: List[List[Literal]] = clauses
        self.var_priority: List[str] = var_priority or []

    def solve(self) -> Optional[Dict[str, bool]]:
        """Formül tatmin edilebilirse {var: bool} ataması döner; aksi takdirde None."""
        assignment: Dict[str, bool] = {}
        return self._dpll(self.clauses, assignment)

    def _dpll(self, clauses: List[List[Literal]], assignment: Dict[str, bool]) -> Optional[Dict[str, bool]]:
        # 1. Unit Propagation
        changed = True
        while changed:
            changed = False
            unit_literals = []
            for clause in clauses:
                # Zaten doğru olan literal varsa bu cümlecik sağlanmıştır
                unresolved = []
                satisfied = False
                for lit in clause:
                    val = assignment.get(lit.var)
                    if val is not None:
                        if (val and lit.positive) or (not val and not lit.positive):
                            satisfied = True
                            break
                    else:
                        unresolved.append(lit)

                if satisfied:
                    continue

                if len(unresolved) == 0:
                    # Boş cümlecik -> Çelişki (Conflict)!
                    return None

                if len(unresolved) == 1:
                    unit_literals.append(unresolved[0])

            for unit in unit_literals:
                val = assignment.get(unit.var)
                if val is not None:
                    expected = unit.positive
                    if val != expected:
                        return None
                else:
                    assignment[unit.var] = unit.positive
                    changed = True

        # 2. Tüm cümlecikler sağlandı mı?
        all_satisfied = True
        unassigned_vars: Set[str] = set()

        for clause in clauses:
            sat = False
            for lit in clause:
                val = assignment.get(lit.var)
                if val is not None:
                    if (val and lit.positive) or (not val and not lit.positive):
                        sat = True
                        break
                else:
                    unassigned_vars.add(lit.var)
            if not sat:
                all_satisfied = False

        if all_satisfied:
            return assignment

        if not unassigned_vars:
            return None

        # 3. Dal seçimi (Branching Heuristic)
        chosen_var = None
        for v in self.var_priority:
            if v in unassigned_vars and v not in assignment:
                chosen_var = v
                break

        if not chosen_var:
            chosen_var = next(iter(unassigned_vars))

        # Önce True dene (en yeni sürümü seçme eğilimi)
        branch_true = dict(assignment)
        branch_true[chosen_var] = True
        res = self._dpll(clauses, branch_true)
        if res is not None:
            return res

        # Ardından False dene
        branch_false = dict(assignment)
        branch_false[chosen_var] = False
        return self._dpll(clauses, branch_false)


# ─────────────────────────────────────────────────────────────────────────────
# Bağımlılık Probleminden SAT'a Dönüştürücü (CNF Encoding)
# ─────────────────────────────────────────────────────────────────────────────

class DependencySATSolver:
    """Python bağımlılık grafiğini SAT formülüne derleyip çözer."""

    def __init__(
        self,
        requirements: List[str],
        client: PyPIClient,
        cache: MetadataCache,
    ):
        self.requirements = [Requirement(r) for r in requirements]
        self.client = client
        self.cache = cache
        self.version_cache: Dict[str, List[Version]] = {}
        self.meta_cache: Dict[Tuple[str, str], List[str]] = {}

    def _get_versions(self, name: str) -> List[Version]:
        norm = canonicalize_name(name)
        if norm in self.version_cache:
            return self.version_cache[norm]

        cached = self.cache.get_versions(norm)
        if cached is not None:
            vers = sorted([parse_version(v) for v in cached if not parse_version(v).is_prerelease], reverse=True)
            self.version_cache[norm] = vers
            return vers

        raw_versions = None
        if hasattr(self.client, "get_versions"):
            try:
                raw_versions = self.client.get_versions(norm)
            except Exception:
                raw_versions = None

        if not raw_versions:
            try:
                meta = self.client.get_metadata(norm)
                raw_versions = getattr(meta, "versions", [meta.version]) if meta else []
            except Exception:
                raw_versions = []

        if not raw_versions:
            self.version_cache[norm] = []
            return []

        self.cache.set_versions(norm, raw_versions)
        vers = sorted([parse_version(v) for v in raw_versions if not parse_version(v).is_prerelease], reverse=True)
        self.version_cache[norm] = vers
        return vers

    def _get_deps(self, name: str, version: str) -> List[str]:
        norm = canonicalize_name(name)
        key = (norm, version)
        if key in self.meta_cache:
            return self.meta_cache[key]

        cached = self.cache.get(norm, version)
        if cached is not None:
            deps = getattr(cached, "requires_dist", getattr(cached, "dependencies", []))
            self.meta_cache[key] = deps
            return deps

        try:
            meta = self.client.get_metadata(norm, version)
        except Exception:
            meta = None

        if not meta:
            self.meta_cache[key] = []
            return []

        self.cache.set(norm, version, meta)
        deps = getattr(meta, "requires_dist", getattr(meta, "dependencies", []))
        self.meta_cache[key] = deps
        return deps

    def solve(self) -> SolveResult:
        clauses: List[List[Literal]] = []
        var_priority: List[str] = []
        processed_packages: Set[str] = set()
        queue: List[str] = [canonicalize_name(r.name) for r in self.requirements]

        # 1. İlgili tüm paketleri ve aday sürümlerini topla (en yeni en fazla 5 sürüm)
        package_versions: Dict[str, List[str]] = {}

        while queue:
            pkg_name = queue.pop(0)
            if pkg_name in processed_packages:
                continue
            processed_packages.add(pkg_name)

            all_vers = self._get_versions(pkg_name)
            if not all_vers:
                raise ResolveError(f"Paket için hiçbir sürüm bulunamadı: {pkg_name}")

            # Çözümleme hızını optimize etmek için en yeni kararlı sürümleri al
            top_vers = [str(v) for v in all_vers[:5]]
            package_versions[pkg_name] = top_vers

            # Öncelik sırasına en yenilerden başlayarak ekle
            for v_str in top_vers:
                var = f"{pkg_name}:{v_str}"
                var_priority.append(var)

            # Bu sürümlerin bağımlılıklarını kuyruğa ekle
            for v_str in top_vers:
                deps = self._get_deps(pkg_name, v_str)
                for dep_str in deps:
                    try:
                        req = Requirement(dep_str)
                        if req.marker and not req.marker.evaluate({"extra": ""}):
                            continue
                        dep_norm = canonicalize_name(req.name)
                        if dep_norm not in processed_packages and dep_norm not in queue:
                            queue.append(dep_norm)
                    except Exception:
                        continue

        # 2. Kısıtlama: Kök gereksinimler sağlanmalıdır
        for req in self.requirements:
            pkg_name = canonicalize_name(req.name)
            valid_literals = []
            for v_str in package_versions.get(pkg_name, []):
                ver = parse_version(v_str)
                if not req.specifier or req.specifier.contains(ver, prereleases=True):
                    valid_literals.append(Literal(f"{pkg_name}:{v_str}", True))

            if not valid_literals:
                raise ResolveError(f"Kök gereksinim '{req}' için uyumlu bir sürüm bulunamadı.")
            clauses.append(valid_literals)

        # 3. Kısıtlama: Bir paketten EN FAZLA bir sürüm seçilebilir (At-most-one)
        for pkg_name, vers in package_versions.items():
            for i in range(len(vers)):
                for j in range(i + 1, len(vers)):
                    clauses.append([
                        Literal(f"{pkg_name}:{vers[i]}", False),
                        Literal(f"{pkg_name}:{vers[j]}", False),
                    ])

        # 4. Kısıtlama: Seçilen sürümün bağımlılıkları sağlanmalıdır (Implication)
        for pkg_name, vers in package_versions.items():
            for v_str in vers:
                parent_lit = Literal(f"{pkg_name}:{v_str}", False)
                deps = self._get_deps(pkg_name, v_str)

                for dep_str in deps:
                    try:
                        req = Requirement(dep_str)
                        if req.marker and not req.marker.evaluate({"extra": ""}):
                            continue
                        dep_norm = canonicalize_name(req.name)
                        dep_vers = package_versions.get(dep_norm, [])

                        valid_dep_lits = []
                        for dv in dep_vers:
                            if not req.specifier or req.specifier.contains(parse_version(dv), prereleases=True):
                                valid_dep_lits.append(Literal(f"{dep_norm}:{dv}", True))

                        if not valid_dep_lits:
                            # Bu sürüm kurulursa bağımlılığı çözülemez -> Bu sürüm seçilemez!
                            clauses.append([parent_lit])
                        else:
                            clauses.append([parent_lit] + valid_dep_lits)
                    except Exception:
                        continue

        # 5. SAT Çözücüyü Çalıştır
        solver = DPLLSolver(clauses=clauses, var_priority=var_priority)
        assignment = solver.solve()

        if assignment is None:
            raise ResolveError(
                "Bağımlılıklar Native SAT çözücü ile çözümlenemedi (UNSAT / Çakışan Kısıtlamalar)."
            )

        # 6. Sonuçları Çıkart
        mapping: Dict[str, Tuple[str, str]] = {}
        for var, val in assignment.items():
            if val:
                pkg_name, version = var.split(":", 1)
                mapping[pkg_name] = (pkg_name, version)

        return SolveResult(mapping=mapping)


def solve_with_sat(
    requirements: List[str],
    client: PyPIClient,
    cache: MetadataCache,
) -> SolveResult:
    """Native SAT / DPLL algoritmasıyla bağımlılık grafiğini çözer."""
    solver = DependencySATSolver(requirements=requirements, client=client, cache=cache)
    return solver.solve()
