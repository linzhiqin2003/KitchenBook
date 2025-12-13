# Chapter 5: The Hack Architecture and Assembly

## 5-1: The Hack Architecture

### Page 1
The fetch-execute cycle
COMSM1302 Overview of Computer Architecture
John Lapinskas, University of Bristol

### Page 2
Where the unit is going
High-level language
Intermediate representation
Assembly
Machine code
Computer microarchitecture
Components
Gates
Transistors
Physics

Software
Hardware

First part of unit: Focused on hardware.
Built components for a Hack CPU in labs (e.g. registers, the PC and ALU).

### Page 3
Where the unit is going
High-level language
Intermediate representation
[pink] Assembly
[pink] Machine code
[pink] Computer microarchitecture
Components
Gates
Transistors
Physics

Software (above dashed line)
Hardware (below dashed line)

First part of unit: Focused on *hardware*.
Built components for a Hack CPU in labs (e.g. registers, the PC and ALU).
To understand the Hack architecture, we must think about *software*.

### Page 4
Where the unit is going
High-level language
Intermediate representation
Assembly
Machine code
-------------------
Computer microarchitecture
Components
Gates
Transistors
Physics

Software (corresponds to High-level language, Intermediate representation, Assembly, Machine code)
Hardware (corresponds to Computer microarchitecture, Components, Gates, Transistors, Physics)

First part of unit: Focused on hardware.
Built components for a Hack CPU in labs (e.g. registers, the PC and ALU).
After building the Hack CPU, we will write a Hack assembler in C.

### Page 5
Where the unit is going
High-level language
Intermediate representation
Assembly
Machine code
Computer microarchitecture
Components
Gates
Transistors
Physics

Software
Hardware

First part of unit: Focused on hardware.
Built components for a Hack CPU in labs (e.g. registers, the PC and ALU).
After building the Hack CPU, we will write a Hack assembler in C.
We will then build towards a high-level language for Hack ("Minijack"), using C to write a VM translator

### Page 6
Where the unit is going
High-level language
Intermediate representation
Assembly
Machine code
---------------------
Computer microarchitecture
Components
Gates
Transistors
Physics

Software
Hardware

First part of unit: Focused on hardware.
Built components for a Hack CPU in labs (e.g. registers, the PC and ALU).
After building the Hack CPU, we will write a Hack assembler.
We will then build towards a high-level language for Hack ("Minijack"), using C to write a VM translator, then a (very simple!) compiler.

### Page 7
The Hack architecture
ROM
CPU
RAM

On each clock cycle, the Hack central processing unit (CPU) reads (fetches) one 16-bit binary instruction from read-only memory (ROM).

### Page 8
The Hack architecture
ROM
CPU
RAM
I/O

On each clock cycle, the Hack central processing unit (CPU) reads (fetches) one 16-bit binary instruction from read-only memory (ROM).
The CPU then executes this instruction, which may read from or write to the keyboard, screen, or 32KB of random access memory (RAM).

### Page 9
The Hack architecture
ROM
CPU
RAM
I/O

On each clock cycle, the Hack central processing unit (CPU) reads (fetches) one 16-bit binary instruction from read-only memory (ROM).
The CPU then executes this instruction, which may read from or write to the keyboard, screen, or 32KB of random access memory (RAM).
This is called the fetch-execute cycle, and is common to all CPUs.
(Not all CPUs fetch from ROM, though — see later in unit.)

### Page 10
The Hack architecture
ROM
CPU
ALU
Registers
A
M
D
PC
RAM
I/O

The most complex part of the CPU is an arithmetic logic unit (ALU), which handles arithmetic and boolean operations like +, -, and &.
The CPU also contains four registers including the program counter (PC), which holds the address of the next instruction for the CPU to fetch.
Why registers? Because we can only read one word from RAM per clock tick.

### Page 11
The Hack architecture
ROM
CPU
ALU
Registers
A
M
D
PC
I/O
RAM

You've made all these parts in labs — we'll put them together next week!
We'll talk about the A, D and M registers next video. First, here's a simple program to compute RAM[0]+RAM[1]+17 and store the result in RAM[2]. (We write RAM[i] for the 16-bit word stored in RAM at address i.)
Don't worry about how it works yet — focus on the fetch-execute cycle.

### Page 12
The Hack architecture
ROM
CPU
ALU
Registers
A M D
PC 0
I/O
RAM

The first instruction stores 0 in A. The PC auto-increments to 1.
The M register always holds RAM[A]. Here, that's RAM[0] = 10.

### Page 13
The Hack architecture
Registers
A: 0
M: 10
D
PC: 1
I/O

The first instruction stores 0 in A. The PC auto-increments to 1.
The M register always holds RAM[A]. Here, that's RAM[0] =10.

### Page 14
The Hack architecture
Registers
A 0
M 10
D
PC 1
I/O

The first instruction stores 0 in A. The PC auto-increments to 1.
The M register always holds RAM[A]. Here, that's RAM[0] =10.
The second instruction reads RAM[A] from M and stores it in D.
The PC auto-increments to 2.

### Page 15
The Hack architecture
Registers: A=0, M=10, D=10
PC=2

The first instruction stores 0 in A. The PC auto-increments to 1.
The M register always holds RAM[A]. Here, that's RAM[0] =10.
The second instruction reads RAM[A] from M and stores it in D. The PC auto-increments to 2.

### Page 16
The Hack architecture
Registers: A=0, M=10, D=10
PC=2

The next two instructions read RAM[1] the same way, but this time add it to D rather than storing it in D. Again, the PC auto-increments.

### Page 17
The Hack architecture
Registers:
A: 1
M: 42
D: 10
PC: 3

The next two instructions read RAM[1] the same way, but this time add it to D rather than storing it in D. Again, the PC auto-increments.

### Page 18
The Hack architecture
Registers
A: 1
M: 42
D: 10
PC: 3

The next two instructions read RAM[1] the same way, but this time add it to D rather than storing it in D. Again, the PC auto-increments.

### Page 19
The Hack architecture
Registers: A=1, M=42, D=52
PC=4

The next two instructions read RAM[1] the same way, but this time add it to D rather than storing it in D. Again, the PC auto-increments.

### Page 20
The Hack architecture
Registers
A 1
M 42
D 52
PC 4

The next two instructions read RAM[1] the same way, but this time add it to D rather than storing it in D. Again, the PC auto-increments.
The next two instructions load 17 into A directly, and add it to D.
So now D contains RAM[0] + RAM[1] +17.

### Page 21
The Hack architecture
Registers
A 17
M 0
D 52
PC 5

The next two instructions read RAM[1] the same way, but this time add it to D rather than storing it in D. Again, the PC auto-increments.
The next two instructions load 17 into A directly, and add it to D. So now D contains RAM[0] + RAM[1] + 17.

### Page 22
The Hack architecture
Registers: A=17, M=0, D=52
PC:5

The next two instructions read RAM[1] the same way, but this time add it to D rather than storing it in D. Again, the PC auto-increments.
The next two instructions load 17 into A directly, and add it to D. So now D contains RAM[0] + RAM[1] +17.

### Page 23
The Hack architecture
Registers
A [17] M [0] D [69]
PC [6]

The next two instructions read RAM[1] the same way, but this time add it to D rather than storing it in D. Again, the PC auto-increments.
The next two instructions load 17 into A directly, and add it to D. So now D contains RAM[0] + RAM[1] +17.

### Page 24
The Hack architecture
Registers: A=17, M=0, D=69
PC=6

The next two instructions read RAM[1] the same way, but this time add it to D rather than storing it in D. Again, the PC auto-increments.
The next two instructions load 17 into A directly, and add it to D. So now D contains RAM[0] + RAM[1] +17.
The next two instructions copy D into RAM[2]. Nice! Just like reading from RAM, we always write to RAM[A] — so we had to load 2 into A first.

### Page 25
The Hack architecture
Registers
A 2
M 0
D 69
PC 7

The next two instructions read RAM[1] the same way, but this time add it to D rather than storing it in D. Again, the PC auto-increments.
The next two instructions load 17 into A directly, and add it to D. So now D contains RAM[0] + RAM[1] + 17.
The next two instructions copy D into RAM[2]. Nice! Just like reading from RAM, we always write to RAM[A] — so we had to load 2 into A first.

### Page 26
The Hack architecture
Registers: A=2, M=0, D=69
PC=7

The next two instructions read RAM[1] the same way, but this time add it to D rather than storing it in D. Again, the PC auto-increments.
The next two instructions load 17 into A directly, and add it to D. So now D contains RAM[0] + RAM[1] +17.
The next two instructions copy D into RAM[2]. Nice! Just like reading from RAM, we always write to RAM[A] — so we had to load 2 into A first.

### Page 27
The Hack architecture
Registers: A(2), M(69), D(69)
PC:8

The next two instructions read RAM[1] the same way, but this time add it to D rather than storing it in D. Again, the PC auto-increments.
The next two instructions load 17 into A directly, and add it to D. So now D contains RAM[0] + RAM[1] +17.
The next two instructions copy D into RAM[2]. Nice! Just like reading from RAM, we always write to RAM[A] — so we had to load 2 into A first.

### Page 28
The Hack architecture
Registers
A: 2
M: 69
D: 69
PC: 8

We then enter an infinite loop. All Hack programs end this way (there's no "halt" instruction).
Notice how the CPU always fetches the instruction whose address is given by the PC — manipulating the PC is how we implement loops and conditionals.

### Page 29
The Hack architecture
Registers: A=8, M=0, D=69
PC=9

We then enter an infinite loop. All Hack programs end this way (there's no "halt" instruction).
Notice how the CPU always fetches the instruction whose address is given by the PC — manipulating the PC is how we implement loops and conditionals.

### Page 30
The Hack architecture
Registers
A: 8
M: 0
D: 69
PC:9

We then enter an infinite loop. All Hack programs end this way (there's no "halt" instruction).
Notice how the CPU always fetches the instruction whose address is given by the PC — manipulating the PC is how we implement loops and conditionals.

### Page 31
The Hack architecture
Registers
A:8
M:0
D:69
PC:8

We then enter an infinite loop. All Hack programs end this way (there's no "halt" instruction).
Notice how the CPU always fetches the instruction whose address is given by the PC — manipulating the PC is how we implement loops and conditionals.

### Page 32
The Hack architecture
Registers: A=8, M=0, D=69
PC=8

We then enter an infinite loop. All Hack programs end this way (there's no "halt" instruction).
Notice how the CPU always fetches the instruction whose address is given by the PC — manipulating the PC is how we implement loops and conditionals.

### Page 33
The Hack architecture
Registers
A: 8
M: 0
D: 69
PC:9

We then enter an infinite loop. All Hack programs end this way (there's no "halt" instruction).
Notice how the CPU always fetches the instruction whose address is given by the PC — manipulating the PC is how we implement loops and conditionals.

### Page 34
The Hack architecture
Registers:
A: 8
M: 0
D: 69
PC: 9

We then enter an infinite loop. All Hack programs end this way (there's no "halt" instruction).
Notice how the CPU always fetches the instruction whose address is given by the PC — manipulating the PC is how we implement loops and conditionals.

### Page 35
The Hack architecture
Registers: A=8, M=0, D=69
PC=8

We then enter an infinite loop. All Hack programs end this way (there's no "halt" instruction).
Notice how the CPU always fetches the instruction whose address is given by the PC — manipulating the PC is how we implement loops and conditionals.

### Page 36
The Hack architecture
Registers
A: 8
M: 0
D: 69
PC: 8

We then enter an infinite loop. All Hack programs end this way (there's no "halt" instruction).
Notice how the CPU always fetches the instruction whose address is given by the PC — manipulating the PC is how we implement loops and conditionals.

### Page 37
The Hack architecture
Registers: A=8, M=0, D=69
PC=9

We then enter an infinite loop. All Hack programs end this way (there's no "halt" instruction).
Notice how the CPU always fetches the instruction whose address is given by the PC — manipulating the PC is how we implement loops and conditionals.

### Page 38
The Hack architecture
Registers
A:8
M:0
D:69
PC:9

We then enter an infinite loop. All Hack programs end this way (there's no "halt" instruction).
Notice how the CPU always fetches the instruction whose address is given by the PC — manipulating the PC is how we implement loops and conditionals.

### Page 39
The Hack architecture
Registers: A=8, M=0, D=69
PC=8

We then enter an infinite loop. All Hack programs end this way (there's no "halt" instruction).
Notice how the CPU always fetches the instruction whose address is given by the PC — manipulating the PC is how we implement loops and conditionals.

### Page 40
Demonstration of CPU simulator
[See video.]

## 5-2: Hack Assembly I: The Basics

### Page 1
Hack assembly I: The basics
COMSM1302 Overview of Computer Architecture
John Lapinskas, University of Bristol

### Page 2-4
The early days of computing
In 1949, EDSAC was one of the first stored-program computers ever to go into regular use.
And even then people didn't want to write in machine code.
Instead, they used mnemonics: One line of text per instruction. This was the first assembly language, and they became ubiquitous in the 1950s. A program called an assembler translates assembly into machine code.

### Page 5-7
Wait, what about punchcards?
People did program computers with machine code on punchcards even into the 1970s, but not because assembly hadn't been invented!
If you only have one giant mainframe in the company, it's much faster to load batches of code or data in from punchcards than it is to have people come into the computer room one by one and type it out...

### Page 8
The rise of the PC
Punchcards gave way to dumb terminals (with no computing power of their own but connected to a mainframe via a wired network) in the 1970s.
Dumb terminals gave way to personal computers in the 1980s–90s.

### Page 9-11
Hack assembly: Why?
We don't have to worry about this, so we will focus on Hack assembly.
We'll discuss machine code later, when we assemble the Hack CPU.
Since one line of assembly corresponds to one instruction, there is no one “assembly language”. Different architectures (e.g. x86-64, i386, ARM, MIPS) have different assembly languages.
We teach Hack assembly not because it’s directly useful, but because it primes you to learn assembly for any other architecture.
Optimised assembly code is often faster than compiled code. Most high-performance languages (e.g. C, C++, Rust) allow assembly to be embedded inline for optimisation.
Warning: Assembly is neither portable nor legible nor easily maintainable!
You should only “optimise” a piece of code by using assembly if you already know that code is a serious performance bottleneck. In general, premature optimisation is a bad idea.

### Page 12-16
Registers in Hack
The Hack CPU has registers A, M, D and PC. Each holds one 16-bit word.
A is the address register. It's the only register we can load values into directly, rather than needing to read them from memory first.
M is the memory register. When read from, it returns RAM[A]. When written to, it updates RAM[A]. It's interpreting A's value as a pointer and dereferencing it, like in C.
D is the data register for general-purpose storage that (unlike A) doesn't alter the value of M. For longer-term or larger storage, we use RAM.
PC is the program counter. The next instruction to be executed is always ROM[PC], so by writing to PC we can jump around in the code.

### Page 17-21
Operations on (non-PC) registers in Hack
@[number] loads number into A, e.g. @42 sets A to 42.

All other operations are of the form:
Constants: M=0, D=1, A=-1
Unary operations: D=A, A=-D, D=!D, A=A+1, M=M-1
Binary operations: D=A+D, M=M-D, D=D&A, A=D|M

Important: All binary operations are between two different registers, at least one of which is D. So e.g. D=A+M or M=D+D are not allowed.
More complex expressions like A=D+M+A or D=17 are also not allowed.
You can do also multiple assignment, replacing the left-hand side by two or three registers. E.g. MD=D-M assigns D − M to both M and D.
The syntax for this is that A, M and D must appear in order — so e.g. AMD=D+M is valid but DAM=D+M is not.

### Page 22
Example: add.asm
@0
D=M
@1
D=D+M
@17
D=D+A
@2
M=D

This is assembly code to store RAM[0] + RAM[1] + 17 in RAM[2].
(NB all Hack programs should end with an infinite loop — see next video.)

### Page 23
A small mercy: Comments and keywords
Another benefit of assembly over machine code is comments. The assembler skips lines starting with //, plus empty lines and leading spaces. Mid-line comments (e.g. "A=D // Comment") are also fine.
The assembler will also replace any instance of @R0 with @0, @R1 with @1, and so on up to @R15 with @15.
We sometimes call RAM addresses 0 through 15 virtual registers.
By writing e.g. @R5 instead of @5, we signal to ourselves that we care about 5 as a memory address rather than as a literal number.
Other keywords: SP ↔ 0, LCL ↔1, ARG ↔2, THIS ↔3, THAT ↔4, SCREEN ↔16384, KBD ↔24576.

### Page 24
Example: add.asm redux
// D <- RAM[0]
@R0
D=M
// D <- D + RAM[1]
@R1
D=D+M
// D <- D + 17
@17
D=D+A
// RAM[2] <- D
@R2
M=D

### Page 25-27
A larger mercy: Variables
The assembler also handles alphabetical variables in @ statements.
The first time you write e.g. @var, it associates the string var with a unique address in RAM (say 16). It then replaces that and every future instance of @var with @16.
Addresses are assigned to variables starting from 16.
Use variables rather than memory addresses where possible — it makes code more legible.
Where might it not be possible or sensible to use variables?
E.g. if your desired output is two lists of a hundred numbers each! Or worse, two lists of length determined at run-time.

## 5-3: Hack Assembly II: Loops and Conditionals

### Page 1
Hack assembly II: Loops and conditionals
COMSM1302 Overview of Computer Architecture
John Lapinskas, University of Bristol

### Page 2-4
A terror from the past
So far, we can compute simple expressions, but we don't have a "real computer" yet. Hack assembly as we've covered it so far is more like a calculator attached to a clock.
We need loops and conditionals, but we don't have ifs or while loops.
Let's instead discuss something... older. Darker. Hungrier.
(Reference to XKCD about GOTO)

### Page 5-13
Gotos in C and "Go to statement considered harmful"
In C, a goto statement allows you to "jump" from anywhere in the code to a specific label.
All flow control in C can be expressed as gotos and one-line if statements!
Why use whiles and elses instead of gotos?
Gotos are completely unrestricted. You can goto one label from 20 different places in a 10,000-line function.
The use of ifs and whiles and function calls to control program flow is known as structured programming and rose to prominence in the 1960s.
"Go to statement considered harmful" - Dijkstra.

### Page 15
Gotos in Hack: Jumps
In assembly, gotos with simple if statements are usually the only form of flow control we have.
We call them jumps or branches.
Any instruction in Hack assembly not starting with @ can be followed by a semicolon and one of seven jump instructions.
This reads as "if [result of instruction] satisfies [condition], goto the ROM address contained in A".
For example, M=A+D;JGT stores A + D in M, then jumps to the address contained in A if A + D > 0.

### Page 16
List of jump conditions in Hack
JMP: Always
JGT: > 0
JEQ: = 0
JLT: < 0
JGE: ≥ 0
JNE: ≠ 0
JLE: ≤ 0
Remember, all jumps are to the address stored in A.
Warning: The PC is updated at the same time as A, at the start of the next clock cycle! An instruction like A=A+D; JMP has undefined behaviour.

### Page 17-19
Help from the assembler: Labels
Each (non-comment) line of assembly is one line of machine code.
To unconditionally jump to line 100, we would use @99 followed by 0;JMP.
Problem: This is awful to maintain.
Solution: Labels.
A line of the form (Label) doesn't correspond to any machine code. Instead, if the next line would appear at e.g. ROM position 100, then it tells the assembler to replace all instances of @Label with @100.

### Page 20
Example: Computing a sum
Sum.asm outputs to RAM[1] a sum of all the integers from 0 to RAM[0].

### Page 21-38
What is a "real" computer anyway?
A Turing machine is a two-sided infinite string of tape divided into cells containing binary values, plus a tape head and a collection of possible states.
At each time step, based on the current cell and its internal state, the tape head writes a 1 or 0 and moves left or right along the tape, and then the Turing machine changes state or halts.
Why care? Because the Church-Turing thesis says that if a computing problem is solvable, then a well-chosen Turing machine can solve it.
So if we can simulate any Turing machine, we have a "real" computer! We say a computer model which can do this is Turing-complete.

## 5-4: Hack Assembly III: Input and Output

### Page 1
Hack assembly III: Input and output
COMSM1302 Overview of Computer Architecture
John Lapinskas, University of Bristol

### Page 2-4
Input and output in Hack
In Hack, the only input peripheral is the keyboard and the only output peripheral is the monitor.
All input/output (I/O) is memory-mapped.
Recall Hack has 32KB of physical memory divided into 16-bit words.
Addresses 0x0000 to 0x3FFF (0-16383).
Anything written to addresses 0x4000 to 0x5FFF will appear on screen.
If a key is held on the keyboard, its value appears in 0x6000.

### Page 5
Keyboard input
The keyword KBD is mapped to 0x6000 (= 24576).
For example, if "d" is being held, then @KBD will load 24576 into A and 100 into M.
If no key is being pressed, then 0x6000 contains 0.

### Page 6-27
Monitor output
Hack works in a resolution of 512x256, i.e. 256 rows of 512 pixels per row.
Pixels are numbered from left to right and top to bottom in "book order".
Pixel number 1 corresponds to RAM[0x4000].
The i’th pixel displays black if the i’th bit in memory counting from the lsb of address 0x4000 is 1, and white if it's 0.
So each word in 0x4000–0x5FFF controls not one pixel, but 16!
Equivalently, the pixel at row r from the top and column c from the left is controlled by the (c % 16)'th bit from the right at address 0x4000 + 32r + (c/16).
SCREEN is mapped to 0x4000.

### Page 28-33
Tricks and traps
Warning: The @ command only works on values of up to 15 bits!
If you want to write 0xFFFF into address 0x4000, @65535 won’t load 0xFFFF into A. You’ll instead need to write e.g. @0 followed by A=!A or A=-1.
You can use the CPU emulator to see register and memory values in hex or binary.
You can read from the screen as well as writing to it!

### Page 34
Example: Filling the screen
Fill.asm fills every pixel of the screen black. While any key is held, the screen is instead filled white.
