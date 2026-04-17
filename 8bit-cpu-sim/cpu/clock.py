"""
8-bit CPU Simulator — Clock (Extended)

Drives the control unit with step-by-step or free-running execution.
After each instruction, checks for pending hardware interrupts.
"""

from __future__ import annotations

from cpu.control_unit import ControlUnit
from cpu.interrupt_controller import InterruptController

DEFAULT_MAX_CYCLES = 10_000


class Clock:
    """System clock that ticks the control unit and services interrupts."""

    def __init__(
        self,
        control_unit: ControlUnit,
        interrupt_controller: InterruptController | None = None,
    ) -> None:
        """Bind the clock to a control unit and optional interrupt controller."""
        self.control_unit = control_unit
        self.interrupt_controller = interrupt_controller or InterruptController()
        self.cycle_count: int = 0
        self.halted: bool = False

    def step(self) -> bool:
        """Execute a single clock tick.

        1. Run one fetch-decode-execute cycle.
        2. If the CPU halted, record it and return ``False``.
        3. Check for pending interrupts (if IE is set).
        4. Increment the cycle counter and return ``True``.
        """
        if self.halted:
            return False

        running = self.control_unit.step()
        self.cycle_count += 1

        if not running:
            self.halted = True
            return False

        regs = self.control_unit.registers
        ic = self.interrupt_controller
        if ic.has_pending() and regs.interrupt_enable:
            ic.acknowledge()
            self.control_unit.handle_interrupt()

        return True

    def run(self, max_cycles: int = DEFAULT_MAX_CYCLES) -> int:
        """Run until HALT or *max_cycles* reached.

        Returns the total number of cycles executed.
        """
        while not self.halted and self.cycle_count < max_cycles:
            self.step()
        return self.cycle_count


if __name__ == "__main__":
    from cpu.memory import Memory
    from cpu.registers import Registers
    from cpu.alu import ALU
    from cpu.io_bus import IOBus

    mem = Memory()
    regs = Registers()
    alu = ALU()
    io = IOBus()
    cu = ControlUnit(mem, regs, alu, io)
    ic = InterruptController()
    clk = Clock(cu, ic)

    mem.load_program([0x1E, 0x3F, 0x2D, 0xFF])
    mem.write(14, 5)
    mem.write(15, 3)

    cycles = clk.run()
    print(f"Halted after {cycles} cycles — A = 0x{regs.a:02X}")
