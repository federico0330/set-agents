# 049 — adversarial judge reopen after option 2

- **Integrated tip:** `5076dd27e997451ef0a2b10aad5434d0dd6d738d`
- **Prior FAIL:** J-049-001 (verify red on isolated C2+D2), J-049-002 (quartet absent from candidate).
- **Remediation:** User chose option 2 — commit 045–048 (+049 delivery) as one integrated tree; factory `models.toml` leaves `discovered_providers` absent (`auto`); seven verify fails fixed.
- **Contract hash on tip:** `sha256:47923adc4a83d40a78edd210aedf91959397e97d319d9d64f406258a07813278`
- **Verify:** `VERIFY_PASS` on tip (debugger re-run after fixes).
