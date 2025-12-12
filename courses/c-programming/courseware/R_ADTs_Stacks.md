ADTs  
At the highest level of abstraction, ADTs that we can represent using both dynamic structures (pointers) and also fixed structures (arrays) include:  
● Collections (Lists)  
● Stacks  
● Queues  
● Sets  
● Graphs  
● Trees  
Binary Trees:  
Unidirectional Graph:

Stacks
The push-down stack:
Top
LIFO (Last in, First out):
Push "15"
Pop
15
13
117
12
15
13
117
12
13
117
12
• Operations include push and pop.
• In the C run-time system, function calls are implemented using stacks.
• Most recursive algorithms can be re-written using stacks instead.
• But, once again, we are faced with the question: How best to implement such a data type?

ADT:Stacks Arrays (Realloc) I
stack.h:
1 #pragma once
2 
3 #include "../General/general.h"
4 
5 typedef int stacktype;
6 
7 typedef struct stack stack;
8 
9 #include <stdio.h>
10 #include <stdlib.h>
11 #include <assert.h>
12 #include <string.h>
13 
14 /* Create an empty stack */
15 stack* stack_init(void);
16 /* Add element to top */
17 void stack_push(stack* s, stacktype i);
18 /* Take element from top */
19 bool stack_pop(stack* s, stacktype* d);
20 /* Clears all space used */
21 bool stack_free(stack* s);
22 
23 /* Optional? */
24 
25 /* Copy top element into d (but don't pop it) */
26 bool stack_peek(stack* s, stacktype* d);
27 /* Make a string version - keep .dot in mind */
28 void stack_tostring(stack*, char* str);
Realloc/specific.h:
1 #pragma once
2 
3 #define FORMATSTR "%i"
4 #define ELEMSIZE 20
5 
6 #define STACKTYPE "Realloc"
7 
8 #define FIXEDSIZE 16
9 #define SCALEFACTOR 2
10 
11 struct stack {
12     /* Underlying array */
13     stacktype* a;
14     int size;
15     int capacity;
16 };

ADT:Stacks Arrays (Realloc) II  
Realloc/realloc.c  
#include "../stack.h"  
#include "specific.h"  
#define DOTFILE 5000  
stack* stack_init(void)  
{  
    stack* s = (stack*) ncalloc(1, sizeof(stack));  
    /* Some implementations would allow you to pass  
       a hint about the initial size of the stack */  
    s->a = (stacktype*) ncalloc(FIXEDSIZE, sizeof(stacktype));  
    s->size = 0;  
    s->capacity = FIXEDSIZE;  
    return s;  
}  
void stack_push(stack* s, stacktype d)  
{  
    if(s==NULL){  
        return;  
    }  
    if(s->size >= s->capacity){  
        s->a = (stacktype*) nremalloc(s->a, sizeof(stacktype)*s->capacity*SCALEFACTOR);  
        s->capacity = s->capacity*SCALEFACTOR;  
    }  
    s->a[s->size] = d;  
    s->size = s->size +1;  
}  
bool stack_pop(stack* s, stacktype* d)  
{  
    if((s==NULL) || (s->size <1)){  
        return false;  
    }  
    s->size = s->size -1;  
    *d = s->a[s->size];  
    return true;  
}  
bool stack_peek(stack* s, stacktype* d)  
{  
    if((s==NULL) || (s->size <=0)){  
        /* Stack is Empty */  
        return false;  
    }  
    *d = s->a[s->size -1];  
    return true;  
}

ADT:Stacks Arrays (Realloc) III  
Realloc/realloc.c  
1 void stack_tostring(stack* s, char* str)  
2 {  
3     char tmp[ELEMSIZE];  
4     str[0] = '\0';  
5     if((s==NULL) || (s->size <1)){  
6         return;  
7     }  
8     for(int i=s->size-1; i>=0; i--){  
9         sprintf(tmp, FORMATSTR, s->a[i]);  
10        strcat(str, tmp);  
11        strcat(str, "|");  
12    }  
13    str[strlen(str)-1] = '\0';  
14 }  
15  
16 bool stack_free(stack* s)  
17 {  
18     if(s==NULL){  
19         return true;  
20     }  
21     free(s->a);  
22     free(s);  
23     return true;  
24 }  
- We need a thorough testing program teststack.c  
- See also revstr.c : a version of the string reverse code (for which we already seen an iterative (in-place) and a recursive solution).

### ADT:Stacks Linked I  
---
#### Linked/specific.h  
```c
#pragma once
#define FORMATSTR "%i"
#define ELEMSIZE 20
#define STACKTYPE "Linked"
struct dataframe {
  stacktype i;
  struct dataframe* next;
};
typedef struct dataframe dataframe;
struct stack {
  /* Underlying array */
  dataframe* start;
  int size;
};
```  
---
#### Linked/linked.c  
```c
#include "../stack.h"
#include "specific.h"
#define DOTFILE 5000
stack* stack_init(void)
{
  stack* s = (stack*) ncalloc(1, sizeof(stack));
  return s;
}
void stack_push(stack* s, stacktype d)
{
  if(s){
    dataframe* f = ncalloc(1, sizeof(dataframe));
    f->i = d;
    f->next = s->start;
    s->start = f;
    s->size = s->size +1;
  }
}
```  
---

bool stack_pop(stack* s, stacktype* d)
{
    if((s==NULL) || (s->start==NULL)){
        return false;
    }
    dataframe* f = s->start->next;
    *d = s->start->i;
    free(s->start);
    s->start = f;
    s->size = s->size -1;
    return true;
}
bool stack_peek(stack* s, stacktype* d)
{
    if((s==NULL) || (s->start==NULL)){
        return false;
    }
    *d = s->start->i;
    return true;
}
void stack_tostring(stack* s, char* str)
{
    char tmp[ELEMSIZE];
    str[0] = '\0';
    if((s==NULL) || (s->size <1)){
        return;
    }
    dataframe* p = s->start;
    while(p){
        sprintf(tmp, FORMATSTR, p->i);
        strcat(str, tmp);
        strcat(str, "-");
        p = p->next;
    }
    str[strlen(str)-1] = '\0';
}
bool stack_free(stack* s)
{
    if(s){
        dataframe* p = s->start;
        while(p!=NULL){
            dataframe* tmp = p->next;
            free(p);
            p = tmp;
        }
        free(s);
    }
    return true;
}