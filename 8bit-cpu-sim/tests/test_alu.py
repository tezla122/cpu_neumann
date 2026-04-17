"""Tests for cpu.alu.ALU — original + extended ALU tests."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from cpu.alu import ALU


class TestAdd:
    """ADD operation."""

    def test_add_basic(self) -> None:
        alu = ALU()
        result, zf, cf = alu.execute("ADD", 10, 20)
        assert result == 30
        assert zf is False

    def test_add_overflow_wraps(self) -> None:
        alu = ALU()
        result, zf, cf = alu.execute("ADD", 200, 100)
        assert result == (200 + 100) & 0xFF  # 44
        assert zf is False

    def test_add_zero_flag(self) -> None:
        alu = ALU()
        result, zf, cf = alu.execute("ADD", 0, 0)
        assert result == 0
        assert zf is True

    def test_add_overflow_to_zero(self) -> None:
        alu = ALU()
        result, zf, cf = alu.execute("ADD", 128, 128)
        assert result == 0
        assert zf is True


class TestSub:
    """SUB operation."""

    def test_sub_basic(self) -> None:
        alu = ALU()
        result, zf, cf = alu.execute("SUB", 20, 10)
        assert result == 10
        assert zf is False

    def test_sub_underflow_wraps(self) -> None:
        alu = ALU()
        result, zf, cf = alu.execute("SUB", 0, 1)
        assert result == 0xFF  # 255
        assert zf is False

    def test_sub_zero_flag(self) -> None:
        alu = ALU()
        result, zf, cf = alu.execute("SUB", 42, 42)
        assert result == 0
        assert zf is True


class TestUnknownOperation:
    """Error handling."""

    def test_unknown_operation_raises(self) -> None:
        alu = ALU()
        with pytest.raises(ValueError, match="Unknown ALU operation"):
            alu.execute("MUL", 1, 2)

    def test_another_unknown_operation(self) -> None:
        alu = ALU()
        with pytest.raises(ValueError):
            alu.execute("DIV", 10, 2)


# ============================================================================
# Extended ALU tests
# ============================================================================


class TestCarryFlag:
    """Carry / borrow flag behaviour."""

    def test_add_no_carry(self) -> None:
        alu = ALU()
        _, _, cf = alu.execute("ADD", 10, 20)
        assert cf is False

    def test_add_sets_carry_on_overflow(self) -> None:
        alu = ALU()
        result, _, cf = alu.execute("ADD", 0xFF, 0x01)
        assert result == 0x00
        assert cf is True

    def test_add_carry_wraps_to_nonzero(self) -> None:
        alu = ALU()
        result, zf, cf = alu.execute("ADD", 200, 100)
        assert result == 44
        assert zf is False
        assert cf is True

    def test_sub_no_borrow(self) -> None:
        alu = ALU()
        _, _, cf = alu.execute("SUB", 20, 10)
        assert cf is False

    def test_sub_sets_carry_on_borrow(self) -> None:
        alu = ALU()
        result, _, cf = alu.execute("SUB", 0x01, 0x02)
        assert result == 0xFF
        assert cf is True

    def test_sub_equal_no_borrow(self) -> None:
        alu = ALU()
        _, zf, cf = alu.execute("SUB", 42, 42)
        assert zf is True
        assert cf is False


class TestAnd:
    """AND operation."""

    def test_and_basic(self) -> None:
        alu = ALU()
        result, zf, cf = alu.execute("AND", 0xFF, 0x0F)
        assert result == 0x0F
        assert zf is False

    def test_and_zero_result(self) -> None:
        alu = ALU()
        result, zf, cf = alu.execute("AND", 0xF0, 0x0F)
        assert result == 0
        assert zf is True

    def test_and_clears_carry(self) -> None:
        alu = ALU()
        _, _, cf = alu.execute("AND", 0xFF, 0xFF)
        assert cf is False


class TestOr:
    """OR operation."""

    def test_or_basic(self) -> None:
        alu = ALU()
        result, zf, cf = alu.execute("OR", 0xA0, 0x05)
        assert result == 0xA5
        assert zf is False

    def test_or_zero_result(self) -> None:
        alu = ALU()
        result, zf, cf = alu.execute("OR", 0x00, 0x00)
        assert result == 0
        assert zf is True

    def test_or_clears_carry(self) -> None:
        alu = ALU()
        _, _, cf = alu.execute("OR", 0xAA, 0x55)
        assert cf is False
