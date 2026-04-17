"""
8-bit CPU Simulator — CLI Entry Point (Extended)

Usage:
    python main.py                                 # built-in add_two_numbers demo
    python main.py programs/add_two_numbers.asm
    python main.py programs/countdown.asm
    python main.py programs/fibonacci.asm
    python main.py programs/io_echo.asm
    python main.py programs/interrupt_demo.asm
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from cpu import CPU
from assembler import Assembler


# ---------------------------------------------------------------------------
# Data-setup helpers (per-program)
# ---------------------------------------------------------------------------

def setup_add_two(cpu: CPU) -> None:
    """Pre-load data for add_two_numbers: 5 + 3."""
    cpu.memory.write(14, 5)
    cpu.memory.write(15, 3)


def setup_countdown(cpu: CPU) -> None:
    """Pre-load data for countdown from 5."""
    cpu.memory.write(14, 1)  # decrement
    cpu.memory.write(15, 5)  # start count


def setup_fibonacci(cpu: CPU) -> None:
    """Pre-load data for fibonacci(7)."""
    cpu.memory.write(0x0A, 0)   # fib_prev
    cpu.memory.write(0x0B, 1)   # fib_curr
    cpu.memory.write(0x0C, 7)   # counter (n iterations)
    cpu.memory.write(0x0D, 0)   # temp
    cpu.memory.write(0x0E, 0)   # result
    cpu.memory.write(0x0F, 1)   # constant 1


def setup_io_echo(cpu: CPU) -> list[int]:
    """Wire I/O callbacks for io_echo: inputs=[5, 3, 0], capture outputs."""
    inputs = iter([5, 3, 0])
    outputs: list[int] = []
    cpu.io_bus.register_input(0, lambda: next(inputs))
    cpu.io_bus.register_output(1, lambda v: outputs.append(v))
    return outputs


def setup_interrupt_demo(cpu: CPU) -> None:
    """Pre-load data and IVT for interrupt_demo."""
    cpu.memory.write(0x0A, 0)    # counter
    cpu.memory.write(0x0B, 0)    # snapshot
    cpu.memory.write(0x0C, 1)    # constant 1
    cpu.memory.write(0xE0, 0x10) # IVT[0] → ISR at address 0x10


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def print_state(label: str, cpu: CPU) -> None:
    """Pretty-print the CPU state with a heading."""
    s = cpu.state()
    print(f"\n--- {label} ---")
    print(
        f"  PC=0x{s['PC']:02X}  IR=0x{s['IR']:02X}  A=0x{s['A']:02X}  SP=0x{s['SP']:02X}  "
        f"ZF={s['ZF']}  CF={s['CF']}  IE={s['IE']}  "
        f"cycles={s['cycles']}  halted={s['halted']}"
    )


# ---------------------------------------------------------------------------
# Run modes
# ---------------------------------------------------------------------------

def run_demo(cpu: CPU) -> None:
    """Built-in add_two_numbers using hardcoded bytecode."""
    program = [0x1E, 0x3F, 0x2D, 0xFF]
    cpu.load(program)
    setup_add_two(cpu)


def run_asm_file(cpu: CPU, path: str) -> str | None:
    """Assemble an .asm file, load it, and set up data.

    Returns a tag identifying special run logic, or None.
    """
    with open(path, "r", encoding="utf-8") as fh:
        source = fh.read()

    asm = Assembler()
    bytecode = asm.assemble(source)
    cpu.load(bytecode)

    basename = os.path.basename(path)
    if "add_two" in basename:
        setup_add_two(cpu)
    elif "countdown" in basename:
        setup_countdown(cpu)
    elif "fibonacci" in basename:
        setup_fibonacci(cpu)
        return "fibonacci"
    elif "io_echo" in basename:
        return "io_echo"
    elif "interrupt" in basename:
        setup_interrupt_demo(cpu)
        return "interrupt_demo"
    return None


def run_interrupt_demo(cpu: CPU) -> None:
    """Step-based execution for interrupt_demo (no HALT in main loop)."""
    print_state("Initial State", cpu)

    for _ in range(20):
        cpu.step()
    print(f"  Counter after 20 steps: {cpu.memory.read(0x0A)}")

    cpu.fire_interrupt()
    for _ in range(10):
        cpu.step()

    snapshot = cpu.memory.read(0x0B)
    counter = cpu.memory.read(0x0A)
    print(f"\n  Interrupt fired!  Snapshot = {snapshot},  Counter now = {counter}")
    print_state("Final State", cpu)


def run_io_echo(cpu: CPU) -> None:
    """Run io_echo with simulated I/O."""
    outputs = setup_io_echo(cpu)
    print_state("Initial State", cpu)
    cpu.run()
    print_state("Final State", cpu)
    print(f"\n  I/O outputs (doubled inputs): {outputs}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI entry point."""
    cpu = CPU()
    tag: str | None = None

    args = sys.argv[1:]
    trace = "--trace" in args
    if trace:
        args = [a for a in args if a != "--trace"]

    # Optional: --max-cycles=123 (only used for trace stepping)
    max_cycles: int | None = None
    for a in list(args):
        if a.startswith("--max-cycles="):
            _, val = a.split("=", 1)
            max_cycles = int(val)
            args.remove(a)
            break

    if len(args) > 0:
        asm_path = args[0]
        if not os.path.isfile(asm_path):
            print(f"Error: file '{asm_path}' not found.", file=sys.stderr)
            sys.exit(1)
        print(f"Assembling and running: {asm_path}")
        tag = run_asm_file(cpu, asm_path)
    else:
        print("No .asm file given — running built-in add_two_numbers demo")
        run_demo(cpu)

    if tag == "interrupt_demo":
        run_interrupt_demo(cpu)
    elif tag == "io_echo":
        run_io_echo(cpu)
    else:
        print_state("Initial State", cpu)
        if trace:
            # Step-by-step trace: show state after every instruction.
            # (Printing after the step shows the *result* of the operation.)
            while cpu.step():
                if max_cycles is not None and cpu.clock.cycle_count >= max_cycles:
                    break
                print_state(f"After step {cpu.clock.cycle_count}", cpu)
        else:
            cpu.run()
        print_state("Final State", cpu)
        print("\n--- Memory 0x00-0x0F ---")
        print(cpu.dump_memory(0x00, 0x0F))


if __name__ == "__main__":
    main()
