# Chapter 7: Computer Architecture

## 7-1: The Hack Instruction Set Architecture

### Page 1
The Hack instruction set architecture
COMSM1302 Overview of Computer Architecture
John Lapinskas, University of Bristol

### Page 2-4
What is an ISA?
The microarchitecture is the physical design of the computer in hardware — circuit diagrams and PCB layouts.
The instruction set architecture (ISA) is the way the computer acts in response to machine code instructions.
Once you've implemented a C function to a specification, you can use that function without needing to remember how you coded it.
In the same way, the microarchitecture implements the ISA. When you're writing assembly, you don't need to know how the ISA is implemented.
For example, modern CPUs from both AMD and Intel generally implement the x86-64 ISA despite having very different microarchitectures.

### Page 5
ISAs versus microarchitecture — a comparison
ISA properties: Word length, Machine code instructions, Registers and memory, I/O memory-mapping, Execution model.
Microarchitecture properties: Clock speed, Energy efficiency, ALU circuit design, Connections between I/O and CPU, Response to unspecified behaviour.

### Page 6
A-instructions
An address instruction or A-instruction is as follows:
0vvv vvvv vvvv vvvv
Opcode 0, followed by a single 15-bit operand.
It simply copies its operand into A. (Note this also sets M to RAM[A].)

### Page 7
C-instructions
A compute instruction or C-instruction is as follows:
111a cccccc ddd jjj
Opcode 1, followed by two unused bits (11 by convention).
- comp (a cccccc) specifies which computation to do.
- dest (ddd) specifies where the result should be stored.
- jump (jjj) specifies whether or not to update the program counter to A.

### Page 8
C-instructions: comp
With input bits a c1 c2 c3 c4 c5 c6:
(a=0 for A, a=1 for M)
0: 101010
1: 111111
-1: 111010
D: 001100
A/M: 110000
!D: 001101
!A/!M: 110001
-D: 001111
-A/-M: 110011
D+1: 011111
A+1/M+1: 110111
D-1: 001110
A-1/M-1: 110010
D+A/D+M: 000010
D-A/D-M: 010011
A-D/M-D: 000111
D&A/D&M: 000000
D|A/D|M: 010101

### Page 9
C-instructions: dest
d1 d2 d3
null: 000
M: 001
D: 010
DM: 011
A: 100
AM: 101
AD: 110
ADM: 111

### Page 10
C-instructions: jump
j1 j2 j3
null: 000
JGT: 001
JEQ: 010
JGE: 011
JLT: 100
JNE: 101
JLE: 110
JMP: 111

### Page 11-20
C-instructions: Two examples
Machine code: 1110101010000111
comp: 0101010 (0)
dest: 000 (none)
jump: 111 (JMP)
Assembly: 0;JMP

Machine code: 1111000010101000
comp: 1000010 (D+M)
dest: 101 (AM)
jump: 000 (none)
Assembly: AM=D+M

## 7-2: The Hack Microarchitecture

### Page 1
The Hack microarchitecture
COMSM1302 Overview of Computer Architecture
John Lapinskas, University of Bristol

### Page 2
The Hack microarchitecture
This week, your main assignment is to build a Hack computer in Logisim.
We do recommend you use the Logisim built-in ROM, RAM and registers rather than the ones you designed.

### Page 3
Components: Memory
ROM: 64KB, 15-bit address space, 16-bit words. Stores program.
RAM: 64KB, 15-bit address space, 16-bit words. Stores data.

### Page 4-5
Components: The CPU
Inputs: from data memory (inM), instruction, reset.
Outputs: outM, writeM, addressM, pc.
The CPU should follow the fetch-execute cycle.
- Execute instruction ROM[pc].
- inM is M.
- pc is Program Counter.
- addressM is A.
- writeM is 1 if writing to memory.

### Page 6
CPU components: The program counter
Inputs: load, inc, reset, in.
Output: out.
If reset=1, out=0.
If inc=1, out=out+1.
If load=1, out=in.

### Page 7-8
CPU components: The ALU
Inputs: x, y, zx, nx, zy, ny, f, no.
Output: out.
Also needs sub-circuit to check for jump conditions (pos, neg, zero).
Table of ALU control bits matches C-instruction comp bits c1-c6.

### Page 9
Building the CPU
Internal structure involves Mux16s, A register, D register, ALU, PC.
(Refer to diagram description in source)

## 7-3: Comparative Architecture

### Page 1
Comparative architecture
COSM1302 Overview of Computer Architecture
John Lapinskas, University of Bristol

### Page 2-3
What to look for in a new ISA
- Word size (e.g. 64-bit).
- Address space.
- Instruction length.
- Design philosophy (Harvard vs von Neumann, RISC vs CISC).
- Registers.
- Addressing modes.
- Hardware interrupts.
- The stack.

### Page 4-5
Harvard vs von Neumann
Hack uses Harvard architecture: Separate memory for instructions (ROM) and data (RAM).
Most modern ISAs use von Neumann: Instructions and data in same memory.

### Page 6
RISC vs CISC
RISC (Reduced Instruction Set Computing): Simple microarchitecture, simple instructions, fixed-length, "standard" features.
CISC (Complex Instruction Set Computing): Complex microarchitecture, complex instructions, variable-length, "extra" features.
Modern CPUs: CISC often runs faster, but RISC is efficient for low-power (embedded, mobile).

### Page 7-8
Registers
Hack: Special-purpose registers A, M, PC. D is general-purpose.
Most ISAs have PC (or IR).
General-purpose registers can fill any role. Most architectures have 32+.

### Page 9-12
Addressing modes
- Immediate addressing: Operand is data. (e.g. @511)
- Direct addressing: Operand is data's location. (e.g. D=A+D, operand implies location)
- Indirect addressing: Operand is location of a pointer. (e.g. M=D+1, accessing RAM[A])
CISC ISAs have more, e.g. Indexed indirect addressing (ARM7 LDR R0, [R1, #0xBEEF]).

### Page 13
Common ISAs: x64
Most modern desktop/laptop. CISC. Fast, power-hungry.

### Page 14
Common ISAs: ARM
Mobile/portable. RISC. Lower power.

### Page 15-16
Common ISAs: MIPS
Simple RISC. Embedded applications. (Nintendo 64 used MIPS).

### Page 17-20
Advanced feature: Hardware interrupts
Hack uses polling (wasteful).
Modern ISAs use interrupts.
- CPU has dedicated interrupt pins.
- On signal, CPU saves state, branches to interrupt handler.
- Restores state after handling.

## 7-4: Microarchitecture Optimisation: Pipelining and Caching

### Page 1
Microarchitecture optimisation: Pipelining and caching
COMSM1302 Overview of Computer Architecture
John Lapinskas, University of Bristol

### Page 2-6
Pipelining by analogy
Washing laundry: Wash (2h), Dry (3h), Iron (1h).
Sequential: 6 hours per load.
Pipelined: Start Load 2 while Load 1 is drying. Throughput increases.

### Page 7-9
The ideal of pipelining
Main barrier to clock speed is propagation delay.
Divide fetch-execute into stages: Fetch, Decode, Execute, Writeback.
Set clock speed to delay of slowest stage, not entire cycle.

### Page 10-14
The reality of pipelining: Stalls and hazards
- Data hazards: Instruction needs data from previous unfinished instruction.
- Conditional hazards: Branch outcome unknown.
- Structural hazards: Contention for resources.
Hazards lead to stalls (bubbles).

### Page 15-16
What about multiple cores?
Multiple cores allow parallel execution but introduce complexity. Multithreading.

### Page 17-21
Memory caching
Main memory (RAM) is slow (e.g. 73ns vs 0.175ns CPU cycle).
Solution: Cache hierarchy (L1, L2, L3).
Smaller, faster, closer memory.
Most frequently used data goes to L1.
Minimise cache misses.

### Page 22-23
Applications of architecture: Predication
Branchless programming to avoid control hazards.
Convert `if (x<=50) y+=10; else y=3;` to `y = (y+10)*(x<=50) + 3*(x>50);`

### Page 24-26
Applications of architecture: Loop unrolling
Write out multiple iterations of a loop to reduce branch overhead.
Duff's device (switch statement with fall-through into a loop).
