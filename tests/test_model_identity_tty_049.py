"""049 PKG-D2 / AC-09 — isolated TTY observation without data retention."""

import json
import os
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai/scripts"))


def _minimal_sanitized_env(*, home: Path, state: Path, bindir: Path) -> dict[str, str]:
    """Hermetic env: no host inheritance, PATH is exactly the fake bin directory."""
    return {
        "HOME": str(home),
        "SET_AGENTS_STATE": str(state),
        "PATH": str(bindir),
    }


def _write_fake_opencode_11814(bindir: Path, project: Path, *, last_model=("opaque", "luna"), marker: Path | None = None):
    """Allow-listed OpenCode 1.18.14 observation surface only — no auth/install."""
    provider, model_id = last_model
    canonical = str(project.resolve())
    marker_line = f'MARKER = {str(marker)!r}' if marker else "MARKER = None"
    script = bindir / "opencode"
    script.write_text(
        textwrap.dedent(
            f"""\
            #!{sys.executable}
            import json, sys
            from pathlib import Path
            PROJECT = {canonical!r}
            {marker_line}
            FORBIDDEN = {{"auth", "login", "install"}}
            if len(sys.argv) >= 2 and sys.argv[1] in FORBIDDEN:
                print("forbidden command", file=sys.stderr)
                raise SystemExit(1)
            if sys.argv[1:] == ["session", "list", "--format", "json", "--pure"]:
                if MARKER is not None:
                    Path(MARKER).write_text("fake-invoked", encoding="utf-8")
                print(json.dumps([{{
                    "id": "root-private-id",
                    "directory": PROJECT,
                    "parentID": None,
                    "time": {{"updated": 1770000002000}},
                }}]))
                raise SystemExit(0)
            if len(sys.argv) == 5 and sys.argv[1:4] == ["export", "--sanitize", "--pure"] and sys.argv[4]:
                if MARKER is not None:
                    Path(MARKER).write_text("fake-invoked", encoding="utf-8")
                print(json.dumps({{
                    "info": {{"id": "root-private-id"}},
                    "messages": [{{
                        "info": {{
                            "id": "msg-luna-private",
                            "role": "user",
                            "time": {{"created": 1770000020000}},
                            "model": {{"providerID": {provider!r}, "modelID": {model_id!r}}},
                        }},
                        "parts": [{{"text": "secret prompt must never persist"}}],
                    }}],
                }}))
                raise SystemExit(0)
            print("unsupported", file=sys.stderr)
            raise SystemExit(1)
            """
        ),
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return script


def _write_hostile_opencode(bindir: Path, *, marker: Path) -> Path:
    """Trap binary that records host/cwd invocation — must never run under sanitized PATH."""
    script = bindir / "opencode"
    script.write_text(
        textwrap.dedent(
            f"""\
            #!{sys.executable}
            from pathlib import Path
            Path({str(marker)!r}).write_text("host-invoked", encoding="utf-8")
            print("host trap", file=__import__("sys").stderr)
            raise SystemExit(99)
            """
        ),
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return script


def _run_fake_opencode(script: Path, argv: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *argv],
        capture_output=True,
        text=True,
        env=env,
    )


class FakeOpenCodeAllowListTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        self.home = root / "home"
        self.state = root / "state"
        self.bin = root / "bin"
        for directory in (self.home, self.state, self.bin):
            directory.mkdir()
        self.env = _minimal_sanitized_env(home=self.home, state=self.state, bindir=self.bin)
        self.script = _write_fake_opencode_11814(self.bin, ROOT)

    def test_exact_session_list_argv_accepted(self):
        result = _run_fake_opencode(
            self.script,
            ["session", "list", "--format", "json", "--pure"],
            self.env,
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_incomplete_session_list_argv_rejected(self):
        for argv in (
            ["session", "list", "--format"],
            ["session", "list"],
            ["session"],
        ):
            with self.subTest(argv=argv):
                result = _run_fake_opencode(self.script, argv, self.env)
                self.assertNotEqual(0, result.returncode)
                self.assertIn("unsupported", result.stderr)

    def test_exact_export_argv_accepted(self):
        result = _run_fake_opencode(
            self.script,
            ["export", "--sanitize", "--pure", "root-private-id"],
            self.env,
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_incomplete_export_argv_rejected(self):
        for argv in (
            ["export"],
            ["export", "--sanitize"],
            ["export", "--sanitize", "--pure"],
        ):
            with self.subTest(argv=argv):
                result = _run_fake_opencode(self.script, argv, self.env)
                self.assertNotEqual(0, result.returncode)
                self.assertIn("unsupported", result.stderr)

    def test_auth_login_install_rejected(self):
        for command in ("auth", "login", "install"):
            with self.subTest(command=command):
                result = _run_fake_opencode(self.script, [command], self.env)
                self.assertNotEqual(0, result.returncode)
                self.assertIn("forbidden command", result.stderr)


class IsolatedTtyObservationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        self.state = root / "state"
        self.home = root / "home"
        self.bin = root / "bin"
        for directory in (self.state, self.home, self.bin):
            directory.mkdir()
        self.env = _minimal_sanitized_env(home=self.home, state=self.state, bindir=self.bin)
        self.assertFalse(self.env["PATH"].endswith(os.pathsep))
        overlay = self.home / ".local/state/set-agentes/models.local.toml"
        overlay.parent.mkdir(parents=True, exist_ok=True)
        overlay.write_text('[areas.coord]\nopencode = "opaque/terra"\n', encoding="utf-8")
        installed = self.home / ".config/opencode/agents/orchestrator.md"
        installed.parent.mkdir(parents=True)
        installed.write_text('---\nmodel: opaque/terra\n---\n', encoding="utf-8")

    def test_refresh_observes_allowlisted_model_without_retaining_private_fields(self):
        import setup_models

        _write_fake_opencode_11814(self.bin, ROOT, last_model=("opaque", "luna"))
        with mock.patch.dict(os.environ, self.env, clear=True):
            state, error = setup_models._refresh_model_state()

        self.assertIsNone(error)
        self.assertEqual("opaque/luna", state["observed"]["model"])
        self.assertEqual("observed", state["observed"]["status"])
        self.assertEqual("opaque/terra", state["desired"]["model"])

        cache_path = self.state / "model-state.json"
        self.assertTrue(cache_path.is_file())
        cached = cache_path.read_text(encoding="utf-8")
        for forbidden in (
            "root-private-id",
            "msg-luna-private",
            "secret prompt must never persist",
            "session_id",
            "messages",
            "parts",
        ):
            self.assertNotIn(forbidden, cached)

    def test_sanitized_path_never_invokes_host_or_cwd_opencode(self):
        import setup_models

        marker = Path(self.temporary.name) / "invocation-marker.txt"
        host_bin = Path(self.temporary.name) / "host-bin"
        cwd_trap = Path(self.temporary.name) / "cwd-trap"
        host_bin.mkdir()
        cwd_trap.mkdir()
        _write_hostile_opencode(host_bin, marker=marker)
        _write_hostile_opencode(cwd_trap, marker=marker)
        _write_fake_opencode_11814(self.bin, ROOT, last_model=("opaque", "luna"), marker=marker)

        self.assertEqual(str(self.bin), self.env["PATH"])
        self.assertNotIn(os.pathsep, self.env["PATH"])

        with mock.patch.dict(os.environ, self.env, clear=True):
            state, error = setup_models._refresh_model_state()

        self.assertIsNone(error)
        self.assertEqual("observed", state["observed"]["status"])
        self.assertEqual("fake-invoked", marker.read_text(encoding="utf-8"))

        # cwd holds a hostile binary, but exact PATH (no trailing colon) keeps fake bin.
        result = subprocess.run(
            ["opencode", "session", "list", "--format", "json", "--pure"],
            cwd=cwd_trap,
            capture_output=True,
            text=True,
            env=self.env,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotEqual("host-invoked", marker.read_text(encoding="utf-8"))

    def test_wizard_actualizar_uses_observation_path_without_auth_or_install(self):
        import setup_models

        _write_fake_opencode_11814(self.bin, ROOT, last_model=("opaque", "luna"))
        config = {
            "runtime": {"primary": "opencode"},
            "areas": {"coord": {"opencode": "opaque/terra"}},
            "roles": {},
        }
        roster = [{"role": "orchestrator", "duty": "coord"}]
        picks = [
            setup_models.tui.Selected(index=2),  # actualizar
            setup_models.tui.Selected(index=3),  # listo
        ]
        with mock.patch.dict(os.environ, self.env, clear=True), \
             mock.patch.object(setup_models.sys.stdin, "isatty", return_value=True), \
             mock.patch.object(setup_models.models_config, "detect_subscriptions", return_value=None), \
             mock.patch.object(setup_models.tui, "with_progress", side_effect=lambda _m, fn, **_k: fn()), \
             mock.patch.object(setup_models, "_load_pins", return_value={}), \
             mock.patch.object(setup_models.tui, "run_picker", side_effect=picks):
            rc = setup_models.wizard(
                config, roster, ROOT / "roles.tsv", ROOT / "models.toml",
            )

        self.assertEqual(0, rc)
        cache_path = self.state / "model-state.json"
        self.assertTrue(cache_path.is_file())
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
        self.assertEqual("opaque/luna", payload["observed"]["model"])
        self.assertNotIn("root-private-id", json.dumps(payload))

    def test_absent_opencode_degrades_with_closed_reason_and_no_side_effects(self):
        import setup_models

        overlay_key = ".local/state/set-agentes/models.local.toml"
        before = {
            path.relative_to(self.home).as_posix(): path.read_bytes()
            for path in self.home.rglob("*")
            if path.is_file()
        }
        with mock.patch.dict(os.environ, self.env, clear=True):
            state, error = setup_models._refresh_model_state()

        self.assertIsNone(error)
        self.assertEqual("unobserved", state["observed"]["status"])
        self.assertIn(
            state["observed"]["reason"],
            {"opencode_absent", "child_failed"},
        )
        after = {
            path.relative_to(self.home).as_posix(): path.read_bytes()
            for path in self.home.rglob("*")
            if path.is_file()
        }
        self.assertEqual(before.get(overlay_key), after.get(overlay_key))


class TtyPanelPresentationTests(unittest.TestCase):
    def test_model_panel_separates_observed_luna_from_neutral_terra_default(self):
        import setup_models

        state = {
            "observed": {
                "model": "opaque/luna",
                "source": "opencode-sanitized-export",
                "reason": None,
            },
            "desired": {
                "model": "opaque/terra",
                "source": "set-effective-config",
                "reason": None,
            },
            "installed": {
                "model": "opaque/terra",
                "source": "installed-role-artifact",
                "reason": None,
            },
            "routing": {
                "status": "dynamic",
                "source": "model-preference.toml",
                "reason": None,
            },
            "convergence": {"status": "applied"},
            "refresh": {},
        }
        text = "\n".join(setup_models._model_state_lines(state))
        self.assertIn("Último envío observado", text)
        self.assertIn("opaque/luna", text)
        self.assertIn("Default de SET", text)
        self.assertIn("opaque/terra", text)
        self.assertIn("/model es una elección temporal", text)
        self.assertNotIn("modelo actual", text.lower())


if __name__ == "__main__":
    unittest.main()
