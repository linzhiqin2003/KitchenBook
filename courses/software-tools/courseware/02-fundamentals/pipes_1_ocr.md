# pipes_1.pdf OCR 结果

## 第1页

Pipes 1
COMS10012 / COMSM0085
Software Tools

## 第2页

standard IO

## 第3页

Unix Philosophy

It is easier to maintain 10 small programs than one large program. Therefore,

1. Each program should do one thing well.

2. Programs should be able to cooperate to perform larger tasks.

3. The universal interface between programs should be a text stream.

3

## 第4页

SOURCE

#include <stdio.h>
// gives stdin etc.
// fread, fwrite, FILE* - C abstraction

#include <unistd.h>
// pulls in /usr/include/sys/unistd.h
// read, write - POSIX abstraction

#define STDIN_FILENO  0
#define STDOUT_FILENO 1
#define STDERR_FILENO 2

4

## 第5页

standard input/output

Internally, programs read(fd, buffer, size) and write(fd, buffer, size).

Each program starts with three file descriptors open:

0 = standard input
1 = standard output
2 = standard error

program

## 第6页

standard input/output
Running a program in the terminal:
program
shell

## 第7页

pipes

## 第8页

pipe  
$ ls -1 | head  
head [-n NUM]  
tail [-n NUM]

## 第9页

pipe

$ ls -1 | grep software | sort -r

grep: "global regular expression parser"

sort: read all lines into buffer, sort, output

uniq: remove duplicates immediately following
    best used as: command | sort | uniq

9

## 第10页

grep
$ grep PATTERN FILENAMES
$ grep -nHi PATTERN FILENAMES
$ grep [OPTIONS] PATTERN

## 第11页

sort

$ sort
aaa
ccc
bbb
^D
aaa
bbb
ccc
$

sort
