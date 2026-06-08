# Pointers

## Call-by-Value

```c
#include <stdio.h>

void changex(int x);

int main(void)
{
    int x = 1;

    changex(x);
    printf("%d\n", x);
    return 0;
}

void changex(int x)
{
    x = x + 1;
}
```

*   In the program, the function cannot change the value of v as defined in `main()` since a copy is made of it.
*   To allow a function to modify the value of a variable passed to it we need a mechanism known as call-by-reference, which uses the address of variables (pointers).

Execution :
1

## Call-by-Reference

*   We have already seen addresses used with `scanf()`. The function call:
    `scanf("%i", &v);
    causes the appropriate value to be stored at a particular address in memory.

*   If `v` is a variable, then `&v` is its address, or location, in memory.

*   `int i, *p;`

*   Here i is an `int` and p is of type pointer to `int`.

*   Pointers have a legal range which includes the special address 0 and a set of positive integers which are the machine addresses of a particular system.

## The NULL Pointer

*   `p = NULL;
*   `p = &i;

## Equivalence of i and *p

*   `i = 5;

```c
#include <stdio.h>

int main(void)
{

    int i = 5;
    int* p = &i;
    printf("%i\n", *p);
    i = 17;
    printf("%i\n", *p);
    *p = 99;
    printf("%i\n", i);

    return 0;
}
```

Execution :
5
17
99

## scanf Again

```c
#include <stdio.h>
int main(void)
{
    int i;
    int* p = &i;
    printf("Please Type a number : ");
    scanf("%d", &i);
    printf("%d\n", &i);
    printf("%d\n", i);
    printf("Please Type a number : ");
    scanf("%d", p);
    printf("%d\n", i);

    return 0;
}
```

Execution :
Please Type a number : 70
70
3
Please Type a number : 3
3

In many ways the dereference operator `*` is the inverse of the address operator `&`.

```c
float x = 5, y = 8, *p;
p = &x;
y = *p;
```

What is this equivalent to ?

## The swap Function

```c
#include <stdio.h>

void swap(int* p, int* q);

int main(void)
{
    int a = 3, b = 7;

    // 3 7 printed
    printf("%d %d\n", a, b);
    swap(&a, &b);
    // 7 3 printed
    printf("%d %d\n", a, b);
    return 0;
}

void swap(int* p, int* q)
{
    int tmp;

    tmp = *p;
    *p = *q;
    *q = tmp;
}
```

At beginning of function:
a holds 3, b holds 7; p points to a, q points to b; tmp is empty.

At end of function:
a holds 7, b holds 3; p points to a, q points to b; tmp holds 3.

Remember that the variables a and b are not in the scope of `swap()`.

Execution:
3 7
7 3

## Arrays are Pointers?

*   An array name by itself is simply an address (Array Decay).
*   For instance:
    ```c
    int a[5];
    int *p;
    ```
    declares an array of 5 elements, and a is the address of the start of the array.
*   Assigning:
    `p = a;
    is completely valid and the same as:
    `p = &a[0];

*   To assign p to point to the next element, we could either:
    `p = a + 1;
    `p = &a[1];
*   Notice that `p = a + 1` advances the pointer 4 bytes and not 1 byte. This is because an integer is 4 bytes long and p is a pointer to an `int`.
*   we can use the pointer p is exactly the same way as normal, i.e.:
    `*p = 5;

## Summing an Array

```c
#include <stdio.h>
#define NUM 5

int sum(int a[]);

int main(void)
{
    int n[NUM] = {10, 12, 6, 7, 2};
    printf("%d\n", sum(n));
    return 0;
}

int sum(int a[])
{
    int tot = 0;
    for(int i=0; i<NUM; i++){
        tot += a[i];
    }
    return tot;
}
```
Execution :
37

```c
#include <stdio.h>
#define NUM 5

int sum(int a[]);

int main(void)
{
    int n[NUM] = {10, 12, 6, 7, 2};
    printf("%d\n", sum(n));
    return 0;
}

int sum(int a[])
{
    int tot =0;
    for(int i=0; i<NUM; i++){
        tot += *(a + i);
    }
    return tot;
}
```
Execution :
37

```c
#include <stdio.h>
#define NUM 5

int sum(int* p);

int main(void)
{
    int n[NUM] = {10,12,6,7,2};
    printf("%d\n", sum(n));
    return 0;
}

int sum(int* p )
{
    int tot=0;
    for(int i=0; i<NUM; i++){
        tot += *p;
        p++;
    }
    return tot;
}
```
Execution :
37

## Pointers to Structures

*   By default, structures are passed by value (copied) when used as a parameter to a function.
*   But, like any other type, we could pass a pointer instead.
*   The complication is that to access the elements of a structure via a pointer, we use the `->` operator, and not the `.`.

```c
void print_deck(card d[DECK], int n)
{
    char str[BIGSTR];
    for(int i=0; i<n; i++){
        print_card(str, &d[i]);
        printf("%s\n", str);
    }
    printf("\n\n");
}

#define SMALLSTR 20
void print_card(char s[BIGSTR], const card* p)
{
    // Note the +1 below : zero pips not used, but makes easier coding ?
    char pipnames[PERSUIT+1][SMALLSTR] = {"Zero", "One", "Two", "Three",
                                           "Four", "Five", "Six", "Seven",
                                           "Eight", "Nine", "Ten", "Jack",
                                           "Queen", "King"};
    char suitnames[SUITS][SMALLSTR] = {"Hearts", "Diamonds", "Spades", "Clubs"};
    snprintf(s, BIGSTR, "%s of %s", pipnames[p->pips], suitnames[p->stl]);
}
```

## Nested Structures

```c
#include <stdio.h>

struct dateofbirth {
    unsigned char day;
    unsigned short month;
    unsigned short year;
};

typedef struct dateofbirth dob;

typedef struct {
    char* name;
    dob date;
} person;

void print_byval(person b);
void print_byref(const person* p);

int main(void)
{
    person a = {"Gary", {17, 5, 1999}};
    print_byval(a);
    print_byref(&a);
}

void print_byval(person b)
{
    printf("%s %hhu/%hi/%hi\n", b.name, b.date.day, b.date.month, b.date.year);
}

void print_byref(const person* p)
{
    printf("%s %hhu/%hi/%hi\n", p->name, p->date.day, p->date.month, p->date.year);
}
```

Execution:
Gary 17/5/1999
Gary 17/5/1999

```