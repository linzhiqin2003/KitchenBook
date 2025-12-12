Collections  
● One of the simplest ADTs is the Collection.  
● This is just a simple place to search for/add/delete data elements.  
● Some collections allow duplicate elements and others do not (e.g. Sets).  
● Some are ordered (for faster searching) and others unordered.  
● Our Collection will be unsorted and will allow duplicates.  
#include "../General/general.h"  
typedef int colltype;  
typedef struct coll coll;  
#include <stdio.h>  
#include <stdlib.h>  
#include <assert.h>  
// Create an empty coll  
coll* coll_init(void);  
// Add element onto top  
void coll_add(coll* c, colltype i);  
// Take element out  
bool coll_remove(coll* c, colltype d);  
// Does this exist?  
bool coll_is_in(coll* c, colltype i);  
// Return size of coll  
int coll_size(coll* c);  
// Clears all space used;  
bool coll_free(coll* c);

Collection ADT  
• Note that the interface gives you no hints as to the actual underlying implementation of the ADT.  
• A user of the ADT doesn’t really need to know how it’s implemented - ideally.  
• The ADT developer could have several different implementations.  
• Here we’ll see Collection implemented using:  
  • A fixed-size array  
  • A dynamic array  
  • A linked-list  
Fixed/specific.h:  
1 #pragma once  
2  
3 #define COLTYPE "Fixed"  
4  
5 #define FIXEDSIZE 5000  
6 struct coll {  
7     // Underlying array  
8     coltype a[FIXEDSIZE];  
9     int size;  
10 };

Collection ADT using a Fixed-size Array
Fixed/fixed.c:
1 #include "../coll.h"
2 #include "specific.h"
3 
4 coll* coll_init(void)
5 {
6     coll* c = (coll*) ncalloc(1, sizeof(coll));
7     c->size = 0;
8     return c;
9 }
10 
11 int coll_size(coll* c)
12 {
13     if(c==NULL){
14         return 0;
15     }
16     return c->size;
17 }
18 
19 bool coll_isin(coll* c, colltype d)
20 {
21     for(int i=0; i<coll_size(c); i++){
22         if(c->a[i] == d){
23             return true;
24         }
25     }
26     return false;
27 }
void coll_add(coll* c, colltype d)
{
    if(c){
        if(c->size >= FIXEDSIZE){
            on_error("Collection overflow");
        }
        c->a[c->size] = d;
        c->size = c->size +1;
    }
}
bool coll_remove(coll* c, colltype d)
{
    for(int i=0; i<coll_size(c); i++){
        if(c->a[i] == d){
            // Shuffle end of array left one
            for(int j=i; j<coll_size(c); j++){
                c->a[j] = c->a[j+1];
            }
            c->size = c->size -1;
            return true;
        }
    }
    return false;
}
bool coll_free(coll* c)
{
    free(c);
    return true;
}

Collection ADT via an Array (Realloc)
Realloc/specific.h:
1 #pragma once
2 
3 #define COLLTYPE "Realloc"
4 
5 #define INITSIZE 16
6 #define SCALEFACTOR 2
7 struct coll {
8     // Underlying array
9     colltype* a;
10    int size;
11    int capacity;
12 };
Realloc/realloc.c:
1 #include "../coll.h"
2 #include "specific.h"
3 
4 coll* coll_init(void)
5 {
6     coll* c = (coll*) calloc(1, sizeof(coll));
7     c->a = (colltype*) calloc(INITSIZE, sizeof(colltype));
8     c->size = 0;
9     c->capacity = INITSIZE;
10    return c;
11 }
12 
13 void coll_add(coll* c, colltype d)
14 {
15    if(c){
16        if(c->size >= c->capacity){
17            c->a = (colltype*) realloc(c->a, 
18                sizeof(colltype)*c->capacity*SCALEFACTOR);
19            c->capacity = c->capacity * SCALEFACTOR;
20        }
21        c->a[c->size] = d;
22        c->size = c->size +1;
23    }
24 }

Collection ADT via a Linked List
Linked/specific.h:
1 #pragma once
2 
3 #define COLLTYPE "Linked"
4 
5 struct dataframe {
6   colltype i;
7   struct dataframe* next;
8 };
9 typedef struct dataframe dataframe;
10 
11 struct coll {
12   // Underlying array
13   dataframe* start;
14   int size;
15 };
Linked/linked.c:
#include "../coll.h"
#include "specific.h"
coll* coll_init(void)
{
  coll* c = (coll*) calloc(1, sizeof(coll));
  return c;
}
int coll_size(coll* c)
{
  if(c==NULL){
    return 0;
  }
  return c->size;
}
bool coll_isin(coll* c, colltype d)
{
  if(c == NULL || c->start==NULL){
    return false;
  }
  dataframe* f = c->start;
  do{
    if(f->i == d){
      return true;
    }
    f = f->next;
  } while(f != NULL);
  return false;
}

Collection ADT via a Linked List II
void coll_add(coll* c, colltype d)
{
    if(c){
        dataframe* f = ncalloc(1, sizeof(dataframe));
        f->i = d;
        f->next = c->start;
        c->start = f;
        c->size = c->size + 1;
    }
}
bool coll_free(coll* c)
{
    if(c){
        dataframe* tmp;
        dataframe* p = c->start;
        while(p!=NULL){
            tmp = p->next;
            free(p);
            p = tmp;
        }
        free(c);
    }
    return true;
}
bool coll_remove(coll* c, colltype d)
{
    dataframe* f1, *f2;
    if((c==NULL) || (c->start==NULL)){
        return false;
    }
    // if Front
    if(c->start->i == d){
        f1 = c->start->next;
        free(c->start);
        c->start = f1;
        c->size = c->size -1;
        return true;
    }
    f1 = c->start;
    f2 = c->start->next;
    do{
        if(f2->i == d){
            f1->next = f2->next;
            free(f2);
            c->size = c->size -1;
            return true;
        }
        f1 = f2;
        f2 = f1->next;
    }while(f2 != NULL);
    return false;
}

Collection Summary  
● Any code using the ADT can be compiled against any of the implementations, e.g. the test (testcoll.c) code.  
● The Collection interface (coll.h) is never changed.  
● There are pros and cons of each implementation:  
  ● Fixed Array: Simple to implement - can’t avoid the problems of it being a fixed-size. Deletion expensive.  
  ● Realloc Array: Implementation fairly simple. Deletion expensive. Every realloc() is very expensive. Need to tune SCALEFACTOR.  
  ● Linked: Slightly fiddly implementation - fast to delete an element.  
| Task                  | Fixed Array               | Realloc Array             | Linked List               |  
|-----------------------|---------------------------|---------------------------|---------------------------|  
| Insert new element    | O(1) at end if space      | O(1) at end but realloc() if needed | O(1) at front             |  
| Search for an element | O(n) (brute force)        | O(n) (brute force)        | O(n) (brute force)        |  
| Search + delete       | O(n) + O(n) move left     | O(n) + O(n) move left     | O(n) + O(1) delete 'free' |  
● If we had ordered our ADT (ie. the elements were sorted), then the searches could be via a binary / interpolation search, leading to O(log n) or O(log log n) search times.

ADTs Making Coding Simpler  
Linked List code from the previous Chapter :  
1 #include <stdio.h>  
2 #include <stdlib.h>  
3 #include "general.h"  
4  
5 typedef struct data{  
6     int i;  
7     struct data* next;  
8 } Data;  
9  
10 Data* allocateData(int i);  
11 void printList(Data* l);  
12  
13 int main(void)  
14 {  
15     int i;  
16     Data* start, *current;  
17     start = current = NULL;  
18     printf("Enter the first number: ");  
19     if(scanf("%d", &i) == 1){  
20         start = current = allocateData(i);  
21     }  
22     else{  
23         on_error("Couldn't read an int");  
24     }  
25  
26     printf("Enter more numbers: ");  
27     while(scanf("%d", &i) == 1){  
28         current->next = allocateData(i);  
29         current = current->next;  
30     }  
31     printList(start);  
32     return 0; // Should Free List  
33 }  
Becomes :  
1 #include "coll.h"  
2 #include "Fixed/specific.h"  
3  
4 int main(void)  
5 {  
6     printf("Please type some numbers: ");  
7     coll* c = coll_init();  
8     int i;  
9     while(scanf("%d", &i) == 1){  
10         coll_add(c, i);  
11     }  
12     // Do print etc.  
13     coll_free(c);  
14     return 0;  
15 }