# Hello, World

## Hello World!

```c
main( ) {
    extrn a, b, c;
    putchar(a); putchar(b); putchar(c); putchar('|'*n');
}

a 'hell';
b 'o, w';
c 'orld';
```

Hello World first seen in: Brian Kernighan, A Tutorial Introduction to the Language B, 1972

```c
/* The traditional first program
  in honour of Dennis Ritchie
  who invented C at Bell Labs
  in 1972 */

#include <stdio.h>

int main(void)
{
  printf("Hello, world!\n");
  return 0;
}
```

Execution:
Hello, world!

## Dissecting the 1st Program

*   Comments are bracketed by the `/*` and `*/` pair.
*   `#include <stdio.h>`
    Lines that begin with a `#` are called preprocessing directives.
*   `int main(void)`
    Every program has a function called `main()`
*   Statements are grouped using braces,
    `{ ... }`
*   `printf()` One of the pre-defined library functions being called (invoked) using a single argument the string :
    `"Hello, world!\n"`
*   The `\n` means print the single character newline.
*   Notice all declarations and statements are terminated with a semi-colon.
*   `return(0)` Instruct the Operating System that the function `main()` has completed successfully.

## Area of a Rectangle

```c
#include <stdio.h>

int main(void)
{
    // Compute the area of a rectangle
    int side1, side2, area;
    side1 = 7;
    side2 = 8;
    area = side1 * side2;

    printf("Length of side 1 = %i metres\n", side1);
    printf("Length of side 2 = %i metres\n", side2);
    printf("Area of rectangle = %i metres squared\n", area);
    return 0;
}
```

Execution:

Length of side 1 = 7 metres
Length of side 2 = 8 metres
Area of rectangle = 56 metres squared

## Dissecting the Area Program

*   `//` One line comment.
*   `#include <stdio.h>` Always required when using I/O.
*   `int side1, side2, area;` Declaration
*   `side2 = 8;` Assignment
*   `printf()` has 2 Arguments. The control string contains a `%i` to indicate an integer is to be printed.

```c
1 preprocessing directives
2
3 int main(void)
4 {
5   declarations
6
7   statements
8 }
```

## Arithmetic Operators

`+`, `-`, `/`, `*`, `%`
Addition, Subtraction, Division, Multiplication, Modulus.
Integer arithmetic discards remainder i.e. 1/2 is 0, 7/2 is 3.
Modulus (Remainder) Arithmetic. 7%4 is 3, 12%6 is 0.
Only available for integer arithmetic.

## The Character Type

```c
// Demonstration of character arithmetic
#include <stdio.h>

int main(void)
{
    char c;

    c = 'A';
    printf("%c ", c);
    printf("%c\n", c+1);
    return 0;
}
```

Execution:
A B

*   The keyword `char` stands for character.
*   Used with single quotes i.e. `'A'`, or `'+'`.
*   Some keyboards have a second single quote the back quote ``` ` ```
*   Note the `%c` conversion format.

## Floating Types

```c
#include <stdio.h>

int main(void)
{

    double x, y;

    x = 1.888888;
    y = 2.111111;

    printf("Sum of x & y is %.f.\n", x + y);

    return 0;
}
```

Execution :
Sum of x & y is 3.999999.

*   In C there are three common floating types :
    1.  `float`
    2.  `double`
    3.  `long double`
*   The Working Type is doubles.

## The Preprocessor

*   A `#` in the first column signifies a preprocessor statement.
*   `#include <file.h>` Exchange this line for the entire contents of file.h, which is to be found in a standard place.
*   `#define PI 3.14159265358979` Replaces all occurrences of PI with 3.14159265358979.
*   Include files generally contain other `#define`'s and `#include`'s (amongst other things).

## Using printf()

*   `printf( fmt-str, arg1, arg2, ...);`

Format | Type
---|---
%c | Characters
%i | Integers
%e | Floats/Doubles (Engineering Notation)
%f | Floats/Doubles
%s | Strings

*   Fixed-width fields: `printf("F:%7f\n", f);`
    `F: 3.0001`

*   Fixed Precision: `printf("F:%.2f\n", f);`
    `F:3.00`

## Using scanf()

*   Similar to `printf()` but deals with input rather than output.
*   `scanf(fmt-str, &arg1, &arg2, ...);`
*   Note that the address of the argument is required.

Format | Type
---|---
%c | Characters
%i | Integers
%f | Floats
%lf | Doubles
%s | Strings

*   Note doubles handled differently than floats.

## While Loops

```c
while (test is true) {
    statement 1;
    ...
    statement n;
}
```

```c
// Sums are computed.
#include <stdio.h>
int main(void)
{
    int cnt = 0;
    float sum = 0.0, x;
    printf("Input some numbers: ");
    while (scanf("%f", &x) == 1) {
        cnt = cnt + 1;
        sum = sum + x;
    }

    printf("\n%s%5i\n%s%5f\n\n",
           "Count: ", cnt, "Sum: ", sum);

    return 0;
}
```

Execution:
Input some numbers: 1 5 9 10

Count:     4
Sum: 25.000000

## Common Mistakes

*   Missing `"`
    `printf("%c\n, ch);
*   Missing `;`
    `a = a + 1`
*   Missing Address in `scanf()`
    `scanf("%d", a);

```