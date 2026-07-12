---
description: Deep read-only review of one integrated package
agent: package-reviewer
---
Review the integrated package specified by:
$ARGUMENTS

Inputs must include approved spec/version, package id, covered acceptance criteria, package diff, ownership paths,
gate results, assumptions, and risks. Return one consolidated package review with `pass`, `repair_required`, or
`blocked`. Do not edit files and do not ask the user.
