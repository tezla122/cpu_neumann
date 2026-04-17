"""
8-bit CPU Simulator — Memory Module

Implements a 256-byte Von Neumann RAM with read, write, program loading,
and hex-dump capabilities.
"""

RAM_SIZE = 256
BYTE_MIN = 0
BYTE_MAX = 255
DUMP_ROW_WIDTH = 16


class Memory:
    """256-byte random-access memory for the 8-bit CPU."""

    def __init__(self) -> None:
        """Initialise RAM: all 256 bytes zeroed."""
        self._ram = bytearray(RAM_SIZE)

    def read(self, address: int) -> int:
        """Return the byte stored at *address*.

        Raises:
            IndexError: if address is outside 0x00–0xFF.
        """
        self._validate_address(address)
        return self._ram[address]

    def write(self, address: int, value: int) -> None:
        """Write *value* (0–255) to *address*.

        Raises:
            IndexError: if address is outside 0x00–0xFF.
            ValueError: if value is not a valid unsigned byte.
        """
        self._validate_address(address)
        self._validate_value(value)
        self._ram[address] = value

    def load_program(self, program: list[int], start_address: int = 0) -> None:
        """Load a sequence of bytes into memory starting at *start_address*.

        Raises:
            OverflowError: if the program would exceed available memory.
            ValueError:    if any byte is not in 0–255.
        """
        if start_address + len(program) > RAM_SIZE:
            raise OverflowError(
                f"Program of {len(program)} bytes at start address "
                f"0x{start_address:02X} exceeds {RAM_SIZE}-byte memory"
            )
        for offset, byte in enumerate(program):
            self._validate_value(byte)
            self._ram[start_address + offset] = byte

    def dump(self, start: int = 0, end: int = BYTE_MAX) -> str:
        """Return a formatted hex dump from *start* to *end* (inclusive).

        Output has 16 bytes per row, e.g.:

            0x00: 1E 3F 2D FF 00 00 00 00 00 00 00 00 00 00 05 03
        """
        lines: list[str] = []
        row_start = (start // DUMP_ROW_WIDTH) * DUMP_ROW_WIDTH
        while row_start <= end:
            row_end = min(row_start + DUMP_ROW_WIDTH, end + 1)
            hex_bytes = " ".join(
                f"{self._ram[addr]:02X}" for addr in range(row_start, row_end)
            )
            lines.append(f"0x{row_start:02X}: {hex_bytes}")
            row_start += DUMP_ROW_WIDTH
        return "\n".join(lines)

    # ---- internal helpers ---------------------------------------------------

    @staticmethod
    def _validate_address(address: int) -> None:
        if not (BYTE_MIN <= address <= BYTE_MAX):
            raise IndexError(
                f"Address 0x{address:02X} out of range "
                f"(0x{BYTE_MIN:02X}–0x{BYTE_MAX:02X})"
            )

    @staticmethod
    def _validate_value(value: int) -> None:
        if not (BYTE_MIN <= value <= BYTE_MAX):
            raise ValueError(
                f"Value {value} out of range ({BYTE_MIN}–{BYTE_MAX})"
            )


if __name__ == "__main__":
    mem = Memory()
    mem.load_program([0x1E, 0x3F, 0x2D, 0xFF], start_address=0)
    mem.write(14, 5)
    mem.write(15, 3)
    print(mem.dump(0, 0x0F))
