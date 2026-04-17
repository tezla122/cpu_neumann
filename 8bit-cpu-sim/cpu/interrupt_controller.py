"""
8-bit CPU Simulator — Interrupt Controller

Single IRQ line.  External code calls ``request_interrupt()`` to fire an
IRQ; the Clock polls ``has_pending()`` after each instruction.
"""

from __future__ import annotations


class InterruptController:
    """Single-line interrupt controller for the 8-bit CPU."""

    def __init__(self) -> None:
        """Initialise with no pending interrupt."""
        self._pending: bool = False
        self._irq_count: int = 0

    def request_interrupt(self) -> None:
        """Fire an interrupt request (edge-triggered)."""
        self._pending = True
        self._irq_count += 1

    def has_pending(self) -> bool:
        """Return ``True`` if an IRQ is waiting to be serviced."""
        return self._pending

    def acknowledge(self) -> None:
        """Called by the Clock when the interrupt begins being serviced."""
        self._pending = False

    @property
    def irq_count(self) -> int:
        """Total number of interrupt requests fired (for debugging)."""
        return self._irq_count


if __name__ == "__main__":
    ic = InterruptController()
    print("Pending:", ic.has_pending())
    ic.request_interrupt()
    print("Pending after request:", ic.has_pending())
    ic.acknowledge()
    print("Pending after ack:", ic.has_pending())
    print("IRQ count:", ic.irq_count)
