"""Tests for cpu.interrupt_controller.InterruptController — minimum 6 tests."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cpu.interrupt_controller import InterruptController


class TestInit:
    """Initial state."""

    def test_not_pending_on_init(self) -> None:
        ic = InterruptController()
        assert ic.has_pending() is False

    def test_irq_count_zero_on_init(self) -> None:
        ic = InterruptController()
        assert ic.irq_count == 0


class TestRequestAndAcknowledge:
    """Request / acknowledge cycle."""

    def test_request_sets_pending(self) -> None:
        ic = InterruptController()
        ic.request_interrupt()
        assert ic.has_pending() is True

    def test_acknowledge_clears_pending(self) -> None:
        ic = InterruptController()
        ic.request_interrupt()
        ic.acknowledge()
        assert ic.has_pending() is False

    def test_acknowledge_does_not_reset_irq_count(self) -> None:
        ic = InterruptController()
        ic.request_interrupt()
        ic.acknowledge()
        assert ic.irq_count == 1


class TestIrqCount:
    """Counting interrupt requests."""

    def test_irq_count_increments(self) -> None:
        ic = InterruptController()
        ic.request_interrupt()
        ic.request_interrupt()
        assert ic.irq_count == 2

    def test_irq_count_after_multiple_ack(self) -> None:
        ic = InterruptController()
        ic.request_interrupt()
        ic.acknowledge()
        ic.request_interrupt()
        ic.acknowledge()
        ic.request_interrupt()
        assert ic.irq_count == 3

    def test_multiple_requests_before_ack(self) -> None:
        ic = InterruptController()
        ic.request_interrupt()
        ic.request_interrupt()
        ic.request_interrupt()
        ic.acknowledge()
        assert ic.has_pending() is False
        assert ic.irq_count == 3
