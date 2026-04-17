"""Tests for cpu.io_bus.IOBus — minimum 8 tests."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from cpu.io_bus import IOBus


class TestDefaults:
    """Unregistered port behaviour."""

    def test_read_unregistered_returns_zero(self) -> None:
        bus = IOBus()
        assert bus.read(0) == 0

    def test_write_unregistered_does_not_raise(self) -> None:
        bus = IOBus()
        bus.write(0, 42)

    def test_write_then_read_fallback(self) -> None:
        bus = IOBus()
        bus.write(3, 77)
        assert bus.read(3) == 77


class TestCallbacks:
    """Registered callback behaviour."""

    def test_read_callback_invoked(self) -> None:
        bus = IOBus()
        bus.register_input(0, lambda: 99)
        assert bus.read(0) == 99

    def test_write_callback_invoked(self) -> None:
        captured: list[int] = []
        bus = IOBus()
        bus.register_output(1, lambda v: captured.append(v))
        bus.write(1, 42)
        assert captured == [42]

    def test_read_callback_called_each_time(self) -> None:
        counter = {"n": 0}

        def incrementing_read() -> int:
            counter["n"] += 1
            return counter["n"]

        bus = IOBus()
        bus.register_input(2, incrementing_read)
        assert bus.read(2) == 1
        assert bus.read(2) == 2


class TestBoundsChecking:
    """Port range validation."""

    def test_read_port_too_high(self) -> None:
        bus = IOBus()
        with pytest.raises(IndexError):
            bus.read(16)

    def test_write_port_negative(self) -> None:
        bus = IOBus()
        with pytest.raises(IndexError):
            bus.write(-1, 0)

    def test_register_input_port_too_high(self) -> None:
        bus = IOBus()
        with pytest.raises(IndexError):
            bus.register_input(16, lambda: 0)


class TestPortIndependence:
    """Ports must not interfere with each other."""

    def test_ports_are_independent(self) -> None:
        bus = IOBus()
        bus.write(0, 11)
        bus.write(1, 22)
        assert bus.read(0) == 11
        assert bus.read(1) == 22

    def test_callback_on_one_port_does_not_affect_another(self) -> None:
        bus = IOBus()
        bus.register_input(0, lambda: 99)
        bus.write(1, 55)
        assert bus.read(0) == 99
        assert bus.read(1) == 55
