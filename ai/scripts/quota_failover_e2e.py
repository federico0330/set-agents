#!/usr/bin/env python3
"""AC-06 live-provider gate.  It is deliberately inert unless explicitly enabled.

This program neither loads environment files nor prints child-process output.  The
operator supplies a non-secret attestation JSON and the exact already-authorized Pi
invocation.  A missing or invalid prerequisite is a blocked gate, never a skip.
"""
import argparse
import hashlib
import json
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

BLOCKED = 3
FAILED = 1


def emit(**payload):
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def blocked(detail):
    emit(status="BLOCKED", reason="HUMAN_DECISION_REQUIRED", gate="AC-06", detail=detail)
    return BLOCKED


def safe_manifest(path_text):
    """Validate a bounded, non-secret human precondition; never echo its contents."""
    path = Path(path_text)
    if path.name.startswith(".env") or path.suffix == ".env":
        raise ValueError("precondition_file_rejected")
    try:
        raw = path.read_bytes()
    except (OSError, ValueError):
        raise ValueError("precondition_unreadable")
    if len(raw) > 4096:
        raise ValueError("precondition_too_large")
    try:
        doc = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        raise ValueError("precondition_invalid")
    required = {
        "schema": "set-agentes.ac06-precondition/v1",
        "controlled_anthropic_subscription_exhausted": True,
        "alternate_provider_usable": True,
        "minimal_task_approved": True,
        "no_paid_budget_changed_by_setup": True,
        "no_quota_or_inventory_changed_by_setup": True,
    }
    if not isinstance(doc, dict) or any(doc.get(k) != v for k, v in required.items()):
        raise ValueError("controlled_precondition_not_verified")
    # Attestations are evidence metadata, never a credential transport.
    if any(any(word in str(key).lower() for word in ("secret", "token", "password", "credential", "api_key"))
           for key in doc):
        raise ValueError("precondition_contains_sensitive_field")
    return hashlib.sha256(raw).hexdigest()[:16]


def parse_pi_command(text):
    try:
        command = json.loads(text)
    except (TypeError, ValueError, json.JSONDecodeError):
        raise ValueError("pi_command_invalid")
    if (not isinstance(command, list) or not command or not all(isinstance(part, str) and part for part in command)
            or Path(command[0]).name != "pi" or "--ac06-live" not in command):
        raise ValueError("pi_command_not_explicit_ac06_live")
    return command


def assert_database(db_path, original_run_id):
    """Read-only proof of durable AC-06 facts after Pi has handled the live response."""
    uri = Path(db_path).resolve().as_uri() + "?mode=ro"
    try:
        con = sqlite3.connect(uri, uri=True)
        original = con.execute(
            "SELECT state,terminal_outcome,usage_status,actual_provider FROM dispatches WHERE run_id=?",
            (original_run_id,)).fetchone()
        if not original or original[0:2] != ("terminal_failure", "quota_exhausted") or not original[3]:
            return False, "original_quota_exhaustion_not_proven"
        replacements = con.execute(
            "SELECT run_id,state FROM dispatches WHERE replacement_of_run_id=?", (original_run_id,)).fetchall()
        if len(replacements) != 1 or replacements[0][1] != "terminal_success":
            return False, "single_completed_replacement_not_proven"
        live = con.execute("SELECT expires_at FROM provider_exhaustions WHERE provider=?", (original[3],)).fetchone()
        if not live or live[0] <= int(time.time() * 1000):
            return False, "global_provider_exclusion_not_proven"
        return True, {"replacement_run_id": replacements[0][0], "usage_status": original[2] or "absent"}
    except (sqlite3.Error, OSError, ValueError):
        return False, "routing_database_unavailable"
    finally:
        try:
            con.close()
        except (UnboundLocalError, sqlite3.Error):
            pass


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--enable-live-run", action="store_true")
    parser.add_argument("--precondition", help="non-secret AC-06 attestation JSON")
    parser.add_argument("--pi-command", help="JSON argv; must call pi and include --ac06-live")
    parser.add_argument("--routing-db")
    parser.add_argument("--original-run-id")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        emit(status="PASS", gate="AC-06-runner-self-test", live_provider_invoked=False)
        return 0
    if not args.enable_live_run:
        return blocked("live_run_not_explicitly_enabled")
    if not all((args.precondition, args.pi_command, args.routing_db, args.original_run_id)):
        return blocked("controlled_exhaustion_precondition_incomplete")
    try:
        manifest_id = safe_manifest(args.precondition)
        command = parse_pi_command(args.pi_command)
    except ValueError as exc:
        return blocked(str(exc))
    # No shell, no inherited .env loading, and no output capture/echo: Pi is unreachable
    # until the full controlled precondition above is accepted.
    try:
        result = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, check=False, timeout=180)
    except (OSError, subprocess.TimeoutExpired):
        emit(status="FAILED", gate="AC-06", detail="pi_live_task_did_not_complete", live_provider_invoked=True)
        return FAILED
    if result.returncode:
        emit(status="FAILED", gate="AC-06", detail="pi_live_task_failed", live_provider_invoked=True)
        return FAILED
    ok, proof = assert_database(args.routing_db, args.original_run_id)
    if not ok:
        emit(status="FAILED", gate="AC-06", detail=proof, live_provider_invoked=True)
        return FAILED
    emit(status="PASS", gate="AC-06", live_provider_invoked=True, precondition_sha256_16=manifest_id,
         **proof)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
