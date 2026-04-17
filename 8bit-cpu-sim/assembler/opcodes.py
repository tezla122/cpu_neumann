"""
8-bit CPU Simulator — Opcode Table (Extended ISA)

Single source of truth for mnemonic → opcode mapping.
Imported by both the assembler and the control unit.
"""

# ---------------------------------------------------------------------------
# 1-byte instructions
#   For "operand" instructions: encoded as (base | (operand & 0x0F)), 1 byte.
#   For "implied" instructions: encoded as the literal byte value.
# ---------------------------------------------------------------------------

OPCODES_1BYTE: dict[str, int] = {
    "NOP":   0x00,
    "LOAD":  0x10,
    "STORE": 0x20,
    "ADD":   0x30,
    "SUB":   0x40,
    "JMP":   0x50,
    "JZ":    0x60,
    "AND":   0x70,
    "OR":    0x80,
    "JC":    0x90,
    "IN":    0xA0,
    "OUT":   0xB0,
    "PUSH":  0xC0,
    "POP":   0xC1,
    "RET":   0xC2,
    "RETI":  0xC3,
    "EI":    0xC4,
    "DI":    0xC5,
    # Register-move family: MOV regD, regS encoded as 0xE0 | pair_code.
    "MOV":   0xE0,
    "HALT":  0xFF,
}

# ---------------------------------------------------------------------------
# 2-byte instructions (prefix byte + full 8-bit address byte)
# ---------------------------------------------------------------------------

OPCODES_2BYTE: dict[str, int] = {
    "CALL":      0xF0,
    "JMPF":      0xF1,
    "JZF":       0xF2,
    "JCF":       0xF3,
    # Immediate and indirect addressing modes
    "LOADI":     0xF4,   # A = val  (load 8-bit immediate)
    "LOAD_IND":  0xF5,   # A = mem[mem[addr]]  (load indirect)
    "STORE_IND": 0xF6,   # mem[mem[addr]] = A  (store indirect)
    # B/C register memory+immediate load/store
    "LOAD_B":    0xF7,   # B = mem[addr]
    "LOAD_C":    0xF8,   # C = mem[addr]
    "LOADI_B":   0xF9,   # B = val
    "LOADI_C":   0xFA,   # C = val
    "STORE_B":   0xFB,   # mem[addr] = B
    "STORE_C":   0xFC,   # mem[addr] = C
}

# 3-byte instructions (prefix + op selector + register-pair selector)
OPCODES_3BYTE: dict[str, int] = {
    "ALU_REG": 0xFD,  # ADD/SUB/AND/OR with register operands
}

# Register encoding used by MOV and ALU_REG.
REGISTER_CODES: dict[str, int] = {
    "A": 0,
    "B": 1,
    "C": 2,
}

# Pair encoding: pair_code = dest * 3 + src
# (A,A)=0, (A,B)=1, ..., (C,C)=8

ALU_REG_OPS: dict[str, int] = {
    "ADD": 0,
    "SUB": 1,
    "AND": 2,
    "OR": 3,
}

# ---------------------------------------------------------------------------
# Instruction categories
# ---------------------------------------------------------------------------

OPERAND_INSTRUCTIONS: frozenset[str] = frozenset({
    "LOAD", "STORE", "ADD", "SUB", "JMP", "JZ",
    "AND", "OR", "JC", "IN", "OUT",
})

IMPLIED_INSTRUCTIONS: frozenset[str] = frozenset({
    "NOP", "PUSH", "POP", "RET", "RETI", "EI", "DI", "HALT",
})

# ---------------------------------------------------------------------------
# Special byte values
# ---------------------------------------------------------------------------

HALT_BYTE = 0xFF

# Memory-map constants
IVT_ADDRESS = 0xE0
STACK_START = 0xFF

# ---------------------------------------------------------------------------
# Reverse lookup (nibble → mnemonic) for debugging
# ---------------------------------------------------------------------------

_ALL_OPCODES: dict[str, int] = {**OPCODES_1BYTE, **OPCODES_2BYTE}
OPCODE_TO_MNEMONIC: dict[int, str] = {v: k for k, v in _ALL_OPCODES.items()}


if __name__ == "__main__":
    print("1-byte instructions:")
    for mnemonic, code in OPCODES_1BYTE.items():
        print(f"  {mnemonic:6s} → 0x{code:02X}")
    print("2-byte instructions:")
    for mnemonic, prefix in OPCODES_2BYTE.items():
        print(f"  {mnemonic:6s} → 0x{prefix:02X} <addr>")
