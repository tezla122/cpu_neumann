"""
8-bit CPU Simulator — I/O Bus

16-port I/O bus with optional read/write callbacks for each port.
Unregistered ports fall back to internal port registers.
"""

from __future__ import annotations

from collections.abc import Callable

NUM_PORTS = 16
PORT_MIN = 0
PORT_MAX = NUM_PORTS - 1


class IOBus:
    """16-port I/O bus for the 8-bit CPU.

    Each port can have an optional ``read_callback`` (for IN instructions)
    and ``write_callback`` (for OUT instructions).  When no callback is
    registered, reads return the port-register value and writes store into
    the port register.
    """

    def __init__(self) -> None:
        """Initialise with no callbacks and all port registers zeroed."""
        self._read_callbacks: dict[int, Callable[[], int]] = {}
        self._write_callbacks: dict[int, Callable[[int], None]] = {}
        self._port_registers: list[int] = [0] * NUM_PORTS

    def register_input(self, port: int, callback: Callable[[], int]) -> None:
        """Wire *port* to a read source (e.g. keyboard, sensor)."""
        self._validate_port(port)
        self._read_callbacks[port] = callback

    def register_output(self, port: int, callback: Callable[[int], None]) -> None:
        """Wire *port* to an output sink (e.g. display, LED)."""
        self._validate_port(port)
        self._write_callbacks[port] = callback

    def read(self, port: int) -> int:
        """IN instruction: read a byte from *port*."""
        self._validate_port(port)
        if port in self._read_callbacks:
            return self._read_callbacks[port]()
        return self._port_registers[port]

    def write(self, port: int, value: int) -> None:
        """OUT instruction: write *value* to *port*."""
        self._validate_port(port)
        if port in self._write_callbacks:
            self._write_callbacks[port](value)
        else:
            self._port_registers[port] = value

    @staticmethod
    def _validate_port(port: int) -> None:
        """Raise IndexError if *port* is outside 0–15."""
        if not (PORT_MIN <= port <= PORT_MAX):
            raise IndexError(
                f"Port {port} out of range ({PORT_MIN}–{PORT_MAX})"
            )


if __name__ == "__main__":
    bus = IOBus()
    bus.write(0, 42)
    print(f"Port 0 = {bus.read(0)}")
    bus.register_input(1, lambda: 99)
    print(f"Port 1 (callback) = {bus.read(1)}")
