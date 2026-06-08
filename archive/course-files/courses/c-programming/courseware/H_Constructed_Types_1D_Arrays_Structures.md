# Constructed Types - 1D Arrays & Structures

## 1D Arrays

*   One-Dimensional arrays are declared by a type followed by an identifier with a bracketed constant expression:
    `float x[10];`
    `int k[ARRAY_SIZE];`

*   The following, (a variable-length array), is not valid:
    `float y[i*2];`
    we prevent these using the `-Wvla` compiler flag.

*   Arrays are stored in contiguous memory, e.g.:
    `int a[5];`

*   Arrays are indexed 0 to n-1.

```c
#include <stdio.h>
#define N 500

int main(void)
{
    /* allocate space a[0]...a[N-1] */
    int a[N];
    int i, sum = 0;
    /* fill array */
    for (i = 0; i < N; ++i) {
        a[i] = 7 + i * i;
    }
    /* print array */
    for (i = 0; i < N; ++i) {
        printf("a[%i]=%i ", i, a[i]);
    }
    /* sum elements */
    for (i = 0; i < N; ++i) {
        sum += a[i];
    }
    /* print sum */
    printf("\nsum=%i\n", sum);
    return 0;
}
```

## 1D Arrays : Initialisation

By default, arrays are uninitialised. When they are declared, they may be assigned a value:

`float x[7] = {-1.1,0.2,2.0,4.4,6.5,0.0,7.7};`

or,

`float x[7] = {-1.1, 0.2};`

the elements 2 ... 6 are set to zero. Also:

`int a[] = {3, 8, 9, 1};`

is valid, the compiler assumes the array size to be 4.

*   `a[5] = a[4] + 1;`
*   `k[9]++;`
*   `n[12+i] = 0;`
*   Accessing an array out of bounds will not be identified by the compiler. It may cause an error at run-time. One frequent result is that an entirely unrelated variable is altered.

## 1D Arrays : Call by Reference

```c
#include <stdio.h>
#include <math.h>
#include <assert.h>
#define MAX 5

// Pass array, AND number of elements
void set_array(int a[MAX], unsigned int len, int n);

int main(void)
{
    int x[MAX] = {2, 3, 3, 3, 3};
    set_array(x, 5, 3); assert(x[0] == 3);
    x[0] = 5; x[1] =5; x[2] =5; x[3] =5; x[4] =5;
    set_array(x,5,4); assert(x[2] ==4);
    set_array(x,1,0); assert(x[0] ==0);
    x[0] =1; x[1] =2; x[2] =3;
    set_array(x,3,2);
    assert(x[2] ==2); assert(x[3] ==4);
}

// Set all values of array (size len) to n
void set_array(int a[MAX], unsigned int len, int n)
{
    if(len ==0){
        return;
    }
    for(unsigned int i=0; i<len; i++){
        a[i] =n;
    }
}
```

Here, the array is passed by Reference - no copy of the array is made - the function processes the array that was created inside `main()`, despite it apparently having a 'different' name.
All arrays are passed like this in C - we'll see later when we look at pointers why this is the case.

## Structures

*   A structure type allows the programmer to aggregate components into a single, named variable. Other languages call these Records or Tuples.
*   Each component has individually named members.
*   ```c
    struct employee {
        long id;
        double salary;
        short age;
    };
    ```
*   `struct` is a keyword, `employee` is the structure tag name, and `id`, `salary` and `age` are members of the structure.

*   A statement of the form:
    `struct employee e1, e2;`
    actually creates storage for the variables.
*   A member is accessed using the member operator "."
*   `e1.salary = 35000.2;`
    `e2.age = 29;`
*   The member name must be unique within the same structure.
*   Arrays of structures are possible, i.e.:
    `struct employee team[400];`

## Arrays of Structures

```c
#include <stdio.h>
#include <stdbool.h>
#include <stdlib.h>
#include <assert.h>

#define SUITS 4
#define PERSUIT 13
#define DECK (SUITS*PERSUIT)
#define SHUFFLE 3

typedef enum {hearts, diamonds, spades, clubs} suit;

struct card {
    suit st;
    int pips;
};
typedef struct card card;

void shuffle_deck(card d[DECK]);
void init_deck(card d[DECK]);
void print_deck(card d[DECK], int n);
void test(void);

int main(void)
{
    card d[DECK];
    test();
    init_deck(d);
    print_deck(d,7);
    shuffle_deck(d);
    print_deck(d,7);
    return 0;
}

void init_deck(card d[DECK])
{
    for(int i=0; i<DECK; i++){
        // Number 1..13
        d[i].pips = (i%PERSUIT)+1;
        switch (i/PERSUIT) {
            case hearts: d[i].st = hearts; break;
            case diamonds: d[i].st = diamonds; break;
            case spades: d[i].st = spades; break;
            case clubs: d[i].st = clubs; break;
            // Force an abort?
            default : assert(false);
        }
    }
}

void shuffle_deck(card d[DECK])
{
    for(int i=0; i<SHUFFLE*DECK; i++){
        int n1 = rand()%DECK;
        int n2 = rand()%DECK;
        card c = d[n1]; d[n1] = d[n2]; d[n2] = c;
    }
}
```

## Arrays of Structures

```c
void print_deck(card d[DECK], int n)
{
    for(int i=0; i<n; i++){
        switch(d[i].pips){
            case 11:
                printf("Jack");
                break;
            case 12:
                printf("Queen");
                break;
            case 13:
                printf("King");
                break;
            default:
                printf("%2i", d[i].pips);
        }
        switch(d[i].st){
            case hearts:
                printf(" of Hearts\n");
                break;
            case diamonds:
                printf(" of Diamonds\n");
                break;
            case spades:
                printf(" of Spades\n");
                break;
            default:
                printf(" of Clubs\n");
        }
    }
    printf("\n");
}
```

Execution:
1 of Hearts
2 of Hearts
3 of Hearts
4 of Hearts
5 of Hearts
6 of Hearts
7 of Hearts

4 of Spades
Jack of Spades
7 of Clubs
9 of Spades
10 of Spades
7 of Hearts
2 of Spades

*   The `print_deck()` function is clearly messy! We can simplify this a little when we understand strings.

## Testing

```c
void test(void)
{
    int n = 0;
    card d[DECK];
    int deck(d); // This line seems to be a syntax error in the original text.
    // Direct assignment
    card c = {hearts, 10};
    // Is element initialised correctly
    assert(d[9].pips == c.pips);
    assert(d[9].st == c.st);
    for(int i=0; i<1000; i++){
        shuffle_deck(d);
        // Happens 1 time in 52?
        if((d[0].st == c.st) && (d[0].pips == c.pips)){
            n++;
        }
    }
    // Is this a reasonable test?
    assert(n > 10 && n < 30);
}
```

*   Note the direct ability to copy a structure.
*   You can't compare them using `==` though.
*   Tricky to think of a good test for `shuffle_deck`.
*   You could also typedef away the array, e.g.:
    `typedef card deck[DECK];`
    `void shuffle_deck(deck d);`
    But this hides the fact it's an array (which seems odd?)
