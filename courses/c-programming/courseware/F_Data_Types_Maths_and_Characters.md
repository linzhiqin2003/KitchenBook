# Data Types, Maths and Characters

## Fundamental Data types

*   `[ unsigned | signed ]`
*   `[ long | short ]`
*   `[ char | int | float | double ]`
*   The use of `int` implies signed int without the need to state it.
*   Likewise `unsigned short` means `unsigned short int`.

Type | Minimum size (bits) | Format specifier
---|---|---
char | 8 | %c
signed char | 8 | %c (or %hi for numerical output)
unsigned char | 8 | %c (or %hu for numerical output)
short | 16 | %hi or %hi
signed short | 16 |
signed short int | 16 |
unsigned short | 16 | %hu
unsigned short int | 16 | %hu
int | 16 | Identical for printf: %i or %d
For scanf: %d input decimal only
For scanf: %i auto-detects format (octal,decimal,hex)
signed | 16 |
signed int | 16 |
unsigned int | 16 | %u
long | 32 | %ld or %li
long int | 32 | %ld or %li
signed long | 32 | %ld or %li
signed long int | 32 | %ld or %li
unsigned long | 32 | %lu
unsigned long int | 32 | %lu
long long | 64 | %lli or %lld
long long int | 64 | %lli or %lld
signed long long | 64 | %lli or %lld
signed long long int | 64 | %lli or %lld
unsigned long long | 64 | %llu
unsigned long long int | 64 | %llu
float | - | scanf(): %f, %g, %e, %a
double | - | %lf, %lg, %le, %la
long double | - | %Lf, %Lg, %Le, %La

## Binary Storage of Numbers

In an unsigned char :
2⁷ 2⁶ 2⁵ 2⁴ 2³ 2² 2¹ 2⁰
0   1   0   0   1   1   0   0

The above represents :
1 * 64 + 1 * 8 + 1 * 4 = 76.

*   Floating operations need not be exact.

```c
#include <stdio.h>
int main(void)
{
    float d = 0.1;
    printf("%.12f\n", 3.0*d);
    return 0;
}
```

Execution :
0.300000004470

*   Not all floats are representable so are only approximated.
*   Since floats may not be stored exactly, it doesn't make sense to try and compare them:
    `if (d == 0.3 )`
*   Therefore, we don't allow this by explicitly using the compiler warning flag: `-Wfloat-equal`

## sizeof()

To find the exact size in bytes of a type on a particular machine, use `sizeof()`. On a Dell Windows 10 laptop running WSL:

```c
#include <stdio.h>

int main(void)
{
    printf("char          :%31d\n", sizeof(char));
    printf("short         :%31d\n", sizeof(short));
    printf("long          :%31d\n", sizeof(long));
    printf("unsigned      :%31d\n", sizeof(unsigned));
    printf("long long     :%31d\n", sizeof(long long));
    printf("float         :%31d\n", sizeof(float));
    printf("dbl           :%31d\n", sizeof(double));
    printf("long dbl      :%31d\n", sizeof(long double));
    printf("\n");

    return 0;
}
```

Execution:
char           : 1
short          : 2
long           : 8
unsigned       :4
long long      :8
float          :4
dbl            :8
long dbl       :16

## Mathematical Functions

*   There are no mathematical functions built into the C language.
*   However, there are many functions in the maths library which may linked in using the `-lm` option with the compiler e.g. `gcc math1.c -o math1 -lm`
*   Functions include :
    `sqrt()` `pow()` `round()`
    `fabs()` `exp()` `log()`
    `sin()` `cos()` `tan()`
*   Most take doubles as arguments and return doubles.

## Casting

```c
/* Compute the Volume of a Sphere
   to the nearest integer          */
#include <stdio.h>
#include <math.h>

#define PI 3.14159265358979323846

int main(void)
{
  double r;
  printf("Enter a radius : ");
  scanf("%lf", &r);
  // Make sure radius is positive
  r = fabs(r);
  double v = 4.0 / 3.0 * PI * pow(r, (double)3);
  printf("Volume of your ball = %f\n", v);
  printf("Volume of your ball = %.2f\n", v);
  printf("Volume of your ball = %d\n", (int)v);
  printf("Volume of your ball = %.0f\n", v);
  printf("Volume of your ball = %f\n", round(v));
  return 0;
}
```

*   An explicit type conversion is called a cast.
*   If it moves - cast it. Don't trust the compiler to do it for you!

Execution:
Enter a radius :7.75
Volume of your ball =1949.816390
Volume of your ball =1949.82
Volume of your ball =1949
Volume of your ball =1950
Volume of your ball =1950.000000

## Storage of Characters

*   Characters are stored in the machine as one byte (generally 8-bits storing one of 256 possible values).
*   These may be thought of a characters, or very small integers.
*   Only a subset of these 256 values are required for the printable characters, space, newline etc.
*   Declaration:
    `char c;`
    `c = 'A';`
    or:
    `char c1 = 'A', c2 = '*', c3 = ';';`

*   The particular integer used to represent a character is dependent on the encoding used. The most common of these, used on most UNIX and PC platforms, is ASCII.

Type | 'a' | 'b' | 'c' | ... | 'z'
---|---|---|---|---|---
ASCII value | 97 | 98 | 99 | ... | 122

Type | 'A' | 'B' | 'C' | ... | 'Z'
---|---|---|---|---|---
ASCII value | 65 | 66 | 67 | ... | 90

Type | '0' | '1' | '2' | ... | '9'
---|---|---|---|---|---
ASCII value | 48 | 49 | 50 | ... | 57

Type | '&' | '*' | '+' | ... |
---|---|---|---|---|---
ASCII value | 38 | 42 | 43 | ... |

## Using Characters

*   When using `printf()` and `scanf()` the formats `%c` and `%i` do very different things :
    ```c
    char c = 'a'
    printf("%c\n", c); /* prints : a */
    printf("%i\n", c); /* prints : 97 */
    ```
*   Hard-to-print characters have an escape sequence i.e. to print a newline, the 2 character escape `\n` is used.

Escape sequence | Hex value | Character
---|---|---
\a | 07 | Alert (Beep, Bell)
\b | 08 | Backspace
\e | 1B | Escape character
\f | 0C | Formfeed Page Break
\n | 0A | Newline (Line Feed)
\r | 0D | Carriage Return
\t | 09 | Horizontal Tab
\v | 0B | Vertical Tab
\\ | 5C | Backslash
\' | 27 | Apostrophe
\" | 22 | Double quote
\? | 3F | Question mark

## Using getchar() and putchar()

```c
// Outputs characters twice

#include <stdio.h>

int main(void)
{

    char c;
    do{
       c = getchar();
       putchar(c);
       putchar(c);
    }while(c != '!');
    putchar('\n');

    return 0;
}
```

Execution :
abc123!
aabbcc112233!!

This has the unfortunate problem of requiring a 'special' character to terminate. More aggressively, the user could terminate by pressing CTRL-C.

```c
// Outputs characters twice

#include <stdio.h>

int main(void)
{

    char c; // char or int ?
    while ((c = getchar()) != EOF) {
       putchar(c);
       putchar(c);
    }
    putchar('\n');

    return 0;
}
```

Execution:
abc123
aabbcc112233

The end-of-file constant is defined in `stdio.h`. Although system dependent, -1 is often used. On the UNIX system this is generated when the end of a file being piped is reached, or when CTRL-D is pressed.

## Capitalization

```c
// Outputs characters twice
#include <stdio.h>

#define CAPS ('A' - 'a')

int main(void)
{
    int c;
    while ((c = getchar()) != '\n'){
        if (c >= 'a' && c <= 'z'){
            putchar(c + CAPS);
        }
        else {
            putchar(c);
        }
    }
    putchar('\n');

    return 0;
}
```

Macro | true returned if:
---|---
`isalnum(int c)` | Letter or digit
`isalpha(int c)` | Letter
`iscntrl(int c)` | Control character
`isdigit(int c)` | Digit
`isgraph(int c)` | Printable (not space)
`islower(int c)` | Lowercase
`isprint(int c)` | Printable
`ispunct(int c)` | Punctuation
`isspace(int c)` | White Space
`isupper(int c)` | Uppercase
`isxdigit(int c)` | Hexadecimal
`isascii(int c)` | ASCII code

Execution:
Hello World!
HELLO WORLD

This is more easily achieved by using some of the definitions found in `ctype.h`.

## ctype.h

Some useful functions are :

| Function/Macro       | Returns:           |
|----------------------|--------------------|
| int tolower(int c)   | Lowercase c        |
| int toupper(int c)   | Uppercase c        |
| int toascii(int c)   | ASCII code for c   |

```c
#include <stdio.h>
#include <ctype.h>

int main(void)
{
    int c;
    while ((c = getchar()) != EOF){
        if (islower(c)){
            putchar(toupper(c));
        } else {
            putchar(c);
        }
    }
    putchar('\n');
    return 0;
}
```

```c
#include <stdio.h>
#include <ctype.h>

int main(void)
{
    int c;
    while ((c = getchar()) != EOF){
        /* toupper() returns non-lowercase chars unaltered */
        putchar(toupper(c));
    }
    putchar('\n');
    return 0;
}
```

Execution :

Hello World!
HELLO WORLD!

