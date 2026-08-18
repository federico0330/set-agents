# PKG-2 repair (F-PKG2-01, F-PKG2-02)

## Bite (`cp`, never git restore/checkout/stash)

force_refresh-only: `test_stale_cache_auto_probes_after_first_paint_not_before` RED
`AssertionError: 0 not greater than or equal to 1`

auto-probe ON + `live_discovered=None`: `test_auto_live_measure_fills_live_discovered_not_probe_failed` RED
`AssertionError: 'probe falló' unexpectedly found in "...auto → no verificable ahora (probe falló..."`

`cp /tmp/pkg2-repair/setup_models.py.green ai/scripts/setup_models.py` → both GREEN (`Ran 2 tests in 0.037s OK`)

## Gates

`python3 -m unittest` (listed PKG-2 modules): `Ran 38 tests in 3.057s OK`
`./build.sh --check`: `BUILD_CHECK_PASS`
`git diff --check`: exit 0
`git diff --numstat 28dd891770b5c2a10faf612661caae09cfbf6164`: 193 WT (staged repair 121)
