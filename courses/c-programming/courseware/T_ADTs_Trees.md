Binary Trees : Data Structures
● Binary trees are used extensively in computer science  
● Game Trees  
● Searching  
● Sorting  
● Trees drawn upside-down !  
● Ancestor relationships: '50' is the parent of '25' and '75'.  
● Can refer to left and right children  
● In a tree, there is only one path from the root to any child  
● A node with no children is a leaf  
● Most trees need to be created dynamically  
● Empty subtrees are set to NULL

Binary Search Trees  
In a binary search tree the left-hand tree of a parent contains all keys less than the parent node, and the right-hand side all the keys greater than the parent node.  
（Tree structure:  
Root node: 50  
Left child of 50: 25; Right child of 50:75  
Left child of 25:20; Right child of25:30  
Left child of20:19; Right child of20:21  
Left child of30:29; Right child of30:31  
Left child of75:70; Right child of75:80  
Left child of70:69; Right child of70:71  
Left child of80:79; Right child of80:81）  
bst.h  
1 #include "../General/general.h"  
2 #include "../Queue/queue.h"  
3  
4 #include <stdio.h>  
5 #include <stdlib.h>  
6 #include <assert.h>  
7  
8 bst* bst_init(void);  
9  
10 /* Insert 1 item into the tree */  
11 bool bst_insert(bst* b, treetype d);  
12  
13 /* Return number of nodes in tree */  
14 int bst_size(bst* b);  
15  
16 /* Whether the data d is stored in the tree */  
17 bool bst_isin(bst* b, treetype d);  
18  
19 /* Bulk insert n items from an array a into an initialised tree */  
20 bool bst_insertarray(bst* b, treetype* a, int n);  
21  
22 /* Clear all memory associated with tree, & set pointer to NULL */  
23 bool bst_free(bst* b);  
24  
25 /* Optional ? */  
26  
27 char* bst_preorder(bst* b);  
28 void bst_printlevel(bst* b);  
29 /* Create string with tree as ((head)(left)(right)) */  
30 char* bst_printlisp(bst* b);  
31 /* Use Graphviz via a .dot file */  
32 void bst_todot(bst* b, char* dotname);

Binary Search Trees : Linked I
specific.h
1 #include <string.h>
2
3 typedef int treetype;
4 #define FORMATSTR "%i"
5 #define ELEMSIZE 20
6 #define BSTTYPE "Linked"
7
8 struct dataframe {
9     treetype d;
10    struct dataframe* left;
11    struct dataframe* right;
12 };
13 typedef struct dataframe dataframe;
14
15 struct bst {
16     dataframe* top;
17     /* Data element size, in bytes */
18 };
19 typedef struct bst bst;
/* Based on geeksforgeeks.org */
dataframe* _insert(dataframe* t, treetype d)
{
    dataframe* f;
    /* If the tree is empty, return a new frame */
    if (t == NULL) {
        f = nalloc(sizeof(dataframe), 1);
        f->d = d;
        return f;
    }
    /* Otherwise, recurs down the tree */
    if (d < t->d) {
        t->left = _insert(t->left, d);
    } else if (d > t->d) {
        t->right = _insert(t->right, d);
    }
    /* return the (unchanged) dataframe pointer */
    return t;
}

Binary Search Trees : Linked II
bool _isin(dataframe* t, treetype d)
{
    if(t==NULL){
        return false;
    }
    if(t->d == d){
        return true;
    }
    if(d < t->d){
        return _isin(t->left, d);
    } else {
        return _isin(t->right, d);
    }
    return false;
}
char* _printlist(dataframe* t)
{
    char tmp[ELEMSIZE];
    char *s1, *s2, *p;
    if(t==NULL){
        /* \0 string */
        p = ncalloc(1,1);
        return p;
    }
    sprintf(tmp, FORMATSTR, t->d);
    s1 = _printlist(t->left);
    s2 = _printlist(t->right);
    p = ncalloc(strlen(s1)+strlen(s2)+strlen(tmp)+ strlen("()") + strlen(" ") +1,1);
    sprintf(p, "(%s %s %s)", tmp, s1, s2);
    free(s1);
    free(s2);
    return p;
}

Binary Trees using Arrays?  
● Don’t rush to assume a linked data structure must be used to implement trees.  
● You could use 1 cell of an array for the first node, the next two cells for its children, the next 4 cells for their children and so on.  
● You need to mark which cells are in use & which aren’t ...  
Counting from cell 1, for a tree with n nodes:  
| To find                  | Use       | Iff               |  
|--------------------------|-----------|-------------------|  
| The root                 | A[1]      | A is nonempty     |  
| The left child of A[i]   | A[2i]     | 2i ≤ n            |  
| The parent of A[i]       | A[i/2]    | i > 1             |  
| Is A[i] a leaf?          | True      | 2i > n            |

Binary Search Trees : Realloc
specific.h
1 #include <stdbool.h>
2 
3 typedef int treetype;
4 #define FORMATSTR "%i "
5 #define ELEMSIZE 20
6 #define BSTTYPE "Realloc"
7 
8 // Probably (2^n) -1
9 #define INITSIZE 31
10 #define SCALEFACTOR 2
11 
12 struct dataframe {
13     treetype d;
14     bool isvalid;
15 };
16 typedef struct dataframe dataframe;
17 
18 struct bst {
19     dataframe* a;
20     int capacity;
21 };
22 typedef struct bst bst;
Using a queue for Level-Order traversal:
void bst_printlevel(bst* b)
{
    treetype n;
    if((b==NULL) || (!_isvalid(b, 0))){
        return;
    }
    /* Make a queue of cell indices */
    queue* q = queue_init();
    queue_enqueue(q, 0);
    while(queue_dequeue(q, &n) && _isvalid(b, (int)n)){
        printf(FORMATSTR, b->a[n].d);
        putchar(' ');
        queue_enqueue(q, _leftchild((int)n));
        queue_enqueue(q, _rightchild((int)n));
    }
}

Binary Search Trees: Complexity  
- So, in a nicely balanced tree, insertion, deletion and search are all O(log n).  
- But: if the root of the tree is not well chosen, or the keys to be inserted are ordered, the tree can become a linked list!  
- In this case, complexity becomes O(n).  
- The tree search performs best when well balanced trees are formed.  
- Large body of literature about creating & re-balancing trees - Red-Black trees, Tries, 2-3 trees, AVL trees etc.

Binary Trees: Huffman Compression I  
- Often we wish to compress data, to reduce storage requirements, or to speed transmission.  
- Text is particularly suited to compression since using one byte per character is wasteful - some letters occur much more frequently.  
- Need to give frequently occurring letters short codes, typically a few bits. Less common letters can have long bit patterns.  
- To encode the string "BABBAGE":  
  B: 3/7, A:2/7, E:1/7, G:1/7  
- Keep a list of characters, ordered by their frequency

Binary Trees: Huffman Compression II  
● Use the two least frequent to form a sub-tree, and re-order (sort) the nodes :  
（Left-side nodes）  
3/7 B  
2/7 A  
2/7 （root node with children: 1/7 E, 1/7 G）  
1/7 E  
1/7 G  
（Right-side tree structure）  
7/7  
├─0: 3/7 B  
└─1: 4/7  
   ├─0: 2/7 A  
   └─1: 2/7  
      ├─0:1/7 E  
      └─1:1/7 G  
● A = 10, B = 0, E = 110, G = 111  
● String stored using 13 bits.