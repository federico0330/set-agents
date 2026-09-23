"""Structured HCE denial errors — exit 2, zero state writes."""

from __future__ import annotations


class HceDenial(Exception):
    """Fail-closed HCE denial with stable token."""

    def __init__(self, token: str, reason: str, **fields: object) -> None:
        self.token = token
        self.reason = reason
        self.fields = fields
        super().__init__(f"{token}: {reason}")

    def to_payload(self, *, feature_id: str | None = None, package_id: str | None = None,
                   exception_id: str | None = None, revision: int | None = None) -> dict:
        payload = {
            "ok": False,
            "error": f"{self.token}: {self.reason}",
            "code": self.token,
        }
        if feature_id is not None:
            payload["feature_id"] = feature_id
        if package_id is not None:
            payload["package_id"] = package_id
        if exception_id is not None:
            payload["exception_id"] = exception_id
        if revision is not None:
            payload["revision"] = revision
        payload.update(self.fields)
        return payload


class HceCommittedRenderFailed(HceDenial):
    """State committed but post-replace rendering failed."""

    def __init__(self, reason: str, *, outcome_id: str, revision: int, **fields: object) -> None:
        super().__init__(
            "HCE_COMMITTED_RENDER_FAILED",
            reason,
            state_committed=True,
            outcome_id=outcome_id,
            revision=revision,
            **fields,
        )
