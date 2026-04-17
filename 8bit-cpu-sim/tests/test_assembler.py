"""Tests for assembler.assembler.Assembler — original + extended tests."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from assembler.assembler import Assembler


@pytest.fixture
def asm() -> Assembler:
    return Assembler()


# ============================================================================
# Original tests (encoding behaviour preserved)
# ============================================================================


class TestSingleInstructions:
    """Individual mnemonic encoding."""

    def test_load_5_assembles_to_0x15(self, asm: Assembler) -> None:
        result = asm.assemble("LOAD 5")
        assert result == [0x15]

    def test_halt_assembles_to_0xFF(self, asm: Assembler) -> None:
        result = asm.assemble("HALT")
        assert result == [0xFF]

    def test_store_encodes_correctly(self, asm: Assembler) -> None:
        result = asm.assemble("STORE 13")
        assert result == [0x2D]

    def test_jmp_encodes_correctly(self, asm: Assembler) -> None:
        result = asm.assemble("JMP 1")
        assert result == [0x51]

    def test_jz_encodes_correctly(self, asm: Assembler) -> None:
        result = asm.assemble("JZ 6")
        assert result == [0x66]


class TestMultiLine:
    """Multi-instruction programs."""

    def test_multi_line_program(self, asm: Assembler) -> None:
        source = "LOAD 14\nADD 15\nSTORE 13\nHALT"
        result = asm.assemble(source)
        assert result == [0x1E, 0x3F, 0x2D, 0xFF]

    def test_comments_and_blank_lines_ignored(self, asm: Assembler) -> None:
        source = """\
; comment line
LOAD 14

; another comment
ADD 15

HALT
"""
        result = asm.assemble(source)
        assert result == [0x1E, 0x3F, 0xFF]


class TestErrors:
    """Error handling."""

    def test_unknown_mnemonic_raises_syntax_error(self, asm: Assembler) -> None:
        with pytest.raises(SyntaxError, match="Unknown mnemonic"):
            asm.assemble("MULTIPLY 5")

    def test_missing_operand_raises_syntax_error(self, asm: Assembler) -> None:
        with pytest.raises(SyntaxError, match="requires an operand"):
            asm.assemble("LOAD")


class TestRoundTrip:
    """Full program assembly."""

    def test_add_two_numbers_round_trip(self, asm: Assembler) -> None:
        source = """\
; Adds the values at addresses 14 and 15, stores result at address 13
LOAD 14
ADD 15
STORE 13
HALT
"""
        expected = [0x1E, 0x3F, 0x2D, 0xFF]
        assert asm.assemble(source) == expected

    def test_countdown_round_trip(self, asm: Assembler) -> None:
        source = """\
; Counts down from value at address 15 until zero
LOAD 15
SUB 14
STORE 15
JZ 5
JMP 1
HALT
"""
        expected = [0x1F, 0x4E, 0x2F, 0x65, 0x51, 0xFF]
        assert asm.assemble(source) == expected

    def test_case_insensitive_mnemonics(self, asm: Assembler) -> None:
        result = asm.assemble("load 14\nadd 15\nhalt")
        assert result == [0x1E, 0x3F, 0xFF]


# ============================================================================
# Extended tests — 2-byte instructions, labels, new mnemonics
# ============================================================================


class TestNewMnemonics:
    """New 1-byte instructions."""

    def test_nop(self, asm: Assembler) -> None:
        assert asm.assemble("NOP") == [0x00]

    def test_push(self, asm: Assembler) -> None:
        assert asm.assemble("PUSH") == [0xC0]

    def test_pop(self, asm: Assembler) -> None:
        assert asm.assemble("POP") == [0xC1]

    def test_ret(self, asm: Assembler) -> None:
        assert asm.assemble("RET") == [0xC2]

    def test_reti(self, asm: Assembler) -> None:
        assert asm.assemble("RETI") == [0xC3]

    def test_ei(self, asm: Assembler) -> None:
        assert asm.assemble("EI") == [0xC4]

    def test_di(self, asm: Assembler) -> None:
        assert asm.assemble("DI") == [0xC5]

    def test_and(self, asm: Assembler) -> None:
        assert asm.assemble("AND 15") == [0x7F]

    def test_or(self, asm: Assembler) -> None:
        assert asm.assemble("OR 10") == [0x8A]

    def test_jc(self, asm: Assembler) -> None:
        assert asm.assemble("JC 3") == [0x93]

    def test_in(self, asm: Assembler) -> None:
        assert asm.assemble("IN 0") == [0xA0]

    def test_out(self, asm: Assembler) -> None:
        assert asm.assemble("OUT 1") == [0xB1]


class TestTwoByteInstructions:
    """2-byte prefix instructions."""

    def test_call_assembles_to_two_bytes(self, asm: Assembler) -> None:
        result = asm.assemble("CALL 64")
        assert result == [0xF0, 64]

    def test_jmpf_assembles_to_two_bytes(self, asm: Assembler) -> None:
        result = asm.assemble("JMPF 128")
        assert result == [0xF1, 128]

    def test_jzf_assembles_to_two_bytes(self, asm: Assembler) -> None:
        result = asm.assemble("JZF 200")
        assert result == [0xF2, 200]

    def test_jcf_assembles_to_two_bytes(self, asm: Assembler) -> None:
        result = asm.assemble("JCF 255")
        assert result == [0xF3, 255]


class TestLabels:
    """Label definitions and references."""

    def test_label_on_own_line(self, asm: Assembler) -> None:
        source = """\
start:
    JMPF start
"""
        result = asm.assemble(source)
        assert result == [0xF1, 0x00]

    def test_forward_reference(self, asm: Assembler) -> None:
        source = """\
    JZF end
    NOP
end:
    HALT
"""
        result = asm.assemble(source)
        assert result == [0xF2, 0x03, 0x00, 0xFF]

    def test_label_inline_with_instruction(self, asm: Assembler) -> None:
        source = "loop: LOAD 5\nJMPF loop"
        result = asm.assemble(source)
        assert result == [0x15, 0xF1, 0x00]

    def test_loop_with_backward_reference(self, asm: Assembler) -> None:
        source = """\
loop:
    LOAD 15
    SUB 14
    STORE 15
    JZF done
    JMPF loop
done:
    HALT
"""
        # Addresses: loop=0, LOAD=0(1B), SUB=1(1B), STORE=2(1B),
        # JZF=3(2B), JMPF=5(2B), done=7, HALT=7(1B)
        result = asm.assemble(source)
        assert result == [0x1F, 0x4E, 0x2F, 0xF2, 0x07, 0xF1, 0x00, 0xFF]


class TestAddressingModes:
    """LOADI, LOAD [addr] (indirect), and STORE [addr] (indirect)."""

    # ------------------------------------------------------------------
    # LOADI — 8-bit immediate load
    # ------------------------------------------------------------------

    def test_loadi_assembles_to_two_bytes(self, asm: Assembler) -> None:
        assert asm.assemble("LOADI 42") == [0xF4, 42]

    def test_loadi_max_byte_value(self, asm: Assembler) -> None:
        assert asm.assemble("LOADI 255") == [0xF4, 255]

    def test_loadi_zero(self, asm: Assembler) -> None:
        assert asm.assemble("LOADI 0") == [0xF4, 0]

    def test_loadi_correct_size_for_label_resolution(self, asm: Assembler) -> None:
        """LOADI must occupy 2 bytes so that subsequent label offsets are right."""
        source = "LOADI 10\nHALT"
        assert asm.assemble(source) == [0xF4, 10, 0xFF]

    def test_loadi_label_after_loadi(self, asm: Assembler) -> None:
        source = "LOADI 5\nend:\nHALT\nJZF end"
        # LOADI=2B (addrs 0-1), end: at addr 2, HALT=1B (addr 2), JZF=2B (addrs 3-4)
        # end resolves to 2
        assert asm.assemble(source) == [0xF4, 5, 0xFF, 0xF2, 2]

    # ------------------------------------------------------------------
    # LOAD [addr] — load indirect
    # ------------------------------------------------------------------

    def test_load_indirect_assembles_to_two_bytes(self, asm: Assembler) -> None:
        assert asm.assemble("LOAD [20]") == [0xF5, 20]

    def test_load_indirect_full_address(self, asm: Assembler) -> None:
        assert asm.assemble("LOAD [200]") == [0xF5, 200]

    def test_load_indirect_with_label_operand(self, asm: Assembler) -> None:
        source = "ptr:\n    NOP\n    LOAD [ptr]"
        # ptr = 0, NOP = 1 byte → LOAD [ptr] at addr 1, operand = 0
        assert asm.assemble(source) == [0x00, 0xF5, 0x00]

    def test_load_direct_unaffected(self, asm: Assembler) -> None:
        """Plain LOAD N must still encode as a 1-byte instruction."""
        assert asm.assemble("LOAD 5") == [0x15]

    # ------------------------------------------------------------------
    # STORE [addr] — store indirect
    # ------------------------------------------------------------------

    def test_store_indirect_assembles_to_two_bytes(self, asm: Assembler) -> None:
        assert asm.assemble("STORE [30]") == [0xF6, 30]

    def test_store_indirect_full_address(self, asm: Assembler) -> None:
        assert asm.assemble("STORE [255]") == [0xF6, 255]

    def test_store_indirect_with_label_operand(self, asm: Assembler) -> None:
        source = "ptr:\n    NOP\n    STORE [ptr]"
        assert asm.assemble(source) == [0x00, 0xF6, 0x00]

    def test_store_direct_unaffected(self, asm: Assembler) -> None:
        """Plain STORE N must still encode as a 1-byte instruction."""
        assert asm.assemble("STORE 13") == [0x2D]

    # ------------------------------------------------------------------
    # Mixed program using all three new modes
    # ------------------------------------------------------------------

    def test_mixed_addressing_modes_program(self, asm: Assembler) -> None:
        source = """\
LOADI 42
STORE [200]
LOAD [200]
HALT
"""
        # LOADI  = [0xF4, 42]
        # STORE [200] = [0xF6, 200]
        # LOAD [200]  = [0xF5, 200]
        # HALT   = [0xFF]
        assert asm.assemble(source) == [0xF4, 42, 0xF6, 200, 0xF5, 200, 0xFF]

    def test_case_insensitive_loadi(self, asm: Assembler) -> None:
        assert asm.assemble("loadi 10") == [0xF4, 10]


class TestMultiRegisterEncoding:
    """B/C load-store, MOV, and register-register ALU assembly."""

    def test_load_b_address(self, asm: Assembler) -> None:
        assert asm.assemble("LOAD B, 200") == [0xF7, 200]

    def test_load_c_address(self, asm: Assembler) -> None:
        assert asm.assemble("LOAD C, 201") == [0xF8, 201]

    def test_loadi_b_immediate(self, asm: Assembler) -> None:
        assert asm.assemble("LOADI B, 77") == [0xF9, 77]

    def test_loadi_c_immediate(self, asm: Assembler) -> None:
        assert asm.assemble("LOADI C, 88") == [0xFA, 88]

    def test_store_b_address(self, asm: Assembler) -> None:
        assert asm.assemble("STORE B, 202") == [0xFB, 202]

    def test_store_c_address(self, asm: Assembler) -> None:
        assert asm.assemble("STORE C, 203") == [0xFC, 203]

    def test_mov_all_9_pairs(self, asm: Assembler) -> None:
        expected = [0xE0 + i for i in range(9)]
        code: list[int] = []
        for d in ("A", "B", "C"):
            for s in ("A", "B", "C"):
                code.extend(asm.assemble(f"MOV {d},{s}"))
        assert code == expected

    def test_add_reg_a_b(self, asm: Assembler) -> None:
        assert asm.assemble("ADD A,B") == [0xFD, 0x00, 0x01]

    def test_sub_reg_c_a(self, asm: Assembler) -> None:
        assert asm.assemble("SUB C,A") == [0xFD, 0x01, 0x06]

    def test_and_reg_b_c(self, asm: Assembler) -> None:
        assert asm.assemble("AND B,C") == [0xFD, 0x02, 0x05]

    def test_or_reg_c_b(self, asm: Assembler) -> None:
        assert asm.assemble("OR C,B") == [0xFD, 0x03, 0x07]

    def test_legacy_add_memory_form_unchanged(self, asm: Assembler) -> None:
        assert asm.assemble("ADD 15") == [0x3F]


class TestOperandRange:
    """Operand validation for 4-bit instructions."""

    def test_operand_above_15_raises_value_error(self, asm: Assembler) -> None:
        with pytest.raises(ValueError, match="exceeds 4-bit max"):
            asm.assemble("LOAD 16")

    def test_operand_15_is_valid(self, asm: Assembler) -> None:
        result = asm.assemble("LOAD 15")
        assert result == [0x1F]


class TestFibonacciRoundTrip:
    """Full fibonacci program assembly."""

    def test_fibonacci_bytecode(self, asm: Assembler) -> None:
        source = """\
main_loop:
    LOAD 12
    OR 12
    JZF done
    CALL fib_step
    LOAD 12
    SUB 15
    STORE 12
    JMP 0
    NOP
    NOP
    NOP
    NOP
    NOP
    NOP
done:
    LOAD 11
    STORE 14
    HALT
fib_step:
    LOAD 10
    ADD 11
    STORE 13
    LOAD 11
    STORE 10
    LOAD 13
    STORE 11
    RET
"""
        code = asm.assemble(source)
        # done label = 0x10, fib_step label = 0x13
        expected = [
            0x1C, 0x8C,              # LOAD 12, OR 12
            0xF2, 0x10,              # JZF done(0x10)
            0xF0, 0x13,              # CALL fib_step(0x13)
            0x1C, 0x4F, 0x2C, 0x50, # LOAD 12, SUB 15, STORE 12, JMP 0
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # 6 × NOP
            0x1B, 0x2E, 0xFF,        # LOAD 11, STORE 14, HALT
            0x1A, 0x3B, 0x2D,        # LOAD 10, ADD 11, STORE 13
            0x1B, 0x2A, 0x1D, 0x2B,  # LOAD 11, STORE 10, LOAD 13, STORE 11
            0xC2,                     # RET
        ]
        assert code == expected
