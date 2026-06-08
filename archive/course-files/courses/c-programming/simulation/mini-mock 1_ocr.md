# mini-mock 1.pdf OCR 结果

## 第1页

UNIVERSITY OF BRISTOL  
Mini Mock 1  
School of Computer Science  

Theory examination for the Degree of  
Master of Science in Computer Science (conversion)  

COMSM1201  
Programming in C  

TIME ALLOWED:  
45 minutes  

This paper contains twenty-five questions.  
All questions will be marked.  
All questions must be answered on the multiple choice answer sheet.  
The maximum for this paper is 25 marks.  

Other Instructions  

Calculators and notes are not permitted for this examination.  

All questions in this examination will be computer marked, so it is crucial that you fill in the answer sheet carefully. Use a pencil (not pen) to fill in the answer sheet, and a pencil eraser to remove any mistakes you make.  

Write your candidate name, title of the examination, unit code, date, desk number, and your student number on the answer sheet in the relevant boxes.  

TURN OVER ONLY WHEN TOLD TO BEGIN WORK  

Page 1 of 6

## 第2页

1. Which of the following lines of codes will result in no compilation errors or warnings, for the user-written header file mydefs.h?  
a) #include <mydefs.h>;  
c) #include 'mydefs.h';  
e) #include "mydefs.h"  
b) #include "mydefs.h";  
d) #include <mydefs.h>  

2. What compiler flag is required in order to use the pre-defined functions defined in math.h?  
a) -g3  
b) -lm  
c) -o  
d) -O3  
e) -std=99  

3. Which of the following statements about identifiers is false?  
a) Identifiers are case-sensitive.  
b) Identifiers cannot contain spaces.  
c) Identifiers cannot contain special characters, except an underscore.  
d) Identifiers cannot start with a digit.  
e) Identifiers cannot start with an underscore.  

4. Which standard data type is used to store enumerators?  
a) bool  
b) char  
c) char*  
d) float  
e) int  

5. Which of the following correctly initialises a 2D array with 2 rows and 4 columns?  
a) int arr[2][4] = {1, 2, 3, 4, 5, 6, 7, 8};  
b) int arr[2][4] = {1, 2}, {3, 4}, {5, 6}, {7, 8};  
c) int arr[2][4] = {1, 2}, {3, 4}, {5, 6}, {7, 8};  
d) int arr[2][4] = {1, 2, 3, 4}, {5, 6, 7, 8};  
e) int arr[2][4] = {1, 2, 3, 4}, {5, 6, 7, 8};  

6. What will happen when executing code that contains the following snippet?  
int x = 10, y = 4;  
float z = x/y;  
printf("%.1f\n", z);  
a) 1.1 will be printed to the terminal.  
b) 2.0 will be printed to the terminal.  
c) 2.5 will be printed to the terminal.  
d) z will be printed to the terminal.  
e) The code will not compile due to a syntax error.  

Page 2 of 6

## 第3页

7. For the following code snippet, what will be printed to the terminal?  
    int x = 2, y = 3, z = 3;  
    printf("%d", x = y == z);  
a) -1  b) 0  c) 1  d) 2  e) 3  

8. For the following code snippet, what will be printed to the terminal?  
    printf("%d", !2);  
a) -3  b) -2  c) -1  d) 0  e) 1  

9. For the following code snippet, what will be printed to the terminal?  
    printf("%d\n", 1<<2);  
a) 0  b)1  c)2  d)3  e)4  

10. Which of the following lines of code correctly combines an enumerated type with typedef?  
a) enum typedef colours{red, yellow, blue} colours;  
b) enum colours{red, yellow, blue} typedef colours colours;  
c) typedef enum colours{red, yellow, blue};  
d) typedef colours enum colours{red, yellow, blue};  
e) typedef enum colours{red, yellow, blue} colours;  

11. For the following code snippet, what will be printed to the terminal?  
    int i = 2, j = 3;  
    switch (i){  
        case 1:  
            j++;  
        case 2:  
        case 3:  
            i++;  
        case 4:  
            j--;  
        default:  
            i--;  
    }  
    printf("%d%d", i, j);  
a)22  b)23  c)32  d)33  e)42  

12. Which statement best explains the effect of using == to compare floating-point numbers?  
a) Floating-point comparison is only problematic when the numbers are very big.  
b) The == operator is not defined for floating-point numbers.  
c) Floating-point numbers are stored approximately, making direct comparisons unreliable.  
d) Floating-point comparisons are only accurate if both numbers are positive.  
e) The use of == for floating-point comparison is always safe.  

Page 3 of 6  
Turn Over...

## 第4页

13. Which of the following for() top lines will result in different behaviour to the others, assuming that the value of num is not modified within the code block?  
a) for(int num = 0; num < 5; num++)  
d) for(int num = 10; num > 5; --num)  
b) for(int num = 0; num <= 4; ++num)  
e) for(int num =5; num !=0; num--)  
c) for(int num =5; num <=10; num++)  


14. What will happen when trying to compile and run code that contains the following snippet, if the program is compiled using the sanitizer flags?  
int list[10];  
int i =0;  
while(i !=10){  
    list[++i] =0;  
}  

a) The code won't compile due to a syntax error.  
b) The code will get stuck in an infinite loop.  
c) The code will produce an out of bounds error.  
d) The code will never enter the loop.  
e) The code will run successfully.  


15. What will the return value of calc() be, where calc() is defined below??  
int calc(void){  
    static int n =4;  
    int a[] = {0,1,2,3}, b[]={1,0,1,1};  
    if(--n >=0){  
        return a[n]*b[n]+calc();  
    }  
    return 0;  
}  

a)1  b)2  c)3  d)4  e)5  


16. What will the value of a be after the following snippet is executed?  
int a =5;  
int *p = &a;  
*p = *p +3;  
p = NULL;  

a)0  b)3  c)5  d)8  e)NULL  


Page 4 of 6

## 第5页

17. What is the correct way to access the fifth element of an array arr?  
a) (*arr)+4  b) *(arr+4)  c) arr[5]  d) (*arr)+5  e) *(arr+5)  

18. Which of the following is a cause of memory leaks in C?  
a) Declaring a variable but never using it within the program.  
b) Opening a file but not closing it before the program ends.  
c) Returning the address of a local variable from a function.  
d) Using an uninitialised pointer in a calculation.  
e) Writing to an index beyond the bounds of an array.  

19. Which fopen() mode enables both reading and writing to a file without truncating it?  
a) "a"  b) "r++"  c) "r+"  d) "w++"  e) "w"  

20. A binary tree is shown below, with the node top node stored in a variable named root. Given the node structure definition below, what will be printed after the function print(&root) is called?  

Tree structure:  
    1  
   / \  
  2   3  
 / \  
4   5  

struct node {  
    int data;  
    struct node* left;  
    struct node* right;  
};  

void print(struct node *n) {  
    if (n == NULL) return;  
    printf("%d ", n->data);  
    print(n->left);  
    print(n->right);  
}  

a) 1 2 4 5 3  c) 1 4 5 2 3  e) 4 5 2 3 1  
b) 1 3 2 5 4  d) 4 2 5 1 3  

21. For the array of sorted integers below, what is the sequence of values examined when performing a binary search for the target value 48?  
1, 7, 12, 25, 37, 48, 51, 59, 72, 73, 86, 94, 98, 105, 120  
a) 72, 48  b) 59, 48  c) 59, 37, 48  d) 72, 37, 48  e) 59, 25, 48  

22. What is the average time complexity of inserting an element at the end of a fixed size array, if there's space available?  
a) O(1)  b) O(log n)  c) O(n)  d) O(n log n)  e) O(n²)  

Page 5 of 6  
Turn Over...  
```

## 第6页

23. What is the worst case time complexity of a merge sort on an array?  
a) O(1)  
b) O(log n)  
c) O(n)  
d) O(n log n)  
e) O(n²)  

24. Which of the following ADTs uses the Last In First Out (LIFO) approach?  
a) Stacks  
b) Queues  
c) Sets  
d) Graphs  
e) Trees  

25. Which of the following is not a method used to manage collisions in a hash table?  
a) Hashing the data again with a different algorithm.  
b) Moving one of the entries to a second table with a different hash function.  
c) Shifting all entries after the collision forward by one position to create a free slot.  
d) Chaining entries so that each slot in the table holds several entries.  
e) Taking linear steps backwards until a free slot is found.  

END OF EXAMINATION  

Page 6 of 6

## 第7页

THIS PAGE IS INTENTIONALLY LEFT BLANK

## 第8页

THIS PAGE IS INTENTIONALLY LEFT BLANK
