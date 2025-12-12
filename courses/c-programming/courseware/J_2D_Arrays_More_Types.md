# 2D Arrays & More Types

## Initializing 2D Arrays

A 2D array is declared as follows:
```c
#define ROWS 3
#define COLS 5
int a[ROWS][COLS];
```

2D array initialisation :
`int b[2][3] = {1, 2, 3, 4, 5, 6};`
`int b[2][3] = {{1, 2, 3}, {4, 5, 6}};`
`int b[][3] = {{1, 2, 3}, {4, 5, 6}};`

Although 2D arrays are stored in a contiguous block of memory, we may think of them as a 2D rectangle of data.
`int c[3][5] = {{1,2,3,4,5}, {6,7,8,9,10}, {11,12,13,14,15}};`

`c[2][1]` → 12
`c[1][2]` → 8

Table representation of array c:
1  2  3  4  5
6  7  8  9 10
11 12 13 14 15

## 2D Distance

```c
#include <stdio.h>
#include <math.h>

#define M 7
#define N 9

void fillarray(int a[M][N]);

int main(void)
{
    int a[M][N];

    fillarray(a);
    // Print Array
    for (int j = 0; j < M; j++){
        for(int i = 0; i < N; i++){
            printf("%i", a[j][i]);
        }
        printf("\n");
    }
    printf("\n");
    return 0;
}

void fillarray(int a[M][N])
{
    for (int j = 0; j < M; j++){
        double y = ((double)j - ((double)(M-1)/2.0));
        for(int i = 0; i < N; ++i){ // Column-first
            double x = ((double)i - ((double)(N-1)/2.0));
            a[j][i] = round(sqrt(x*x + y*y));
        }
    }
}
```

Execution :

544333445
443222344
432111234
432101234
432111234
443222344
544333445

## Cards (again!)

```c
#define SMALLSTR 20
void print_card(char s[BIGSTR], card c)
{
    // Note the +1 below : zero pips not used, but makes easier coding?
    char pipnames[PERSUIT +1][SMALLSTR] = {"Zero", "One", "Two", "Three",
                                           "Four", "Five", "Six", "Seven",
                                           "Eight", "Nine", "Ten", "Jack",
                                           "Queen", "King"};
    char suitnames[SUITS][SMALLSTR] = {"Hearts", "Diamonds", "Spades", "Clubs"};
    sprintf(s, BIGSTR, "%s of %s", pipnames[c.pips], suitnames[c.st]);
}
```

*   The 2D arrays of characters here have one string per row.
*   They are of a fixed-width, sometime called ragged-right or jagged-right arrays.

## Storage Classes

*   `auto`
    `auto int a, b, c;`
    `auto float f;`
    Because this is the default, it is seldom used.

*   `extern`
    Tells the compiler to look for the variable elsewhere, possibly another file.

*   `register`
    Informs the compiler to place the variable in a high-speed memory register if possible, i.e. if there are enough such registers available & the hardware supports this.

```c
#include <stdio.h>
#include <stdlib.h>  // Corrected: Added missing include for rand()
void printstuff(void);

#define MAXLOOP 20

int main(void)
{
    int r = rand() % MAXLOOP;
    for(int i=0; i<r; i++){
        printstuff();
    }
    return 0;
}

void printstuff(void)
{
    static int cnt = 0;
    printf("You've been here %i times\n", ++cnt);
}
```

Execution:

You've been here 1 times
You've been here 2 times
You've been here 3 times

```