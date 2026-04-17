"""Tests for cpu.control_unit.ControlUnit — original + extended tests."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from cpu.memory import Memory
from cpu.registers import Registers
from cpu.alu import ALU
from cpu.io_bus import IOBus
from cpu.control_unit import ControlUnit


def _make_cu() -> tuple[Memory, Registers, ALU, IOBus, ControlUnit]:
    """Helper: build a fresh set of components."""
    mem = Memory()
    regs = Registers()
    alu = ALU()
    io = IOBus()
    cu = ControlUnit(mem, regs, alu, io)
    return mem, regs, alu, io, cu


# ============================================================================
# Original tests (adapted for new 5-tuple helper and 3-tuple ALU return)
# ============================================================================


class TestFetch:
    """Fetch cycle."""

    def test_fetch_loads_ir_and_increments_pc(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        mem.write(0, 0xAB)
        cu.fetch()
        assert regs.ir == 0xAB
        assert regs.pc == 1

    def test_fetch_sequential(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        mem.write(0, 0x11)
        mem.write(1, 0x22)
        cu.fetch()
        assert regs.ir == 0x11
        cu.fetch()
        assert regs.ir == 0x22
        assert regs.pc == 2


class TestDecode:
    """Decode cycle."""

    def test_decode_extracts_opcode_and_operand(self) -> None:
        _, regs, _, _, cu = _make_cu()
        regs.ir = 0x1E  # LOAD 14
        opcode, operand = cu.decode()
        assert opcode == 0x1
        assert operand == 0xE

    def test_decode_halt(self) -> None:
        _, regs, _, _, cu = _make_cu()
        regs.ir = 0xFF
        opcode, operand = cu.decode()
        assert opcode == 0xF
        assert operand == 0xF


class TestExecute:
    """Execute cycle — one test per instruction."""

    def test_execute_load(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        mem.write(0x0E, 42)
        regs.ir = 0x1E
        running = cu.execute(0x1, 0x0E)
        assert running is True
        assert regs.a == 42

    def test_execute_store(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        regs.a = 99
        regs.ir = 0x2D
        cu.execute(0x2, 0x0D)
        assert mem.read(0x0D) == 99

    def test_execute_add(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        regs.a = 10
        mem.write(0x0F, 20)
        regs.ir = 0x3F
        cu.execute(0x3, 0x0F)
        assert regs.a == 30
        assert regs.zero_flag is False

    def test_execute_sub_sets_zero_flag(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        regs.a = 5
        mem.write(0x0F, 5)
        regs.ir = 0x4F
        cu.execute(0x4, 0x0F)
        assert regs.a == 0
        assert regs.zero_flag is True

    def test_execute_jmp(self) -> None:
        _, regs, _, _, cu = _make_cu()
        regs.ir = 0x5A
        cu.execute(0x5, 0x0A)
        assert regs.pc == 0x0A

    def test_execute_jz_jumps_when_flag_set(self) -> None:
        _, regs, _, _, cu = _make_cu()
        regs.zero_flag = True
        regs.ir = 0x6A
        cu.execute(0x6, 0x0A)
        assert regs.pc == 0x0A

    def test_execute_jz_no_jump_when_flag_clear(self) -> None:
        _, regs, _, _, cu = _make_cu()
        regs.zero_flag = False
        regs.pc = 5
        regs.ir = 0x6A
        cu.execute(0x6, 0x0A)
        assert regs.pc == 5  # unchanged

    def test_execute_halt(self) -> None:
        _, regs, _, _, cu = _make_cu()
        regs.ir = 0xFF
        running = cu.execute(0xF, 0xF)
        assert running is False


class TestStep:
    """Full step integration."""

    def test_step_runs_full_cycle(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        mem.write(0, 0x1E)  # LOAD 14
        mem.write(14, 77)
        running = cu.step()
        assert running is True
        assert regs.a == 77
        assert regs.pc == 1

    def test_step_halts_on_0xFF(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        mem.write(0, 0xFF)
        running = cu.step()
        assert running is False


# ============================================================================
# Extended tests — stack, I/O, interrupts, 2-byte instructions
# ============================================================================


class TestPushPop:
    """PUSH and POP stack operations."""

    def test_push_decrements_sp_and_writes(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        regs.a = 42
        regs.ir = 0xC0  # PUSH
        cu.execute(0xC, 0x0)
        assert mem.read(0xFF) == 42
        assert regs.sp == 0xFE

    def test_pop_increments_sp_and_reads(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        mem.write(0xFF, 77)
        regs.sp = 0xFE
        regs.ir = 0xC1  # POP
        cu.execute(0xC, 0x1)
        assert regs.a == 77
        assert regs.sp == 0xFF

    def test_push_then_pop_round_trip(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        regs.a = 0xAB
        regs.ir = 0xC0  # PUSH
        cu.execute(0xC, 0x0)
        regs.a = 0x00
        regs.ir = 0xC1  # POP
        cu.execute(0xC, 0x1)
        assert regs.a == 0xAB
        assert regs.sp == 0xFF


class TestCallRet:
    """CALL and RET subroutine support."""

    def test_call_pushes_pc_and_jumps(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        regs.pc = 0x10
        regs.ir = 0xF0  # CALL prefix
        cu.execute(0xF0, 0x40)
        assert regs.pc == 0x40
        assert mem.read(0xFF) == 0x10  # old PC on stack
        assert regs.sp == 0xFE

    def test_ret_pops_pc(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        mem.write(0xFF, 0x10)  # return address on stack
        regs.sp = 0xFE
        regs.ir = 0xC2  # RET
        cu.execute(0xC, 0x2)
        assert regs.pc == 0x10
        assert regs.sp == 0xFF

    def test_call_ret_round_trip(self) -> None:
        """CALL pushes PC, subroutine runs, RET returns to next instruction."""
        mem, regs, _, _, cu = _make_cu()
        # Program: CALL 0x10, HALT
        # At 0x10: RET
        mem.write(0x00, 0xF0)  # CALL prefix
        mem.write(0x01, 0x10)  # address byte
        mem.write(0x02, 0xFF)  # HALT (should return here)
        mem.write(0x10, 0xC2)  # RET

        cu.step()  # CALL 0x10 → pushes PC=0x02, jumps to 0x10
        assert regs.pc == 0x10
        cu.step()  # RET → pops 0x02 into PC
        assert regs.pc == 0x02
        running = cu.step()  # HALT
        assert running is False


class TestIO:
    """IN and OUT instructions."""

    def test_in_reads_from_port(self) -> None:
        _, regs, _, io, cu = _make_cu()
        io.register_input(5, lambda: 0xAB)
        regs.ir = 0xA5  # IN 5
        cu.execute(0xA, 0x5)
        assert regs.a == 0xAB

    def test_out_writes_to_port(self) -> None:
        _, regs, _, io, cu = _make_cu()
        captured: list[int] = []
        io.register_output(3, lambda v: captured.append(v))
        regs.a = 42
        regs.ir = 0xB3  # OUT 3
        cu.execute(0xB, 0x3)
        assert captured == [42]


class TestInterruptHandling:
    """handle_interrupt() and RETI."""

    def test_handle_interrupt_pushes_and_jumps(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        mem.write(0xE0, 0x40)  # IVT → ISR at 0x40
        regs.pc = 0x10
        regs.zero_flag = True
        regs.carry_flag = False
        regs.interrupt_enable = True

        cu.handle_interrupt()

        assert regs.pc == 0x40
        assert regs.interrupt_enable is False
        assert regs.sp == 0xFD
        assert mem.read(0xFF) == 0x10  # saved PC
        flags = mem.read(0xFE)
        assert flags == 0b101  # ZF=1, CF=0, IE=1

    def test_reti_restores_pc_flags_and_reenables_ie(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        # Simulate stack left by handle_interrupt
        mem.write(0xFF, 0x10)  # saved PC
        mem.write(0xFE, 0x07)  # flags: ZF=1, CF=1, IE=1
        regs.sp = 0xFD
        regs.zero_flag = False
        regs.carry_flag = False
        regs.interrupt_enable = False

        regs.ir = 0xC3  # RETI
        cu.execute(0xC, 0x3)

        assert regs.zero_flag is True
        assert regs.carry_flag is True
        assert regs.interrupt_enable is True
        assert regs.pc == 0x10
        assert regs.sp == 0xFF

    def test_interrupt_isr_and_reti_full_cycle(self) -> None:
        """Interrupt fires, ISR runs, RETI resumes main code."""
        mem, regs, _, _, cu = _make_cu()
        # Main program at 0x00: NOP, NOP, HALT
        mem.write(0x00, 0x00)  # NOP
        mem.write(0x01, 0x00)  # NOP
        mem.write(0x02, 0xFF)  # HALT
        # ISR at 0x20: RETI
        mem.write(0x20, 0xC3)  # RETI
        mem.write(0xE0, 0x20)  # IVT → 0x20

        cu.step()  # NOP at 0x00, PC now 0x01
        assert regs.pc == 0x01

        regs.interrupt_enable = True
        cu.handle_interrupt()  # triggers interrupt
        assert regs.pc == 0x20
        assert regs.interrupt_enable is False

        cu.step()  # RETI at 0x20
        assert regs.pc == 0x01  # back to where we were
        assert regs.interrupt_enable is True

        cu.step()  # NOP at 0x01
        running = cu.step()  # HALT at 0x02
        assert running is False


class TestEIDI:
    """EI and DI instructions."""

    def test_ei_enables_interrupts(self) -> None:
        _, regs, _, _, cu = _make_cu()
        regs.ir = 0xC4  # EI
        cu.execute(0xC, 0x4)
        assert regs.interrupt_enable is True

    def test_di_disables_interrupts(self) -> None:
        _, regs, _, _, cu = _make_cu()
        regs.interrupt_enable = True
        regs.ir = 0xC5  # DI
        cu.execute(0xC, 0x5)
        assert regs.interrupt_enable is False


class TestTwoByteInstructions:
    """2-byte JMPF, JZF, JCF."""

    def test_jmpf_jumps_to_full_address(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        mem.write(0x00, 0xF1)  # JMPF prefix
        mem.write(0x01, 0x80)  # address byte
        cu.step()
        assert regs.pc == 0x80

    def test_jzf_jumps_when_zf_set(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        regs.zero_flag = True
        mem.write(0x00, 0xF2)  # JZF prefix
        mem.write(0x01, 0x50)
        cu.step()
        assert regs.pc == 0x50

    def test_jzf_no_jump_when_zf_clear(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        regs.zero_flag = False
        mem.write(0x00, 0xF2)  # JZF prefix
        mem.write(0x01, 0x50)
        cu.step()
        assert regs.pc == 0x02  # skipped over both bytes

    def test_jcf_jumps_when_cf_set(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        regs.carry_flag = True
        mem.write(0x00, 0xF3)  # JCF prefix
        mem.write(0x01, 0x30)
        cu.step()
        assert regs.pc == 0x30

    def test_jcf_no_jump_when_cf_clear(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        regs.carry_flag = False
        mem.write(0x00, 0xF3)
        mem.write(0x01, 0x30)
        cu.step()
        assert regs.pc == 0x02


class TestNop:
    """NOP instruction."""

    def test_nop_does_nothing(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        mem.write(0x00, 0x00)  # NOP
        old_a = regs.a
        running = cu.step()
        assert running is True
        assert regs.a == old_a
        assert regs.pc == 1


class TestAndOr:
    """AND and OR in control unit context."""

    def test_and_updates_a_and_flags(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        regs.a = 0xFF
        mem.write(0x0F, 0x0F)
        regs.ir = 0x7F  # AND 15
        cu.execute(0x7, 0xF)
        assert regs.a == 0x0F
        assert regs.zero_flag is False
        assert regs.carry_flag is False

    def test_or_updates_a_and_flags(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        regs.a = 0xA0
        mem.write(0x05, 0x05)
        regs.ir = 0x85  # OR 5
        cu.execute(0x8, 0x5)
        assert regs.a == 0xA5
        assert regs.zero_flag is False


class TestJc:
    """JC instruction."""

    def test_jc_jumps_when_carry_set(self) -> None:
        _, regs, _, _, cu = _make_cu()
        regs.carry_flag = True
        regs.ir = 0x9A  # JC 0xA
        cu.execute(0x9, 0xA)
        assert regs.pc == 0xA

    def test_jc_no_jump_when_carry_clear(self) -> None:
        _, regs, _, _, cu = _make_cu()
        regs.carry_flag = False
        regs.pc = 5
        regs.ir = 0x9A
        cu.execute(0x9, 0xA)
        assert regs.pc == 5


class TestAddressingModes:
    """LOADI, LOAD_IND (LOAD [addr]), and STORE_IND (STORE [addr])."""

    # ------------------------------------------------------------------
    # LOADI — load 8-bit immediate value directly into A
    # ------------------------------------------------------------------

    def test_loadi_via_execute(self) -> None:
        _, regs, _, _, cu = _make_cu()
        regs.ir = 0xF4
        cu.execute(0xF4, 0x7F)
        assert regs.a == 0x7F

    def test_loadi_full_step(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        mem.write(0x00, 0xF4)  # LOADI prefix
        mem.write(0x01, 0x2A)  # immediate value = 42
        cu.step()
        assert regs.a == 0x2A
        assert regs.pc == 0x02  # consumed both bytes

    def test_loadi_zero_value(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        regs.a = 0xFF
        mem.write(0x00, 0xF4)
        mem.write(0x01, 0x00)
        cu.step()
        assert regs.a == 0x00

    def test_loadi_does_not_touch_flags(self) -> None:
        """LOADI is a move; it must not modify ZF or CF."""
        mem, regs, _, _, cu = _make_cu()
        regs.zero_flag = False
        regs.carry_flag = True
        mem.write(0x00, 0xF4)
        mem.write(0x01, 0x00)
        cu.step()
        assert regs.zero_flag is False
        assert regs.carry_flag is True

    # ------------------------------------------------------------------
    # LOAD_IND — A = mem[mem[addr]]
    # ------------------------------------------------------------------

    def test_load_ind_via_execute(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        mem.write(0x10, 0x20)  # mem[0x10] = 0x20  (pointer)
        mem.write(0x20, 0x99)  # mem[0x20] = 0x99  (value)
        regs.ir = 0xF5
        cu.execute(0xF5, 0x10)
        assert regs.a == 0x99

    def test_load_ind_full_step(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        mem.write(0x30, 0x50)
        mem.write(0x50, 0xAB)
        mem.write(0x00, 0xF5)  # LOAD_IND prefix
        mem.write(0x01, 0x30)  # addr = 0x30
        cu.step()
        assert regs.a == 0xAB
        assert regs.pc == 0x02

    def test_load_ind_does_not_touch_flags(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        mem.write(0x10, 0x20)
        mem.write(0x20, 0x55)
        regs.zero_flag = True
        regs.carry_flag = True
        mem.write(0x00, 0xF5)
        mem.write(0x01, 0x10)
        cu.step()
        assert regs.zero_flag is True
        assert regs.carry_flag is True

    # ------------------------------------------------------------------
    # STORE_IND — mem[mem[addr]] = A
    # ------------------------------------------------------------------

    def test_store_ind_via_execute(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        mem.write(0x10, 0x20)  # mem[0x10] = 0x20  (pointer)
        regs.a = 0xBB
        regs.ir = 0xF6
        cu.execute(0xF6, 0x10)
        assert mem.read(0x20) == 0xBB

    def test_store_ind_full_step(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        mem.write(0x40, 0x60)
        regs.a = 0x77
        mem.write(0x00, 0xF6)  # STORE_IND prefix
        mem.write(0x01, 0x40)  # addr = 0x40
        cu.step()
        assert mem.read(0x60) == 0x77
        assert regs.pc == 0x02

    def test_store_ind_does_not_touch_flags(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        mem.write(0x10, 0x20)
        regs.a = 0x00
        regs.zero_flag = False
        regs.carry_flag = False
        mem.write(0x00, 0xF6)
        mem.write(0x01, 0x10)
        cu.step()
        assert regs.zero_flag is False
        assert regs.carry_flag is False

    # ------------------------------------------------------------------
    # Round-trip: indirect store then indirect load
    # ------------------------------------------------------------------

    def test_store_then_load_indirect_round_trip(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        # ptr_slot at 0x50 holds the target address 0x70
        mem.write(0x50, 0x70)
        regs.a = 0xCC
        # STORE [0x50]  →  mem[0x70] = 0xCC
        mem.write(0x00, 0xF6)
        mem.write(0x01, 0x50)
        cu.step()
        assert mem.read(0x70) == 0xCC

        regs.a = 0x00
        # LOAD [0x50]  →  A = mem[0x70] = 0xCC
        mem.write(0x02, 0xF5)
        mem.write(0x03, 0x50)
        cu.step()
        assert regs.a == 0xCC


class TestMultiRegisterOps:
    """B/C load-store, MOV, and register-register ALU behavior."""

    def test_load_b_from_memory(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        mem.write(0x80, 0x2A)
        regs.ir = 0xF7
        cu.execute(0xF7, 0x80)
        assert regs.b == 0x2A

    def test_load_c_from_memory(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        mem.write(0x81, 0x3B)
        regs.ir = 0xF8
        cu.execute(0xF8, 0x81)
        assert regs.c == 0x3B

    def test_loadi_b(self) -> None:
        _, regs, _, _, cu = _make_cu()
        regs.ir = 0xF9
        cu.execute(0xF9, 0x44)
        assert regs.b == 0x44

    def test_loadi_c(self) -> None:
        _, regs, _, _, cu = _make_cu()
        regs.ir = 0xFA
        cu.execute(0xFA, 0x55)
        assert regs.c == 0x55

    def test_store_b_to_memory(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        regs.b = 0xAA
        regs.ir = 0xFB
        cu.execute(0xFB, 0x82)
        assert mem.read(0x82) == 0xAA

    def test_store_c_to_memory(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        regs.c = 0xBB
        regs.ir = 0xFC
        cu.execute(0xFC, 0x83)
        assert mem.read(0x83) == 0xBB

    @pytest.mark.parametrize(
        ("pair_code", "a", "b", "c", "expect_a", "expect_b", "expect_c"),
        [
            (0, 1, 2, 3, 1, 2, 3),  # A<-A
            (1, 1, 2, 3, 2, 2, 3),  # A<-B
            (2, 1, 2, 3, 3, 2, 3),  # A<-C
            (3, 1, 2, 3, 1, 1, 3),  # B<-A
            (4, 1, 2, 3, 1, 2, 3),  # B<-B
            (5, 1, 2, 3, 1, 3, 3),  # B<-C
            (6, 1, 2, 3, 1, 2, 1),  # C<-A
            (7, 1, 2, 3, 1, 2, 2),  # C<-B
            (8, 1, 2, 3, 1, 2, 3),  # C<-C
        ],
    )
    def test_mov_all_9_pairs(
        self,
        pair_code: int,
        a: int,
        b: int,
        c: int,
        expect_a: int,
        expect_b: int,
        expect_c: int,
    ) -> None:
        _, regs, _, _, cu = _make_cu()
        regs.a = a
        regs.b = b
        regs.c = c
        regs.ir = 0xE0 | pair_code
        cu.execute(0xE, pair_code)
        assert regs.a == expect_a
        assert regs.b == expect_b
        assert regs.c == expect_c

    def test_add_reg_a_b(self) -> None:
        _, regs, _, _, cu = _make_cu()
        regs.a = 10
        regs.b = 5
        regs.ir = 0xFD
        cu.execute(0xFD, (0 << 8) | 0x01)  # ADD, pair A<-B
        assert regs.a == 15
        assert regs.b == 5
        assert regs.zero_flag is False
        assert regs.carry_flag is False

    def test_sub_reg_c_a(self) -> None:
        _, regs, _, _, cu = _make_cu()
        regs.c = 20
        regs.a = 7
        regs.ir = 0xFD
        cu.execute(0xFD, (1 << 8) | 0x06)  # SUB, pair C<-A
        assert regs.c == 13
        assert regs.a == 7

    def test_and_reg_b_c(self) -> None:
        _, regs, _, _, cu = _make_cu()
        regs.b = 0xF0
        regs.c = 0x0F
        regs.ir = 0xFD
        cu.execute(0xFD, (2 << 8) | 0x05)  # AND, pair B<-C
        assert regs.b == 0x00
        assert regs.zero_flag is True
        assert regs.carry_flag is False

    def test_or_reg_c_b(self) -> None:
        _, regs, _, _, cu = _make_cu()
        regs.c = 0xA0
        regs.b = 0x0F
        regs.ir = 0xFD
        cu.execute(0xFD, (3 << 8) | 0x07)  # OR, pair C<-B
        assert regs.c == 0xAF
        assert regs.zero_flag is False

    def test_alu_reg_three_byte_decode_and_step(self) -> None:
        mem, regs, _, _, cu = _make_cu()
        regs.a = 1
        regs.b = 2
        mem.write(0x00, 0xFD)  # ALU_REG prefix
        mem.write(0x01, 0x00)  # ADD op
        mem.write(0x02, 0x01)  # pair A<-B
        cu.step()
        assert regs.a == 3
        assert regs.pc == 0x03
