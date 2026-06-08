Q1. How many operands does a C-instruction have?

    ________________

Q2. What value does Hack VM use to represent "true" internally? Give your answer as a signed decimal value.

    ________________

Q3. Which of the following ISAs would you be most likely to see in a mobile phone?

    A. ARM
    B. Hack
    C. MIPS
    D. x64
    E. x86-64

Q4. Which of the following are properties of an ISA, and which are properties of a microarchitecture?

    a) Word length and address space of memory
    b) Energy efficiency
    c) Clock speed
    d) Number of transistors used
    e) Addressing modes supported

Q5. The Hack assembly grammar is reproduced here for reference.

    ![q5-1.png](q5-1.png)

    Using this grammar, complete the below parse tree.

    ![q5-2.png](q5-2.png)

    a = ________________
    b = ________________
    c = ________________
    d = ________________

Q6. Mark the following statements true or false:

    a) A Hack VM program implemented on a Hack CPU under the standard memory mapping can never go 360 levels deep into recursive function calls without a stack overflow.
    b) In order to compile labels, a typical Hack VM translator will keep careful track of the current ROM address in the produced assembly code.
    c) Typically, manual heap allocation functions (such as C's malloc and free or Jack's Memory.alloc and Memory.deAlloc) do not prevent memory fragmentation.
    d) A program calling malloc and free can manually defragment memory by freeing all malloc'd variables, then re-malloc'ing them.
    e) Compilers for several different programming languages might use the same intermediate representation.
    f) One intermediate representation might compile into several different assembly languages.
    g) A function in Hack VM is expected to start with the non-".vm" part of its filename, followed by a ".", followed by a more descriptive name.

Q7. Fill in the blanks: The Hack instruction 0xE564 computes ________________, and stores the result in ________________ and ________________.

Q8. Memory allocated on the heap remains in use until ________________. Variables can be allocated on the heap if their size is known ________________. Memory allocated on the stack remains in use until ________________. Variables can be allocated on the stack if their size is known ________________. In C, we should normally expect variables to be allocated on ________________ unless an explicit call to malloc or free is made, in which case they will be allocated on ________________.

Q9. John is trying to put together a grammar that will match strings that include matching parentheses. For example, he wants "()" or "(())" or "((())())" to be valid under the grammar, but not "(" or "(()". He doesn't care about the empty string "". He puts together the following in BNF, with tokens of '(' and ')' :

    <pair> ::= '(' ')'
    <expression> ::= <pair> | '(' <expression> ')' | '(' <expression> ')' <expression>

    Which of the following is correct?

    A. A string will be valid under the grammar if and only if it is a string of matching parentheses.
    B. Any string of matching parentheses will be valid under the grammar, but some strings of non-matching parentheses will also be valid. In other words, the grammar incorrectly declares some strings as "matching".
    C. Any string that's valid under the grammar is a string of matching parentheses, but not all strings of matching parentheses are valid under the grammar. In other words, the grammar incorrectly declares some strings as "not matching".
    D. None of the other options. In other words, the grammar incorrectly declares some strings "matching" and incorrectly declares other strings "not matching".

Q10. Suppose you have a list of binary words stored sequentially in RAM, starting at an address stored in the variable list_start. Which of the following code fragments will load the 50th item of the list into M?

    A.
    @list_start
    A=M
    D=A
    @50
    D=D+A
    M=D

    B.
    @list_start
    A=M
    D=A
    @50
    D=D+A
    A=D

    C.
    @list_start
    D=A
    @49
    D=D+A
    A=D

    D.
    @list_start
    D=A
    @50
    D=D+A
    A=D

    E.
    @list_start
    A=M
    D=A
    @49
    D=D+A
    M=D

    F. None of the other options.

Q11. Fill in the blanks in the following Hack VM program. Each Hack VM instruction contains 1-3 words. If you want to fill a line with an instruction containing only one word (like "add"), then choose "add", "N/A", and "N/A" from the drop-downs in that order. Likewise for instructions containing only two words.

    // Add a character to the end of the given String object.
    // The first argument will be the String's address. The second argument is the character to append (given as an integer).
    // The String's fields are, in order:
    // - The length of the String.
    // - The maximum length of the String.
    // - The base address of a segment of heap memory containing the characters that make up the String.
    // Note that Jack strings are not null-terminated.

    function String.appendChar 1

    // Check whether string has space to append a new character.
    // If not, crash by calling Sys.error(52).

    push argument 0
    ________________
    ________________

    push this 0
    push this 1
    lt
    ________________
    ________________

    push constant 52
    ________________
    ________________

    label nocrash

    // Store address of new last character of string in local 0.

    push this 2
    push this 0
    add
    ________________
    ________________

    // Append character to string.

    push local 0
    pop pointer 1
    push argument 1
    ________________
    ________________

    // Update length

    push this 0
    push constant 1
    add
    pop this 0

    // End of function

    push constant 0
    ________________
    ________________

Q12. Consider the first-fit memory allocation algorithm discussed in lectures with coalescence of freed segments but without bins ("attempt 3"). Recall that in this algorithm, a value of "true" is used to denote a free segment and a value of "false" is used to denote a used segment. Here are the partial contents of three memory segments:

    Segment 1:
    RAM[0x759] = ________ (a)
    RAM[0x75A] = 0xFFFF
    RAM[0x75B] = ________ (b)
    RAM[0x75C] = 0x2003
    RAM[0x75D] = 0x1422
    ...
    RAM[0x1105] = 0x9AB
    RAM[0x1106] = ________

    Segment 2:
    RAM[0x1420] = ________
    RAM[0x1421] = 0x0000
    RAM[0x1422] = ________ (c)
    RAM[0x1423] = 0x75C
    RAM[0x1424] = ________
    ...
    RAM[0x1500] = 0xDE
    RAM[0x1501] = ________ (d)

    Segment 3:
    RAM[0x2000] = ________
    RAM[0x2001] = 0xFFFF
    RAM[0x2002] = ________ (e)
    RAM[0x2003] = ________ (f)
    RAM[0x2004] = ________
    ...
    RAM[0x22FF] = ________ (g)
    RAM[0x2300] = ________ (h)

    Fill in the values of each of the following segments.

    (a) ________________
    (b) ________________
    (c) ________________
    (d) ________________
    (e) ________________
    (f) ________________
    (g) ________________
    (h) ________________
