ADTs : Graphs  
- A graph, G, consists of a set of vertices (nodes), V, together with a set of edges (links), E, each of which connects two vertices.  
- This is a directed graph (digraph). Vertices are joined to adjacent vertices by these edges.  
- Every edge has a non-negative weight attached which may correspond to time, distance, cost etc.  
graph.h (partial)  
#include <limits.h>  
#define INF (INT_MAX)  
/* Initialise an empty graph */  
graph* graph_init(void);  
/* Add new vertex */  
int graph_addVert(graph* g, char* label);  
/* Add new edge between two Vertices */  
bool graph_addEdge(graph* g, int from, int to, edge_weight);  
/* Returns NO_VERT if not already a vert else 0 ... (size-1) */  
int graph_getVertNum(graph* g, char* label);  
/* Returns label of vertex v */  
char* graph_getLabel(graph* g, int v);  
/* Returns edge weight - if none = INF */  
edge_weight graph_getWeight(graph* g, int from, int to);  
/* Number of edges & Vertices */  
int graph_numVerts(graph* b);  
/* Output edge weights e.g. "0->1 200 2->1 100" */  
void graph_toString(graph* g, char* str);  
/* Clear all memory associated with graph */  
bool graph_free(graph* g);

Graph ADT: 2D Realloc I
The graph type could be implemented in a large number of different ways.
● As two sets, one for vertices, one for edges. We haven't looked at an implentation for sets, but one could use lists.
● As an adjacency table - simply encode the weighted edges in a 2D array.
Adjacency Table:
    0  1  2  3  4
0 | 0  5  3  ∞  2
1 | ∞  0  2  6  ∞
2 | ∞  1  0  2  ∞
3 | ∞  ∞  ∞  0  ∞
4 | ∞  6 10  4  0
specific.h
1 #define GRAPHTYPE "Realloc"
2 
3 #define INITSIZE 8
4 #define SCALEFACTOR 2
5 
6 #define TMPSTR 1000
7 
8 #define NO_VERT -1
9 
10 typedef unsigned int edge;
11 
12 struct graph {
13     edge** adjMat;
14     char** labels;
15     /* Actual number of verts */
16     int size;
17     /* Max verts before realloc() */
18     int capacity;
19 };
20 typedef struct graph graph;

graph* graph_init(void)
{
    graph* g = (graph*) ncalloc(sizeof(graph), 1);
    int h = INITSIZE;
    int w = h;
    g->capacity = h;
    g->adjMat = (edge**) n2dcalloc(h, w, sizeof(edge));
    g->labels = (char**) n2dcalloc(h, MAXLABEL+1, sizeof(char));
    g->size = 0;
    for(int i = 0; i < h; i++){
        for(int j = 0; j < w; j++){
            /* It's not clear if weight[j][i] should be 0 or INF */
            g->adjMat[j][i] = INF;
        }
    }
    return g;
}
edge graph_getEdgeWeight(graph* g, int from, int to)
{
    if((g==NULL) || (from >= g->size) || (to >= g->size)){
        return INF;
    }
    return g->adjMat[from][to];
}
int graph_numVerts(graph* g)
{
    if(g==NULL){
        return 0;
    }
    return g->size;
}
int graph_addVert(graph* g, char* label)
{
    if(g==NULL){
        return NO_VERT;
    }
    if(graph_getVertNum(g, label) != NO_VERT){
        return NO_VERT;
    }
    /* Resize */
    if(g->size >= g->capacity){
        g->adjMat = (edge**) n2drecalloc((void**)g->adjMat, 
            g->capacity, g->capacity*SCALEFACTOR, 
            g->capacity, g->capacity*SCALEFACTOR, 
            sizeof(edge));
        g->labels = (char**) n2drecalloc((void**)g->labels, 
            g->capacity, g->capacity*SCALEFACTOR, 
            MAXLABEL+1, MAXLABEL+1, 1);
        for(int j = 0; j < g->capacity*SCALEFACTOR; j++){
            for(int i = 0; i < g->capacity*SCALEFACTOR; i++){
                if(i >= g->capacity || j >= g->capacity){
                    g->adjMat[j][i] = INF;
                }
            }
        }
        g->capacity = g->capacity*SCALEFACTOR;
    }
    strcpy(g->labels[g->size], label);
    g->size = g->size + 1;
    return g->size -1;
}

Graph ADT - Linked  
顶点0的出边链表：5 → 3 → 2（末尾带黑点）  
顶点1的出边链表：2 → 6（末尾带黑点）  
顶点2的出边链表：1 → 2（末尾带黑点）  
顶点3：（带黑点，无出边）  
顶点4的出边链表：6 → 10 → 4（末尾带黑点）  
箭头关系：0向下指向1，1向下指向2，2向下指向3，3向下指向4；5指向1；3指向6；2指向...（图中其他箭头连接）  
specific.h  
#define GRAPHTYPE "Linked"  
#define INITSIZE 8  
#define SCALEFACTOR 2  
#define TMPSTR 1000  
#define NO_VERT -1  
typedef unsigned int edge;  
struct vertex {  
    char* label;  
    struct vertex* nextv;  
    void* firste;  
    int num;  
};  
typedef struct vertex vertex;  
struct edge {  
    edge weight;  
    vertex* v;  
    struct edge* nexte;  
};  
typedef struct edge edge1;  
struct graph {  
    vertex* firstv;  
    vertex* endv;  
    int size;  
};  
typedef struct graph graph;

Linked II
graph* graph_init(void)
{
    graph* g = (graph*) ncalloc(1, sizeof(graph));
    return g;
}
edge graph_getEdgeWeight(graph* g, int from, int to)
{
    if((g==NULL) || (from >= g->size) || (to >= g->size)){
        return INF;
    }
    vertex* v = g->firstv;
    for(int i=0; i<from; i++){
        v = v->nextv;
    }
    if((v==NULL) || (v->num != from)){
        return INF;
    }
    edge* e = v->firste;
    while(e != NULL){
        if(e->v_num == to){
            return e->weight;
        }
        e = e->nexte;
    }
    return INF;
}
bool graph_addEdge(graph* g, int from, int to, edge w)
{
    if((g==NULL) || (g->size == 0)){
        return false;
    }
    if((from >= g->size) || (to >= g->size)){
        return false;
    }
    vertex* f = g->firstv;
    for(int i=0; i<from; i++){
        f = f->nextv;
    }
    vertex* t = g->firstv;
    for(int i=0; i<to; i++){
        t = t->nextv;
    }
    return _addEdge(f, t, w);
}

Sidebar : P = NP ?  
- The P versus NP problem is a major unsolved problem in theoretical computer science.  
- It asks whether every problem whose solution can be quickly verified can also be quickly solved.  
- e.g. the Subset Sum problem — for a set of numbers and a target sum, determine if there exists a subset of numbers that adds up to the target sum.  
- Easy to verify a solution: For {3,4,5,6,7} and a target of 9, a valid subset is {4,5}. This is P.  
- But computing it takes O(2ⁿ) time (non-polynomial) NP.  
- But maybe NP algorithms are 'hard' simply because we haven't found a better solution?  
- It is thought that P ≠ NP, meaning there are problems that can't be solved in polynomial time, but for which the answer could be verified in polynomial time.  
- A proof either way would have profound implications for mathematics, cryptography, AI etc.

Algorithms : TSP on Graphs
Imagine planning a delivery route around a graph, starting from a particular vertex.
What's the least cost by which you can visit every vertex without ever returning to one?
Finding the optimal path (to reduce travelling time) is an NP problem.
For small graphs you could do this exhaustively, but for very large graphs this combinatorial approach becomes untenable.
One 'greedy' approach is to simply go to your closest unvisited neighbour each time.
Typically gives results within 25% of the optimal solution, but sometimes give a worst-case solution ...
A -> B -> C -> D -> J -> I -> E -> F -> G

edge graph_salesman(graph* g, int from, char* str)
{
    bool* unvis;
    int curr, ncurr, nvs;
    int cst, bcst, e;
    nvs = graph_numVerts(g);
    if ((g==NULL) || (from >= nvs) || (str==NULL)){
        return INF;
    }
    unvis = (bool*)ncalloc(nvs, sizeof(bool));
    for(int v=0; v<nvs; v++){
        unvis[v] = true;
    }
    curr = from;
    bcst = 0;
    strcpy(str, graph_getLabel(g, from));
    do{
        unvis[curr] = false;
        cst = INF;
        ncurr = NO_VERT;
        /* Look at neighbours of curr */
        for(int v=0; v<nvs; v++){
            e = graph_getEdgeWeight(g, curr, v);
            if((v != curr) && unvis[v] && (e!=INF)){
                if(e < cst){
                    cst = e;
                    ncurr = v;
                }
            }
        }
        /* Add in cost to go to closest */
        if(cst < INF){
            bcst += cst;
            curr = ncurr;
            strcat(str, " -> ");
            strcat(str, graph_getLabel(g, ncurr));
        }
    }while((cst < INF) && (curr != NO_VERT));
    free(unvis);
    return bcst;
}

Algorithms : Dijkstra on Graphs  
- It's often important to find the shortest path through a graph from one vertex to another.  
- One way of doing this is the greedy algorithm due to Dijkstra discovered 1956.  
- Picks the unvisited vertex with the lowest distance, & calculate the distance through it to each unvisited neighbor, updating the neighbour's distance if smaller.  
- Mark visited when done with neighbors.  
[Top-left graph]  
Green circle vertex A connected to:  
- Red circle vertex B (red arrow, label 1)  
- White circle vertex D (black arrow, label 10)  
- White circle vertex F (black arrow, label 8)  
- White circle vertex J (black arrow, label 9)  
[Top-right graph]  
Green circle vertex B connected to:  
- Red circle vertex C (red arrow, label 12+1)  
- White circle vertex E (black arrow, label 2+1)  
- White circle vertex I (black arrow, label 20+1)  
[Bottom graph]  
Green circle vertex C connected to:  
- White circle vertex A (arrow, label 20+1)  
- Red circle vertex D (red arrow, label 23+13)