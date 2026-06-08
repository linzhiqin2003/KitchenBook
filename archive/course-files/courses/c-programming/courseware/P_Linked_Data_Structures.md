Linked Data Structures  
● Linked data representations are useful when:  
  ● It is difficult to predict the size and the shape of the data structures in advance.  
  ● We need to efficiently insert and delete elements.  
● To create linked data representations we use pointers to connect separate blocks of storage together. If a given block contains a pointer to a second block, we can follow this pointer there.  
● By following pointers one after another, we can travel right along the structure.  
#include <stdio.h>  
#include <stdlib.h>  
#include "general.h"  
typedef struct data{  
    int i;  
    struct data* next;  
} Data;  
Data* allocateData(int i);  
void printList(Data*);  
int main(void)  
{  
    int i;  
    Data* start, *current;  
    start = current = NULL;  
    printf("Enter the first number: ");  
    if(scanf("%d", &i) ==1){  
        start = current = allocateData(i);  
    } else {  
        on_error("Couldn't read an int");  
    }  
    printf("Enter more numbers: ");  
    while(scanf("%d", &i) ==1){  
        current->next = allocateData(i);  
        current = current->next;  
    }  
    printList(start);  
    return 0; // Should Free List  
}

Linked Lists
Data* allocateData(int i)
{
    Data* p;
    p = (Data*) ncalloc(1, sizeof(Data));
    p->i = i;
    // Not really required
    p->next = NULL;
    return p;
}
void printList(Data* l)
{
    printf("\n");
    do
    {
        printf("Number: %i\n", l->i);
        l = l->next;
    } while (l != NULL);
    printf("END\n");
}
Searching and Recursive printing:
Data* inList(Data* n, int i)
{
    do
    {
        if(n->i == i) {
            return n;
        }
        n = n->next;
    } while(n != NULL);
    return NULL;
}
void printList_r(Data* l)
{
    // Recursive Base-Case
    if(l == NULL) return;
    printf("Number: %i\n", l->i);
    printList_r(l->next);
}

Abstract Data Types
● But would we really code something like this every time we need flexible data storage?
● This would be horribly error-prone.
● Build something once, and test it well.
● One example of this is an Abstract Data Type (ADT).
● Each ADT exposes its functionality via an interface. The user only accesses the data via this interface.
● The user of the ADT doesn't need to understand how the data is being stored (e.g. array vs. linked lists etc.)
● Actually, I'll sometimes blur the boundaries of Data Structures (e.g. a linked list) with ADTs (e.g. a dictionary) themselves.