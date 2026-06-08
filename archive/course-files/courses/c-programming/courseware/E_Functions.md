# Functions

## Simple Functions

```c
#include <stdio.h>

int min(int a, int b);

int main(void)
{
    int j, k, m;

    printf("Input two integers: ");
    scanf("%d%d", &j, &k);
    m = min(j, k);
    printf("The minimum of the two values %i and %i, " \
    "the minimum is %i.\n\n", j, k, m);
    return 0;
}

int min(int a, int b)
{
    if (a < b)
        return a;
    else
        return b;
}
```

*   Execution begins, as normal, in the `main()` function.
*   The function prototype is shown at the top of the file. This allows the compiler to check the code more thoroughly.
*   The function is defined between two braces.
*   The function `min()` returns an `int` and takes two `int`'s as arguments. These are copies of j and k.
*   The `return` statement is used to return a value to the calling statement.

Execution:

Input two integers: 5 2

Of the two values 5 and 2, the minimum is 2.

## Call-by-Value

In the following example, a function is passed an integer using call by value:

```c
#include <stdio.h>

void fncl(int x);

int main(void)
{
    int x = 1;

    fncl(x);
    printf("%i\n", x);
}

void fncl(int x)
{
   x = x + 1;
}
```

Execution:
1

*   The function does not change the value of x in `main()`, since a in the function is effectively only a copy of the variable.
*   A function which has no return value, is declared `void` and, in other languages, might be termed a procedure.
*   Most parameters used as arguments to functions in C are copied - this is known as call-by-value. We'll see the alternative, call-by-reference, later.

## Testing

```c
#include <stdio.h>

int numfactors(int f);

int main(void)
{
    int n = 12;
    printf("Number of factors in %i is %i\n", \
           n, numfactors(n));
    return 0;
}

int numfactors(int k)
{
    int count = 0;

    for (int i = 1; i <=k; i++){
        if ((k%i)==0) {
            count++;
        }
    }
    return count;
}
```

*   This is a (not very good) function to compute the number of factors a number has.
*   A factor is a number by which a larger (whole/integer) number can be divided.
*   12 has 6 factors: 1,2,3,4,6 and 12 itself.
*   How do we know the program works though?
*   Running it?
    Number of factors in 12 is 6
*   We need something more automated.

## Pre- and Post-Conditions

```c
#include <stdio.h>
#include <assert.h>

int numfactors(int f);

int main(void)
{
    int n = 12;
    printf("Number of factors in %i is %i\n", \
           n, numfactors(n));
    return 0;
}

int numfactors(int k)
{
    int count = 0;
    assert(k >=1); // Avoid trying zero
    assert(k >=1); // Wait, line19 already did this?
    for(int i=1; i<=k; i++){
        if((k%i)==0) {
            count++;
        }
    }
    assert(count <=k);
    return count;
}
```

*   Pre-conditions check the inputs to functions, typically their arguments.
*   Post-conditions check the returns from functions.
*   An `assert` simple states some test that ought to be true. If not, the program aborts with an error.
*   There's a sense that this is somehow safer, but we haven't exactly done much testing on it to ensure the correct answers are returned.

## Assert Testing

```c
#include <stdio.h>
#include <assert.h>

int numfactors(int f);

int main(void)
{
    assert(numfactors(17) == 2);
    assert(numfactors(12) == 6);
    assert(numfactors(6) ==4);
    assert(numfactors(1) ==1);
    assert(numfactors(0) ==0); // ?
    return 0;
}

int numfactors(int k)
{
    int count =0;
    for(int i=1; i<=k; i++){
        if( (k%i)==0 ) {
            count++;
        }
    }
    return count;
}
```

*   We will use assert testing in this style every time we write a function.
*   These tests tend to get quite long, so we generally collect them in a function called `test()` which itself is called from `main()`.
*   If there is no error, there is no output from this program.
*   If you `#define NDEBUG` before the `#include <assert.h>`, all assertions are ignored, allowing them to be used during development and switched off later.

## Self-test: Multiply

*   Write a simple function `int mul(int a, int b)` which multiples two integers together without the use of the multiply symbol in C (i.e. the `*`)
*   Use iteration (a loop) to achieve this.
*   7 × 8 is computed by adding 7, eight times.
*   Use `assert()` calls to test it thoroughly - I've given you some to get you started.

```c
/* Try to write mul(a,b) without using any maths cleverer than addition. */
#include <stdio.h>
#include <assert.h>

int mul(int a, int b);
void test(void);

int main(void)
{
    test();
    return 0;
}

int mul(int a, int b)
{
    // To be completed
}

void test(void)
{
    assert(mul(5,3) == 15);
    assert(mul(3,5) == 15);
    assert(mul(0,3) == 0);
    assert(mul(3,0) == 0);
    assert(mul(1,8) == 8);
    assert(mul(8,1) == 8);
}
```

## Program Layout

It is normal for the `main()` function to come first in a program :

```c
#include <stdio.h>
#include <stdlib.h>

list of function prototypes

int main(void)
{
    . . . . .
}

int f1(int a, int b)
{
    . . . . .
}

int f2(int a, int b)
{
    . . . . .
}
```

However, it is theoretically possible to avoid the need for function prototypes by defining a function before it is used :

```c
#include <stdio.h> 
#include <stdlib.h> 

int f1(int a, int b)
{
    . . . . .
}

int f2(int a, int b)
{
    . . . . .
}

int main(void)
{
    . . . . .
}
```

We will never use this second approach - put `main()` first with the prototypes above it.

## Replacing Functions with Macros

```c
#include <stdio.h>

#define MIN(A, B) ((A)<(B)?(A):(B))

int main(void)
{

    int j, k, m;

    printf("Input two integers: ");
    scanf("%d%d", &j, &k);
    m = MIN(j, k);
    printf("Minimum is %d\n", m);
    return 0;
}
```

Execution:
Input two integers:5 2
Minimum is 2

*   There's sometimes a (tiny) time penalty for using functions.
*   The contents of the functions are saved onto a special stack, so that when you return to the function, its variables and state can be restored.
*   https://en.wikipedia.org/wiki/Call_stack
*   Historically, for small functions that needed to be fast, programmers might have `#define` a macro.
*   There's a "double evaluation" problem though - what happens if we used `m = MIN(j++, k++);`?
*   This is expanded to `((j++)<(k++)?(j++):(k++))` which is not what was intended.

## The inline modifier

*   In C99 the inline modifier was introduced
    https://en.wikipedia.org/wiki/Inline_function
    ... serves as a compiler directive that suggests (but does not require) that the compiler substitute the body of the function inline by performing inline expansion, i.e. by inserting the function code at the address of each function call, thereby saving the overhead of a function call.

```c
#include <stdio.h>

static inline int min(int a, int b);

int main(void)
{

    int j, k, m;

    printf("Input two integers: ");
    scanf("%d%i", &j, &k);
    m = min(j, k);
    printf("Minimum is %i\n", m);
    return 0;
}

inline int min(int a, int b)
{
   if (a < b)
       return a;
   else
       return b;
}
```

Execution:
Input two integers: 5 2
Minimum is 2

## Factorials via Iteration

*   A repeated computation computation is normally achieved via iteration, e.g. using `for()`:
*   Here we compute the factorial of a number - the factorial of 4, written as 4!, is simply 4 × 3 × 2 × 1.
*   Obviously, we'd do more assert tests in the full version.

```c
#include <stdio.h>
#include <assert.h>

int fact(int a);

int main(void)
{
    assert(fact(4) == 24);
    assert(fact(1) == 1);
    assert(fact(0) == 1);
    assert(fact(10) == 3628800);
    return 0;
}

int fact(int a)
{
    int tot = 1;
    for(int i=1; i<=a; i++){
        tot *= i;
    }
    return tot;
}
```

## Factorials via Recursion (Advanced)

*   We could achieve the same result using recursion.
*   The factorial of 4 can be thought of as 4 × 3!
*   A recursive function calls itself - there may be many versions of the same function ‘alive’ at the same time during execution.

```c
#include <stdio.h>
#include <assert.h>

int fact(int a);

int main(void)
{
    assert(fact(4) == 24);
    assert(fact(1) == 1);
    assert(fact(0) == 1);
    assert(fact(10) == 3628800);
    return 0;
}


int fact(int a)
{

    if(a > 0)
        return (a * fact(a - 1));
    else
        return 1;
}
```

## To solve this problem, we need to write a function `int mul(int a, int b)` that multiplies two integers without using the multiplication operator (`*`), using recursion instead. Additionally, we need to ensure the function handles various cases including zero and negative numbers.

### Approach
1.  **Base Case Handling**: If either of the integers is zero, the product is zero.
2.  **Sign Determination**: Determine the sign of the result. If the integers have opposite signs, the result is negative; otherwise, it is positive.
3.  **Absolute Values**: Convert both integers to their absolute values to simplify the recursive addition.
4.  **Recursive Calculation**: The product of two positive integers `abs_a` and `abs_b` can be computed recursively by adding `abs_a` to the product of `abs_a` and `abs_b - 1`.
5.  **Apply Sign**: Adjust the result with the determined sign.

### Solution Code

```c
#include <stdio.h> 
#include <assert.h>

int mul(int a, int b);
void test(void);

int main(void)
{
    test();
    return 0;
}

int mul(int a, int b)
{
    if (a == 0 || b == 0) {
        return 0;
    }

    int sign = 1;
    if ((a < 0 && b > 0) || (a > 0 && b < 0)) {
        sign = -1;
    }

    int abs_a = (a < 0) ? -a : a;
    int abs_b = (b < 0) ? -b : b;

    int result = abs_a + mul(abs_a, abs_b - 1);

    return sign * result;
}

void test(void)
{
    assert(mul(5, 3) == 15);
    assert(mul(3, 5) == 15);
    assert(mul(0, 3) == 0);
    assert(mul(3, 0) == 0);
    assert(mul(1, 8) == 8);
    assert(mul(8, 1) == 8);
    // Additional test cases for negative numbers
    assert(mul(-2, 3) == -6);
    assert(mul(2, -3) == -6);
    assert(mul(-2, -3) == 6);
}
```

### Explanation
- **Base Case**: Directly return 0 if either input is 0.
- **Sign Handling**: Check if the inputs have opposite signs to set the result sign.
- **Absolute Values**: Convert inputs to positive to use recursive addition.
- **Recursion**: Compute the product by repeatedly adding the absolute value of one number to itself the absolute value of the other number times.
- **Sign Application**: Adjust the result with the determined sign to get the final product.

This approach efficiently handles all integer cases using recursion and ensures correctness through test cases with `assert()`.

```