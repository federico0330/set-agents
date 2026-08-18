"""Tests for docs/modules/ (019-harness-evolution PKG-3, ADR-0036, AC-17..AC-24):
modules.toml fail-closed parsing, the render_modules.py never-raises/atomic engine
reusing render_notes's merge_note/write_note/_short, record-module-impact/
module-impact-detect, the INTEGRATION gate and its cheap waiver, and the digest's
"Qué cambió en el software" section. New coverage only -- never edits to
tests/test_harness.py or tests/test_routing.py (test_harness.py's own two INTEGRATION
happy-path tests are updated separately, in-place, to declare the new waiver -- see
ADR-0036).
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai/scripts"))

from feature_state_lib import render_modules as rm  # noqa: E402
from feature_state_lib.model import done_ready, module_impacts_ready  # noqa: E402

import tests

FEATURE_STATE = ROOT / "PROYECTO/ai/scripts/feature-state.py"

DEMO_TOML = (
    '[module.demo]\n'
    'nombre = "Demo module"\n'
    'responsabilidad = "Cosa de prueba, corta."\n'
    'paths = ["src/demo/**"]\n'
)


def _run(*args, cwd, check=True):
    tests.require_posix_toolchain()
    return subprocess.run(
        ["python3", str(FEATURE_STATE), *args],
        cwd=cwd, env=os.environ.copy(), text=True, capture_output=True, check=check,
    )


def _axes_log(root: Path, feature_id: str) -> Path:
    axes_log = root / "ai/state/axes-log.jsonl"
    axes_log.parent.mkdir(parents=True, exist_ok=True)
    axes_rows = [
        {"at": "2026-08-15T00:00:00Z", "feature_id": feature_id, "axis": axis,
         "stance": "deferred", "origin": "n/a", "reason": "not decided yet"}
        for axis in ("data-store", "api-gateway", "deploy-platform", "audience", "embeddings",
                     "realtime", "mobile", "auth", "cost", "legal")
    ]
    axes_log.write_text("\n".join(json.dumps(row, sort_keys=True) for row in axes_rows) + "\n")
    return axes_log


def _init_ready_package(root: Path) -> Path:
    """A package driven to PACKAGE_ACCEPTED via the real CLI, owned_paths matching
    modules.toml's demo module glob."""
    state = root / "ai/state/features/feat.json"
    spec = root / "feat-spec.md"
    spec.write_text("# contract\n")
    digest = hashlib.sha256(spec.read_bytes()).hexdigest()
    axes_log = _axes_log(root, "feat")
    _run("init", "feat", str(spec), digest, "--state-file", str(state), "--approved-by", "test",
         "--axes-log", str(axes_log), cwd=root)
    _run("create-package", "PKG-01", "objective", "--state-file", str(state),
         "--ac", "AC-1", "--task", "T1", "--task", "T2", "--complexity", "medium",
         "--owned-path", "src/demo/**", "--actor", "test", cwd=root)
    _run("transition", "PACKAGE_IMPLEMENTATION", "--package-id", "PKG-01",
         "--state-file", str(state), "--actor", "test", cwd=root)
    for tid in ("T1", "T2"):
        _run("complete-task", "PKG-01", tid, "--validation", "focused-test",
             "--state-file", str(state), "--actor", "implementer", cwd=root)
    _run("transition", "PACKAGE_GATES", "--package-id", "PKG-01",
         "--state-file", str(state), "--actor", "test", cwd=root)
    _run("record-gate", "package verify", "pass", "--package-id", "PKG-01", "--evidence", "ok",
         "--state-file", str(state), "--actor", "test", cwd=root)
    _run("update-package", "PKG-01", "--integrated", "true", "--diff-ref", "HEAD..work",
         "--state-file", str(state), "--actor", "test", cwd=root)
    _run("transition", "PACKAGE_REVIEW", "--package-id", "PKG-01",
         "--state-file", str(state), "--actor", "test", cwd=root)
    _run("record-review", "PKG-01", "pass", "--actor", "package-reviewer", "--state-file", str(state), cwd=root)
    _run("record-testing", "PKG-01", "pass", "--actor", "gate-runner", "--command", "verify",
         "--state-file", str(state), cwd=root)
    _run("record-runtime-qa", "PKG-01", "pass", "--actor", "runtime-verifier", "--url", "http://x",
         "--browser", "playwright", "--check", "works", "--state-file", str(state), cwd=root)
    _run("accept-package", "PKG-01", "--actor", "orchestrator", "--state-file", str(state), cwd=root)
    return state


def _scaffold(root: Path, toml_body: str = DEMO_TOML) -> None:
    (root / "docs/modules").mkdir(parents=True, exist_ok=True)
    (root / "docs/modules/modules.toml").write_text(toml_body)


class ModulesTomlParsingTests(unittest.TestCase):
    def test_valid_toml_parses(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "modules.toml"
            path.write_text(DEMO_TOML)
            modules = rm.load_modules_toml(path)
            self.assertEqual(modules["demo"]["nombre"], "Demo module")
            self.assertEqual(modules["demo"]["paths"], ["src/demo/**"])

    def test_absent_file_is_empty_not_an_error(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(rm.load_modules_toml(Path(td) / "nope.toml"), {})

    def test_unknown_key_is_a_fail_closed_error(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "modules.toml"
            path.write_text('[module.demo]\nnombre = "x"\nresponsabilidad = "y"\npaths = ["a"]\nextra = "nope"\n')
            with self.assertRaises(rm.ModulesTomlError) as ctx:
                rm.load_modules_toml(path)
            self.assertIn("unknown key", str(ctx.exception))

    def test_malformed_slug_is_a_fail_closed_error(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "modules.toml"
            path.write_text('[module."Bad Slug"]\nnombre = "x"\nresponsabilidad = "y"\npaths = ["a"]\n')
            with self.assertRaises(rm.ModulesTomlError):
                rm.load_modules_toml(path)

    def test_empty_paths_list_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "modules.toml"
            path.write_text('[module.demo]\nnombre = "x"\nresponsabilidad = "y"\npaths = []\n')
            with self.assertRaises(rm.ModulesTomlError):
                rm.load_modules_toml(path)

    def test_matching_modules_globs_span_slashes_like_notes_owned_paths(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "modules.toml"
            path.write_text(DEMO_TOML)
            modules = rm.load_modules_toml(path)
            hits = rm.matching_modules(["src/demo/deep/nested/file.py"], modules)
            self.assertEqual(hits, ["demo"])
            self.assertEqual(rm.matching_modules(["other/file.py"], modules), [])

    def test_unmatched_candidate_paths_reports_orphans_only(self):
        """F-06 (P3 review): unit-level check of the helper `module-impact-detect` uses."""
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "modules.toml"
            path.write_text(DEMO_TOML)
            modules = rm.load_modules_toml(path)
            paths = ["src/demo/a.py", "src/orphan/b.py", "src/demo/c.py"]
            self.assertEqual(rm.unmatched_candidate_paths(paths, modules), ["src/orphan/b.py"])
            self.assertEqual(rm.unmatched_candidate_paths(["src/demo/a.py"], modules), [])


class RenderModuleDocMergeTests(unittest.TestCase):
    """AC-23: the machine block regenerates; the human zone survives a round trip."""

    def test_idempotent_merge_and_human_zone_survives_a_round_trip(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "demo.md"
            entry = {"nombre": "Demo module", "responsabilidad": "Cosa de prueba.", "paths": ["src/demo/**"]}
            changes = [{"at": "2026-08-10T10:00:00", "feature_id": "feat", "package_id": "PKG-01", "cambio": "primer cambio"}]
            changed = rm.render_module_doc(path, "demo", entry, changes)
            self.assertTrue(changed)
            first = path.read_text(encoding="utf-8")
            self.assertIn("<!-- notas:auto -->", first)
            self.assertIn("primer cambio", first)
            for section in rm.HUMAN_SCAFFOLD_SECTIONS:
                self.assertIn(f"## {section}", first)

            # Re-rendering the SAME data is a true no-op (write_note's own contract).
            self.assertFalse(rm.render_module_doc(path, "demo", entry, changes))
            self.assertEqual(path.read_text(encoding="utf-8"), first)

            # A human edits the human-owned zone (below the marker) by hand.
            edited = first.replace(
                "## Puntos de entrada\n\n_(completar)_\n",
                "## Puntos de entrada\n\n`demo.main()` es el único punto de entrada real.\n",
            )
            path.write_text(edited, encoding="utf-8")

            # A NEW impact triggers a re-render.
            changes2 = changes + [{"at": "2026-08-11T10:00:00", "feature_id": "feat", "package_id": "PKG-01", "cambio": "segundo cambio"}]
            self.assertTrue(rm.render_module_doc(path, "demo", entry, changes2))
            second = path.read_text(encoding="utf-8")
            self.assertIn("segundo cambio", second)
            self.assertIn("primer cambio", second)  # capped list, both still fit under 10
            # The human edit survived the re-render byte-for-byte.
            self.assertIn("`demo.main()` es el único punto de entrada real.", second)

    def test_recent_changes_are_capped_at_ten_most_recent_first(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "demo.md"
            entry = {"nombre": "Demo module", "responsabilidad": "x", "paths": ["src/demo/**"]}
            changes = [
                {"at": f"2026-08-{i:02d}T00:00:00", "feature_id": "feat", "package_id": "PKG-01", "cambio": f"cambio-{i}"}
                for i in range(1, 13)
            ]
            # render_modules() itself sorts most-recent-first before slicing; render_module_doc
            # trusts its caller's ordering, so pass it pre-sorted here.
            changes.sort(key=lambda c: c["at"], reverse=True)
            rm.render_module_doc(path, "demo", entry, changes)
            text = path.read_text(encoding="utf-8")
            self.assertIn("cambio-12", text)
            self.assertIn("cambio-3", text)
            self.assertNotIn("cambio-2\n", text)
            self.assertNotIn("cambio-1\n", text)


class RenderModuleDocInjectionTests(unittest.TestCase):
    """F-03 (P3 repair): feature_id/package_id from module_impacts are state-sourced, not
    schema-validated, and land inside the machine block on every render -- they must be
    neutralized by `_short` exactly like every other agent-authored field, or a crafted
    package_id can inject a fake heading/arbitrary content that survives every
    regeneration."""

    def test_a_newline_carrying_package_id_cannot_inject_a_fake_heading(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "demo.md"
            entry = {"nombre": "Demo module", "responsabilidad": "Cosa de prueba.", "paths": ["src/demo/**"]}
            malicious_package_id = "PKG-01\n\n## Invariantes\n\nEsto no lo escribió nadie.\n<!-- notas:auto -->"
            changes = [{
                "at": "2026-08-10T10:00:00",
                "feature_id": "feat\n<!-- injected -->",
                "package_id": malicious_package_id,
                "cambio": "cambio legítimo",
            }]
            rm.render_module_doc(path, "demo", entry, changes)
            text = path.read_text(encoding="utf-8")
            # No raw newline from the malicious field survived inside the rendered line --
            # _short collapses whitespace, so the fake "## Invariantes" heading and the
            # forged "<!-- notas:auto -->" terminator never appear as their own lines.
            self.assertNotIn("\n## Invariantes\n\nEsto no lo escribió nadie.\n", text)
            self.assertIn("PKG-01 ## Invariantes Esto no lo escribió nadie.", text)
            # The forged notas:auto terminator was neutralized (<!-- / --> replaced), so it
            # can never be mistaken for the real marker that delimits the machine block.
            self.assertEqual(text.count("<!-- notas:auto -->"), 1)
            self.assertIn("‹!-- injected --›", text)


class RenderModulesNeverRaisesTests(unittest.TestCase):
    def test_render_modules_never_raises_and_logs_the_failure(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            state = root / "ai/state/features/feat.json"
            state.parent.mkdir(parents=True)
            state.write_text(json.dumps({
                "feature_id": "feat", "phase": "PACKAGE_ACCEPTED",
                "packages": [{
                    "package_id": "PKG-01", "status": "accepted", "owned_paths": ["src/demo/**"],
                    "module_impacts": [{"module": "demo", "cambio": "x", "at": "2026-08-10T10:00:00",
                                        "feature_id": "feat", "package_id": "PKG-01"}],
                }],
                "history": [], "blockers": [], "updated_at": "2026-08-10T10:00:00",
            }))
            _scaffold(root)
            with mock.patch.object(rm, "render_module_doc", side_effect=RuntimeError("boom")):
                written = rm.render_modules(state)  # never raises
            self.assertEqual(written, [])
            log_file = root / "ai/state/render-failures.log"
            self.assertTrue(log_file.exists())
            log_text = log_file.read_text()
            self.assertIn("module=demo", log_text)
            self.assertIn("RuntimeError: boom", log_text)

    def test_no_ai_state_marker_means_no_render_no_failure(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            state = root / "feat.json"  # not under ai/state/features/
            state.write_text(json.dumps({"feature_id": "feat", "packages": []}))

            # F-05 repair evidence (P3 review): assert the "ai/state/ marker" check
            # directly, not only the observable no-op behaviour it is supposed to cause.
            # The previous version of this test only asserted the latter, and the
            # absent-toml fallback (`load_modules_toml` on a missing path -> `{}`) made
            # `render_modules` return `[]` regardless of whether `modules_toml_path`
            # actually applied the `ai/state/` check at all -- a regression that dropped
            # the check entirely (falling through to `out_dir.parent.parent / "docs" /
            # "modules"`, unconditionally) still made this test pass, because that
            # fallback path also had no modules.toml on disk. Asserting the resolver's
            # own return value closes that hole regardless of what happens to exist on
            # disk at whatever path a broken resolver would guess.
            self.assertIsNone(rm.modules_toml_path(state))

            written = rm.render_modules(state)
            self.assertEqual(written, [])
            self.assertFalse((root / "ai" / "state" / "render-failures.log").exists())

    def test_repo_without_modules_toml_never_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            state = root / "ai/state/features/feat.json"
            state.parent.mkdir(parents=True)
            state.write_text(json.dumps({"feature_id": "feat", "packages": []}))
            written = rm.render_modules(state)  # no docs/modules/modules.toml at all
            self.assertEqual(written, [])
            self.assertFalse((root / "docs" / "modules").exists())

    def test_only_modules_with_impacts_render(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            state = root / "ai/state/features/feat.json"
            state.parent.mkdir(parents=True)
            state.write_text(json.dumps({
                "feature_id": "feat", "phase": "PACKAGE_ACCEPTED",
                "packages": [{"package_id": "PKG-01", "status": "accepted", "owned_paths": []}],
                "history": [], "blockers": [], "updated_at": "2026-08-10T10:00:00",
            }))
            _scaffold(root)
            written = rm.render_modules(state)
            self.assertEqual(written, [])
            self.assertFalse((root / "docs/modules/demo.md").exists())

    def test_force_still_renders_a_module_with_no_impacts(self):
        """D-01 (P3 review, delta cycle 2): a module declared in modules.toml with zero
        recorded impacts must still be reachable by the `force` full-regen pass
        (sync-notes), or the engine can never re-apply a machine-block format change to a
        doc it itself seeded -- e.g. this exact package's F-04 staleness line landed on
        only 2 of 5 docs/modules/*.md because the other 3 had no impacts and `force`
        skipped them exactly like the incremental per-mutation pass does. The incremental
        pass (no `force`) must still skip a module with no impacts -- that half is
        `test_only_modules_with_impacts_render` above."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            state = root / "ai/state/features/feat.json"
            state.parent.mkdir(parents=True)
            state.write_text(json.dumps({
                "feature_id": "feat", "phase": "PACKAGE_ACCEPTED",
                "packages": [{"package_id": "PKG-01", "status": "accepted", "owned_paths": []}],
                "history": [], "blockers": [], "updated_at": "2026-08-10T10:00:00",
            }))
            _scaffold(root)
            written = rm.render_modules(state, force=True)
            self.assertEqual(written, ["demo.md"])
            doc = (root / "docs/modules/demo.md").read_text()
            self.assertIn("sin cambios registrados todavía", doc)
            self.assertIn(rm.STALENESS_NOTICE, doc)


class ModuleImpactCliTests(unittest.TestCase):
    def test_module_impact_detect_lists_candidates_without_mutating(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _scaffold(root)
            state = _init_ready_package(root)
            before = state.read_text()
            result = _run("module-impact-detect", "--package-id", "PKG-01", "--state-file", str(state), cwd=root)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["candidates"], ["demo"])
            self.assertFalse(payload["already_covered"])
            self.assertEqual(payload["unmatched_paths"], [])
            self.assertEqual(state.read_text(), before, "module-impact-detect must never mutate state")

    def test_module_impact_detect_reports_unmatched_paths_advisory_only(self):
        """F-06 (P3 review): a package path that matches no module glob is surfaced as an
        orphan candidate for a NEW modules.toml entry, in its own section, distinct from
        `candidates` -- and never mutates state, since this is advisory only."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _scaffold(root)
            state = root / "ai/state/features/feat.json"
            spec = root / "feat-spec.md"
            spec.write_text("# contract\n")
            digest = hashlib.sha256(spec.read_bytes()).hexdigest()
            axes_log = _axes_log(root, "feat")
            _run("init", "feat", str(spec), digest, "--state-file", str(state), "--approved-by", "test",
                 "--axes-log", str(axes_log), cwd=root)
            _run("create-package", "PKG-01", "objective", "--state-file", str(state),
                 "--ac", "AC-1", "--task", "T1", "--task", "T2", "--complexity", "medium",
                 "--owned-path", "src/demo/**", "--owned-path", "src/orphan/unmatched.py",
                 "--actor", "test", cwd=root)
            before = state.read_text()
            result = _run("module-impact-detect", "--package-id", "PKG-01", "--state-file", str(state), cwd=root)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["candidates"], ["demo"])
            self.assertEqual(payload["unmatched_paths"], ["src/orphan/unmatched.py"])
            self.assertNotIn("src/demo/**", payload["unmatched_paths"])
            self.assertEqual(state.read_text(), before, "module-impact-detect must never mutate state")

    def test_record_module_impact_appends_renders_doc_and_prints_impacto_humano(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _scaffold(root)
            state = _init_ready_package(root)
            result = _run(
                "record-module-impact", "--package-id", "PKG-01",
                "--module", "demo", "--cambio", "se agregó el render de docs/modules",
                "--modelo-mental", "docs/modules/<slug>.md ahora existe y se regenera solo",
                "--state-file", str(state), "--actor", "implementer", cwd=root,
            )
            self.assertIn("Impacto humano:", result.stdout)
            self.assertIn("Módulo: Demo module", result.stdout)
            self.assertIn("Cambio de modelo mental: se agregó el render de docs/modules", result.stdout)
            self.assertIn("Tenés que saber: docs/modules/<slug>.md ahora existe y se regenera solo", result.stdout)
            data = json.loads(state.read_text())
            impacts = data["packages"][0]["module_impacts"]
            self.assertEqual(len(impacts), 1)
            self.assertEqual(impacts[0]["module"], "demo")
            doc = root / "docs/modules/demo.md"
            self.assertTrue(doc.exists())
            self.assertIn("se agregó el render de docs/modules", doc.read_text())

    def test_record_module_impact_rejects_unknown_module_slug(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _scaffold(root)
            state = _init_ready_package(root)
            result = _run(
                "record-module-impact", "--package-id", "PKG-01",
                "--module", "no-existe", "--cambio", "x", "--modelo-mental", "y",
                "--state-file", str(state), "--actor", "implementer", cwd=root, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unknown module slug", result.stdout)

    def test_waiver_is_cheap_mutually_exclusive_and_prints_no_impacto_humano_block(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _scaffold(root)
            state = _init_ready_package(root)
            combo = _run(
                "record-module-impact", "--package-id", "PKG-01", "--module", "demo",
                "--module-impact-waived", "--reason", "x",
                "--state-file", str(state), "--actor", "implementer", cwd=root, check=False,
            )
            self.assertNotEqual(combo.returncode, 0)
            self.assertIn("cannot combine", combo.stdout)

            no_reason = _run(
                "record-module-impact", "--package-id", "PKG-01", "--module-impact-waived",
                "--state-file", str(state), "--actor", "implementer", cwd=root, check=False,
            )
            self.assertNotEqual(no_reason.returncode, 0)
            self.assertIn("requires --reason", no_reason.stdout)

            ok = _run(
                "record-module-impact", "--package-id", "PKG-01", "--module-impact-waived",
                "--reason", "quick-fix trivial, no module doc needed",
                "--state-file", str(state), "--actor", "implementer", cwd=root,
            )
            self.assertNotIn("Impacto humano:", ok.stdout)
            data = json.loads(state.read_text())
            self.assertEqual(
                data["packages"][0]["module_impact_waiver"]["reason"],
                "quick-fix trivial, no module doc needed",
            )


class IntegrationGateTests(unittest.TestCase):
    def test_integration_blocks_without_coverage_and_the_waiver_unblocks_it(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _scaffold(root)
            state = _init_ready_package(root)
            blocked = _run("transition", "INTEGRATION", "--package-id", "PKG-01",
                           "--state-file", str(state), "--actor", "orchestrator", cwd=root, check=False)
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("module impact required", blocked.stdout)
            data = json.loads(state.read_text())
            self.assertNotEqual(data["phase"], "INTEGRATION")

            _run("record-module-impact", "--package-id", "PKG-01", "--module-impact-waived",
                 "--reason", "no real module touched", "--state-file", str(state),
                 "--actor", "orchestrator", cwd=root)
            _run("transition", "INTEGRATION", "--package-id", "PKG-01",
                 "--state-file", str(state), "--actor", "orchestrator", cwd=root)
            data = json.loads(state.read_text())
            self.assertEqual(data["phase"], "INTEGRATION")

    def test_integration_unblocks_with_a_recorded_impact_instead_of_a_waiver(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _scaffold(root)
            state = _init_ready_package(root)
            _run("record-module-impact", "--package-id", "PKG-01", "--module", "demo",
                 "--cambio", "x", "--modelo-mental", "y", "--state-file", str(state),
                 "--actor", "implementer", cwd=root)
            result = _run("transition", "INTEGRATION", "--package-id", "PKG-01",
                          "--state-file", str(state), "--actor", "orchestrator", cwd=root)
            data = json.loads(state.read_text())
            self.assertEqual(data["phase"], "INTEGRATION")

    def test_module_impacts_ready_unit_fixture(self):
        accepted_no_coverage = {"packages": [{"package_id": "P", "status": "accepted"}]}
        self.assertTrue(module_impacts_ready(accepted_no_coverage))
        accepted_with_impact = {"packages": [{"package_id": "P", "status": "accepted",
                                              "module_impacts": [{"module": "demo"}]}]}
        self.assertEqual(module_impacts_ready(accepted_with_impact), [])
        accepted_with_waiver = {"packages": [{"package_id": "P", "status": "accepted",
                                              "module_impact_waiver": {"reason": "x"}}]}
        self.assertEqual(module_impacts_ready(accepted_with_waiver), [])
        superseded_ignored = {"packages": [{"package_id": "P", "status": "superseded"}]}
        self.assertEqual(module_impacts_ready(superseded_ignored), [])

    def test_done_ready_also_checks_module_impacts_as_a_backstop(self):
        data = {
            "packages": [{"package_id": "P", "status": "accepted", "acceptance_criteria": ["AC-1"]}],
            "global_gates": [{"name": "g", "status": "pass", "required": True}],
            "acceptance_criteria": ["AC-1"],
            "blockers": [],
        }
        errors = done_ready(data)
        self.assertTrue(any("module impact" in e for e in errors))
        data["packages"][0]["module_impact_waiver"] = {"reason": "x"}
        self.assertFalse(any("module impact" in e for e in done_ready(data)))


class DigestModuleSectionTests(unittest.TestCase):
    def test_digest_includes_module_changes_in_the_window(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            state_dir = root / "ai/state"
            (state_dir / "features").mkdir(parents=True)
            (state_dir / "features/feat.json").write_text(json.dumps({
                "feature_id": "feat", "phase": "PACKAGE_ACCEPTED", "history": [], "blockers": [],
                "updated_at": "2026-08-10T10:00:00",
                "packages": [{
                    "package_id": "PKG-01", "status": "accepted",
                    "module_impacts": [{
                        "module": "demo", "cambio": "se documentó el módulo demo",
                        "feature_id": "feat", "package_id": "PKG-01", "at": "2026-08-10T09:00:00",
                    }],
                }],
            }))
            result = _run("digest", "--state-dir", str(state_dir), "--since", "2026-08-01T00:00:00", cwd=root)
            self.assertIn("DIGEST_WRITTEN", result.stdout)
            digest_file = root / "docs/notas/BUENOS-DIAS.md"
            text = digest_file.read_text(encoding="utf-8")
            self.assertIn("## Qué cambió en el software", text)
            self.assertIn("se documentó el módulo demo", text)
            self.assertIn("demo", text)


if __name__ == "__main__":
    unittest.main()
