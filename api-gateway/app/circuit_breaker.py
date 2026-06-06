import time
from enum import Enum as PyEnum
from typing import Dict


class CircuitState(PyEnum):
    CLOSED = "closed"       # Normal — requests pass through
    OPEN = "open"           # Tripped — requests rejected immediately
    HALF_OPEN = "half_open" # Recovery probe — one request allowed through


class CircuitBreaker:
    """
    Simple state-machine circuit breaker.

    CLOSED  → fail_max consecutive failures → OPEN
    OPEN    → reset_timeout seconds elapsed → HALF_OPEN
    HALF_OPEN → next success → CLOSED  |  next failure → OPEN
    """

    def __init__(self, name: str, fail_max: int = 5, reset_timeout: float = 30.0):
        self.name = name
        self.fail_max = fail_max
        self.reset_timeout = reset_timeout
        self._failures = 0
        self._last_failure_time: float = 0.0
        self._state = CircuitState.CLOSED

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.monotonic() - self._last_failure_time >= self.reset_timeout:
                self._state = CircuitState.HALF_OPEN
        return self._state

    def allow_request(self) -> bool:
        return self.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)

    def record_success(self) -> None:
        self._failures = 0
        self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        self._failures += 1
        self._last_failure_time = time.monotonic()
        if self._failures >= self.fail_max:
            self._state = CircuitState.OPEN

    def status(self) -> dict:
        return {
            "name": self.name,
            "state": self.state.value,
            "failures": self._failures,
            "fail_max": self.fail_max,
            "reset_timeout_seconds": self.reset_timeout,
        }


# One breaker per downstream service (module-level singletons)
_breakers: Dict[str, CircuitBreaker] = {
    "auth":    CircuitBreaker("auth-service",   fail_max=5, reset_timeout=30),
    "books":   CircuitBreaker("book-service",   fail_max=5, reset_timeout=30),
    "members": CircuitBreaker("member-service", fail_max=5, reset_timeout=30),
    "loans":   CircuitBreaker("loan-service",   fail_max=5, reset_timeout=30),
    "fines":   CircuitBreaker("fine-service",   fail_max=5, reset_timeout=30),
}

_PREFIX_MAP = [
    ("/auth",    "auth"),
    ("/books",   "books"),
    ("/members", "members"),
    ("/loans",   "loans"),
    ("/fines",   "fines"),
]


def get_breaker(path: str) -> CircuitBreaker:
    for prefix, key in _PREFIX_MAP:
        if path.startswith(prefix):
            return _breakers[key]
    return _breakers["auth"]  # fallback — should never happen if routing is correct


def get_all_breakers() -> Dict[str, CircuitBreaker]:
    return _breakers
