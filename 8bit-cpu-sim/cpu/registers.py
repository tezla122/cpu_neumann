"""
8-bit CPU Simulator — Register File (Extended)

Holds PC, IR, A, B, C, SP, Zero Flag, Carry Flag, and Interrupt Enable.
Every setter enforces 8-bit / boolean bounds.
"""

BYTE_MIN = 0
BYTE_MAX = 255

STACK_START = 0xFF

ZF_BIT = 0
CF_BIT = 1
IE_BIT = 2


class Registers:
    """Register file for the 8-bit CPU."""

    def __init__(self) -> None:
        """Initialise all registers to power-on defaults."""
        self._pc: int = 0
        self._ir: int = 0
        self._a: int = 0
        self._b: int = 0
        self._c: int = 0
        self._sp: int = STACK_START
        self._zero_flag: bool = False
        self._carry_flag: bool = False
        self._interrupt_enable: bool = False

    # ---- PC -----------------------------------------------------------------

    @property
    def pc(self) -> int:
        """Program Counter (0–255)."""
        return self._pc

    @pc.setter
    def pc(self, value: int) -> None:
        self._validate_byte(value, "PC")
        self._pc = value

    # ---- IR -----------------------------------------------------------------

    @property
    def ir(self) -> int:
        """Instruction Register (0–255)."""
        return self._ir

    @ir.setter
    def ir(self, value: int) -> None:
        self._validate_byte(value, "IR")
        self._ir = value

    # ---- A ------------------------------------------------------------------

    @property
    def a(self) -> int:
        """Accumulator (0–255)."""
        return self._a

    @a.setter
    def a(self, value: int) -> None:
        self._validate_byte(value, "A")
        self._a = value

    # ---- B ------------------------------------------------------------------

    @property
    def b(self) -> int:
        """General-purpose register B (0-255)."""
        return self._b

    @b.setter
    def b(self, value: int) -> None:
        self._validate_byte(value, "B")
        self._b = value

    # ---- C ------------------------------------------------------------------

    @property
    def c(self) -> int:
        """General-purpose register C (0-255)."""
        return self._c

    @c.setter
    def c(self, value: int) -> None:
        self._validate_byte(value, "C")
        self._c = value

    # ---- SP -----------------------------------------------------------------

    @property
    def sp(self) -> int:
        """Stack Pointer (0–255). Starts at 0xFF, grows downward."""
        return self._sp

    @sp.setter
    def sp(self, value: int) -> None:
        self._validate_byte(value, "SP")
        self._sp = value

    # ---- Zero Flag ----------------------------------------------------------

    @property
    def zero_flag(self) -> bool:
        """Zero Flag — set when an ALU result is 0."""
        return self._zero_flag

    @zero_flag.setter
    def zero_flag(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError(f"zero_flag must be bool, got {type(value).__name__}")
        self._zero_flag = value

    # ---- Carry Flag ---------------------------------------------------------

    @property
    def carry_flag(self) -> bool:
        """Carry Flag — set on arithmetic carry / borrow."""
        return self._carry_flag

    @carry_flag.setter
    def carry_flag(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError(f"carry_flag must be bool, got {type(value).__name__}")
        self._carry_flag = value

    # ---- Interrupt Enable ---------------------------------------------------

    @property
    def interrupt_enable(self) -> bool:
        """Master interrupt-enable flag."""
        return self._interrupt_enable

    @interrupt_enable.setter
    def interrupt_enable(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError(
                f"interrupt_enable must be bool, got {type(value).__name__}"
            )
        self._interrupt_enable = value

    # ---- flags byte packing / unpacking -------------------------------------

    def get_flags_byte(self) -> int:
        """Pack ZF, CF, IE into a single byte.

        Bit 0 = ZF, bit 1 = CF, bit 2 = IE.
        """
        flags = 0
        if self._zero_flag:
            flags |= (1 << ZF_BIT)
        if self._carry_flag:
            flags |= (1 << CF_BIT)
        if self._interrupt_enable:
            flags |= (1 << IE_BIT)
        return flags

    def set_flags_byte(self, byte: int) -> None:
        """Restore ZF, CF, IE from a packed flags byte."""
        self._zero_flag = bool(byte & (1 << ZF_BIT))
        self._carry_flag = bool(byte & (1 << CF_BIT))
        self._interrupt_enable = bool(byte & (1 << IE_BIT))

    # ---- utility ------------------------------------------------------------

    def reset(self) -> None:
        """Reset every register to its power-on default."""
        self._pc = 0
        self._ir = 0
        self._a = 0
        self._b = 0
        self._c = 0
        self._sp = STACK_START
        self._zero_flag = False
        self._carry_flag = False
        self._interrupt_enable = False

    def __repr__(self) -> str:
        return (
            f"Registers(PC=0x{self._pc:02X}, IR=0x{self._ir:02X}, "
            f"A=0x{self._a:02X}, B=0x{self._b:02X}, C=0x{self._c:02X}, "
            f"SP=0x{self._sp:02X}, "
            f"ZF={self._zero_flag}, CF={self._carry_flag}, "
            f"IE={self._interrupt_enable})"
        )

    # ---- internal -----------------------------------------------------------

    @staticmethod
    def _validate_byte(value: int, name: str) -> None:
        if not (BYTE_MIN <= value <= BYTE_MAX):
            raise ValueError(
                f"{name} value {value} out of range "
                f"({BYTE_MIN}–{BYTE_MAX})"
            )


if __name__ == "__main__":
    regs = Registers()
    regs.pc = 0x10
    regs.a = 0xFF
    regs.zero_flag = True
    regs.carry_flag = True
    regs.interrupt_enable = True
    print(regs)
    print(f"Flags byte: 0x{regs.get_flags_byte():02X}")
    regs.reset()
    print(regs)
