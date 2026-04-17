# 8-bit CPU Simulator (Python)

An educational **8-bit CPU** simulator written in Python. It includes:

- A 256-byte **von Neumann** memory (program + data)
- A **fetch → decode → execute** control unit
- An **ALU** with flags (zero/carry)
- A 16-port **I/O bus** (`IN` / `OUT`)
- A simple **stack** (PUSH/POP/CALL/RET) and basic **interrupt** support
- A tiny **assembler** for writing `.asm` programs

## Quick start

From the `8bit-cpu-sim/` folder:

```bash
python main.py
```

Run one of the included programs:

```bash
python main.py programs/add_two_numbers.asm
python main.py programs/countdown.asm
python main.py programs/fibonacci.asm
python main.py programs/io_echo.asm
python main.py programs/interrupt_demo.asm
```

## Trace (see every instruction result)

To print CPU state **after every executed instruction**:

```bash
python main.py --trace programs/add_two_numbers.asm
```

If your program loops, you can limit trace length:

```bash
python main.py --trace --max-cycles=200 programs/fibonacci.asm
```

## What gets printed

`main.py` prints:

- **Initial State / Final State**: `PC`, `IR`, `A`, `SP`, flags (`ZF`, `CF`, `IE`), cycle count, halted state
- **Memory dump**: by default `0x00–0x0F` at the end of a normal run

With `--trace`, it prints the same state **after each `step()`**, which is the easiest way to observe “results from operations” (ALU ops, loads/stores, jumps, stack, I/O).

## Architecture overview

The top-level `CPU` object composes these parts:

- **`cpu/memory.py`**: 256-byte RAM with read/write and hex dump
- **`cpu/registers.py`**: PC/IR/A/B/C/SP, flags, interrupt-enable (IE)
- **`cpu/alu.py`**: ADD/SUB/AND/OR + flag generation
- **`cpu/io_bus.py`**: 16 ports; supports callbacks for `IN`/`OUT`
- **`cpu/control_unit.py`**: instruction decoding + execution logic
- **`cpu/clock.py`**: runs instructions and services interrupts between them
- **`cpu/interrupt_controller.py`**: manages pending IRQ requests/acks

Execution flow:

1. **Fetch**: `IR = mem[PC]`, then `PC += 1`
2. **Decode**:
   - Most instructions are **1 byte**: `opcode = IR >> 4`, `operand = IR & 0x0F`
   - Some are **2 bytes** (prefix `0xF0–0xFC`): next byte is an 8-bit operand (and `PC` advances again)
   - `ALU_REG` is **3 bytes** (`0xFD` prefix): selects an ALU op + register pair
3. **Execute**: updates registers/flags/memory/I/O based on the instruction
4. **Interrupt check**: after each instruction, if an IRQ is pending and `IE` is set, the CPU vectors to the handler

## I/O

Ports are `0–15`. If you don’t register callbacks, ports act like internal registers.

To capture output in code (example pattern used by `io_echo.asm` in `main.py`):

- Register an input source with `register_input(port, callback)`
- Register an output sink with `register_output(port, callback)`

## Writing your own programs

Put `.asm` files in `programs/` and run:

```bash
python main.py programs/your_program.asm
```

The opcode mapping lives in `assembler/opcodes.py`, and the assembler is in `assembler/`.

## Tests

If you have `pytest` installed:

```bash
pytest
```

## License

Add a license file if you plan to open source this on GitHub (MIT is common for learning projects).

