# shell.pdf OCR 结果

## 第1页

The shell
COMS10012 / COMSM0085
Software Tools

## 第2页

The shell

seis-f5-d0.services.bris.ac.uk - PuTTY

csxdb@it075734:~vagrant$ls
micro  sample-data.sql  user  Vagrantfile.mariadb
sampledata  secure-setup.sql  Vagrantfile  Vagrantfile.original
csxdb@it075734:~vagrant$ls -l sampledata/
total 8
drwxr-xr-x. 2 csxdb cosc 4096 Jul 22 11:47 census
drwxr-xr-x. 2 csxdb cosc 4096 Jul 22 11:47 elections
csxdb@it075734:~vagrant$cat sampledata/elections/elections-2014.csv | grep Bris lington | wc -l
12
csxdb@it075734:~vagrant$

## 第3页

Terms

shell xterm
terminal rxvt
console konsole
command line (gnome)-terminal
(command) prompt putty (Windows)

3

## 第4页

shell workflow
request
response
4

## 第5页

prompt
$   You are in a shell, most likely POSIX (sh) compatible.
#   You are in a root shell. With great power comes great responsibility.
%   You are probably in the C shell.
>   You are on a continuation line e.g. inside a string.
5

## 第6页

shell tricks

TAB: complete command or filename

DOUBLE TAB: show list of possible completions

UP/DOWN: scroll through history

^R text: search history for command

6

## 第7页

builtins

$ which ls
/bin/ls
$ which cd
$

## 第8页

options and conventions

$ ls
file1          file2

$ ls -l
-rwx------    1 vagrant ... 40 ... file1
-rwxr-----    1 vagrant ... 80 ... file2

$ ls -a
.          ..          file        file2

## 第9页

help
$ ls --help
BusyBox v1.30.1 multi-call binary.

Usage: ls [-1AaCxdLHRFplinshrSXvctu] [-w WIDTH] [FILE]...

List directory contents

  -1        One column output
  -a        Include entries which start with .
  ...       ...
9

## 第10页

manuals

$ man [SECTION] COMMAND

- On lab machines: fairly user-friendly manual.
- On alpine: programmer's manual.

Section 1 is shell commands, section 2 system calls, section 3 the C library etc.

e.g. man 1 printf and man 3 printf are different.

10

## 第11页

shell expansion

## 第12页

shell expansion

cat * → shell → cat file1 file2 ... → cat

Separation of responsibility:
• shell deals with expanding pattern
• program deals with its arguments

12

## 第13页

shell expansion

*   all filenames in current scope
    e.g a* is filenames starting with a etc.

?   single character in filename
    e.g. image???.jpg matches
image001.jpg

[ab] single character in list
    e.g. image[0-9].jpg

$   variable name expansion

## 第14页

shell quoting

"double quotes"   turn off pattern matching
keeps variable interpolation and backslashes on

'single quotes'   turn off everything

\*, \?, \[, \$
do not treat as pattern

## 第15页

example
cp [-rfi] SRC... DEST copy files
    -r    recursive
    -f    overwrite readonly
    -i    ask before overwriting (interactive)
mv [-nf] SRC... DEST move files
    -n    no overwrite
    -f    force overwrite
15

## 第16页

examples

$ cp index.html style.css web
$ cp * web

in empty folder:
$ cp * web
cp: can't stat '*': No such file or directory

## 第17页

find files

$ find DIR [EXPRESSION]
    find all files in directory (recursively)
    that match an expression

e.g. find . -name "a*"

17
