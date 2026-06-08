# Prettifying (New Types and Aliasing)

## Enumerated Types

`enum day { sun, mon, tue, wed, thu, fri, sat };`

*   This creates a user-defined type `enum day`.
*   The enumerators are constants of type `int`.
*   By default the first (sun) has the value 0, the second has the value 1 and so on.

*   An example of their use:
    ```c
    enum day d1;
    ...
    d1 = fri;
    ```

*   The default numbering may be changed as well:
    `enum fruit{apple=7, pear, orange=3, lemon};

*   Use enumerated types as constants to aid readability - they are self-documenting.
*   Declare them in a header (.h) file.
*   Note that the type is `enum day`; the keyword `enum` is not enough.

## Typedefs

*   Sometimes it is useful to associate a particular name with a certain type, e.g.:
    `typedef int colour;`
*   Now the type `colour` is synonymous with the type `int`.
*   Makes code self-documenting.
*   Helps to control complexity when programmers are building complicated or lengthy user-defined types (See Structures later).

## Combining typedefs and enums

Often typedef's are used in conjunction with enumerated types:

```c
#include <stdio.h>
#include <assert.h>

enum day {mon,tue,wed,thu,fri,sat, sun};
typedef enum day day;

day find_next_day(day d);

int main(void)
{
    assert(find_next_day(mon)==tue);
    assert(find_next_day(sat)==sun);
    assert(find_next_day(sun)==mon);
    return 0;
}

day find_next_day(day d)
{
    day next_day;
    switch(d){
        case sun:
            next_day = mon;
            break;
        case mon:
            next_day = tue;
            break;
        case tue:
            next_day = wed;
            break;
        case wed:
            next_day = thu;
            break;
        case thu:
            next_day = fri;
            break;
        case fri:
            next_day = sat;
            break;
        case sat:
            next_day = sun;
            break;
        default:
            printf("I wasn't expecting that!\n");
    }
    return next_day;
}
```

## Style

```c
enum veg {beet, carrot, pea};
typedef enum veg veg;
veg v1, v2;
v1 = carrot;
```

*   We can combine the two operations into one:
    ```c
    typedef enum veg {beet,carrot,pea} veg;
    veg v1, v2;
    v1 = carrot;
    ```

*   Assigning:
    `v1 = 10;`
    is very poor programming style!

## Booleans

Before C99 you might have been tempted to define your own Boolean type:

```c
#include <stdio.h>
#include <assert.h>

typedef enum bool {false, true} bool;

int main(void)
{

    bool b = true;
    if (b){
        printf("It's true!\n");
    }
    else{
        printf("It's false!\n");
    }
    return 0;
}
```

Execution:
It's true!

However, we can just use `#include <stdbool.h>`

```c
#include <stdio.h>
#include <stdbool.h>
#include <assert.h>

int main(void)
{
    bool b = true;
    if (b){
        printf("It's true!\n");
    }
    else{
        printf("It's false!\n");
    }
    return 0;
}
```

Execution:
It's true!

## Fever

Rewrite/complete this code using typedefs and enums to create self-documenting code in any manner you wish.

```c
#include <stdio.h>
#include <assert.h>

// Argument 1 is temperature
// Argument 2 is scale (0=>Celsius, 1=>Farenheit)
int fvr(double t, int s);

int main(void)
{
    assert(fvr(37.5, 0) == 1);
    assert(fvr(36.5, 0) == 0);
    assert(fvr(96.5, 1) == 0);
    assert(fvr(99.5, 1) == 1);
    return 0;
}

int fvr(double t, int s)
{
}
```
