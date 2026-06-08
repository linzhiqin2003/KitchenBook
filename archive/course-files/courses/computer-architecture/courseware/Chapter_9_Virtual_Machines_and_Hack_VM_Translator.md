# Chapter 9: Virtual Machines and Hack VM Translator

## 9-1: Virtual Machines and Intermediate Representations

### Page 1
Virtual machines and intermediate representations
John Lapinskas, University of Bristol

### Page 2-4
Why use an IR?
Recall that most high-level languages are compiled to an intermediate representation (IR) before further compilation to assembly.
This allows a clean separation of compilation into three phases:
- Front end: High-level language to IR. Architecture-independent.
- Middle end: Optimisations within IR.
- Back end: IR to assembly. Architecture-dependent.

Examples: LLVM, GIMPLE, JVM.

### Page 5
Virtual machines
In Hack assembly, designs were tightly bound to hardware.
In an IR, we sever these connections. We think of IR code as running on a virtual machine (VM).
The Hack VM is the IR we will use.

### Page 6-13
The other kind of virtual machine
VMs for IRs vs VMs for running software (e.g. running Linux on Windows).
Real-world VMs allow running untrusted software, failover, distributed computing (AWS), etc.

### Page 14-21
Goals of Hack VM
- Implement function calls.
- Proper compile-time memory allocation.
- Multi-file compilation.
- Cleaner arithmetic expressions (stack-based).
- More working storage than just D register.
- Compact syntax.
- Memory addresses separated from physical memory (Virtual Memory).

### Page 22-27
Non-goals of Hack VM
- Human-friendly code (no variable names, for loops).
- Complex expressions directly implemented.
- Types (strings, arrays, structs).
- Run-time memory allocation.
These are handled by the high-level language (Jack) compiler.

## 9-2: The Hack VM I: Structure, Arithmetic and Logic

### Page 1
The Hack VM I: Structure, arithmetic and logic
COMSM1302 Overview of Computer Architecture
John Lapinskas, University of Bristol

### Page 2-19
Stacks
The Hack VM is a stack machine.
Operations:
- `push(x)`: Adds x to top.
- `pop()`: Removes and returns top.
LIFO: Last In, First Out.

### Page 20-21
Virtual memory
Assembly uses physical memory. VM uses virtual memory segments.
Hack VM has 8 segments.
- `local`: General-purpose local variables.
- `constant`: Virtual segment where address `i` holds value `i`. Read-only.

### Page 22-36
Syntax: Pushing and popping
`push [segment] [index]`
`pop [segment] [index]`
Example:
`push local 34` (pushes value at local[34] to stack)
`push constant 255` (pushes 255 to stack)
`pop local 35` (pops stack top to local[35])

### Page 37-49
Stack operations in Hack VM
Arithmetic happens via the stack.
`add`: Pops top two values, adds them, pushes result.
Example: `push local 50`, `push local 50`, `push constant 2`, `add`, `add`, `pop local 50`.

### Page 50-62
Logical comparisons
`eq`, `gt`, `lt`.
Pops two values, compares, pushes result.
True is represented as `-1` (0xFFFF), False as `0` (0x0000).

### Page 63
Quick reference
- `add`, `sub`: Arithmetic (+, -).
- `neg`: Negation (-y).
- `and`, `or`, `not`: Bitwise/Logical.
- `eq`, `gt`, `lt`: Equality/Comparison.
Note: For operations popping two values (x, y), y is the first popped (top), x is the second. `sub` computes x - y.

### Page 64-73
Example: Arithmetic
To test `(local 3 > 42) and (local 3 < local 5 - 100)`:
```
push local 3
push constant 42
gt
push local 3
push local 5
push constant 100
sub
lt
and
```

## 9-3: The Hack VM II: Branching and Memory

### Page 1
The Hack VM II: Branching and memory
COMSM1302 Overview of Computer Architecture
John Lapinskas, University of Bristol

### Page 2-4
Labels and gotos
Syntax:
- `label LABEL_NAME`
- `goto LABEL_NAME`
- `if-goto LABEL_NAME`: Pops stack; if non-zero, jumps to label.

### Page 5-8
pointer and this
`local` requires fixed addresses. To access arrays/dynamic memory:
Segments `this` and `pointer`.
`pointer 0` stores the base address of `this`.
`pointer 1` stores the base address of `that`.
Accessing `this i` accesses RAM at `(value in pointer 0) + i`.
Example array access: Calculate address, `pop pointer 0`, `push this 0`.

### Page 9-11
Implementing I/O
`this` usually restricted to heap area.
Use `that` for arbitrary memory access (like Screen/Keyboard).
`that` works like `this` but uses `pointer 1`.

### Page 12-17
The eight virtual memory segments
1. `local`: Local variables. Resets on function return.
2. `argument`: Function arguments.
3. `static`: Persists between calls (class variables).
4. `constant`: Virtual constants.
5. `this`: Object fields / heap access.
6. `that`: Array elements / heap access.
7. `pointer`: Base addresses for this/that.
8. `temp`: Scratch space (size 8).

## 9-4: Implementing the Hack VM Translator

### Page 1
Implementing the Hack VM translator
John Lapinskas, University of Bristol

### Page 2
Tokens for Hack VM
Keywords (`push`, `pop`, `add`...), Integers, Identifiers, Newlines.

### Page 3-4
Implementing labels and gotos
VM labels become assembly labels.
`goto` becomes `0;JMP`.

### Page 5
A grammar for Hack VM
Simple LL(1) grammar.
Instruction type determined by first token.

### Page 6-7
Allocating memory
Map virtual segments to physical RAM using Base Address + Offset.
`local i` -> `RAM[LCL + i]`.

### Page 8-9
Hardware limitations
Segments have fixed maximum sizes or boundaries to prevent overlap/overflow.
Hack VM: 64KB total.

### Page 15-21
Memory allocation in Hack (Implementation details)
Base addresses stored in fixed RAM locations:
- `local` base: RAM[1] (LCL)
- `argument` base: RAM[2] (ARG)
- `this` base: RAM[3] (THIS)
- `that` base: RAM[4] (THAT)
- `temp`: Fixed at RAM[5-12].
- `static`: Fixed at RAM[16-255].
- `pointer`: Mapped to RAM[3] (THIS) and RAM[4] (THAT).

### Page 22-26
Implementing the stack
Stack base address: 256.
Stack Pointer (SP): stored in RAM[0].
Push x: `*SP = x, SP++`.
Pop to i: `SP--, *i = *SP`.

### Page 27
Hack VM memory: A summary
| Keyword | Address | Usage |
|---|---|---|
| SP | 0 | Stack Pointer |
| LCL | 1 | Base of local |
| ARG | 2 | Base of argument |
| THIS | 3 | Base of this (pointer 0) |
| THAT | 4 | Base of that (pointer 1) |
| R5-R12 | 5-12 | temp segment |
| R13-R15 | 13-15 | Temp vars for translator |
| static | 16-255 | static segment |
| stack | 256-2047 | Stack area |
| heap | 2048-16383 | Heap (this/that target) |
| SCREEN | 16384... | Screen |
| KBD | 24576 | Keyboard |
