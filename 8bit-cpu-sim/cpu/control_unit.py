"""
8-bit CPU Simulator — Control Unit (Extended)

Implements the full fetch / decode / execute cycle for the extended ISA,
including stack operations, I/O, 2-byte instructions, and interrupt handling.
All opcode constants are derived from the shared ``assembler.opcodes`` table.
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from assembler.opcodes import (
    HALT_BYTE, OPCODES_1BYTE, OPCODES_2BYTE, OPCODES_3BYTE,
    IVT_ADDRESS,
)
from cpu.memory import Memory
from cpu.registers import Registers
from cpu.alu import ALU
from cpu.io_bus import IOBus

# ---------------------------------------------------------------------------
# Opcode-nibble constants (derived from the canonical table)
# ---------------------------------------------------------------------------

OP_NOP   = OPCODES_1BYTE["NOP"] >> 4       # 0x0
OP_LOAD  = OPCODES_1BYTE["LOAD"] >> 4      # 0x1
OP_STORE = OPCODES_1BYTE["STORE"] >> 4     # 0x2
OP_ADD   = OPCODES_1BYTE["ADD"] >> 4       # 0x3
OP_SUB   = OPCODES_1BYTE["SUB"] >> 4       # 0x4
OP_JMP   = OPCODES_1BYTE["JMP"] >> 4       # 0x5
OP_JZ    = OPCODES_1BYTE["JZ"] >> 4        # 0x6
OP_AND   = OPCODES_1BYTE["AND"] >> 4       # 0x7
OP_OR    = OPCODES_1BYTE["OR"] >> 4        # 0x8
OP_JC    = OPCODES_1BYTE["JC"] >> 4        # 0x9
OP_IN    = OPCODES_1BYTE["IN"] >> 4        # 0xA
OP_OUT   = OPCODES_1BYTE["OUT"] >> 4       # 0xB
OP_STACK = OPCODES_1BYTE["PUSH"] >> 4      # 0xC
OP_MOV   = OPCODES_1BYTE["MOV"] >> 4       # 0xE

# Stack-group sub-opcodes (lower nibble)
STACK_PUSH = OPCODES_1BYTE["PUSH"] & 0x0F  # 0
STACK_POP  = OPCODES_1BYTE["POP"]  & 0x0F  # 1
STACK_RET  = OPCODES_1BYTE["RET"]  & 0x0F  # 2
STACK_RETI = OPCODES_1BYTE["RETI"] & 0x0F  # 3
STACK_EI   = OPCODES_1BYTE["EI"]   & 0x0F  # 4
STACK_DI   = OPCODES_1BYTE["DI"]   & 0x0F  # 5

# 2-byte prefixes (full IR byte values)
PREFIX_CALL      = OPCODES_2BYTE["CALL"]       # 0xF0
PREFIX_JMPF      = OPCODES_2BYTE["JMPF"]       # 0xF1
PREFIX_JZF       = OPCODES_2BYTE["JZF"]        # 0xF2
PREFIX_JCF       = OPCODES_2BYTE["JCF"]        # 0xF3
PREFIX_LOADI     = OPCODES_2BYTE["LOADI"]      # 0xF4  A = val
PREFIX_LOAD_IND  = OPCODES_2BYTE["LOAD_IND"]   # 0xF5  A = mem[mem[addr]]
PREFIX_STORE_IND = OPCODES_2BYTE["STORE_IND"]  # 0xF6  mem[mem[addr]] = A
PREFIX_LOAD_B    = OPCODES_2BYTE["LOAD_B"]     # 0xF7  B = mem[addr]
PREFIX_LOAD_C    = OPCODES_2BYTE["LOAD_C"]     # 0xF8  C = mem[addr]
PREFIX_LOADI_B   = OPCODES_2BYTE["LOADI_B"]    # 0xF9  B = val
PREFIX_LOADI_C   = OPCODES_2BYTE["LOADI_C"]    # 0xFA  C = val
PREFIX_STORE_B   = OPCODES_2BYTE["STORE_B"]    # 0xFB  mem[addr] = B
PREFIX_STORE_C   = OPCODES_2BYTE["STORE_C"]    # 0xFC  mem[addr] = C

_TWO_BYTE_LO = PREFIX_CALL        # 0xF0
_TWO_BYTE_HI = PREFIX_STORE_C     # 0xFC
PREFIX_ALU_REG = OPCODES_3BYTE["ALU_REG"]  # 0xFD


class ControlUnit:
    """Orchestrates the fetch-decode-execute cycle for the extended ISA."""

    def __init__(
        self,
        memory: Memory,
        registers: Registers,
        alu: ALU,
        io_bus: IOBus | None = None,
    ) -> None:
        """Wire the control unit to memory, registers, ALU, and I/O bus."""
        self.memory = memory
        self.registers = registers
        self.alu = alu
        self.io_bus = io_bus or IOBus()

    # ---- fetch / decode / execute ------------------------------------------

    def fetch(self) -> None:
        """Load the next instruction byte into IR and advance PC."""
        self.registers.ir = self.memory.read(self.registers.pc)
        self.registers.pc = self.registers.pc + 1

    def decode(self) -> tuple[int, int]:
        """Decode the current IR into (opcode, operand).

        * Regular 1-byte: opcode = IR >> 4, operand = IR & 0x0F.
        * 2-byte prefixes (0xF0-0xFC): opcode = IR, operand = mem[PC]; PC += 1.
        * ALU_REG 3-byte prefix (0xFD): opcode = IR, operand = (op_id << 8) | pair.
        * All other cases (including HALT 0xFF): standard nibble decode.
        """
        ir = self.registers.ir
        if ir == PREFIX_ALU_REG:
            op_id = self.memory.read(self.registers.pc)
            self.registers.pc = self.registers.pc + 1
            pair = self.memory.read(self.registers.pc)
            self.registers.pc = self.registers.pc + 1
            return ir, ((op_id & 0xFF) << 8) | (pair & 0xFF)
        if _TWO_BYTE_LO <= ir <= _TWO_BYTE_HI:
            operand = self.memory.read(self.registers.pc)
            self.registers.pc = self.registers.pc + 1
            return ir, operand
        return (ir >> 4) & 0x0F, ir & 0x0F

    def execute(self, opcode: int, operand: int) -> bool:
        """Execute one decoded instruction.

        Returns ``True`` to continue, ``False`` on HALT.
        """
        if self.registers.ir == HALT_BYTE:
            return False

        if opcode == OP_NOP:
            pass

        elif opcode == OP_LOAD:
            self.registers.a = self.memory.read(operand)

        elif opcode == OP_STORE:
            self.memory.write(operand, self.registers.a)

        elif opcode == OP_ADD:
            b = self.memory.read(operand)
            result, zf, cf = self.alu.execute("ADD", self.registers.a, b)
            self.registers.a = result
            self.registers.zero_flag = zf
            self.registers.carry_flag = cf

        elif opcode == OP_SUB:
            b = self.memory.read(operand)
            result, zf, cf = self.alu.execute("SUB", self.registers.a, b)
            self.registers.a = result
            self.registers.zero_flag = zf
            self.registers.carry_flag = cf

        elif opcode == OP_JMP:
            self.registers.pc = operand

        elif opcode == OP_JZ:
            if self.registers.zero_flag:
                self.registers.pc = operand

        elif opcode == OP_AND:
            b = self.memory.read(operand)
            result, zf, cf = self.alu.execute("AND", self.registers.a, b)
            self.registers.a = result
            self.registers.zero_flag = zf
            self.registers.carry_flag = cf

        elif opcode == OP_OR:
            b = self.memory.read(operand)
            result, zf, cf = self.alu.execute("OR", self.registers.a, b)
            self.registers.a = result
            self.registers.zero_flag = zf
            self.registers.carry_flag = cf

        elif opcode == OP_JC:
            if self.registers.carry_flag:
                self.registers.pc = operand

        elif opcode == OP_IN:
            self.registers.a = self.io_bus.read(operand)

        elif opcode == OP_OUT:
            self.io_bus.write(operand, self.registers.a)

        elif opcode == OP_STACK:
            self._execute_stack(operand)

        elif opcode == OP_MOV:
            dest_code = operand // 3
            src_code = operand % 3
            value = self._read_reg_by_code(src_code)
            self._write_reg_by_code(dest_code, value)

        elif opcode == PREFIX_CALL:
            self._push(self.registers.pc)
            self.registers.pc = operand

        elif opcode == PREFIX_JMPF:
            self.registers.pc = operand

        elif opcode == PREFIX_JZF:
            if self.registers.zero_flag:
                self.registers.pc = operand

        elif opcode == PREFIX_JCF:
            if self.registers.carry_flag:
                self.registers.pc = operand

        elif opcode == PREFIX_LOADI:
            self.registers.a = operand

        elif opcode == PREFIX_LOAD_IND:
            ptr = self.memory.read(operand)
            self.registers.a = self.memory.read(ptr)

        elif opcode == PREFIX_STORE_IND:
            ptr = self.memory.read(operand)
            self.memory.write(ptr, self.registers.a)

        elif opcode == PREFIX_LOAD_B:
            self.registers.b = self.memory.read(operand)

        elif opcode == PREFIX_LOAD_C:
            self.registers.c = self.memory.read(operand)

        elif opcode == PREFIX_LOADI_B:
            self.registers.b = operand

        elif opcode == PREFIX_LOADI_C:
            self.registers.c = operand

        elif opcode == PREFIX_STORE_B:
            self.memory.write(operand, self.registers.b)

        elif opcode == PREFIX_STORE_C:
            self.memory.write(operand, self.registers.c)

        elif opcode == PREFIX_ALU_REG:
            op_id = (operand >> 8) & 0xFF
            pair = operand & 0xFF
            if pair > 8:
                raise RuntimeError(
                    f"Invalid ALU_REG pair code 0x{pair:02X} in "
                    f"instruction 0x{self.registers.ir:02X}"
                )
            op_map = {
                0: "ADD",
                1: "SUB",
                2: "AND",
                3: "OR",
            }
            if op_id not in op_map:
                raise RuntimeError(
                    f"Invalid ALU_REG op id 0x{op_id:02X} in "
                    f"instruction 0x{self.registers.ir:02X}"
                )
            dest_code = pair // 3
            src_code = pair % 3
            left = self._read_reg_by_code(dest_code)
            right = self._read_reg_by_code(src_code)
            result, zf, cf = self.alu.execute(op_map[op_id], left, right)
            self._write_reg_by_code(dest_code, result)
            self.registers.zero_flag = zf
            self.registers.carry_flag = cf

        else:
            raise RuntimeError(
                f"Unknown opcode 0x{opcode:X} in instruction "
                f"0x{self.registers.ir:02X}"
            )

        return True

    def step(self) -> bool:
        """Run one complete fetch-decode-execute cycle.

        Returns ``True`` to continue, ``False`` on HALT.
        """
        self.fetch()
        opcode, operand = self.decode()
        return self.execute(opcode, operand)

    # ---- interrupt support --------------------------------------------------

    def handle_interrupt(self) -> None:
        """Service a hardware interrupt.

        Called by the Clock when an IRQ is pending and IE is set.
        Pushes PC and flags onto the stack, disables interrupts,
        and jumps to the handler address stored in the IVT.
        """
        self._push(self.registers.pc)
        self._push(self.registers.get_flags_byte())
        self.registers.interrupt_enable = False
        self.registers.pc = self.memory.read(IVT_ADDRESS)

    # ---- stack helpers ------------------------------------------------------

    def _push(self, value: int) -> None:
        """Push *value* onto the stack: mem[SP] = value; SP -= 1."""
        self.memory.write(self.registers.sp, value)
        self.registers.sp = self.registers.sp - 1

    def _pop(self) -> int:
        """Pop a byte from the stack: SP += 1; return mem[SP]."""
        self.registers.sp = self.registers.sp + 1
        return self.memory.read(self.registers.sp)

    # ---- stack-group dispatch -----------------------------------------------

    def _execute_stack(self, operand: int) -> None:
        """Dispatch PUSH / POP / RET / RETI / EI / DI."""
        if operand == STACK_PUSH:
            self._push(self.registers.a)

        elif operand == STACK_POP:
            self.registers.a = self._pop()

        elif operand == STACK_RET:
            self.registers.pc = self._pop()

        elif operand == STACK_RETI:
            flags_byte = self._pop()
            self.registers.set_flags_byte(flags_byte)
            self.registers.pc = self._pop()
            self.registers.interrupt_enable = True

        elif operand == STACK_EI:
            self.registers.interrupt_enable = True

        elif operand == STACK_DI:
            self.registers.interrupt_enable = False

        else:
            raise RuntimeError(
                f"Unknown stack sub-opcode 0x{operand:X} in instruction "
                f"0x{self.registers.ir:02X}"
            )

    # ---- register-code helpers ----------------------------------------------

    def _read_reg_by_code(self, code: int) -> int:
        if code == 0:
            return self.registers.a
        if code == 1:
            return self.registers.b
        if code == 2:
            return self.registers.c
        raise RuntimeError(f"Unknown register code {code}")

    def _write_reg_by_code(self, code: int, value: int) -> None:
        if code == 0:
            self.registers.a = value
            return
        if code == 1:
            self.registers.b = value
            return
        if code == 2:
            self.registers.c = value
            return
        raise RuntimeError(f"Unknown register code {code}")


if __name__ == "__main__":
    mem = Memory()
    regs = Registers()
    alu = ALU()
    io = IOBus()
    cu = ControlUnit(mem, regs, alu, io)

    mem.load_program([0x1E, 0x3F, 0x2D, 0xFF])
    mem.write(14, 5)
    mem.write(15, 3)

    while cu.step():
        print(regs)
    print("HALTED:", regs)
