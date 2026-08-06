"""Bind ``docs/architecture.md``'s dependency claims to the actual imports.

``docs/architecture.md`` stated that "`bioweapon_counter` is the only module the
others depend on … everything else is a sibling". That was false for as long as
it existed: ``antidote_screening`` imports ``PlantToxin`` and
``fraction_affected`` from ``toxicology``. Nothing checked it, so the prose was
free to drift.

The graph is now derived by AST from the source and compared against a declared
edge set that mirrors the doc. Adding, removing, or reversing an import edge
fails here, and ``TestGraphGateCanFail`` proves the derivation reports each of
those rather than shrugging.

The layer rules the same doc states are checked here too: only ``mission.py``
may import ``bond_api``, and no module may import ``infrastructure``.
"""

from __future__ import annotations

import ast
import importlib
import re
from pathlib import Path

_PKG = Path(__file__).resolve().parents[1]
_SRC = _PKG / "src" / "no_time_to_die"
_DOC = _PKG / "docs" / "architecture.md"

#: Every intra-package import edge, as documented in docs/architecture.md.
#: ``(importer, imported)`` by module stem.
DOCUMENTED_EDGES = frozenset(
    {
        # Domain core — exactly two edges, acyclic.
        ("targeting_design", "bioweapon_counter"),
        ("antidote_screening", "toxicology"),
        # Composition point: demo imports every domain module.
        ("demo", "antidote_screening"),
        ("demo", "bioweapon_counter"),
        ("demo", "delivery_forensics"),
        ("demo", "exposure_assessment"),
        ("demo", "targeting_design"),
        ("demo", "toxicology"),
        # Consumers of the shared result.
        ("mission", "antidote_screening"),
        ("mission", "delivery_forensics"),
        ("mission", "demo"),
        ("mission", "toxicology"),
        ("manuscript_variables", "antidote_screening"),
        ("manuscript_variables", "delivery_forensics"),
        ("manuscript_variables", "demo"),
        ("manuscript_variables", "toxicology"),
        ("plots", "antidote_screening"),
        ("plots", "bioweapon_counter"),
        ("plots", "delivery_forensics"),
        ("plots", "demo"),
        ("plots", "targeting_design"),
        ("plots", "toxicology"),
    }
)

#: Modules with no intra-package dependency at all (pure leaves).
DOCUMENTED_LEAVES = frozenset(
    {"bioweapon_counter", "toxicology", "exposure_assessment", "delivery_forensics"}
)


def _source_files() -> tuple[Path, ...]:
    return tuple(sorted(p for p in _SRC.rglob("*.py") if p.name != "__init__.py"))


def module_stems() -> frozenset[str]:
    """Names of the modules that actually exist in the package."""
    return frozenset(path.stem for path in _SRC.rglob("*.py") if path.name != "__init__.py")


def import_edges_of(path: Path, stems: frozenset[str] | None = None) -> set[tuple[str, str]]:
    """Intra-package ``(importer, imported)`` edges declared by one file.

    ``from no_time_to_die import demo, __version__`` mixes a submodule with a
    package attribute; only names that resolve to a real module file become
    edges.
    """
    known = module_stems() if stems is None else stems
    tree = ast.parse(path.read_text(encoding="utf-8"))
    stem = path.stem
    edges: set[tuple[str, str]] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            parts = node.module.split(".")
            if parts[0] != "no_time_to_die":
                continue
            if len(parts) == 1:
                # `from no_time_to_die import a, b` — submodules and attributes.
                edges.update((stem, alias.name) for alias in node.names if alias.name in known)
            else:
                edges.add((stem, parts[-1]))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                if parts[0] == "no_time_to_die" and len(parts) > 1:
                    edges.add((stem, parts[-1]))
    return {(a, b) for a, b in edges if a != b}


def package_graph() -> set[tuple[str, str]]:
    """The whole intra-package import graph, derived from source."""
    edges: set[tuple[str, str]] = set()
    for path in _source_files():
        edges |= import_edges_of(path)
    return edges


def external_importers(module_name: str) -> set[str]:
    """Which source files import a given third-party/top-level module."""
    importers: set[str] = set()
    for path in _source_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            if any(name.split(".")[0] == module_name for name in names):
                importers.add(path.name)
    return importers


class TestDocumentedGraph:
    def test_graph_matches_the_documented_edges(self) -> None:
        derived = package_graph()
        assert derived - DOCUMENTED_EDGES == set(), "undocumented import edge"
        assert DOCUMENTED_EDGES - derived == set(), "documented edge no longer exists"

    def test_the_derivation_is_not_empty(self) -> None:
        """Non-vacuity: an empty derived graph would satisfy a subset check."""
        assert len(package_graph()) >= 20

    def test_antidote_screening_depends_on_toxicology(self) -> None:
        """The specific edge the old doc denied."""
        assert ("antidote_screening", "toxicology") in package_graph()

    def test_declared_leaves_import_nothing_from_the_package(self) -> None:
        importers = {importer for importer, _ in package_graph()}
        assert DOCUMENTED_LEAVES & importers == set()

    def test_the_domain_core_graph_is_acyclic(self) -> None:
        core = {
            "bioweapon_counter",
            "targeting_design",
            "toxicology",
            "antidote_screening",
            "exposure_assessment",
            "delivery_forensics",
        }
        edges = {(a, b) for a, b in package_graph() if a in core and b in core}
        assert edges == {
            ("targeting_design", "bioweapon_counter"),
            ("antidote_screening", "toxicology"),
        }
        assert not {(b, a) for a, b in edges} & edges, "core graph has a cycle"


class TestLayerBoundaries:
    def test_only_mission_imports_bond_api(self) -> None:
        assert external_importers("bond_api") == {"mission.py"}

    def test_nothing_imports_infrastructure(self) -> None:
        assert external_importers("infrastructure") == set()


class TestGraphGateCanFail:
    """Positive controls on the AST derivation itself."""

    def test_a_new_edge_is_detected(self, tmp_path) -> None:
        broken = tmp_path / "exposure_assessment.py"
        broken.write_text(
            "from no_time_to_die.toxicology import PlantToxin\n\nX = PlantToxin\n",
            encoding="utf-8",
        )
        assert import_edges_of(broken) == {("exposure_assessment", "toxicology")}

    def test_the_package_style_import_form_is_detected(self, tmp_path) -> None:
        broken = tmp_path / "toxicology.py"
        broken.write_text("from no_time_to_die import demo, mission\n", encoding="utf-8")
        assert import_edges_of(broken) == {("toxicology", "demo"), ("toxicology", "mission")}

    def test_package_attributes_are_not_mistaken_for_modules(self, tmp_path) -> None:
        """`__version__` is an attribute of the package, not a dependency."""
        source = tmp_path / "mission.py"
        source.write_text("from no_time_to_die import __version__, demo\n", encoding="utf-8")
        assert import_edges_of(source) == {("mission", "demo")}

    def test_a_plain_import_statement_is_detected(self, tmp_path) -> None:
        broken = tmp_path / "toxicology.py"
        broken.write_text("import no_time_to_die.demo\n", encoding="utf-8")
        assert import_edges_of(broken) == {("toxicology", "demo")}

    def test_a_clean_leaf_reports_no_edges(self, tmp_path) -> None:
        clean = tmp_path / "toxicology.py"
        clean.write_text("import math\n\nX = math.pi\n", encoding="utf-8")
        assert import_edges_of(clean) == set()


def _inventory_rows(text: str) -> list[tuple[str, list[str]]]:
    """Parse ``(module_stem, backticked_identifiers)`` out of the
    ``## The domain modules, individually`` table in ``docs/architecture.md``.
    """
    rows: list[tuple[str, list[str]]] = []
    in_block = False
    for line in text.splitlines():
        if line.strip().startswith("## The domain modules"):
            in_block = True
            continue
        if in_block and line.strip().startswith("The intra-package dependency"):
            break
        if not in_block:
            continue
        m = re.match(r"\|\s*`([A-Za-z_][A-Za-z0-9_]*\.py)`\s*\|\s*(.*)\s*\|", line)
        if not m:
            continue
        stem = m.group(1)[:-3]
        ids = re.findall(r"`([A-Za-z_][A-Za-z0-9_]*)`", m.group(2))
        rows.append((stem, ids))
    return rows


class TestInventoryBinding:
    """Bind the per-module function/constant inventory in the table at
    ``docs/architecture.md:28-36`` to the code. Renaming or deleting any public
    identifier named there must fail here, so the table cannot silently drift —
    the exact doc-vs-code drift class the Phase-6 audit hunted.

    The module *name* in each row is trusted (rows are keyed by module); every
    backticked identifier inside a row must resolve on that module.
    """

    def test_every_inventory_identifier_resolves_on_its_module(self) -> None:
        rows = _inventory_rows(_DOC.read_text(encoding="utf-8"))
        assert rows, "no inventory rows parsed; the table may have moved"
        for stem, identifiers in rows:
            module = importlib.import_module(f"no_time_to_die.{stem}")
            for identifier in identifiers:
                assert hasattr(module, identifier), (
                    f"{stem}.{identifier} is in docs/architecture.md but not on "
                    f"no_time_to_die.{stem}"
                )

    def test_the_inventory_is_not_vacuous(self) -> None:
        assert len(_inventory_rows(_DOC.read_text(encoding="utf-8"))) >= 6

    def test_parse_detects_a_fabricated_identifier(self, tmp_path) -> None:
        """Positive control: the parser sees identifiers verbatim, so an
        injected non-existent name would be caught by the resolution test.
        """
        broken = tmp_path / "architecture.md"
        broken.write_text(
            "## The domain modules, individually\n\n"
            "| `toxicology.py` | `fraction_affected`, `not_a_real_function` |\n\n"
            "The intra-package dependency graph\n",
            encoding="utf-8",
        )
        stem, identifiers = _inventory_rows(broken.read_text(encoding="utf-8"))[0]
        assert (stem, identifiers) == ("toxicology", ["fraction_affected", "not_a_real_function"])
        # ... and the resolution assertion on the real module would catch it.
        module = importlib.import_module(f"no_time_to_die.{stem}")
        assert hasattr(module, "fraction_affected")
        assert not hasattr(module, "not_a_real_function")
