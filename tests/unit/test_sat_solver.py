"""Unit tests for Native SAT / DPLL solver."""

import pytest
from paketci.core.exceptions import ResolveError
from paketci.resolver.sat_solver import DPLLSolver, Literal, DependencySATSolver
from paketci.index.models import PackageMetadata


def test_dpll_simple_sat():
    # (A v B) ^ (¬A v B) ^ (A v ¬B)
    litA = Literal("A", True)
    notA = Literal("A", False)
    litB = Literal("B", True)
    notB = Literal("B", False)

    clauses = [
        [litA, litB],
        [notA, litB],
        [litA, notB],
    ]
    solver = DPLLSolver(clauses=clauses, var_priority=["A", "B"])
    res = solver.solve()
    assert res is not None
    assert res["A"] is True
    assert res["B"] is True


def test_dpll_simple_unsat():
    # A ^ ¬A
    litA = Literal("A", True)
    notA = Literal("A", False)

    clauses = [
        [litA],
        [notA],
    ]
    solver = DPLLSolver(clauses=clauses)
    res = solver.solve()
    assert res is None


def test_dpll_unit_propagation():
    # A ^ (¬A v B) -> B must be True
    litA = Literal("A", True)
    notA = Literal("A", False)
    litB = Literal("B", True)

    clauses = [
        [litA],
        [notA, litB],
    ]
    solver = DPLLSolver(clauses=clauses)
    res = solver.solve()
    assert res is not None
    assert res["A"] is True
    assert res["B"] is True


def test_dependency_sat_solver_with_mock(tmp_path):
    class MockClient:
        def get_versions(self, name):
            if name == "alpha":
                return ["2.0.0", "1.0.0"]
            if name == "beta":
                return ["1.5.0"]
            return []

        def get_metadata(self, name, version=None):
            if name == "alpha":
                if version == "2.0.0":
                    return PackageMetadata(name="alpha", version="2.0.0", requires_dist=["beta>=1.0"])
                if version == "1.0.0":
                    return PackageMetadata(name="alpha", version="1.0.0", requires_dist=[])
            if name == "beta":
                return PackageMetadata(name="beta", version="1.5.0", requires_dist=[])
            return None

    class MockCache:
        def get_versions(self, name):
            return None
        def set_versions(self, name, versions):
            pass
        def get(self, name, version):
            return None
        def set(self, name, version, meta):
            pass

    solver = DependencySATSolver(
        requirements=["alpha>=1.0"],
        client=MockClient(),
        cache=MockCache(),
    )
    res = solver.solve()
    assert res is not None
    pkgs = dict(res.resolved_packages())
    assert pkgs["alpha"] == "2.0.0"
    assert pkgs["beta"] == "1.5.0"


def test_dependency_sat_solver_conflict_raises(tmp_path):
    class MockClient:
        def get_versions(self, name):
            if name == "pkg":
                return ["1.0.0"]
            if name == "conflict":
                return ["1.0.0"]
            return []

        def get_metadata(self, name, version=None):
            if name == "pkg":
                return PackageMetadata(name="pkg", version="1.0.0", requires_dist=["conflict>=2.0"])
            if name == "conflict":
                return PackageMetadata(name="conflict", version="1.0.0", requires_dist=[])
            return None

    class MockCache:
        def get_versions(self, name): return None
        def set_versions(self, name, v): pass
        def get(self, name, v): return None
        def set(self, name, v, m): pass

    solver = DependencySATSolver(
        requirements=["pkg"],
        client=MockClient(),
        cache=MockCache(),
    )
    with pytest.raises(ResolveError):
        solver.solve()
