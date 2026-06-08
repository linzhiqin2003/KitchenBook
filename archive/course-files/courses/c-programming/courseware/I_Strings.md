# Strings

## Strings

*   Strings are 1D arrays of characters.
*   Any character in a string may be accessed as an array element.
*   The important difference between strings and ordinary arrays is the end-of-string sentinel `\0` or null character.
*   The string "abc" has a length of 3, but its size is 4.
*   Note `'a'` and `"a"` are different. The first is a character constant, the second is a string with 2 elements `'a'` and `'\0'`.

Initialising Strings:
*   `char w[6] = "Hello";`
*   ```c
    char w[250];
    w[0] = 'a';
    w[1] = 'b';
    w[2] = 'c';
    w[3] = '\0';
    ```
*   `scanf("%s", w);`
    Removes leading spaces, reads a string (terminated by a space or EOF). Adds a null character to the end of the string.
*   `char w[250] = {'a', 'b', 'c', '\0'};`

## Unused Letters and string.h

```c
#include <stdio.h>
#include <stdbool.h>
#include <ctype.h>

#define ALPHASIZE 26

int main(void)
{
    char s[100] = "The Quick Brown Fox Leaps " \
                  "Over the Lazy Dog";
    bool used[ALPHASIZE] = {false};
    int i = 0;
    while(s[i]){
        char c = tolower(s[i]);
        if(islower(c)){
            used[c - 'a'] = true;
        }
        i++;
    }
    for(i=0; i<ALPHASIZE; i++){
        if(!used[i]){
            printf("%c has not been used.\n", i+'a');
        }
    }
    return 0;
}
```

In `#include <string.h>` :
`char *strcat(char dest[], const char src[]);`
`int strcmp(const char s1[], const char s2[]);`

*   `strcat()` appends a copy of string src, including the terminating null character, to the end of string dst.
*   `strcmp()` compares two strings byte-by-byte, according to the ordering of your machine's character set. The function returns an integer greater than, equal to, or less than 0, if the string pointed to by s1 is greater than, equal to, or less than the string pointed to by s2 respectively.

Execution :
j has not been used.
m has not been used.

## More string.h

In `#include <string.h>` :

`char *strcpy(char dst[], const char src[]);`
`unsigned strlen(const char s[]);`

*   `strcpy()` copies string src to dst including the terminating null character, stopping after the null character has been copied.
*   `strlen()` returns the number of bytes in s, not including the terminating null character.

One way to write the function `strlen()` :

```c
#include <stdio.h>
#include <assert.h>

unsigned nstrlen(const char s[]);

int main(void)
{
    assert(nstrlen("Neill")==5);
    assert(nstrlen("")==0);
    assert(nstrlen("\n")==1);
    assert(nstrlen("abcdef")==nstrlen("fedcba"));
    return 0;
}

unsigned nstrlen(const char s[])
{
   register unsigned n = 0;

   while(s[n] != '\0'){
       ++n;
   }
   return n;
}
```

## The snprintf() Function

In `#include <string.h>` : This is very similar to the function `printf()`, except that the output is stored in a string rather than written to the output. It is defined as:
`int snprintf(string, str-size, control-arg, other args);

For example:
```c
int i = 7;
float f = 17.041;
char str[100];
snprintf(str, 100, "%i %f", i, f);
printf("%s\n", str);
```

Outputs: 7 17.041000

This is useful if you need to create a string for passing to another function for further processing.

```c
#define SMALLSTR 20
void print_card(char s[BIGSTR], card c)
{
    char pipstr[SMALLSTR];
    char suitstr[SMALLSTR];
    switch(c.pips){
        case 11:
            strcpy(pipstr, "Jack");
            break;
        case 12:
            strcpy(pipstr, "Queen");
            break;
        case 13:
            strcpy(pipstr, "King");
            break;
        default:
            snprintf(pipstr, SMALLSTR, "%2i", c.pips);
    }
    switch(c.suit){
        case hearts :
            strcpy(suitstr, "Hearts");
            break;
        case diamonds :
            strcpy(suitstr, "Diamonds");
            break;
        case spades :
            strcpy(suitstr, "Spades");
            break;
        default:
            strcpy(suitstr, "Clubs");
    }
    snprintf(s, BIGSTR, "%s of %s", pipstr, suitstr);
}
```

## snprintf() and sscanf()

```c
#define FIRSTCARD "1 of Hearts"
void test(void)
{
    int n = 0;
    char str[BIGSTR];
    card d[DECK];
    init_deck(d);
    // Direct assignment
    print_card(str, d[0]);
    // 1st element initialised correctly
    assert(strcmp(str, FIRSTCARD)==0);
    for(int i=0; i<1000; i++){
        shuffle_deck(d);
        print_card(str, d[0]);
        // Happens 1 time in 52?
        if(strcmp(str, FIRSTCARD)==0){
            n++;
        }
    }
    // Is this a reasonable test?
    assert((n >10) && (n <30));
}
```

```c
// Simple demo of sscanf (and fgets in passing)
#include <stdio.h>
#include <assert.h>

#define BIGSTR 1000
#define SMLSTR 100
#define DAYSINYEAR 365.2425

#include <stdio.h>

int main(void)
{
    printf("Please type your first name and your age\n");
    char bigstr[BIGSTR];
    fgets(bigstr, BIGSTR, stdin);
    char name[SMLSTR];
    int age;
    // Note scanf() before name: passed by reference already
    assert(sscanf(bigstr, "%s %d\n", name, &age)==2);
    printf("%s, you've lived approximately %.0f days\n",
           name, ((double)(age)+0.5)*DAYSINYEAR);
    return 0;
}
```

Execution:
Please type your first name and your age
Joe 25
Joe, you've lived approximately 9314 days
