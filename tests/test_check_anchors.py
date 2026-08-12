"""Tests for docs/modules/ anchor verification (020-honest-dashboard PKG-2, ADR-0040,
AC-06..AC-11): the grammar's two forms (complete + abbreviated), SC-01's basename
resolution scoped to the checked module's own `paths`, AC-08's bounded semantic check,
the `check-anchors` CLI, and AC-09's never-raises wiring into `sync-notes`.

Every test here uses a synthetic tempdir fixture, never the real docs/modules/*.md --
see the P2 implementer evidence for a run of the real checker against the real repo
(before/after AC-10's fixes). A test that only re-runs the verifier against today's real
docs and expects rc=0 would pass without proving detection; this file instead builds
adversarial docs (moved symbols, out-of-range lines, unresolvable anchors, ambiguous
basenames, and the four real false positives from AC-06/SC-02) and asserts the verifier
catches exactly what it should, in both directions.
"""

from __future__ import annotations

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

from feature_state_lib import check_anchors as ca  # noqa: E402

FEATURE_STATE = ROOT / "PROYECTO/ai/scripts/feature-state.py"

# Predictable fixture source: two functions at known lines (1-indexed), 9 lines total.
FOO_PY = (
    '"""demo module"""\n'
    "\n"
    "\n"
    "def alpha():\n"
    "    return 1\n"
    "\n"
    "\n"
    "def beta(x, y):\n"
    "    return x + y\n"
)


def _run(*args, cwd, check=False):
    return subprocess.run(
        ["python3", str(FEATURE_STATE), *args],
        cwd=cwd, env=os.environ.copy(), text=True, capture_output=True, check=check,
    )


def _scaffold(root: Path, modules_toml: str, doc_body: str, doc_slug: str = "demo",
              extra_files: dict[str, str] | None = None) -> None:
    (root / "src/demo").mkdir(parents=True, exist_ok=True)
    (root / "src/demo/foo.py").write_text(FOO_PY)
    (root / "docs/modules").mkdir(parents=True, exist_ok=True)
    (root / "docs/modules/modules.toml").write_text(modules_toml)
    (root / f"docs/modules/{doc_slug}.md").write_text(doc_body)
    for rel, content in (extra_files or {}).items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


DEMO_TOML = (
    '[module.demo]\n'
    'nombre = "Demo module"\n'
    'responsabilidad = "Cosa de prueba, corta."\n'
    'paths = ["src/demo/**"]\n'
)


class GrammarAndResolutionTests(unittest.TestCase):
    """Direct calls into feature_state_lib.check_anchors -- one behavior per test."""

    def _check(self, doc_body: str, modules_toml: str = DEMO_TOML, **extra_files):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _scaffold(root, modules_toml, doc_body, extra_files=extra_files)
            return ca.check_anchors(root)

    # -- complete form, both correct and broken (AC-11's two required cases) --------

    def test_complete_form_correct_anchor_with_adjacent_symbol_passes(self):
        result = self._check("- `foo.py:4` `alpha()` — la función alpha.\n")
        self.assertTrue(result["ok"], result["broken"])
        self.assertEqual(result["form_counts"]["complete"], 1)

    def test_ac11_moved_symbol_is_reported_broken(self):
        # `beta` really lives at line 8, not 4 -- the "symbol moved" case AC-11 requires.
        result = self._check("- `foo.py:4` `beta()` — la función beta.\n")
        self.assertFalse(result["ok"])
        self.assertEqual(len(result["broken"]), 1)
        self.assertIn("beta", result["broken"][0]["reason"])
        self.assertIn("not found", result["broken"][0]["reason"])

    def test_ac11_out_of_range_line_is_reported_broken(self):
        result = self._check("- `foo.py:9999` — mucho más allá del archivo.\n")
        self.assertFalse(result["ok"])
        self.assertIn("out of range", result["broken"][0]["reason"])

    # -- abbreviated form: same-item resolution and unresolvable-when-unnamed -------

    def test_abbreviated_form_resolves_against_last_named_file_in_same_item(self):
        result = self._check(
            "- `foo.py` — `alpha()` (`:4`) y también `beta(x, y)` (`:8`).\n"
        )
        # both `:4` and `:8` resolve against the bare `foo.py` named earlier in the item
        self.assertTrue(result["ok"], result["broken"])
        self.assertGreaterEqual(result["form_counts"]["abbreviated"], 2)

    def test_abbreviated_form_with_adjacent_symbol_resolves_and_checks_semantically(self):
        result = self._check("- `foo.py` `:8` `beta(x, y)` — la función beta.\n")
        self.assertTrue(result["ok"], result["broken"])

    def test_abbreviated_form_unresolvable_with_no_file_named_in_item_is_broken(self):
        result = self._check("- sin nombrar ningún archivo, viene `:4` suelto.\n")
        self.assertFalse(result["ok"])
        self.assertIn("unresolvable", result["broken"][0]["reason"])
        self.assertEqual(result["broken"][0]["form"], "abbreviated")

    def test_new_list_item_resets_context_even_after_a_prior_item_named_a_file(self):
        # SC-02: resolution is scoped to "the same list item or paragraph" -- a NEW
        # bullet must not silently inherit the previous bullet's file.
        result = self._check(
            "- `foo.py:4` `alpha()` — primer ítem, nombra el archivo.\n"
            "- acá no se nombra nada y aparece `:8` suelto.\n"
        )
        self.assertFalse(result["ok"])
        broken_lines = {r["line"] for r in result["broken"]}
        self.assertEqual(broken_lines, {2})
        self.assertIn("unresolvable", result["broken"][0]["reason"])

    def test_blank_line_also_resets_context(self):
        result = self._check(
            "`foo.py:4` `alpha()` primer párrafo.\n"
            "\n"
            "segundo párrafo con `:8` suelto.\n"
        )
        self.assertFalse(result["ok"])
        self.assertIn("unresolvable", result["broken"][0]["reason"])

    # -- ranges: resolution + bounds only, semantic check explicitly excluded (AC-08) -

    def test_range_anchor_in_bounds_passes_even_with_a_wrong_adjacent_symbol(self):
        # AC-08 explicitly excludes ranges from the semantic check -- `beta` is wrong for
        # lines 4-5, but a range anchor never gets that check, only resolution+bounds.
        result = self._check("- `foo.py:4-5` `beta()` — rango, no se verifica el símbolo.\n")
        self.assertTrue(result["ok"], result["broken"])

    def test_range_anchor_out_of_bounds_is_broken(self):
        result = self._check("- `foo.py:8-20` — el archivo no tiene 20 líneas.\n")
        self.assertFalse(result["ok"])
        self.assertIn("out of range", result["broken"][0]["reason"])

    # -- AC-08's other explicit exclusions: wildcards and prose-separated symbols ----

    def test_wildcarded_adjacent_symbol_is_never_semantically_checked(self):
        # `alpha_*` cannot be a real identifier (contains `*`); the adjacency regex
        # simply never matches it, so this falls back to resolution+range only and
        # passes regardless of what "alpha_*" would mean.
        result = self._check("- `foo.py:4` `alpha_*` — comodín, no es un símbolo real.\n")
        self.assertTrue(result["ok"], result["broken"])

    def test_symbol_separated_from_anchor_by_prose_is_not_semantically_checked(self):
        # `wrongname` does not exist anywhere in foo.py, but it is separated from the
        # anchor by prose ("es la función"), so AC-08 never looks at it.
        result = self._check("- `foo.py:4` es la función `wrongname()` — no adyacente.\n")
        self.assertTrue(result["ok"], result["broken"])

    def test_prose_connector_lets_a_genuinely_false_claim_about_a_real_symbol_pass(self):
        # F-02 (repair): stronger than the prior test -- `alpha` IS a real symbol in
        # foo.py, just not the one at line 8 (`beta` is). The connector "es" still
        # disables the adjacency check entirely, so this genuinely false claim passes
        # (`ok=True`, rc=0) exactly as the module docstring of `_adjacent_symbol` and
        # ADR-0040 sect. 5 now document explicitly.
        result = self._check("- `foo.py:8` es `alpha()` — línea de beta, no de alpha.\n")
        self.assertTrue(result["ok"], result["broken"])

    # -- SC-01: basename resolution scoped to the checked module's own paths --------

    def test_zero_matches_inside_module_paths_is_broken_even_if_the_file_exists_elsewhere(self):
        toml = (
            '[module.demo]\n'
            'nombre = "Demo module"\n'
            'responsabilidad = "Cosa de prueba, corta."\n'
            'paths = ["src/demo/**"]\n'
            '[module.other]\n'
            'nombre = "Other module"\n'
            'responsabilidad = "Cosa de prueba, corta."\n'
            'paths = ["src/other/**"]\n'
        )
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _scaffold(root, toml, "- `bar.py:1` — no pertenece a `demo`.\n")
            (root / "src/other").mkdir(parents=True, exist_ok=True)
            (root / "src/other/bar.py").write_text("x = 1\n")
            result = ca.check_anchors(root, only_module="demo")
        self.assertFalse(result["ok"])
        self.assertIn("no file named", result["broken"][0]["reason"])

    def test_zero_matches_reason_names_the_cross_module_citation_possibility(self):
        # F-01 (repair): a static hint, not a global search (that would violate SC-01).
        # `bar.py` genuinely exists, just in a different module's `paths` -- the message
        # must not claim flatly "no file named" as if the file did not exist anywhere; it
        # must name the cross-module-citation possibility and point at ADR-0040 sect. 5,
        # the same case AC-10 fixed by hand for routing.md/narracion-notas.md.
        toml = (
            '[module.demo]\n'
            'nombre = "Demo module"\n'
            'responsabilidad = "Cosa de prueba, corta."\n'
            'paths = ["src/demo/**"]\n'
            '[module.other]\n'
            'nombre = "Other module"\n'
            'responsabilidad = "Cosa de prueba, corta."\n'
            'paths = ["src/other/**"]\n'
        )
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _scaffold(root, toml, "- `bar.py:1` — no pertenece a `demo`.\n")
            (root / "src/other").mkdir(parents=True, exist_ok=True)
            (root / "src/other/bar.py").write_text("x = 1\n")
            result = ca.check_anchors(root, only_module="demo")
        reason = result["broken"][0]["reason"]
        self.assertIn("cross-module", reason)
        self.assertIn("ADR-0040", reason)

    def test_ambiguous_basename_inside_module_paths_is_broken(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _scaffold(root, DEMO_TOML, "- `foo.py:1` — ambiguo.\n")
            (root / "src/demo/sub").mkdir(parents=True, exist_ok=True)
            (root / "src/demo/sub/foo.py").write_text(FOO_PY)  # second foo.py, same module
            result = ca.check_anchors(root)
        self.assertFalse(result["ok"])
        self.assertIn("ambiguous basename", result["broken"][0]["reason"])

    # -- false positives, both directions (AC-06/SC-02) ------------------------------

    def test_false_positives_produce_zero_anchors_and_never_appear_broken(self):
        doc = (
            "- server local en `localhost:8080`, cita a las `12:30`, "
            "endpoint `http://x:80` y rango `10-20` — nada de esto es un ancla.\n"
        )
        result = self._check(doc)
        self.assertTrue(result["ok"], result["broken"])
        self.assertEqual(result["anchor_count"], 0)

    def test_false_positives_do_not_hide_a_real_broken_anchor_in_the_same_doc(self):
        # Both directions in one doc: the four false positives must stay silent AND the
        # one genuine broken anchor must still surface.
        doc = (
            "- server en `localhost:8080` y cita `12:30`, ver `http://x:80`, rango `10-20`.\n"
            "- `foo.py:9999` — esta sí es una ancla rota de verdad.\n"
        )
        result = self._check(doc)
        self.assertFalse(result["ok"])
        self.assertEqual(result["anchor_count"], 1)
        self.assertIn("out of range", result["broken"][0]["reason"])

    # -- both forms genuinely covered, not just the obvious one ----------------------

    def test_both_forms_are_counted_not_just_the_complete_one(self):
        result = self._check(
            "- `foo.py:4` `alpha()` completa, y `:8` `beta(x, y)` abreviada.\n"
        )
        self.assertTrue(result["ok"], result["broken"])
        self.assertGreaterEqual(result["form_counts"]["complete"], 1)
        self.assertGreaterEqual(result["form_counts"]["abbreviated"], 1)

    def test_opt_in_no_modules_toml_is_ok_with_nothing_checked(self):
        with tempfile.TemporaryDirectory() as td:
            result = ca.check_anchors(Path(td))
        self.assertTrue(result["ok"])
        self.assertEqual(result["checked_docs"], [])
        self.assertEqual(result["anchor_count"], 0)


class CliCheckAnchorsTests(unittest.TestCase):
    def test_cli_rc0_and_ok_true_when_clean(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _scaffold(root, DEMO_TOML, "- `foo.py:4` `alpha()` — ok.\n")
            proc = _run("check-anchors", cwd=root)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("ANCHORS_OK", proc.stdout)

    def test_cli_rc_nonzero_and_prints_broken_anchor_with_doc_line_and_reason(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _scaffold(root, DEMO_TOML, "- `foo.py:9999` — rota.\n")
            proc = _run("check-anchors", cwd=root)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("ANCHOR_BROKEN", proc.stdout)
        self.assertIn("docs/modules/demo.md:1", proc.stdout)
        self.assertIn("out of range", proc.stdout)

    def test_cli_module_filter_checks_only_that_module(self):
        toml = DEMO_TOML + (
            '\n[module.second]\n'
            'nombre = "Second"\n'
            'responsabilidad = "Otra, corta."\n'
            'paths = ["src/second/**"]\n'
        )
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _scaffold(root, toml, "- `foo.py:4` `alpha()` — ok.\n")
            (root / "src/second").mkdir(parents=True)
            (root / "src/second/bad.py").write_text("x = 1\n")
            (root / "docs/modules/second.md").write_text("- `bad.py:9999` — rota, pero filtrada afuera.\n")
            proc_all = _run("check-anchors", cwd=root)
            proc_demo = _run("check-anchors", "--module", "demo", cwd=root)
        self.assertNotEqual(proc_all.returncode, 0)  # second.md's break is visible unscoped
        self.assertEqual(proc_demo.returncode, 0)  # scoped to demo: clean
        self.assertIn('"demo.md"', proc_demo.stdout)
        self.assertNotIn("second.md", proc_demo.stdout)

    def test_cli_unknown_module_is_a_clean_error_not_a_traceback(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _scaffold(root, DEMO_TOML, "- `foo.py:4` `alpha()` — ok.\n")
            proc = _run("check-anchors", "--module", "nope", cwd=root)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("unknown module slug", proc.stdout)

    def test_cli_never_mutates_the_docs_it_checks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            body = "- `foo.py:4` `alpha()` — ok.\n"
            _scaffold(root, DEMO_TOML, body)
            before = (root / "docs/modules/demo.md").read_bytes()
            _run("check-anchors", cwd=root)
            after = (root / "docs/modules/demo.md").read_bytes()
        self.assertEqual(before, after)


class SyncNotesNeverRaisesTests(unittest.TestCase):
    """AC-09: check-anchors is advisory (spec no-goal: never a gate). sync-notes must
    finish and still print NOTES_SYNCED even when the checker itself blows up."""

    def _scaffold_state(self, root: Path) -> Path:
        state = root / "ai/state/features/feat.json"
        state.parent.mkdir(parents=True)
        state.write_text(json.dumps({
            "feature_id": "feat", "phase": "PACKAGE_PLANNING", "packages": [],
            "history": [], "blockers": [], "updated_at": "2026-08-10T10:00:00",
        }))
        return state

    @staticmethod
    def _import_feature_state():
        # feature-state.py injects model.render_notes/record_event/mutate as a side
        # effect of import (same pattern tests/test_harness.py uses via its own
        # `_import` helper) -- cli_reporting.cmd_sync_notes needs that injection to have
        # already happened, since it calls model.render_notes directly.
        import importlib.util
        spec = importlib.util.spec_from_file_location("feature-state", ROOT / "ai/scripts/feature-state.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_sync_notes_completes_when_check_anchors_raises(self):
        self._import_feature_state()
        from feature_state_lib import cli_reporting

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._scaffold_state(root)
            cwd = os.getcwd()
            os.chdir(root)
            try:
                with mock.patch(
                    "feature_state_lib.check_anchors.check_anchors",
                    side_effect=RuntimeError("boom"),
                ):
                    args = mock.Mock(state_dir=None, notes_dir=None, project_name=None)
                    with mock.patch("builtins.print") as mocked_print:
                        rc = cli_reporting.cmd_sync_notes(args)
            finally:
                os.chdir(cwd)
        self.assertEqual(rc, 0)
        printed = " ".join(str(c) for c in mocked_print.call_args_list)
        self.assertIn("NOTES_SYNCED", printed)

    def test_warn_helper_never_raises_and_reports_broken_anchors_on_stderr(self):
        from feature_state_lib.cli_reporting import _warn_check_anchors_never_raises
        import io, contextlib

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            state_dir = root / "ai/state"
            (state_dir / "features").mkdir(parents=True)
            _scaffold(root, DEMO_TOML, "- `foo.py:9999` — rota.\n")
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                _warn_check_anchors_never_raises(state_dir)  # must not raise
        self.assertIn("ANCHORS_WARN", err.getvalue())
        self.assertIn("out of range", err.getvalue())


if __name__ == "__main__":
    unittest.main()
