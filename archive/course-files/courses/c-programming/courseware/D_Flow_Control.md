# Flow Control

## Comparisons

Operator | Meaning
---|---
`<` | less than
`>` | greater than
`<=` | less than or equal to
`>=` | greater than or equal to
`==` | equal to
`!=` | not equal to
`!` | not
`&&` | logical AND
`||` | logical OR

*   Any relation is either true or false.
*   Any non-zero value is true.
*   `(a < b)` returns the value 0 or 1.
*   `(i == 5)` is a test not an assignment.
*   `(!a)` is either true (1) or false (0).
*   `(a && b)` is true if both a and b are true.
*   Single `&` and `|` are bitwise operators not comparisons - more on this later.

## Short-Circuit Evaluation

```c
if(x >= 0.0 && sqrt(x) < 10.0){
    .... /* Do Something */
}
```

It's not possible to take the `sqrt()` of a negative number. Here, the `sqrt()` statement is never reached if the first test is false. In a logical AND, once any expression is false, the whole must be false.

## The if() Statement

Strictly, you don't need braces if there is only one statement as part of the if :

```c
if (expr)
    statement
```

If more than one statement is required :

```c
if (expr) {
    statement-1
    ...
    statement-n
}
```

However, we will always brace them, even if it's not necessary.

Adding an else statement :

```c
if (expr) {
    statement-1
    ...
    statement-n
} else {
    statement-a
    ...
    statement-e
}
```

## A Practical Example of if:

```c
#include <stdio.h>
int main(void)
{
    int x, y, z;
    printf("Input three integers: ");
    if(scanf("%d%d%d", &x, &y, &z)!=3){
        printf("Didn't get 3 numbers?\n");
        return 1;
    }
    int min;
    if(x <= y){
        min = x;
    }
    // Nasty, dropped braces:
    else
        min = y;
    if(z < min){
        min = z;
    }
    printf("The minimum value is %d\n", min);
    return 0;
}
```

Execution:
Input three integers: 5 7 -4
The minimum value is -4

## The while() Statement

```c
while(expr)
    statement
```

This, as with the for loop, may execute compound statements :

```c
while(expr){
    statement-1
    ...
    statement-n
}
```

However, we will always brace them, even if it's not necessary.

```c
// Simple while countdown
#include <stdio.h>

int main(void)
{
    int n = 9;

    while(n > 0){
        printf("%d ", n);
        n--;
    }
    printf("\n");
    return 0;
}
```

Execution :
9 8 7 6 5 4 3 2 1

## The for() Loop

This is one of the more complex and heavily used means for controlling execution flow.

```c
for ( init ; test ; loop ){
    statement_1
    ...
    ...
    statement_n
}
```

and may be thought of as :

```c
init ;
while (test) {
    statement_1
    ...
    ...
    statement_n
    loop ;
}
```

In the for() loop, note :
*   Semi-colons separate the three parts.
*   Any (or all) of the three parts could be empty.
*   If the test part is empty, it evaluates to true.
*   `for(;;){ a+=1; }` is an infinite loop.

## A Triply-Nested Loop

```c
// Triples of integers that sum to N
#include <stdio.h>
#define N 7

int main(void)
{
    int cnt = 0, i, j, k;

    for(i = 0; i <= N; i++){
        for(j = 0; j <= N; j++){
            for(k = 0; k <= N; k++){
                if(i + j + k == N){
                    ++cnt;
                    printf("%3i%3i%3i\n", i, j, k);
                }
            }
        }
    }
    printf("\nCount: %i\n", cnt);
    return 0;
}
```

Output:
  0  0  7
  0  1  6
  0  2  5
  0  3  4
  0  4  3
  0  5  2
  0  6  1
  0  7  0
etc.
  4  3  0
  5  0  2
  5  1  1
  5  2  0
  6  0  1
  6  1  0
  7  0  0
Count: 36

## The Comma Operator

This has the lowest precedence of all the operators in C and associates left-to-right.

`a = 0, b = 1;`

Hence, the for loop may become quite complex :

```c
for(sum = 0, i = 1; i <= n; ++i){
    sum += i;
}
```

An equivalent, but more difficult to read expression :

```c
for(sum = 0, i = 1; i <= n; sum += i, ++i);
```

Notice the loop has an empty body, hence the semicolon.

## The do-while() Loop

```c
do {
    statement-1
    ...
    statement-n
} while (test);
```

Unlike the `while()` loop, the `do-while()` will always be executed at least once.

```c
// Simple do-while countdown
#include <stdio.h>

int main(void)
{
    int n = 9;

    /* This program always prints at least one
       number, even if n initialised to 0 */
    do
    {
        printf("%i ", n);
        n--;
    } while (n > 0);
    printf("\n");
    return 0;
}
```

Execution:
9 8 7 6 5 4 3 2 1

## The switch() Statement

```c
switch (val) {
    case 1 :
        a++;
        break;
    case 2 :
    case 3 :
        b++;
        break;
    default :
        c++;
}
```

*   The `val` must be an integer.
*   The `break` statement causes execution to jump out of the loop. No `break` statement causes execution to 'fall through' to the next line.
*   The `default` label is a catch-all.

```c
/* A Prime number can only be divided
   exactly by 1 and itself */

#include <stdio.h>

int main(void)
{

   int i, n;
   do{
      printf("\nEnter a number from 2 - 9 : ");
      n = scanf("%d", &i);
   }while( (n!=1) || (i<2) || (i>9) );

   switch(i){
      case 2:
      case 3:
      case 5:
      case 7:
         printf("That's a prime!\n");
         break;
      default:
         printf("That is not a prime!\n");
   }
   return 0;
}
```

Execution：
Enter a number from 2 - 9 : 1
Enter a number from 2 - 9 : 0
Enter a number from 2 - 9 : 10
Enter a number from 2 - 9 : 3
That's a prime!

## The Conditional (?) Operator

As we have seen, C programers have a range of techniques available to reduce the amount of typing :

`expr1 ? expr2 : expr3`

If expr1 is true then expr2 is executed, else expr3 is evaluated.

```c
#include <stdio.h>
int main(void)
{
    int x, y, z;
    printf("Input three integers: ");
    if(scanf("%d%d%d", &x, &y, &z) !=3){
        printf("Didn't get 3 numbers?\n");
        return 1;
    }
    int min;
    min = (x < y)? x : y;
    min = (z < min)? z : min;
    printf("The minimum value is %i\n", min);
    return 0;
}
```
