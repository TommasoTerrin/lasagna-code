"""The only exceptions the core raises. A denial is a decision, not an error."""

from __future__ import annotations


class LasagnaError(Exception):
    """Base class for errors the shell knows how to report."""


class PayloadError(LasagnaError):
    """The hook payload is not a JSON object."""

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class PatternError(LasagnaError):
    """A regex in the stack profile does not compile."""

    def __init__(self, key: str, pattern: str, detail: str) -> None:
        super().__init__(f"{key}: {detail} (pattern: {pattern})")
        self.key = key
        self.pattern = pattern
        self.detail = detail
