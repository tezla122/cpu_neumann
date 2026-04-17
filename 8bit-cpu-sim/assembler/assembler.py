"""
8-bit CPU Simulator — Two-Pass Assembler (Extended)

Parses ``.asm`` source text into bytecode.  Supports labels (forward and
backward references), 1-byte and 2-byte instructions, comments, and blank
lines.  All encoding rules derive from ``assembler.opcodes``.
"""

from __future__ import annotations

from assembler.opcodes import (
    OPCODES_1BYTE, OPCODES_2BYTE,
    OPERAND_INSTRUCTIONS, IMPLIED_INSTRUCTIONS,
    HALT_BYTE, OPCODES_3BYTE, REGISTER_CODES, ALU_REG_OPS,
)

COMMENT_CHAR = ";"
OPERAND_MASK = 0x0F
MAX_4BIT = 0x0F


class Assembler:
    """Translate assembly source (with labels) into bytecode."""

    def assemble(self, source: str) -> list[int]:
        """Assemble *source* text into a list of encoded bytes.

        Performs two passes:

        * **Pass 1** — scan for label definitions and count instruction
          bytes to build a ``label → address`` dict.
        * **Pass 2** — emit bytes, resolving label references as operands.

        Label syntax::

            my_label:           ; standalone label line
            my_label: LOAD 5   ; label + instruction on same line

        Raises:
            SyntaxError:  on unknown mnemonics.
            ValueError:   if a 4-bit operand exceeds 15.
        """
        lines = self._preprocess(source)
        labels = self._pass1(lines)
        return self._pass2(lines, labels)

    # ---- internal -----------------------------------------------------------

    @staticmethod
    def _preprocess(source: str) -> list[tuple[int, str]]:
        """Strip comments and blank lines; return (line_no, stripped_text)."""
        result: list[tuple[int, str]] = []
        for line_no, raw in enumerate(source.splitlines(), start=1):
            text = raw.split(COMMENT_CHAR, 1)[0].strip()
            if text:
                result.append((line_no, text))
        return result

    def _pass1(self, lines: list[tuple[int, str]]) -> dict[str, int]:
        """Build the label → address map (first pass)."""
        labels: dict[str, int] = {}
        address = 0

        for line_no, text in lines:
            tokens = text.split()
            idx = 0

            if tokens[idx].endswith(":"):
                label = tokens[idx][:-1]
                if not label:
                    raise SyntaxError(f"Empty label on line {line_no}")
                labels[label] = address
                idx += 1

            if idx >= len(tokens):
                continue

            address += self._instruction_size(tokens, idx, line_no)

        return labels

    def _pass2(
        self,
        lines: list[tuple[int, str]],
        labels: dict[str, int],
    ) -> list[int]:
        """Emit bytecode (second pass)."""
        bytecode: list[int] = []

        for line_no, text in lines:
            tokens = text.split()
            idx = 0

            if tokens[idx].endswith(":"):
                idx += 1

            if idx >= len(tokens):
                continue

            mnemonic = tokens[idx].upper()
            idx += 1
            operand_text = self._operand_text(tokens, idx)

            # Remap LOAD [addr] → LOAD_IND and STORE [addr] → STORE_IND
            # before dispatching so the 2-byte branch handles them.
            if (
                mnemonic in ("LOAD", "STORE")
                and idx < len(tokens)
                and tokens[idx].startswith("[")
            ):
                mnemonic = "LOAD_IND" if mnemonic == "LOAD" else "STORE_IND"

            if mnemonic in IMPLIED_INSTRUCTIONS:
                bytecode.append(OPCODES_1BYTE[mnemonic])
                continue

            if mnemonic == "MOV":
                if not operand_text:
                    raise SyntaxError(
                        f"Mnemonic '{mnemonic}' requires two register operands "
                        f"(line {line_no})"
                    )
                regs = self._parse_reg_pair(operand_text, line_no)
                dest_code = REGISTER_CODES[regs[0]]
                src_code = REGISTER_CODES[regs[1]]
                pair_code = (dest_code * 3) + src_code
                bytecode.append(OPCODES_1BYTE["MOV"] | (pair_code & OPERAND_MASK))
                continue

            if mnemonic in ALU_REG_OPS:
                maybe_pair = self._try_parse_reg_pair(operand_text)
                if maybe_pair is not None:
                    dest_code = REGISTER_CODES[maybe_pair[0]]
                    src_code = REGISTER_CODES[maybe_pair[1]]
                    pair_code = (dest_code * 3) + src_code
                    bytecode.append(OPCODES_3BYTE["ALU_REG"])
                    bytecode.append(ALU_REG_OPS[mnemonic])
                    bytecode.append(pair_code & 0xFF)
                    continue

            # 2-byte B/C forms expressed via legacy mnemonics + register token:
            # LOAD B, addr / LOAD C, addr / LOADI B, val / STORE B, addr / STORE C, addr
            if mnemonic in ("LOAD", "LOADI", "STORE"):
                reg_addr = self._try_parse_reg_addr(operand_text)
                if reg_addr is not None:
                    reg_name, addr_token = reg_addr
                    remap = self._remap_reg_mem_mnemonic(mnemonic, reg_name)
                    address = self._resolve_operand(addr_token, labels, line_no)
                    bytecode.append(OPCODES_2BYTE[remap])
                    bytecode.append(address & 0xFF)
                    continue

            if mnemonic in OPERAND_INSTRUCTIONS:
                if idx >= len(tokens):
                    raise SyntaxError(
                        f"Mnemonic '{mnemonic}' requires an operand "
                        f"(line {line_no})"
                    )
                operand = self._resolve_operand(tokens[idx], labels, line_no)
                if operand > MAX_4BIT:
                    raise ValueError(
                        f"Operand {operand} exceeds 4-bit max ({MAX_4BIT}) "
                        f"for '{mnemonic}' on line {line_no}"
                    )
                base = OPCODES_1BYTE[mnemonic]
                bytecode.append(base | (operand & OPERAND_MASK))
                continue

            if mnemonic in OPCODES_2BYTE:
                if idx >= len(tokens):
                    raise SyntaxError(
                        f"Mnemonic '{mnemonic}' requires an address operand "
                        f"(line {line_no})"
                    )
                # Strip enclosing brackets for indirect-addressing syntax:
                # LOAD [addr] / STORE [addr] arrive here as "[addr]" tokens.
                raw = tokens[idx]
                operand_token = raw[1:-1] if raw.startswith("[") and raw.endswith("]") else raw
                address = self._resolve_operand(operand_token, labels, line_no)
                bytecode.append(OPCODES_2BYTE[mnemonic])
                bytecode.append(address & 0xFF)
                continue

            raise SyntaxError(
                f"Unknown mnemonic '{mnemonic}' on line {line_no}"
            )

        return bytecode

    # ---- helpers ------------------------------------------------------------

    def _instruction_size(
        self,
        tokens: list[str],
        idx: int,
        line_no: int,
    ) -> int:
        """Return the byte count of *mnemonic* (1 or 2)."""
        mnemonic = tokens[idx].upper()

        # MOV regD,regS
        if mnemonic == "MOV":
            return 1

        # ALU register form: ADD/SUB/AND/OR regD,regS (3 bytes)
        operand_text = self._operand_text(tokens, idx + 1)

        if mnemonic in ALU_REG_OPS:
            if self._try_parse_reg_pair(operand_text) is not None:
                return 3

        # LOAD/LOADI/STORE register-target forms are 2-byte instructions.
        if mnemonic in ("LOAD", "LOADI", "STORE"):
            if self._try_parse_reg_addr(operand_text) is not None:
                return 2

        if mnemonic in IMPLIED_INSTRUCTIONS or mnemonic in OPERAND_INSTRUCTIONS:
            return 1
        if mnemonic in OPCODES_2BYTE:
            return 2
        if mnemonic in OPCODES_3BYTE:
            return 3
        raise SyntaxError(f"Unknown mnemonic '{mnemonic}' on line {line_no}")

    @staticmethod
    def _operand_text(tokens: list[str], idx: int) -> str:
        if idx >= len(tokens):
            return ""
        return "".join(tokens[idx:])

    @staticmethod
    def _try_parse_reg_pair(token: str) -> tuple[str, str] | None:
        text = token.replace(" ", "")
        parts = text.split(",")
        if len(parts) != 2:
            return None
        dest, src = parts[0].upper(), parts[1].upper()
        if dest in REGISTER_CODES and src in REGISTER_CODES:
            return dest, src
        return None

    def _parse_reg_pair(self, token: str, line_no: int) -> tuple[str, str]:
        result = self._try_parse_reg_pair(token)
        if result is None:
            raise SyntaxError(
                f"Expected register pair like 'A,B' for MOV on line {line_no}"
            )
        return result

    @staticmethod
    def _try_parse_reg_addr(token: str) -> tuple[str, str] | None:
        text = token.replace(" ", "")
        parts = text.split(",")
        if len(parts) != 2:
            return None
        reg_name, addr_token = parts[0].upper(), parts[1]
        if reg_name in ("B", "C"):
            return reg_name, addr_token
        return None

    @staticmethod
    def _remap_reg_mem_mnemonic(mnemonic: str, reg_name: str) -> str:
        if mnemonic == "LOAD":
            return "LOAD_B" if reg_name == "B" else "LOAD_C"
        if mnemonic == "LOADI":
            return "LOADI_B" if reg_name == "B" else "LOADI_C"
        if mnemonic == "STORE":
            return "STORE_B" if reg_name == "B" else "STORE_C"
        raise ValueError(f"Unsupported register-memory mnemonic '{mnemonic}'")

    @staticmethod
    def _resolve_operand(
        token: str,
        labels: dict[str, int],
        line_no: int,
    ) -> int:
        """Resolve *token* as a numeric literal or a label reference."""
        try:
            return int(token)
        except ValueError:
            if token in labels:
                return labels[token]
            raise SyntaxError(
                f"Unknown label or invalid operand '{token}' on line {line_no}"
            ) from None


if __name__ == "__main__":
    src = """\
; Fibonacci (abbreviated)
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
    asm = Assembler()
    code = asm.assemble(src)
    print("Bytecode:", [f"0x{b:02X}" for b in code])
    print(f"Length: {len(code)} bytes")
