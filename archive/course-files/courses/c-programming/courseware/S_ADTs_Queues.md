ADTs: Queues  
FIFO (First in, First out):  
[示意图：方框内依次显示20、30、40、50]  
[示意图：链表结构，front指向20节点，20的next指向30节点，30的next指向40节点，40的next指向50节点，end指向50节点]  
- Intuitively more "useful" than a stack.  
- Think of implementing any kind of service (printer, web etc.)  
- Operations include enqueue, dequeue and size.  
queue.h  
1 #pragma once  
2  
3 #include "../General/general.h"  
4  
5 typedef int queuetype;  
6  
7 typedef struct queue queue;  
8  
9 #include <stdio.h>  
10 #include <stdlib.h>  
11 #include <string.h>  
12 #include <assert.h>  
13  
14 /* Create an empty queue */  
15 queue* queue_init(void);  
16 /* Add element on end */  
17 void queue_enqueue(queue* q, queuetype v);  
18 /* Take element off front */  
19 bool queue_dequeue(queue* q, queuetype* d);  
20 /* Return size of queue */  
21 int queue_size(queue* q);  
22 /* Clears all space used */  
23 bool queue_free(queue* q);  
24  
25 /* Helps with visualisation & testing */  
26 void queue_tostring(queue* q, char* str);

ADTs : Queues (Fixed) I
specific.h
1 #pragma once
2 #define FORMATSIR "%a"
3 #define FORMATSIZ "%d"
4 #define ELEMSIZE 20
5 #define QUEUETYPE "Fixed"
6 #define BOUNDED 5000
7 struct queue {
8     /* Underlying array */
9     queuetype a[BOUNDED];
10    int front;
11    int end;
12 };
13 #define DOTFILE 5000
Ring Buffer
Front (dequeue)
End (enqueue)

ADTs : Queues (Fixed) II
fixed.c
#include "../queue.h"
#include "specific.h"
void _inc(int* p);
queue* queue_init(void)
{
    queue* q = (queue*) ncalloc(1, sizeof(queue));
    return q;
}
void queue_enqueue(queue* q, queuetype d)
{
    if(q){
        q->a[q->end] = d;
        _inc(&q->end);
        if(q->end == q->front){
            on_error("Queue too large");
        }
    }
}
bool queue_dequeue(queue* q, queuetype* d)
{
    if((q==NULL) || (q->front==q->end)){
        return false;
    }
    *d = q->a[q->front];
    _inc(&q->front);
    return true;
}
void queue_tostring(queue* q, char* str)
{
    char tmp[ELEMSIZE];
    str[0] = '\0';
    if((q==NULL) || (queue_size(q)==0)){
        return;
    }
    for(int i=q->front; i != q->end; _inc(&i)){
        sprintf(tmp, FORMATSTR, q->a[i]);
        strcat(str, tmp);
        strcat(str, ",");
    }
    str[strlen(str)-1] = '\0';
}

ADTs : Queues (Fixed) III  
```c
int queue_size(queue * q)
{
    if(q==NULL){
        return 0;
    }
    if(q->end >= q->front){
        return q->end - q->front;
    }
    return q->end + BOUNDED - q->front;
}
bool queue_free(queue* q)
{
    free(q);
    return true;
}
void _inc(int* p)
{
    *p = (*p +1) % BOUNDED;
}
```  
- We need a thorough testing program  
- We’ll see queues again for traversing trees  
- Simulating a (slow) printer

### specific.h  
```c  
#pragma once  
#define FORMATSTR "%d"  
#define ELEMSIZE 20  
#define QUEUETYPE "Linked"  
struct dataframe {  
    queuetype i;  
    struct dataframe* next;  
};  
typedef struct dataframe dataframe;  
struct queue {  
    /* Underlying array */  
    dataframe* front;  
    dataframe* end;  
    int size;  
};  
```  
### linked.c  
```c  
#include "../queue.h"  
#include "specific.h"  
queue* queue_init(void)  
{  
    queue* q = (queue*) ncalloc(1, sizeof(queue));  
    return q;  
}  
void queue_enqueue(queue* q, queuetype d)  
{  
    dataframe* f;  
    if(q==NULL){  
        return;  
    }  
    /* Copy the data */  
    f = ncalloc(1, sizeof(dataframe));  
    f->i = d;  
    /* 1st one */  
    if(q->front == NULL){  
        q->front = f;  
        q->end = f;  
        q->size = q->size +1;  
        return;  
    }  
    /* Not 1st */  
    q->end->next = f;  
    q->end = f;  
    q->size = q->size +1;  
}  
```

bool queue_dequeue(queue* q, queuetype* d)
{
    dataframe* f;
    if((q==NULL) || (q->front==NULL) || (q->end==NULL)){
        return false;
    }
    f = q->front->next;
    *d = q->front->i;
    free(q->front);
    q->front = f;
    q->size = q->size - 1;
    return true;
}
bool queue_free(queue* q)
{
    if(q){
        dataframe* tmp;
        dataframe* p = q->front;
        while(p!=NULL){
            tmp = p->next;
            free(p);
            p = tmp;
        }
        free(q);
    }
    return true;
}
void queue_tostring(queue* q, char* str)
{
    dataframe* p;
    char tmp[ELEMENTSIZE];
    str[0] = '\0';
    if((q==NULL) || (q->front == NULL)){
        return;
    }
    p = q->front;
    while(p){
        sprintf(tmp, FORMATSTR, p->i);
        strcat(str, tmp);
        strcat(str, "->");
        p = p->next;
    }
    str[strlen(str)-1] = '\0';
}
int queue_size(queue* q)
{
    if((q==NULL) || (q->front==NULL)){
        return 0;
    }
    return q->size;
}

Detour: Graphviz  
- There exists a nice package, called Graphviz:  
  sudo apt install graphviz  
- This allows the visualisation of graphs/dynamic structures using the simple .dot language:  
  digraph {  
    a -> b; b -> c; c -> a;  
  }  
- To create a .pdf:  
  dot -Tpdf -o graphviz.pdf examp1.dot