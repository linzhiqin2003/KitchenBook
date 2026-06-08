# Chapter 11: The Jack Language and Compiler

## 11-1: The Jack Language

### Page 1
The Jack language
John Lapinskas, University of Bristol

### Page 2-3
Our goals for this week
Compile a high-level language (Jack) to Hack VM.
Combined with the VM translator and assembler, this gives a full compiler.

### Page 4-7
Variables, statements and comments
- Types: `int`, `char`, `boolean` (built-in); `Array`, `String` (libraries).
- Variables: `var int x;`. Must be declared at function start.
- Assignment: `let x = 5;`.
- Comments: `//` or `/* ... */`.

### Page 8-10
Functions
- Declaration: `function int Main.max(int x, int y) { ... }`.
- Void function: `function void ...`.
- Return: `return x;` or `return;`.
- Call: `do Main.print(...);` (if return value is ignored) or `let x = Main.max(...);`.

### Page 11-12
Expressions
- Arithmetic: `+`, `-`, `*`, `/`.
- Logic: `&`, `|`, `~` (NOT).
- Comparison: `=`, `>`, `<`.
- Literals, Variables, Function calls.
- Parentheses `()` for precedence.

### Page 13-14
Control flow
- `if (exp) { ... } else { ... }`.
- `while (exp) { ... }`.

### Page 15-16
Variable types
No casting. Implicit conversion (char as int, boolean true as -1, false as 0).

### Page 17-23
Classes
Jack has classes (similar to C structs but with methods).
- `field`: Instance variable.
- `static`: Class variable (shared).
- `method`: Associated with an instance (`this`).
- `function`: Static method (no `this`).
- `constructor`: Creates new instance, returns `this`.

### Page 24
`[]` syntax
`my_object[i]` accesses memory at address `my_object + i`.
Used for Arrays.

### Page 25-26
Compiling multiple files
Each file contains one class.
Main entry point: `Main.main()`.

## 11-2: Compiling Jack

### Page 1
Compiling Jack
John Lapinskas, University of Bristol

### Page 2
Lexing Jack
Tokens:
- Keywords (`class`, `function`, `if`, `let`...).
- Symbols (`{`, `}`, `+`, `;`...).
- Integer literals.
- String literals.
- Identifiers.

### Page 3-5
Parsing Jack: The grammar
Recursive grammar definition (EBNF).
Example: `<whileStatement> ::= 'while', '(', <expression>, ')', '{', <statements>, '}'`.
Expressions are recursive.

### Page 6-8
Parsing Jack: Use of XML
Parse tree stored as XML.
Readable, standard, flexible.

### Page 9-32
Parsing Jack: A (fairly) general LL(2) parser
Maintain `current` and `lookahead` tokens.
Recursive descent functions (`parse_term`, `parse_while_statement`).
Generate XML output.

## 11-3: Compiling Jack's Classes

### Page 1
Compiling Jack’s classes
John Lapinskas, University of Bristol

### Page 2-5
How objects work
Objects are pointer-based arrays on the heap.
`var Foo myFoo` holds the RAM address.
Fields `x`, `y`, `z` are at `RAM[myFoo]`, `RAM[myFoo+1]`, etc.

### Page 6-9
Desired subroutine behaviour
- Call: Output VM `call` command.
- Body: Use symbol table to map vars/args to `local`/`argument` segments.
- Return: Output VM `return`.

### Page 10-17
Differences between subroutine types
- **Function**: Normal.
- **Method**: Implicit `this` argument (argument 0).
  - On call: Push object instance.
  - On entry: `pop pointer 0` (sets `THIS` to argument 0).
- **Constructor**: Creates object.
  - On entry: `alloc` memory, `pop pointer 0` (sets `THIS` to new address).
  - Returns `this`.

### Page 18-23
Compiling `<term>`s
Generate VM code to evaluate term and push to stack.
- Literals: `push constant`.
- Variables: Look up in symbol tables (subroutine then class).
  - Argument -> `push argument i`.
  - Var -> `push local i`.
  - Static -> `push static i`.
  - Field -> `push this i`.

### Page 24-42
String literals
Official way: `String.new`, `String.appendChar`.
Memory leak issue: Strings created for printing are not freed.
Unofficial fix: Compiler auto-generates `String.dispose` calls after use in `do` statements or expression lists.

## 11-4: Summing Up and Looking Forward

### Page 1
Summing up and looking forward
John Lapinskas, University of Bristol

### Page 2-9
Knowing what we don't know
Topics not covered:
- HDL (Verilog).
- Advanced assembly (MIPS/ARM).
- Advanced hardware (pipelining, caching, interrupts).
- OS (processes).
- Advanced compilers (optimisation, type checking).

### Page 10-13
What we’ve done
- **Jack to Stack Machine**: Compiler (Grammar, recursion, symbol tables).
- **Stack Machine to Assembly**: VM Translator (Stack implementation, function calls, memory mapping).
- **Assembly to Machine Code**: Assembler (Binary translation, symbols).
- **Computer from Scratch**: Hardware (Gates, ALU, RAM, CPU).
From NAND gates to a high-level language game.
