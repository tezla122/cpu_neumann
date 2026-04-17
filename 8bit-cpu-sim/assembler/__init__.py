"""Assembler package — exposes the Assembler class and opcode tables."""

from assembler.assembler import Assembler
from assembler.opcodes import OPCODES_1BYTE, OPCODES_2BYTE, HALT_BYTE

__all__ = ["Assembler", "OPCODES_1BYTE", "OPCODES_2BYTE", "HALT_BYTE"]
