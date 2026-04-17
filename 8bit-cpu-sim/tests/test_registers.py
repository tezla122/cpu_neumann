"""Tests for cpu.registers.Registers — original + extended register tests."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from cpu.registers import Registers


class TestInit:
    """Power-on defaults."""

    def test_all_zero_on_init(self) -> None:
        regs = Registers()
        assert regs.pc == 0
        assert regs.ir == 0
        assert regs.a == 0
        assert regs.b == 0
        assert regs.c == 0
        assert regs.zero_flag is False

    def test_reset_restores_defaults(self) -> None:
        regs = Registers()
        regs.pc = 100
        regs.a = 200
        regs.b = 201
        regs.c = 202
        regs.zero_flag = True
        regs.reset()
        assert regs.pc == 0
        assert regs.ir == 0
        assert regs.a == 0
        assert regs.b == 0
        assert regs.c == 0
        assert regs.zero_flag is False


class TestValidValues:
    """Accept in-range values."""

    def test_pc_accepts_valid_range(self) -> None:
        regs = Registers()
        regs.pc = 0
        assert regs.pc == 0
        regs.pc = 255
        assert regs.pc == 255

    def test_a_accepts_valid_range(self) -> None:
        regs = Registers()
        regs.a = 0
        assert regs.a == 0
        regs.a = 255
        assert regs.a == 255

    def test_ir_accepts_valid_range(self) -> None:
        regs = Registers()
        regs.ir = 0
        assert regs.ir == 0
        regs.ir = 255
        assert regs.ir == 255

    def test_b_accepts_valid_range(self) -> None:
        regs = Registers()
        regs.b = 0
        assert regs.b == 0
        regs.b = 255
        assert regs.b == 255

    def test_c_accepts_valid_range(self) -> None:
        regs = Registers()
        regs.c = 0
        assert regs.c == 0
        regs.c = 255
        assert regs.c == 255

    def test_zero_flag_is_boolean(self) -> None:
        regs = Registers()
        regs.zero_flag = True
        assert regs.zero_flag is True
        regs.zero_flag = False
        assert regs.zero_flag is False


class TestBoundsChecking:
    """Out-of-range values."""

    def test_pc_rejects_negative(self) -> None:
        regs = Registers()
        with pytest.raises(ValueError):
            regs.pc = -1

    def test_pc_rejects_over_255(self) -> None:
        regs = Registers()
        with pytest.raises(ValueError):
            regs.pc = 256

    def test_a_rejects_over_255(self) -> None:
        regs = Registers()
        with pytest.raises(ValueError):
            regs.a = 300

    def test_b_rejects_over_255(self) -> None:
        regs = Registers()
        with pytest.raises(ValueError):
            regs.b = 300

    def test_c_rejects_over_255(self) -> None:
        regs = Registers()
        with pytest.raises(ValueError):
            regs.c = 300

    def test_zero_flag_rejects_non_bool(self) -> None:
        regs = Registers()
        with pytest.raises(TypeError):
            regs.zero_flag = 1  # type: ignore[assignment]


class TestRepr:
    """String representation."""

    def test_repr_contains_hex_values(self) -> None:
        regs = Registers()
        regs.pc = 0x10
        regs.a = 0xFF
        r = repr(regs)
        assert "0x10" in r
        assert "0xFF" in r

    def test_repr_shows_zero_flag(self) -> None:
        regs = Registers()
        regs.zero_flag = True
        assert "True" in repr(regs)


# ============================================================================
# Extended register tests
# ============================================================================


class TestStackPointer:
    """SP register."""

    def test_sp_initializes_to_0xFF(self) -> None:
        regs = Registers()
        assert regs.sp == 0xFF

    def test_sp_resets_to_0xFF(self) -> None:
        regs = Registers()
        regs.sp = 0x80
        regs.reset()
        assert regs.sp == 0xFF

    def test_sp_accepts_valid_range(self) -> None:
        regs = Registers()
        regs.sp = 0
        assert regs.sp == 0
        regs.sp = 255
        assert regs.sp == 255

    def test_sp_rejects_out_of_range(self) -> None:
        regs = Registers()
        with pytest.raises(ValueError):
            regs.sp = 256
        with pytest.raises(ValueError):
            regs.sp = -1


class TestCarryFlag:
    """CF register."""

    def test_carry_flag_initializes_false(self) -> None:
        regs = Registers()
        assert regs.carry_flag is False

    def test_carry_flag_resets_to_false(self) -> None:
        regs = Registers()
        regs.carry_flag = True
        regs.reset()
        assert regs.carry_flag is False

    def test_carry_flag_rejects_non_bool(self) -> None:
        regs = Registers()
        with pytest.raises(TypeError):
            regs.carry_flag = 1  # type: ignore[assignment]


class TestInterruptEnable:
    """IE register."""

    def test_interrupt_enable_initializes_false(self) -> None:
        regs = Registers()
        assert regs.interrupt_enable is False

    def test_interrupt_enable_resets_to_false(self) -> None:
        regs = Registers()
        regs.interrupt_enable = True
        regs.reset()
        assert regs.interrupt_enable is False

    def test_interrupt_enable_rejects_non_bool(self) -> None:
        regs = Registers()
        with pytest.raises(TypeError):
            regs.interrupt_enable = 1  # type: ignore[assignment]


class TestFlagsByte:
    """Flags-byte packing/unpacking."""

    def test_get_flags_byte_all_clear(self) -> None:
        regs = Registers()
        assert regs.get_flags_byte() == 0

    def test_get_flags_byte_zf_only(self) -> None:
        regs = Registers()
        regs.zero_flag = True
        assert regs.get_flags_byte() == 0b001

    def test_get_flags_byte_cf_only(self) -> None:
        regs = Registers()
        regs.carry_flag = True
        assert regs.get_flags_byte() == 0b010

    def test_get_flags_byte_ie_only(self) -> None:
        regs = Registers()
        regs.interrupt_enable = True
        assert regs.get_flags_byte() == 0b100

    def test_get_flags_byte_all_set(self) -> None:
        regs = Registers()
        regs.zero_flag = True
        regs.carry_flag = True
        regs.interrupt_enable = True
        assert regs.get_flags_byte() == 0b111

    def test_set_flags_byte_restores_all(self) -> None:
        regs = Registers()
        regs.set_flags_byte(0b111)
        assert regs.zero_flag is True
        assert regs.carry_flag is True
        assert regs.interrupt_enable is True

    def test_set_flags_byte_partial(self) -> None:
        regs = Registers()
        regs.set_flags_byte(0b010)  # CF only
        assert regs.zero_flag is False
        assert regs.carry_flag is True
        assert regs.interrupt_enable is False

    def test_flags_byte_round_trip(self) -> None:
        regs = Registers()
        regs.zero_flag = True
        regs.carry_flag = False
        regs.interrupt_enable = True
        packed = regs.get_flags_byte()
        regs.reset()
        regs.set_flags_byte(packed)
        assert regs.zero_flag is True
        assert regs.carry_flag is False
        assert regs.interrupt_enable is True


class TestReprExtended:
    """Extended __repr__ fields."""

    def test_repr_contains_sp(self) -> None:
        regs = Registers()
        assert "SP=0xFF" in repr(regs)

    def test_repr_contains_cf(self) -> None:
        regs = Registers()
        regs.carry_flag = True
        assert "CF=True" in repr(regs)

    def test_repr_contains_ie(self) -> None:
        regs = Registers()
        regs.interrupt_enable = True
        assert "IE=True" in repr(regs)

    def test_repr_contains_b_and_c(self) -> None:
        regs = Registers()
        regs.b = 0x12
        regs.c = 0x34
        r = repr(regs)
        assert "B=0x12" in r
        assert "C=0x34" in r
