"""
8-bit CPU Simulator — CPU facade (Extended)

Wires Memory, Registers, ALU, IOBus, InterruptController, ControlUnit,
and Clock into a single top-level ``CPU`` object.
"""

from __future__ import annotations

from cpu.memory import Memory
from cpu.registers import Registers
from cpu.alu import ALU
from cpu.io_bus import IOBus
from cpu.interrupt_controller import InterruptController
from cpu.control_unit import ControlUnit
from cpu.clock import Clock


class CPU:
    """Top-level 8-bit CPU that composes every sub-component."""

    def __init__(self) -> None:
        """Instantiate and wire all internal components."""
        self.memory = Memory()
        self.registers = Registers()
        self.alu = ALU()
        self.io_bus = IOBus()
        self.interrupt_controller = InterruptController()
        self.control_unit = ControlUnit(
            self.memory, self.registers, self.alu, self.io_bus,
        )
        self.clock = Clock(self.control_unit, self.interrupt_controller)

    def load(self, program: list[int], start: int = 0) -> None:
        """Load a program (list of bytecodes) into memory."""
        self.memory.load_program(program, start)

    def run(self, max_cycles: int = 10_000) -> None:
        """Run until HALT or *max_cycles* is reached."""
        self.clock.run(max_cycles)

    def step(self) -> bool:
        """Execute a single fetch-decode-execute cycle.

        Returns ``True`` to continue, ``False`` on HALT.
        """
        return self.clock.step()

    def fire_interrupt(self) -> None:
        """Trigger a hardware IRQ from outside the CPU."""
        self.interrupt_controller.request_interrupt()

    def state(self) -> dict:
        """Return a snapshot of the CPU's current state."""
        return {
            "PC": self.registers.pc,
            "IR": self.registers.ir,
            "A": self.registers.a,
            "SP": self.registers.sp,
            "ZF": self.registers.zero_flag,
            "CF": self.registers.carry_flag,
            "IE": self.registers.interrupt_enable,
            "cycles": self.clock.cycle_count,
            "halted": self.clock.halted,
            "irq_count": self.interrupt_controller.irq_count,
        }

    def dump_memory(self, start: int = 0, end: int = 0xFF) -> str:
        """Return a hex dump of the given memory range."""
        return self.memory.dump(start, end)
