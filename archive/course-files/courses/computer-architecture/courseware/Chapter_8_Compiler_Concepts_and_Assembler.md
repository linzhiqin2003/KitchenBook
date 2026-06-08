# Chapter 8: Compiler Concepts and The Hack Assembler

## 8-1: Compiler Concepts: Lexing

### Page 1
Compiler concepts: Lexing
COMSM1302 Overview of Computer Architecture
John Lapinskas, University of Bristol

### Page 2-4
Our next goal
We now understand both Hack assembly and the Hack ISA.
But how does the assembler work?
This week, our goal is to create a Hack assembler of our own in C!

### Page 5-16
Compilers: A big-picture view
Modern compilers usually work in discrete phases:
- Preprocessing
- Lexing
- Parsing/syntax analysis
- Semantic analysis
- Intermediate representation (IR)
- Optimisation
- Code generation

Lexing is the process of converting a string of code into a list of tokens.
Parsing (Syntax analysis) determines the logical structure (grammar) of the code.
Semantic analysis determines the meaning (e.g., types, variable definitions).
For an assembler, syntax and semantics are almost identical, so we can fold semantic analysis into lexing and parsing.
Our Hack assembler will have just two steps: lexing and parsing.

### Page 17-19
The Joy of Lex
A token (a.k.a. lexeme or lexical element) is an “indivisible” piece of code that can’t be broken down further without losing its meaning.
Lexing involves removing whitespace and comparing strings.

### Page 20-26
Tokens in Hack assembly
We can create a grammar for Hack assembly with the following tokens:
- Keywords: A, D, M, JGT, JEQ, etc., SCREEN, KBD, SP, LCL, ARG, THIS, THAT, R0-R15.
- Symbols: @, +, -, &, |, =, ;, !.
- Integer literals: 0...32767.
- Identifiers: Any string containing no whitespace that’s not a keyword and starts with a letter.
- Newlines.

Note: We throw whitespace and comments away. We also handle labels (declarations like `(LOOP)`) separately, likely during lexing or a pre-pass.

### Page 27-31
Example lexer output
Code: `D;JGT // if D>0...`
Tokens:
1. (type=Keyword, value=D)
2. (type=Symbol, value=;)
3. (type=Keyword, value=JGT)
4. (type=Newline, value=None)

## 8-2: Compiler Concepts: Symbol Tables

### Page 1
Compiler concepts: Symbol tables
COMSM1302 Overview of Computer Architecture
John Lapinskas, University of Bristol

### Page 2-13
Tracking labels and variables
Recall in Hack assembly, `@` can be followed by a number, label, or variable.
The assembler must:
1. Allocate each variable a corresponding address in RAM, starting from 16. Replace variables by their addresses.
2. Assign each label the address in ROM matching the machine code line of its declaration. Replace labels by their addresses.

We do this using "symbol tables".

### Page 14-15
Identifiers and symbol tables
An identifier is a token representing an entity defined in the code (label, variable).
A symbol table maps identifiers to their meanings (addresses).
In Hack, we have:
- Label table: Maps label names to ROM addresses.
- Variable table: Maps variable names to RAM addresses.

### Page 16
Symbol tables in Hack: The goal
Example tables for code with `input1`, `output_first`, `(output_first)`, etc.
Label table: output_first -> 10, ...
Variable table: input1 -> 16, ...

### Page 17-19
How do symbol tables work?
Operations: Add (name, address), Check (name), Retrieve (address).
Implementation: Hash table (efficient) or dynamically-sized collection (simpler).
(Assignment uses provided `symboltable.c`).

### Page 20-22
How do we fill symbol tables?
Both tables start empty.
1. During lexing (Pass 1): Look for label declarations `(Label)`. Add them to the label table with the current ROM address. Remove the label declaration from the stream.
2. During parsing (Pass 2): For each identifier found in an A-instruction (`@Identifier`):
   - Check label table. If present, use ROM address.
   - Check variable table. If present, use RAM address.
   - If in neither, it's a new variable. Add to variable table with next available RAM address (starting 16), and use that.

### Page 23-24
Advanced symbol tables: Scopes
In high-level languages, compilers track scopes (e.g. variables in functions or blocks).
One symbol table per scope, often managed as a stack of tables.

## 8-3: Compiler Concepts: Parsing

### Page 1
Compiler concepts: Parsing
COMSM1302 Overview of Computer Architecture
John Lapinskas, University of Bristol

### Page 2-3
Describing languages
Informal descriptions (like English text) can be ambiguous or inconvenient.

### Page 4-13
Backus-Naur Form (BNF)
A way of rigorously specifying valid syntax (grammar).
Recursive definitions.
Example: `<sentence> ::= 'The' <noun> <presentVerb> 'the' <noun>`
Terminals (tokens) vs Non-terminals (`<...>`).

### Page 14-19
Example: Integers
Defining integers recursively:
`<digit> ::= '0' | ... | '9'`
`<number> ::= <digit> | <digit> <number>`
Refining for negative numbers and no leading zeros.

### Page 20
Parse trees (CST)
Goal of parsing: Convert tokens into a Concrete Syntax Tree (CST) reflecting the BNF structure.
Leaves are tokens; internal nodes are non-terminals.

### Page 21
Abstract Syntax Trees (AST)
Simplified version of CST, removing unnecessary intermediate nodes/tokens (like punctuation) to focus on logical structure.

### Page 22-23
Ambiguity
Some grammars allow multiple valid parse trees for the same string (e.g. arithmetic precedence).
Must be resolved (e.g. by defining precedence rules).

### Page 24-25
Generating parse trees
Parsing is well-understood. Use parser generators (e.g. yacc, bison) or write recursive descent parsers.

### Page 26
Extended Backus-Naur Form (EBNF)
Adds syntax for usability (but same power):
- `()` grouping
- `[]` optional
- `{}` repetition (0 or more)
- `-` exclusion

## 8-4: A Parser for Hack Assembly

### Page 1
A parser for Hack assembly
COMSM1302 Overview of Computer Architecture
John Lapinskas, University of Bristol

### Page 2
Tokens for Hack assembly (reminder)
Keywords, Symbols, Integer literals, Identifiers, Newlines.

### Page 3-7
EBNF for Hack assembly
`<instruction> ::= ( <aInstruction> | <cInstruction> ), newline;
<aInstruction> ::= "@", ( integerLiteral | identifier | <memoryKeyword> );
<cInstruction> ::= [ <assignment> ], <computation>, [ <jump> ];
<assignment> ::= (destinations...), "=";
<jump> ::= ";", (jump conditions...);
<computation> ::= ...` (expressions involving registers and operators)

### Page 8-9
Example CSTs for Hack assembly
`0;JMP\n` -> Instruction -> CInstruction -> (Computation "0", Jump "; JMP")
`DM=M+D;JLE\n` -> Instruction -> CInstruction -> (Assignment "DM=", Computation "M+D", Jump "; JLE")

### Page 10-39
How do we build a Hack CST? (LL Parsing)
We use LL parsing: Look at tokens left-to-right, build top-down.
Hack is LL(2) (needs 2 tokens lookahead) because of cases like `D` (could be `D=...` or `D;...` or just `D`).
Example build-up for `DM=M+D;JLE`:
1. `D`: Start instruction. Lookahead `M`.
2. `DM`: Lookahead `=`. Must be assignment.
3. `DM=`: Assignment confirmed.
4. `M`: Computation start. Lookahead `+`.
5. `M+`: Binary op.
6. `D`: Second operand. Lookahead `;`.
7. `;`: Jump start.
8. `JLE`: Jump condition.
9. `\n`: End instruction.

### Page 40-44
How do we actually parse Hack?
CSTs are overkill for Hack. We can use simple logic on tokens.
- Is first token `@`? -> A-instruction.
  - Value is next token (literal or identifier).
- Otherwise -> C-instruction.
  - Check for `=`. Left side is dest. Right side starts comp.
  - Check for `;`. Right side is jump. Left side ends comp.
  - Map strings to binary bits.

### Page 45
The Hack assembler: A summary

**Pass 1: Lexing**
- Remove comments/whitespace.
- Handle label declarations `(Label)`: Add to label table with current ROM address.
- Output other tokens to temp file.

**Pass 2: Parsing**
- Read tokens.
- **A-instruction**:
  - Handle variables (add to table if new).
  - Resolve address (lookup in table).
  - Output binary `0...`.
- **C-instruction**:
  - Parse dest, comp, jump.
  - Map to binary fields.
  - Output binary `111...`.
