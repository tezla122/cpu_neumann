; Counts down from value at address 15 until zero
LOAD 15
SUB 14
STORE 15
JZ 5
JMP 1
HALT

; mem[14] = 1 (the decrement), mem[15] = starting count
