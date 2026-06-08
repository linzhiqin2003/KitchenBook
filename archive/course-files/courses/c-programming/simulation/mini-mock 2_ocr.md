# mini-mock 2.pdf OCR 结果

## 第1页

UNIVERSITY OF BRISTOL  
Mini Mock 2  
School of Computer Science  

Theory examination for the Degree of  
Master of Science in Computer Science (conversion)  

COMSM1201  
Programming in C  

TIME ALLOWED:  
45 minutes  

This paper contains twenty-six questions.  
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

1. Which header file must be included to use the pre-defined rand() function?  
a) stdio.h b) stdlib.h c) stdbool.h d) string.h e) math.h  


2. Which statement best describes the main purpose of the inline modifier?  
a) To define a function that can be called multiple times without requiring a return value.  
b) To ensure that the function is treated as a local function rather than a global one.  
c) To suggest that the function code should be inserted at each call site to reduce overhead.  
d) To create a function that automatically optimizes its performance during execution.  
e) To ensure that a function has a fixed size in memory regardless of the number of calls.  


3. Which of the following is not a valid numeric constant?  
a) 7 b) 7.0 c) 07 d) 0o7 e) 0x7  


4. Which of the following is not a standard data type in C?  
a) signed c) signed double e) signed short  
b) signed char d) signed long  


5. Which statement best describes a static variable declared inside a function?  
a) The variable retains its value between function calls.  
b) The variable is shared across all functions in the program.  
c) The variable cannot be modified once assigned a value.  
d) The variable is initialized to zero every time the function is called.  
e) The variable is accessible outside the file it is defined in.  


6. For the following code snippet, what will be printed to the terminal?  
printf("%d\n", 2&1);  
a) -1 b) 0 c) 1 d) 2 e) 3  


7. For the following code snippet, what will be printed to the terminal?  
printf("%d\n", 3^2);  
a) 0 b) 1 c) 2 d) 6 e) 9  


8. For the following code snippet, what will be printed to the terminal?  
printf("%d\n", 2 * 3 > 6 ? 5 : 4);  
a) 2 b) 3 c)4 d)5 e)6  


Page 2 of 6

## 第3页

9. For the following code snippet, what will be printed to the terminal?
    int a = 2, b = 3;
    a = b, b = a--;
    printf("%d%d\n", --a, b);
a) 01  
b) 02  
c) 11  
d) 12  
e) 13  

10. For the following code snippet, what will be printed to the terminal?
    float val = 9876.54321;
    printf("%.2f", val);
a) 1.34321  
b) 3.2  
c) 6.54  
d) 876.54  
e) 9876.54  

11. What will happen when executing code that contains the following snippet?
    int i = 0, sum = 1;
    while (i < 2) {
        sum += i;
    }
    printf("%d\n", sum);
a) 0 will be printed to the terminal.  
b) 1 will be printed to the terminal.  
c) 2 will be printed to the terminal.  
d) The program will get stuck in an infinite loop.  
e) The code will not compile due to a syntax error.  

12. What character is stored in arr[1][2] after the following line is executed?
    char arr[3][3] = {{'a','b','c'},{'d','e','f'},{'g','h','i'}};
a) 'b'  
b) 'd'  
c) 'e'  
d) 'f'  
e) 'h'  

13. For a program that contains the following functions, what will be printed to the terminal?
    int func(const int* a, int n){
        if(n >= 0){
            return a[n];
        }
        return 0;
    }
    int main(void){
        int a[] = {1,2,3,4};
        printf("%d\n", func(a, 2));
        return 0;
    }
a) 0  
b) 1  
c) 2  
d) 3  
e) 4  

Page 3 of 6  
Turn Over...

## 第4页

14. In which order should the variables in the below code snippet be freed?  
node1->next = node2;  
node2->next = node3;  
a) node1, node2, node3  
b) node1, node3, node2  
c) node2, node3, node1  
d) node3, node1, node2  
e) node3, node2, node1  

15. For the below code snippet, which of the following function calls would allow the value of x to be edited?  
int y = 5;  
int* x = &y;  
a) func(*x); where the func() prototype is void func(int* a);  
b) func(&x); where the func() prototype is void func(int* a);  
c) func(&y); where the func() prototype is void func(int* a);  
d) func(&x); where the func() prototype is void func(int** a);  
e) func(&y); where the func() prototype is void func(int** a);  

16. Which of the following situations will fopen("a.txt", "r") return a value other than NULL?  
a) The file a.txt does not exist.  
b) The file a.txt exists, but the program lacks read permissions.  
c) The file a.txt exists, but is in a different directory to the program.  
d) The file a.txt is locked or occupied by another process.  
e) The file a.txt is empty.  

17. What does argc contain in a standard program?  
a) The total number of command-line arguments, excluding the program name.  
b) The total number of command-line arguments, including the program name.  
c) The number of characters in the command-line arguments.  
d) The length of the longest command-line argument.  
e) The index of the last command-line argument.  

Page 4 of 6

## 第5页

18. Given the below function definitions and a tree with root node rt, if func1(rt) prints ABDECF and func2(rt) prints DBEAFC, what will func3(rt) print?  

void func1(node* n) {  
    if (n != NULL) {  
        printf("%c", n->data);  
        func1(n->left);  
        func1(n->right);  
    }  
}  

void func2(node* n) {  
    if (n != NULL) {  
        func2(n->left);  
        printf("%c", n->data);  
        func2(n->right);  
    }  
}  

void func3(node* n) {  
    if (n != NULL) {  
        func3(n->left);  
        func3(n->right);  
        printf("%c", n->data);  
    }  
}  

a) DBEFCA  b) DEBFCA  c) EBDFCA  d) EDBFAC  e) EDBFCA  

19. After completing the first pass of a radix sort on the array below, what will be the value of the 4th element in the resulting array?  

170, 45, 75, 90, 802, 24, 2, 66  

a) 2  b) 24  c) 45  d) 90  e) 802  

20. What is the worst case time complexity for inserting an element into a binary search tree?  

a) O(1)  b) O(log log n)  c) O(log n)  d) O(n)  e) O(n²)  

21. What is the average time complexity of a binary search on a sorted array?  

a) O(1)  b) O(log log n)  c) O(log n)  d) O(n)  e) O(n²)  

Page 5 of 6 Turn Over...

## 第6页

22. Which of the following do users of an Abstract Data Type (ADT) need knowledge of?  
a) The data structure(s) used to store the ADT's data.  
b) The operation(s) available to perform on the ADT.  
c) The memory location(s) of the ADT's data.  
d) The source code written to implement the ADT.  
e) The variable name(s) used to store the ADT's data.  

23. Which of the following data structures would be preferable to store a list of strings, if speed of searching is the top priority?  
a) Array c) Doubly linked list e) Singly linked list  
b) Binary tree d) Hash table  

24. Which of these ADTs never allows duplicate elements to be added?  
a) Graphs b) Queues c) Sets d) Stacks e) Trees  

25. Which of the following statements best describes a hashing algorithm?  
a) A function that maps input data to a fixed-size value to facilitate efficient data retrieval.  
b) A method for encrypting data to prevent unauthorized access.  
c) A process of compressing data into a smaller fixed-size format for storage efficiency.  
d) A function that generates a random value for each piece of input data.  
e) A procedure for iteratively improving the accuracy of search results.  

26. Which of the following annoys Neill's the most?  
a) Global variables.  
b) Incorrectly named coursework submissions.  
c) Random uses of the keyword 'static'.  
d) assert(2==2).  
e) All of the above.  

END OF EXAMINATION  

Page 6 of 6

## 第7页

THIS PAGE IS INTENTIONALLY LEFT BLANK

## 第8页

THIS PAGE IS INTENTIONALLY LEFT BLANK
