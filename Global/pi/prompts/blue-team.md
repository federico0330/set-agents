---
description: Hardening + detection plan for findings
---

Before doing anything else, invoke `subagent({ agent: "security-auditor", task: "<the request/arguments below>" })` to delegate this to the `security-auditor` role — never handle it directly.

Turn open security findings (or: $ARGUMENTS) into defenses: harden at the right layer, add detection/
logging (persist failed attempts in their own unit of work), response controls, and a test proving each
mitigation closes the attack. Output the mitigation plan attached to each finding (SEC- schema).
