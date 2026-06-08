# Grammar

## Grammar

*   C has a grammar/syntax like every other language.
*   It has Keywords, Identifiers, Constants, String Constants, Operators and Punctuators.
*   Valid Identifiers :
    `k`, `_id`, `iamanidentifier2`, `so__am__.i`.
*   Invalid Identifiers :
    `not#me`, `101_south`, `-plus`.
*   Constants :
    17 (decimal), 017 (octal), 0x17 (hexadecimal).
*   String Constant enclosed in double-quotes :
    `"I am a string"`

## Operators

*   All operators have rules of both precedence and associativity.
*   `1 + 2 * 3` is the same as `1 + (2 * 3)` because `*` has a higher precedence than `+`.
*   The associativity of `+` is left-to-right, thus `1 + 2 + 3` is equivalent to `(1 + 2) + 3`.
*   Increment and decrement operators: `i++;` is equivalent to `i = i + 1;`
*   May also be prefixed `--i;`

```c
#include <stdio.h>
int main(void)
{
    int a, c = 0;
    a = ++c;
    int b = c++;
    printf("%i %i %i\n", a, b, ++c);
    return 0;
}
```

Question: What is the output?

## Assignment

*   The `=` operator has a low precedence and a right-to-left associativity.
*   `a = b = c = 0;` is valid and equivalent to :
    `a = (b = (c = 0));`
*   `i = i + 3;` is the same as `i += 3;`
*   Many other operators are possible e.g. `-=`, `*=`, `/=` .

```c
// 1st few powers of 2 are printed .
#include <stdio.h>

int main(void)
{
    int i = 0, power = 1;
    while (++i <= 10){
        printf("%5i", power *= 2);
    }
    printf("\n");
    return 0;
}
```

Execution :
    2    4    8   16   32   64  128  256  512 1024

## The Standard Library

```c
#include <stdio.h>
#include <stdlib.h>

int main(void)
{
    printf("Randomly distributed integers are printed.\n");
    printf("How many do you want to see? ");

    int n;
    if (scanf("%d", &n) == 1) {
        for (int i = 0; i < n; ++i) {
            if (i % 4 == 0) {
                printf("\n");
            }
            printf("%12i", rand());
        }
        printf("\n");
        return 0;
    }
    return 1;
}
```

Execution:
Randomly distributed integers are printed.
How many do you want to see? 11

1804289383  846930886 1681692777 1714636915
1957747793  424238335  719885386 1649760492
 596516649 1189641421 1025202362

*   Definitions required for the proper use of many functions such as `rand()` are found in `stdlib.h`.
*   Do not mistake these header files for the libraries themselves!

```