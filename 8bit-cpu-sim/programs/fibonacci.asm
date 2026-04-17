; Computes Fibonacci: F(n) stored at address 0x0E
; Uses CALL/RET to invoke a subroutine
;
; Data (loaded manually before run):
;   mem[0x0A] = 0  (fib_prev)
;   mem[0x0B] = 1  (fib_curr)
;   mem[0x0C] = n  (counter, e.g. 7)
;   mem[0x0D] = 0  (temp)
;   mem[0x0E] = 0  (result)
;   mem[0x0F] = 1  (constant 1 for decrement)
;
; Code occupies 0x00-0x09 and 0x10-0x1A.
; Addresses 0x0A-0x0F are reserved for data (NOP padding).

main_loop:
    LOAD 12             ; A = counter
    OR 12               ; set ZF if counter == 0
    JZF done            ; if done, jump to result store
    CALL fib_step       ; compute next fibonacci
    LOAD 12             ; A = counter
    SUB 15              ; A -= 1 (mem[0x0F] = 1)
    STORE 12            ; save counter
    JMP 0               ; loop back to main_loop
    ; --- data region padding (0x0A-0x0F) ---
    NOP
    NOP
    NOP
    NOP
    NOP
    NOP
done:
    LOAD 11             ; A = fib_curr (the result)
    STORE 14            ; store at address 0x0E
    HALT

fib_step:
    LOAD 10             ; A = fib_prev
    ADD 11              ; A = fib_prev + fib_curr
    STORE 13            ; temp = new value
    LOAD 11             ; A = old fib_curr
    STORE 10            ; fib_prev = old fib_curr
    LOAD 13             ; A = temp (new fib_curr)
    STORE 11            ; fib_curr = temp
    RET
