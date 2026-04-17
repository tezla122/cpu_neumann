"""
8-bit CPU Simulator — Arithmetic Logic Unit (Extended)

Supports ADD, SUB, AND, OR with 8-bit masking, zero-flag, and carry-flag.
"""

BYTE_MASK = 0xFF

OPERATIONS = frozenset({"ADD", "SUB", "AND", "OR"})


class ALU:
    """Arithmetic Logic Unit for the 8-bit CPU."""

    def execute(self, operation: str, a: int, b: int) -> tuple[int, bool, bool]:
        """Perform *operation* on operands *a* and *b*.

        Args:
            operation: ``"ADD"``, ``"SUB"``, ``"AND"``, or ``"OR"``.
            a: First operand (accumulator value).
            b: Second operand (memory value).

        Returns:
            A tuple ``(result, zero_flag, carry_flag)`` where *result* is
            masked to 8 bits, *zero_flag* indicates whether the result is
            zero, and *carry_flag* indicates arithmetic carry or borrow.

        Raises:
            ValueError: if *operation* is not recognised.
        """
        if operation == "ADD":
            raw = a + b
            carry = raw > BYTE_MASK
            result = raw & BYTE_MASK
        elif operation == "SUB":
            carry = a < b
            result = (a - b) & BYTE_MASK
        elif operation == "AND":
            result = (a & b) & BYTE_MASK
            carry = False
        elif operation == "OR":
            result = (a | b) & BYTE_MASK
            carry = False
        else:
            raise ValueError(
                f"Unknown ALU operation '{operation}'; "
                f"expected one of {sorted(OPERATIONS)}"
            )

        return result, result == 0, carry


if __name__ == "__main__":
    alu = ALU()
    print("10 + 20    =", alu.execute("ADD", 10, 20))
    print("0xFF + 0x01=", alu.execute("ADD", 0xFF, 0x01))
    print("0 - 1      =", alu.execute("SUB", 0, 1))
    print("0xAA & 0x0F=", alu.execute("AND", 0xAA, 0x0F))
    print("0xA0 | 0x0F=", alu.execute("OR", 0xA0, 0x0F))
