# Changelog

All notable changes to this project are documented here, following the spirit of
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

This project does not use tagged releases or semantic versioning yet (`git tag --list` is empty as
of this writing) — entries land under `Unreleased` until a first tagged release exists. The
durable, per-decision record already lives in `docs/adr/` (indexed at `docs/adr/README.md`, 49
ADRs as of this writing); this file is a human-readable summary layer for people who clone the
repo, not a replacement for the ADR log.

## [Unreleased]

### Added

- `LICENSE` (MIT), `CONTRIBUTING.md`, `CHANGELOG.md` (this file), `SECURITY.md` — public-repo
  hygiene baseline (feature `024-listo-para-terceros`, package C4, AC-09).
- Re-pointable upstream for the update-distance check (`ai/scripts/set_agents_app.py`) — a fork no
  longer measures itself against `federico0330/set-agents` by default only; the remote is
  configurable, current default preserved as fallback (AC-12).

### Changed

- `HANDOFF-PASO9.md` moved from the repo root to `docs/HANDOFF-PASO9.md` (AC-09).
