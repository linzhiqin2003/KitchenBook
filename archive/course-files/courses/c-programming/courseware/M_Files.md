# Files

## File Properties

*   They have a name.
*   Until a file is opened nothing can be done with it.
*   After use a file must be closed.
*   Files may be read, written or appended.
*   Conceptually a file may be thought of as a stream of characters.

```c
/* Creates a file called helloworld.txt
in the current filesystem and writes to it */
#include <stdio.h>
#include <stdlib.h>

int main(void)
{
    // Clobber the file if it exists already
    FILE* fp = fopen("helloworld.txt", "w");
    if (fp == NULL){
        fprintf(stderr, "Cannot open file?\n");
        exit(EXIT_FAILURE);
    }
    fprintf(fp, "Hello World!\n");
    // fscanf() is also available to read in
    fclose(fp);
    return EXIT_SUCCESS;
}
```

## Reading and Writing

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define BIGSTR 500
#define FNAME "helloworld.txt"

int main(void)
{
    FILE* fp = fopen(FNAME, "w");
    if(fp == NULL){
        fprintf(stderr, "Cannot open file %s ?\n", FNAME);
        exit(EXIT_FAILURE);
    }
    fprintf(fp, "Hello World\n");
    fclose(fp);

    fp = fopen(FNAME, "r");
    if(fp == NULL){
        fprintf(stderr, "Cannot read file %s ?\n", FNAME);
        exit(EXIT_FAILURE);
    }
    char str[BIGSTR];
    if(fgets(str, BIGSTR, fp) == NULL){
        fprintf(stderr, "Cannot read 1st line of %s ?\n", FNAME);
        exit(EXIT_FAILURE);
    }
    fclose(fp);
    // Newline is read too
    if(strcmp(str, "Hello World\n")){
        fprintf(stderr, "1st line of %s not correct?\n", FNAME);
        exit(EXIT_FAILURE);
    }
    return EXIT_SUCCESS;
}
```

*   If you write a file, it overwrites it from the beginning.
*   You must `fclose()` your file pointers otherwise there is a memory leak.
*   The statement `exit()` allows you to exit the code anywhere, not just in `main`.
*   There are three files already open for you: `stdin`, `stdout` and `stderr`.
*   Therefore `printf(...)` is just a shorthand for `fprintf(stdout, ...)`
*   `fscanf()` could be used instead of `fgets()`.

## stderr

*   To write to screen you'd generally use `stdout`, so why is there `stderr`?
*   It's fairly common, when running a program, to want to redirect the output to a file.
*   For instance, if you were to type:
    `$ ls > myfiles.txt`
    this will list all your files into myfiles.txt
*   The ">" at the prompt redirects the output (or "<" input) to file rather than screen.
*   If something went wrong though, the user would never see the message.
*   Therefore, `stderr` exists so that there is a stream to display warnings/errors to the user.

## Interlude : argc/v

A traditional C program has
`int main(int argc, char* argv[]);`

`argc` is the number of words typed on the command line to execute the program.

`argv` is an array of pointers to chars - i.e. an array of strings.

This is not a traditional 2D array of characters - it's a 1D array of pointers - each string could be a different length.

This is sometimes known as a ragged-right or jagged array.

```c
#include <stdio.h>

int main(int argc, char* argv[])
{

    printf("You typed %i arguments\n", argc);
    printf("The name of your executable is : %s\n", argv[0]);
    for(int i=1; i<argc; i++){
        printf("Argument %d is : %s\n", i, argv[i]);
    }

    return 0;
}
```

Execution :

$ ./usingargs -c doof groob
You typed 4 arguments
The name of your executable is : ./usingargs
Argument 1 is : -c
Argument 2 is : doof
Argument 3 is : groob

## Back to Files: One Character at a Time

```c
// Some of the functionality of cp
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char* argv[])
{
    if(argc !=3){
        fprintf(stderr, "Usage : %s <filein> <fileout>\n", argv[0]);
        exit(EXIT_FAILURE);
    }
    FILE* fpin = fopen(argv[1], "r");
    if(!fpin){
        fprintf(stderr, "Cannot read from %s\n", argv[1]);
        exit(EXIT_FAILURE);
    }
    FILE* fpout = fopen(argv[2], "w");
    if(!fpout){
        fprintf(stderr, "Cannot write to %s\n", argv[2]);
        exit(EXIT_FAILURE);
    }

    char c;
    while((c = fgetc(fpin)) != EOF){
        fputc(c, fpout);
    }
    fclose(fpin);
    fclose(fpout);
    return EXIT_SUCCESS;
}
```

*   This is a very basic version of the Linux command `cp`:
    `$ cp oldfile.txt newfile.txt`
*   Almost all Linux programs access arguments typed on the command line.
*   `fgetc()` and `fputc()` are the file equivalents of `getchar` and `putchar`.

## Bulk Copying

*   Copying one character at a time is very slow for large files.
*   `fread()` and `fwrite()` will I/O many characters at once.
*   Here we save an entire array to a binary file - another program could read this in later.

```c
/* Compute some factorials and save them for another program to read back later. */
#include <stdio.h>
#include <stdlib.h>

#define FACTS 20

typedef unsigned long facttype;

int main(int argc, char* argv[])
{
    if(argc != 2){
        fprintf(stderr, "Usage : %s <fileout>\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    FILE* fpout = fopen(argv[1], "wb");
    if(!fpout){
        fprintf(stderr, "Cannot write to %s\n", argv[1]);
        exit(EXIT_FAILURE);
    }

    facttype facts[FACTS] = {1};
    for(facttype i=1; i<FACTS; i++){
        facts[i] = facts[i-1]*i;
    }

    int n = fwrite(facts, sizeof(facttype), FACTS, fpout);
    if(n != FACTS){
        fprintf(stderr, "Cannot write to %s\n", argv[1]);
        exit(EXIT_FAILURE);
    }

    fclose(fpout);
    return EXIT_SUCCESS;
}
```

## Window/DOS vs. Unix Text Files

*   Text files created on DOS/Windows machines have different line endings than files created on Unix/Linux.
*   DOS uses carriage return and line feed ("\r\n") as a line ending.
*   Unix uses just line feed ("\n").
*   You should generally avoid assuming line endings - use a function that reads entire lines at once such as `fgets()`.
*   When you open a file in textmode `fopen("file.txt", "rt")` some automatic translation may be done on input/output.

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BIGSTR 10000

int main(int argc, char* argv[])
{
    if(argc != 2){
        fprintf(stderr, "Usage : %s <file>\n", argv[0]);
        exit(EXIT_FAILURE);
    }
    FILE* fpin = fopen(argv[1], "rb");
    if(!fpin){
        fprintf(stderr, "Cannot read %s\n", argv[1]);
        exit(EXIT_FAILURE);
    }
    char str[BIGSTR];
    if(fgets(str, BIGSTR, fpin)==NULL){
        fprintf(stderr, "Cannot read %s\n", argv[1]);
        exit(EXIT_FAILURE);
    }
}
```
