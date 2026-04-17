; Main loop increments a counter at address 0x0A continuously.
; ISR (at label isr, address stored in mem[0xE0]) stores a snapshot
; of the counter at address 0x0B when interrupt fires, then RETIs.
; Demonstrates that the main loop resumes correctly after interrupt.
;
; Data (loaded manually before run):
;   mem[0x0A] = 0  (counter)
;   mem[0x0B] = 0  (snapshot — written by ISR)
;   mem[0x0C] = 1  (constant 1 for increment)
;   mem[0xE0] = address of isr (IVT entry, set before run)
;
; NOTE: This program loops forever. Run for a fixed number of steps,
; fire an interrupt externally, then inspect mem[0x0B].

    EI                  ; enable interrupts
loop:
    LOAD 10             ; A = counter (addr 0x0A)
    ADD 12              ; A += 1 (mem[0x0C] = 1)
    STORE 10            ; counter = A
    JMP 1               ; loop back to LOAD (addr 1)
    ; --- padding to align ISR at a known address ---
    NOP
    NOP
    NOP
    NOP
    NOP
    NOP
    NOP
    NOP
    NOP
    NOP
    NOP
isr:
    LOAD 10             ; A = counter (snapshot)
    STORE 11            ; mem[0x0B] = snapshot
    RETI                ; return from interrupt
