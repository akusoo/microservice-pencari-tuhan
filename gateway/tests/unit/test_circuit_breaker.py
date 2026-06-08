"""
Unit tests — gateway/app/circuit_breaker.py

No HTTP, no I/O. State machine logic only.
"""
import time
import pytest

from app.circuit_breaker import CircuitBreaker, CircuitState


@pytest.fixture
def cb():
    return CircuitBreaker("test-service", fail_max=3, reset_timeout=30.0)


def test_initial_state_is_closed(cb):
    assert cb.state == CircuitState.CLOSED


def test_allows_request_when_closed(cb):
    assert cb.allow_request() is True


def test_single_failure_does_not_open(cb):
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED


def test_opens_after_fail_max_failures(cb):
    for _ in range(cb.fail_max):
        cb.record_failure()
    assert cb.state == CircuitState.OPEN


def test_rejects_request_when_open(cb):
    for _ in range(cb.fail_max):
        cb.record_failure()
    assert cb.allow_request() is False


def test_success_resets_failure_count(cb):
    cb.record_failure()
    cb.record_failure()
    cb.record_success()
    assert cb._failures == 0
    assert cb.state == CircuitState.CLOSED


def test_transitions_to_half_open_after_timeout(cb, monkeypatch):
    for _ in range(cb.fail_max):
        cb.record_failure()
    assert cb.state == CircuitState.OPEN

    # Fast-forward time past reset_timeout
    monkeypatch.setattr(time, "monotonic", lambda: time.monotonic() + 31.0)
    assert cb.state == CircuitState.HALF_OPEN


def test_half_open_allows_one_request(cb, monkeypatch):
    for _ in range(cb.fail_max):
        cb.record_failure()
    monkeypatch.setattr(time, "monotonic", lambda: time.monotonic() + 31.0)
    assert cb.allow_request() is True


def test_half_open_closes_on_success(cb, monkeypatch):
    for _ in range(cb.fail_max):
        cb.record_failure()
    monkeypatch.setattr(time, "monotonic", lambda: time.monotonic() + 31.0)
    assert cb.state == CircuitState.HALF_OPEN
    cb.record_success()
    assert cb.state == CircuitState.CLOSED


def test_half_open_reopens_on_failure(cb, monkeypatch):
    for _ in range(cb.fail_max):
        cb.record_failure()
    monkeypatch.setattr(time, "monotonic", lambda: time.monotonic() + 31.0)
    assert cb.state == CircuitState.HALF_OPEN
    cb.record_failure()
    assert cb.state == CircuitState.OPEN


def test_status_dict_shape(cb):
    status = cb.status()
    assert status["name"] == "test-service"
    assert status["state"] == "closed"
    assert status["failures"] == 0
    assert status["fail_max"] == 3
    assert status["reset_timeout_seconds"] == 30.0
