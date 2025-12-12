Sequential Search  
- The need to search an array for a particular value is a common problem.  
- This is used to delete names from a mailing list, or upgrading the salary of an employee etc.  
- The simplest method for searching is called the sequential search.  
- Simply move through the array from beginning to end, stopping when you have found the value you require.  
```c
#include <stdio.h>
#include <string.h>
#include <assert.h>
#define NOTFOUND -1
#define NUMPEOPLE 6
typedef struct person{
    char* name; int age;
} person;
int findAge(const char* name, const person* p, int n);
int main(void)
{
    person ppl[NUMPEOPLE] = { {"Ackerby", 21}, {"Bloggs", 25},
                              {"Chumley", 26}, {"Dalton", 25},
                              {"Eggson", 22}, {"Fulton", 41} };
    assert(findAge("Eggson", ppl, NUMPEOPLE)==22);
    assert(findAge("Campbell", ppl, NUMPEOPLE)==NOTFOUND);
    return 0;
}
int findAge(const char* name, const person* p, int n)
{
    for(int j=0; j<n; j++){
        if(strcmp(name, p[j].name) == 0){
            return p[j].age;
        }
    }
    return NOTFOUND;
}
```

Sequential Search
● Sometimes our list of people may not be random.  
● If, for instance, it is sorted, we can use strcmp() in a slightly cleverer manner.  
● We can stop searching once the search key is alphabetically greater than the item at the current position in the list.  
● This halves, on average, the number of comparisons required.  
#include <stdio.h>  
#include <string.h>  
#include <assert.h>  
#define NOTFOUND -1  
#define NUMPOPLE 6  
typedef struct person{  
    char* name; int age;  
} person;  
int findAge(const char* name, const person* p, int n);  
int main(void)  
{  
    person ppl[NUMPOPLE] = { {"Ackerby", 21}, {"Bloggs", 25},  
                             {"Chumley", 26}, {"Dalton", 25},  
                             {"Eggson", 22}, {"Fulton", 41} };  
    assert(findAge("Eggson", ppl, NUMPOPLE)==22);  
    assert(findAge("Campbell", ppl, NUMPOPLE)==NOTFOUND);  
    return 0;  
}  
int findAge(const char* name, const person* p, int n)  
{  
    for(int j=0; j<n; j++){  
        int m = strcmp(name, p[j].name);  
        if(m == 0) // Brace!  
            return p[j].age;  
        if(m < 0)  
            return NOTFOUND;  
    }  
    return NOTFOUND;  
}

Binary Search for 101  
- Searching small lists doesn’t require much computation time.  
- However, as lists get longer (e.g. phone directories), sequential searching becomes extremely inefficient.  
- A binary search consists of examining the middle element of the array to see if it has the desired value. If not, then half the array may be discarded for the next search.  
4 7 19 25 36 37 50 100 101 205 220 270 301 321  
```c
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <time.h>
#define NMERS 1000000
int bin_it(int k, const int* a, int l, int r);
int main(void)
{
    int a[NMERS];
    srand(time(NULL));
    // Put even numbers into array
    for (int i=0; i<NMERS; i++){
        a[i] = 2*i;
    }
    // Do many searches for a random number
    for (int i=0; i<10*NMERS; i++){
        int n = rand()%NMERS;
        if ((n%2) == 0) {
            assert(bin_it(n, a, 0, NMERS-1) == n/2);
        } else { // No odd numbers in this list
            assert(bin_it(n, a, 0, NMERS-1) < 0);
        }
    }
    return 0;
}
```

Iterative v. Recursion Binary Search
int bin_it(int k, const int* a, int l, int r)
{
    while(l <= r){
        int m = (l+r)/2;
        if(k == a[m]){
            return m;
        } else {
            if (k > a[m]){
                l = m + 1;
            } else {
                r = m - 1;
            }
        }
    }
    return -1;
}
int bin_rec(int k, const int* a, int l, int r)
{
    if(l > r) return -1;
    int m = (l+r)/2;
    if(k == a[m]){
        return m;
    } else {
        if (k > a[m]){
            return bin_rec(k, a, m+1, r);
        } else {
            return bin_rec(k, a, l, m-1);
        }
    }
}

Interpolation Search  
● When we look for a word in a dictionary, we don't start in the middle. We make an educated guess as to where to start based on the 1st letter of the word being searched for.  
● This idea led to the interpolation search.  
● In binary searching, we simply used the middle of an ordered list as a best guess as to where to start the search.  
● Now we use an interpolation involving the key, the start of the list and the end.  
i = (k − l[0])/(l[n−1]−l[0]) * n  
● when searching for '15' :  
0 4 5 9 10 12 15 20  
          ↑  
int interp(int k, const int* a, int l, int r)  
{  
    int m;  
    double md;  
    while (l <= r) {  
        md = ( (double)(k - a[l]) ) /  
             ( (double)(a[r] - a[l]) ) *  
             ( (double)(r - l) )  
             + (double)(l);  
        m = 0.5 + md;  
        if (m > r || m < l) {  
            return -1;  
        }  
        if (k == a[m]) {  
            return m;  
        } else if (k < a[m]) {  
            l = m + 1;  
        } else {  
            r = m - 1;  
        }  
    }  
    return -1;  
}

Algorithmic Complexity
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#define CSEC (double)(CLOCKS_PER_SEC)
#define BIGLOOP 100000000
int main(void)
{
    clock_t c1 = clock();
    for(int i=0; i<BIGLOOP; i++){
        int j = i * 2;
    }
    clock_t c2 = clock();
    printf("%f\n", (double)(c2 - c1)/CSEC);
    return 0;
}
- This code on an old Dell laptop took:
  - 3.12 seconds using a non-optimizing compiler -O0
  - 0.00 seconds using an aggressive optimization -O3
- But "wall-clock" time is generally not the thing that excites Computer Scientists.
- Searching and sorting algorithms have a complexity associated with them, called big-O.
- This complexity indicates how, for n numbers, performance deteriorates when n changes.
- Sequential Search: O(n)
- Binary Search: O(log n)
- Interpolation Search: O(log log n)
- We'll discuss the dream of a O(1) search later in "Hashing".

### Left Code Section  
```c
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <time.h>
int bin_it(int k, const int *a, int l, int r);
int bin_rec(int k, const int *a, int l, int r);
int interp(int k, const int *a, int l, int r);
int* parse_args(int argc, char* argv[], int* n, int* srch);
int main(int argc, char* argv[])
{
    int i, n, srch;
    int* a;
    int (*p[3])(int k, const int*a, int l, int r) = 
        {bin_it, bin_rec, interp};
    a = parse_args(argc, argv, &n, &srch);
    srand(time(NULL));
    for(i=0; i<n; i++){
        a[i] = 2*i+1;
    }
    for(i=0; i<5000000; i++){
        assert((*p[srch])(a[rand()%n], a, 0, n-1) >=0);
    }
    free(a);
    return 0;
}
```  
### Right Execution Section  
```
Execution:
Binary Search : Iterative
n = 100000 = 0.39
n = 800000 = 0.57
n = 6400000 = 1.00
n = 51200000 = 2.46
Binary Search : Recursive
n = 100000 = 0.40
n = 800000 = 0.56
n = 6400000 = 0.97
n =51200000 =2.42
Interpolation
n =100000 =0.05
n=800000=0.05
n=6400000=0.10
n=51200000=0.13
```  
### Footer