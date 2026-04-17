"""Tests for cpu.memory.Memory — minimum 10 tests."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from cpu.memory import Memory


class TestMemoryInit:
    """Verify power-on state."""

    def test_all_cells_zero_on_init(self) -> None:
        mem = Memory()
        for addr in range(256):
            assert mem.read(addr) == 0


class TestReadWrite:
    """Basic single-byte operations."""

    def test_write_then_read(self) -> None:
        mem = Memory()
        mem.write(0x10, 0xAB)
        assert mem.read(0x10) == 0xAB

    def test_boundary_address_0x00(self) -> None:
        mem = Memory()
        mem.write(0x00, 42)
        assert mem.read(0x00) == 42

    def test_boundary_address_0xFF(self) -> None:
        mem = Memory()
        mem.write(0xFF, 99)
        assert mem.read(0xFF) == 99

    def test_neighbours_not_corrupted(self) -> None:
        mem = Memory()
        mem.write(0x10, 0xFF)
        assert mem.read(0x0F) == 0
        assert mem.read(0x11) == 0

    def test_overwrite_same_address(self) -> None:
        mem = Memory()
        mem.write(0x20, 100)
        mem.write(0x20, 200)
        assert mem.read(0x20) == 200


class TestBoundsChecking:
    """Out-of-range addresses and values."""

    def test_index_error_address_too_high(self) -> None:
        mem = Memory()
        with pytest.raises(IndexError):
            mem.read(256)

    def test_index_error_address_negative(self) -> None:
        mem = Memory()
        with pytest.raises(IndexError):
            mem.write(-1, 0)

    def test_value_error_value_too_high(self) -> None:
        mem = Memory()
        with pytest.raises(ValueError):
            mem.write(0, 256)

    def test_value_error_value_negative(self) -> None:
        mem = Memory()
        with pytest.raises(ValueError):
            mem.write(0, -1)


class TestLoadProgram:
    """Program loading."""

    def test_load_program_writes_sequentially(self) -> None:
        mem = Memory()
        mem.load_program([0x10, 0x20, 0x30])
        assert mem.read(0) == 0x10
        assert mem.read(1) == 0x20
        assert mem.read(2) == 0x30

    def test_load_program_with_start_address(self) -> None:
        mem = Memory()
        mem.load_program([0xAA, 0xBB], start_address=0x80)
        assert mem.read(0x80) == 0xAA
        assert mem.read(0x81) == 0xBB

    def test_load_program_overflow_error(self) -> None:
        mem = Memory()
        with pytest.raises(OverflowError):
            mem.load_program([0] * 257)

    def test_load_program_overflow_with_offset(self) -> None:
        mem = Memory()
        with pytest.raises(OverflowError):
            mem.load_program([0] * 10, start_address=250)


class TestDump:
    """Hex-dump output."""

    def test_dump_format(self) -> None:
        mem = Memory()
        mem.write(0, 0xAB)
        dump = mem.dump(0, 0)
        assert "0x00:" in dump
        assert "AB" in dump
