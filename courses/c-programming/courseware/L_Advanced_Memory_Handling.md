# Advanced Memory Handling

## String Constants

```c
// A FAILED attempt to
// convert all 'n' chars to 'N'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <ctype.h>

void nifty(char s[]);

int main(void)
{
  nifty("neill");
  return 0;
}

// In-Place : Swaps all 'n' -> 'N'
void nifty(char s[])
{
  for(int i=0; s[i]; i++){
    if(s[i] == 'n'){
      s[i] = 'N';
    }
  }
}
```

*   This looks (at first) like a sensible attempt to accept a string and change it in-place to capitalise all 'n' characters. It crashes though via a segmentation fault.
*   With the usual compile flags we get no more information.
*   But using:
    `gcc nifty1.c -g3 -fsanitize=undefined -fsanitize=address -o nifty1`
    we find that
    `s[i] = 'N';`
    is the culprit.
*   It turns out that in `main()` we have passed a constant string to the function. This is in a part of memory that we have read-only permission.

## Local Variables

```c
// A FAILED attempt to
// convert all 'n' chars to 'N'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#define LINE 500

char* nify(char s[]);

int main(void)
{
    char* s1 = nify("inconveniencing");
    char* s2 = nify("neill");
    assert(strcmp(s2, "Neill")==0);
    assert(strcmp(s1, "iNcoNveNieNciNg")==0);
    return 0;
}

// Local copy : Swaps all 'n' -> 'N'
char* nify(char s[])
{
    char t[LINE];
    strcpy(t, s);
    for(int i=0; t[i]; i++){
        if(t[i] == 'n'){
            t[i] = 'N';
        }
    }
    return t;
}
```

*   Now we try to create a copy of the string, and return a pointer to it.
*   With the usual compile flags we're told:
    `nify2.c: In function ‘nify’:`
    `nify2.c:33:11: warning: function returns address of local variable [-Wreturn-local-addr]`
       `33 |     return t;`
*   The string t is local to `nify()`.
*   What happens in this memory when outside the scope of this function is completely undefined.

## Static Variables

```c
// A FAILED attempt to
// convert all 'n' chars to 'N'
#include <stdio.h>
#include <stdlib.h> 
#include <string.h>
#include <assert.h>

#define LINE 500

char* nify(char s[]);

int main(void)
{
    char* s1 = nify("inconveniencing");
    char* s2 = nify("neill");
    assert(strcmp(s2, "Neill")==0);
    assert(strcmp(s1, "iNCoNVeNieNCiNg")==0);
    return 0;
}

// Local copy : Swaps all 'n' -> 'N'
char* nify(char s[])
{
    static char t[LINE];
    strcpy(t, s);
    for(int i=0; t[i]; i++){
        if(t[i] == 'n'){
            t[i] = 'N';
        }
    }
    return t;
}
```

We could just make the local string a static and return it's address couldn't we?
This only works if we're very careful with the order in which we use the strings.
This code fails because, in `main()`, by the time we `strcmp(s1, "iNCoNVeNieNCiNg")` the contents of s1 have been overwritten by "Neill".
The pointers s1 and s2 are the same.

## Using malloc()

*   We must use `malloc()` instead.
*   `void* malloc(int n);`
    allocates n bytes and returns a pointer to the allocated memory. The memory is not initialized.
*   Now, when our function is called, a dedicated chunk of memory is allocated.
*   This memory is always in scope until `free()` is used on it.
*   We must free the memory somewhere though, otherwise memory leaks develop.
*   We will see `calloc()` (and perhaps `realloc()`) later.

```c
#include <stdlib.h> 
#include <string.h>
#include <assert.h>

char* niffy(char s[]);

int main(void)
{
    char* s1 = niffy("inconveniencing");
    char* s2 = niffy("neill");
    assert(strcmp(s2, "Neill")==0);
    assert(strcmp(s1, "iNcoNveNieNciNg")==0);
    free(s1);
    free(s2);
    return 0;
}

// malloc : Swaps all 'n' -> 'N'
char* niffy(char s[])
{
    int l = strlen(s);
    char* t = (char*)malloc(l+1);
    if(t==NULL){
        exit(EXIT_FAILURE);
    }
    strcpy(t, s);
    for(int i=0; t[i]; i++){
        if(t[i] == 'n'){
            t[i] = 'N';
        }
    }
    return t;
}
```

## Variable Length Arrays (Warning)

```c
// This code is not allowed by the -Wvla flag
#include <stdio.h> 
#include <string.h>
#include <stdlib.h> 
#include <assert.h>

#define WORD 500

int main(void)
{
    printf("Please type a string :\n");
    char s[WORD];
    assert(scanf("%s", s)==1);
    int n = strlen(s) + 1;
    char t[n];
    // Deep copy: character by character
    strcpy(t, s);
    printf("%s %s\n", s, t);
    return 0;
}
```

Here we duplicate a string into t.
This is known as a variable length array.
However, we will always use the `-Wvla` with the compiler to prevent them.
There are a number of reasons for this:
    Some C++ compilers don't accept it.
    The memory comes off the stack not the heap, and you have no idea if the allocation has worked (it'll just crash if not)
    https://nullprogram.com/blog/2019/10/27/
None of these is a problem if we use `malloc()`.

## Memory Leaks

```c
// This leaks - but it's not obvious
#include <stdio.h>
#include <stdlib.h> 
#include <string.h>
#include <assert.h>

#define WORD 500

int main(void)
{
    printf("Please type a string :\n");
    char s[WORD];
    assert(scanf("%s", s)==1);
    int n = strlen(s);
    /* malloc() returns a pointer to memory that you have access to. Note forcing cast. */
    char* t = (char*) malloc(n+1);
    /* t = NULL returns space, returns NULL if no space */
    assert(t != NULL);
    /* Deep copy: character by character */
    strcpy(t, s);
    printf("%s %s\n", s, t);
    return 0;
}
```

*   This code appears to work correctly.
*   However, it actually leaks. The memory allocated was never `free()`'d.
*   This is best found by running the program valgrind.

String String
==474==
==474== HEAP SUMMARY:
==474==     in use at exit:7 bytes in 1 blocks
==474==   total heap usage:2 allocs,1 frees,1,031 bytes allocated
==474==
==474== LEAK SUMMARY:
==474==    definitely lost:7 bytes in 1 blocks
==474==


## free()

```c
#include <stdio.h> 
#include <stdlib.h> 
#include <string.h>
#include <assert.h>

#define WORD 500

int main(void)
{
    char s[WORD] = "String";
    int n = strlen(s);
    /* malloc() returns a pointer to memory that
       you have access to. Note forcing cast. */
    char *t = (char *) malloc(n+1);
    /* If no space, returns NULL */
    assert(t != NULL);
    /* Deep copy: character by character */
    strcpy(t, s);
    printf("%s %s\n", s, t);
    /* All malloc'd memory must be freed
       to prevent memory leaks */
    free(t);
    return 0;
}
```

This code is now correct.

String String
==475==
==475== HEAP SUMMARY:
==475==     in use at exit: 0 bytes in 0 blocks
==475==   total heap usage: 2 allocs, 2 frees, 1,031 bytes allocated
==475==
==475== All heap blocks were freed -- no leaks are possible

## Structures with Self-Referential Pointers

```c
// Store a list of numbers
#include <stdio.h> 
#include <stdlib.h> 
#include <assert.h> 

struct data {
    int num;
    struct data* next;
};
typedef struct data data;

int main(void)
{
    // a b c
    // 11 -> 17 -> 5 . |
    // data c = {5, NULL};
    data c = {5, NULL};
    data b = {17, &c};
    data a = {11, &b};

    // print first number
    printf("%d\n", a.num);
    data* p = &a;
    // Can also get to it via p
    printf("%d\n", p->num);
    // Pointer chasing: The Key concept
    p = p->next;
    // We're accessing b, without using it's name
    printf("%d\n", p->num);
    p = p->next;
    // And c
    printf("%d\n", p->num);
    return 0;
}
```

*   The structure contains a pointer to a something of it's own type (even before we've fully defined the structure itself).
*   Here, if p points to a, then `p->next->next` points to c.

## Linked Lists

```c
// Store a list of numbers (length unknown)
#include <stdio.h> 
#include <stdlib.h> 
#include <assert.h> 

#define MAXNUM 20
#define ENDNUM 10

struct data {
    int num;
    struct data* next;
};
typedef struct data data;

void addtolist(data* tail);
void printlist(data* st);

int main(void)
{
    data *p, *start;
    start = p = calloc(1, sizeof(data));
    assert(p);
    p->num = rand()%MAXNUM;
    // Add other numbers to the list
    do {
        addtolist(p);
        p = p->next;
    } while(p->num != ENDNUM);
    printlist(start);
    // Need to free up list - not shown here ...
    return 0;
}

// Create some new space and store number in it
void addtolist(data* tail)
{
    tail->next = calloc(1, sizeof(data));
    assert(tail->next);
    tail = tail->next;
    tail->num = rand()%MAXNUM;
}

void printlist(data* st)
{
    while(st != NULL){
        printf("%d ", st->num);
        st = st->next;
    }
    printf("\n");
}
```

Execution :
3 6 17 15 13 15 6 12 9 1 2 7 10

*   `calloc()` is similar to `malloc()`, but clears the memory is reserves for you. It's passed the number of array cells you wish to create, and the size of each of them.

```
