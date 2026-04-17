; Reads a byte from port 0 (keyboard), doubles it, writes to port 1 (display)
; Repeats until input is 0
;
; No manual data setup needed — uses I/O ports exclusively.
; Register I/O callbacks before running.

loop:
    IN 0                ; A = io_bus.read(port 0)
    STORE 15            ; temp = A (addr 0x0F)
    OR 15               ; A = A | temp (same value); sets ZF if A == 0
    JZF done            ; if input was 0, exit
    ADD 15              ; A = A + temp = 2 * input
    OUT 1               ; io_bus.write(port 1, A)
    JMPF loop           ; repeat
done:
    HALT
