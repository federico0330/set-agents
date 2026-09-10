# PKG-D2 / feature 049 — adversarial judge HDR

- **Verdict:** JUDGE_FAIL
- **J-049-001:** AC-09 requires `./ai/scripts/verify.sh` rc=0; isolated C2+D2 candidate cannot pass while uncommitted 045–048 sibling work remains out of the candidate. Overlaying dirty root tests onto C2 tip produced 500+ failures (tests expect 045–048 product).
- **J-049-002:** Contractual quartet missing from C2/D2 commits; hash `sha256:47923adc…` computed from root where docs exist.
- **Already green:** focused 049 unittests (19), build `--check`, D2 ownership, hermetic TTY runtime QA, C2 accepted with repair waivers.
- **Human options:** amend AC-09 / integrate 045–048 first / explicit verify waiver for close.

