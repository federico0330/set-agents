# D4 runtime QA — AC09/AC10/AC11

```json
{
  "result": "PASS",
  "base": "bbed1d3",
  "scenarios": [
    {
      "id": "A",
      "command": "python3 ai/scripts/install.py --staging Global --home <tmp-home-a> --target opencode",
      "exit": 0,
      "output": "INSTALL_PASS backup=<tmp-home-a>/.local/state/set-agentes/backups/<id>",
      "before": "virgin temporary home; no lane artifacts",
      "after": "only .config/opencode plus installer state; .claude, .codex and .pi absent",
      "verdict": "AC09 PASS"
    },
    {
      "id": "B",
      "command": "python3 ai/scripts/install.py --home <tmp-home-a> --target opencode --uninstall",
      "exit": 0,
      "output": "UNINSTALL_REMOVED=.config/opencode/...; UNINSTALL_DEMERGED=.config/opencode/opencode.json; UNINSTALL_PASS backup=<tmp-home-a>/.local/state/set-agentes/backups/<id>",
      "before": "A ownership snapshot: opencode managed files present; other lanes absent",
      "after": "opencode managed files removed/demerged; other lanes remained absent/untouched",
      "verdict": "AC10 PASS"
    },
    {
      "id": "C",
      "command": "HOME=<tmp-home-c> PATH=<shim-bin>:$PATH python3 ai/scripts/set_agents_app.py --virgin claude -- --version",
      "exit": 0,
      "output": "VIRGIN_SESSION cli=claude home=temporary xdg=isolated; SHIM_VIRGIN_OK; VIRGIN_SESSION_DONE cli=claude exit=0",
      "before": "<tmp-home-c> has a real four-lane install; hashes of .claude/.config/opencode/.codex/.pi are captured",
      "after": "the shim observed a fresh HOME plus CONFIG/DATA/STATE/CACHE/RUNTIME XDG roots below it; every installed-tree hash and the .claude marker stayed identical; the disposable root was removed",
      "verdict": "AC11 PASS"
    }
  ],
  "git_artifact_proof": {
    "head": "3b2324f",
    "preexisting_changes_preserved": true,
    "runtime_artifact_paths": "temporary homes only (<tmp-home-a>, <tmp-home-c>)",
    "source_tree_or_real_home_modified": false
  }
}
```
