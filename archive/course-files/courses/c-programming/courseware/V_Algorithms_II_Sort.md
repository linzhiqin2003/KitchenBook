Algorithms: Sorting
#define NUMS 6
void bubble_sort(int b[], int s);
int main(void)
{
    int a[] = {3, 4, 1, 2, 9, 0};
    bubble_sort(a, NUMS);
    for(int i=0; i<NUMS; i++){
        printf("%d ", a[i]);
    }
    printf("\n");
    return 0;
}
void bubble_sort(int b[], int s)
{
    bool changes;
    do{
        changes = false;
        for(int i=0; i<s-1; i++){
            if(b[i] > b[i+1]){
                SWAP(b[i], b[i+1]);
                changes = true;
            }
        }
    } while(changes);
}
Execution:
0 1 2 3 4 9
● Bubblesort has complexity O(n²), therefore very inefficient.
● If an algorithm uses comparison keys to decide the correct order then the theoretical lower bound on complexity is O(n log n). From wiki:
[Chart with curve labels: n²/2^n, n log n, n]

Algorithms : Merge Sort  
- Transposition (Bubblesort)  
- Insertion Sort (Lab Work)  
- Priority Queue (Selection sort, Heap sort)  
- Divide & Conquer (Merge & Quick sorts)  
- Address Calculation (Proxmap)  
Merge sort is divide-and-conquer in that you divide the array into two halves, mergesort each half and then merge the two halves into order.  
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
void mergesort(int *src, int *spare, int l, int r);
void merge(int *src, int *spare, int l, int m, int r);
#define NUM 5000
int main(void)
{
    int a[NUM];
    int spare[NUM];
    for(int i = 0; i < NUM; i++){
        a[i] = rand()%100;
    }
    mergesort(a, spare, 0, NUM-1);
    for(int i = 0; i < NUM; i++){
        printf("%d => %d\n", i, a[i]);
    }
    return 0;
}
```

Merge Sort II
void mergesort(int *src, int *spare, int l, int r)
{
    int m = (l+r)/2;
    if(l != r){
        mergesort(src, spare, l, m);
        mergesort(src, spare, m+1, r);
        merge(src, spare, l, m, r);
    }
}
void merge(int *src, int *spare, int l, int m, int r)
{
    int s1 = l;
    int s2 = m+1;
    int d = l;
    do{
        if(src[s1] < src[s2]){
            spare[d++] = src[s1++];
        }
        else{
            spare[d++] = src[s2++];
        }
    }while((s1 <= m) && (s2 <= r));
    if(s1 > m){
        memcpy(&spare[d], &src[s2], sizeof(spare[0])*(r - s2 +1));
    }
    else{
        memcpy(&spare[d], &src[s1], sizeof(spare[0])*(m - s1 +1));
    }
    memcpy(&src[l], &spare[l], (r - l +1)*sizeof(spare[0]));
}
● Quicksort is also divide-and-conquer.
● Choose some value in the array as the pivot key.
● This key is used to divide the array into two partitions. The left partition contains keys ≤ pivot key, the right partition contains keys > pivot.
● Once again, the sort is then applied recursively.

Algorithms : Quicksort
1 #include <stdio.h>
2 #include <stdlib.h>
3 #include <math.h>
4 
5 int partition(int *a, int l, int r);
6 void quicksort(int *a, int l, int r);
7 
8 #define NUM 100000
9 
10 int main(void)
11 {
12     int a[NUM];
13 
14     for(int i=0; i<NUM; i++){
15         a[i] = rand()%100;
16     }
17     quicksort(a, 0, NUM-1);
18 
19     return 0;
20 }
21 
22 void quicksort(int *a, int l, int r)
23 {
24     int pivpoint = partition(a, l, r);
25     if(l < pivpoint){
26         quicksort(a, l, pivpoint-1);
27     }
28     if(r > pivpoint){
29         quicksort(a, pivpoint+1, r);
30     }
31 }
int partition(int *a, int l, int r)
{
    int piv = a[l];
    while(l<r){
        /* Right -> Left Scan */
        while(piv < a[r] && l<r) r--;
        if(r!=l){
            a[l] = a[r];
            l++;
        }
        /* Left -> Right Scan */
        while(piv > a[l] && l<r) l++;
        if(r!=l){
            a[r] = a[l];
            r--;
        }
    }
    a[r] = piv;
    return r;
}

qsort()  
- Theoretically both methods have a complexity O(n log n)  
- Quicksort is preferred because it requires less memory and is generally faster.  
- Quicksort can go badly wrong if the pivot key chosen is either the maximum or minimum value in the array.  
- Quicksort is so loved by programmers that a library version of it exists in ANSI C.  
- If you need an off-the-shelf sort, this is often a good option.  
#include <stdio.h>  
#include <stdlib.h>  
int intcompare(const void *a, const void *b);  
int main(void)  
{  
    int a[10];  
    for(int i=0; i<10; i++){  
        a[i] = 9 - i;  
    }  
    qsort(a, 10, sizeof(int), intcompare);  
    for (int i=0; i<10; i++){  
        printf("%d ", a[i]);  
    }  
    printf("\n");  
    return 0;  
}  
int intcompare(const void *a, const void *b)  
{  
    const int *ia = (const int *)a;  
    const int *ib = (const int *)b;  
    return *ia - *ib;  
}

Algorithms : The Radix Sort
- The radix sort is also know as the bin sort, a name derived from its origin as a technique used on (now obsolete) card sorters.
- For integer data, repeated passes of radix sort focus on the right digit (the units), then the second digit (the tens) and so on.
- Strings could be sorted in a similar manner.
459 254 472 534 649 239 432 654 477
0
1
2 472 432
3
4 254 534 654
5
6
7 477
8
9 459 649 239
Read out the new list:
472 432 254 534 654 477 459 649 239

Radix Sort II
472 432 254 534 654 477 459 649 239
0
1
2
3 432 534 239
4 649
5 254 654 459
6
7 472 477
8
9
432 534 239 649 254 654 459 472 477
432 534 239 649 254 654 459 472 477
0
1
2 239 254
3
4 432 459 472 477
5 534
6 649 654
7
8
9
239 254 432 459 472 477 534 649 654

Radix Sort Discussion and gprof
This has a theoretical complexity of O(n).
It is difficult to write an all-purpose radix sort - you need a different one for doubles, integers, strings etc.
O(n) simply means that the number of operations can be bounded by k.n, for some constant k.
With the radix sort, k is often very large.
For many lists this may be less efficient than more traditional O(nlog n) algorithms.
Sometimes you'll want to profile your code.
Compile with the -pg flag.
Executing your code produces a gmon.out file.
Now: gprof ./executable gmon.out shows the function-call profile of your code.