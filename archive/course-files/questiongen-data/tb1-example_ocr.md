# tb1-example.pdf OCR 结果

## 第1页

UNIVERSITY OF BRISTOL  
Winter Examination Period  
FACULTY OF ENGINEERING  

2024 Examination for the Degree of  
Bachelor and Master of Engineering and Bachelor and Master of  
Science  

COMS10012 and COMSM0085  
Software Tools  

TIME ALLOWED:  
1 Hour  

This paper contains 32 questions, all of which are used for assessment; the maximum for this  
paper is 32.  

Other Instructions:  
This exam is open-book: you may bring in any handwritten or printed materials. You  
may use a faculty-approved calculator model.  

TURN OVER ONLY WHEN TOLD TO START WRITING

## 第2页

1. Please make sure you read the instructions on the answer sheet.
2. Each question is worth 1 mark.
3. Only the answer sheet will be marked, the empty pages at the back of the exam are only used for your calculations.
4. When selecting answers, make clear, horizontal marks within the two sets of brackets, making sure that the contained letter is struck through.
5. Avoid marking the answer sheet outside specified areas.
6. Do not crease, dog-ear or otherwise damage the answer sheet.

Page 2 of 18

## 第3页

Q1. Alice is trying to set up key-based login on a service she currently accesses via using ssh and entering her password. Here are listings of her .ssh directory on her local machine:

    -rw------- 1 alice alice 389 Jan 19 10:56 authorized_keys
    -rw-r--r-- 1 alice alice 395 Feb 21 13:03 id_rsa.pub
    -rw------- 1 alice alice 1766 Feb 21 13:03 id_rsa
    -rw-r--r-- 1 alice alice 225 Feb 21 13:01 known_hosts

And on the server:

    -rw-r--r-- 1 alice alice 395 Feb 21 13:21 id_rsa.pub
    -rw-r--r-- 1 alice alice 225 Jan 19 11:02 known_hosts

There's a problem evident with her current setup that is preventing key-based login from working. Identify which file's presence, absence or visible details indicates the problem.

    A. The problem lies with 'authorized_keys' on the server.
    B. The problem lies with 'known_hosts' on the local machine.
    C. The problem lies with 'id_rsa' on the local machine.
    D. The problem lies with 'id_rsa.pub' on the server.
    E. I do not want any marks for this question.

Q2. To refresh the local list of available packages in Debian, the best command to use is:

    A. apt upgrade
    B. apt update
    C. vagrant box update
    D. apt-cache -gf dump
    E. I do not want any marks for this question.

Q3. Jason has a user account eg1234 on a server accessible via SSH at the domain jserv.ru. He wants to copy the file demo.c from his current local working directory to the code folder in his home directory on that server. Which of these commands should achieve what he wants?

    A. scp ./demo.c eg1234@jserv.ru:/code/
    B. scp /home/eg1234/demo.c jserv.ru:/home/eg1234/
    C. scp ~/demo.c eg1234@jserv.ru/home/code/
    D. scp demo.c eg1234@jserv.ru:~/code/
    E. I do not want any marks for this question.

Page 3 of 18
Turn Over/...

## 第4页

Q4. A process has been appending results to a file output.log, the full content of which currently looks like this:  
count: 1  
count: 2  
count: 2  
count: 1  
count: 3  
count: 2  
count: 2  
count: 4  
count: 1  
count: 2  

You execute the command sequence  
head -n 6 output.log | uniq | wc -l  

What would be the output?  
A. 4  
B. 5  
C. 6  
D. 8  
E. I do not want any marks for this question.  

Q5. Which of the below would redirect both standard output and standard error from the command ping 1.1.1.1 to log.txt?  
A. ping 1.1.1.1 1> log.txt 1> log.txt  
B. ping 1.1.1.1 2&1> log.txt  
C. ping 1.1.1.1 2&1 2> log.txt  
D. ping 1.1.1.1 > log.txt 2>&1  
E. I do not want any marks for this question.  

Page 4 of 18

## 第5页

Q6. Brian is writing a shellscript, part of which involves printing the contents of the current directory, but while hiding file extensions in filenames. Which of the below loops will produce the intended outcome?

A.
for file in *;
do
    echo "${file%.*}"
done

B.
for $file in $(ls);
do
    echo file
done

C.
for file in $(ls -1);
do
    echo "${file#*.}"
done

D.
for $file in *;
do
    echo "${file%.*}"
done

E. I do not want any marks for this question.

Q7. What is the result of the following command?
echo "softwaretools" | sed 's/[ftw][ar]\(\([^o]*\)o\)\+/pol\1o/'

A. sopoletetols
B. sofpolretretools
C. polsoftwaretosoftwaretoo
D. softwaretools
E. I do not want any marks for this question.

Page 5 of 18
Turn Over/...

## 第6页

Q8. Which of these grep commands would print just the lines that contain 'colour' or 'color' (ignoring case) in the file preferences.conf?  
    A. grep -v 'colou?r' preferences.conf  
    B. grep -i 'colou?r' preferences.conf  
    C. grep -i 'colou\?r' preferences.conf  
    D. grep -v 'colo\?u\?r' preferences.conf  
    E. I do not want any marks for this question.  

Q9. Which of these pattern-matching problems could not be solved with a basic regular expression?  
    A. Andy wants to match an arbitrary number of 'a' characters, then the same number of 'b' characters.  
    B. Briony wants to match a 'b' character, then exactly six characters from the set 'c,d,e', then an 'f' character.  
    C. Carl wants to match the word 'cumquat', but only when the first character of the word is incorrect.  
    D. Denise wants to match either 2 or 3 literal dot characters ('.'), followed by a word of any length, followed by a question mark.  
    E. I do not want any marks for this question.  

Q10. Harvey wants to count how many times the letter 'a' appears in file wordlist.txt. Which of the below commands would best achieve that?  
    A. grep -c 'a' wordlist.txt  
    B. wc -w wordlist.txt | grep 'a'  
    C. grep -o 'a' wordlist.txt | wc -l  
    D. grep -a wordlist.txt | wc -c  
    E. I do not want any marks for this question.  

Q11. Brian has run the following Git command: git add README.txt Which of the following statements is true?  
    A. Brian wants to edit README.txt to add extra text.  
    B. Brian has committed README.txt to the source history.  
    C. Brian has staged the README.txt file.  
    D. Brian is pulling changes to README.txt from a remote server.  
    E. I do not want any marks for this question.  

Page 6 of 18

## 第7页

Q12. Which statement best describes what a Git branch is?  
A. It is a reference to a single commit made in the past.  
B. It is a Git repository on a remote server.  
C. It is a reference to a series of Git commits that have been in a sequence.  
D. It is a single commit independent of other commits.  
E. I do not want any marks for this question.  

Q13. Who designed Git?  
A. Microsoft for their Github tool.  
B. Richard Stallman.  
C. Joseph Hallett.  
D. Linus Torvalds.  
E. I do not want any marks for this question.  

Q14. A git pull is equivalent to which other sequence of Git commands?  
A. git add then git commit  
B. git merge then git fetch  
C. git fetch then git push  
D. git fetch then git merge  
E. I do not want any marks for this question.  

Q15. When running git status you see the following message:  
Your branch and 'origin/main' have diverged and have 7 and 42 commits each respectively.  
What does it mean?  
A. Since you started work (and made 7 commits) someone else has pushed work containing 42 commits to the origin remote.  
B. Your Git repo is corrupt and you need to start again.  
C. Since you started work (and made 42 commits) someone else has pushed work containing 7 commits to the origin remote.  
D. You have only saved 7 out of the last 42 changes and may have lost work unless you commit soon.  
E. I do not want any marks for this question.  

Page 7 of 18  
Turn Over/...

## 第8页

Q16. When reading through a source file you find the following text:  
<<<<<<< HEAD  
x += 1;  
=======  
x++;  
>>>>>>> 51224257  

What is going on?  
A. This is SQL: a programming language for interacting with relational databases.  
B. There is a merge conflict. There are 51,224,257 lines of additional code that need merging.  
C. Your repo is corrupt. Restore from a backup.  
D. There is a merge conflict. Commit 51224257 is in conflict with your currently checked out code.  
E. I do not want any marks for this question.  

Q17. What is make?  
A. A shellscript to build code.  
B. A tool for converting files on the basis of rules.  
C. A library management tool for C.  
D. An obsolete configuration management tool.  
E. I do not want any marks for this question.  

Q18. Why might you want to use maven instead of make?  
A. Maven can fetch Java dependencies from remote repos.  
B. Make cannot build Java code as the compiler is incompatible.  
C. Maven is an open source project from the Apache foundation, whereas Make is closed source.  
D. Make is configured using XML which can be hard for a human to read.  
E. I do not want any marks for this question.  

Page 8 of 18

## 第9页

Q19. What does the following GNU Make patternrule say?  
%.a: %.b  
    foo $< -b $@  

A. To build a file ending with .b (for example file.b) from a file ending with .a (for example file.a) run foo file.b -b file.a.  
B. To build a file ending with .a (for example file.a) from a file ending with .b (for example file.b) run foo file.a -b file.b.  
C. To build a file ending with .a (for example file.a) from a file ending with .b (for example file.b) run foo file.b -b file.a.  
D. To build a file ending with .b (for example file.b) from a file ending with .a (for example file.a) run foo file.a -b file.b.  
E. I do not want any marks for this question.  

Q20. To compile a C source file with debugging symbols available what flag should be used with GCC or Clang?  
A. -g  
B. --help  
C. -I  
D. -0  
E. I do not want any marks for this question.  

Q21. Nigel is attempting to write a program, but it is crashing. Read the log from the shell and explain the segmentation fault.  
$ cat hello.c  
#include <stdio.h>  
int main(void) {  
    FILE *f = fopen("out.txt", "r");  
    fprintf(f, "Hello World!\n");  
    return 0;  
}  
$ make hello  
cc     hello.c   -o hello  
$ ./hello  
Segmentation fault (core dumped)  
$ strace ./hello  
execve("./hello", ["./hello"], 0x7fffeec3bee0 /* 55 vars */) = 0  
brk(NULL)                               = 0x1516000  
arch_prctl(0x3001 /* ARCH_??? */, 0x7fffeec3bfb0) = -1 EINVAL (Invalid argument)  
access("/etc/ld.so.preload", R_OK)      = -1 ENOENT (No such file or directory)  
openat(AT_FDCWD, "/etc/ld.so.cache", O_RDONLY|O_CLOEXEC) = 3  
fstat(3, {st_mode=S_IFREG|0644, st_size=125831, ...}) = 0  

Page 9 of 18  
Turn Over/Qu. continues ...

## 第10页

(cont.)

mmap(NULL, 125831, PROT_READ, MAP_PRIVATE, 3, 0) = 0x7f68e4daf000
close(3)                                  = 0
openat(AT_FDCWD, "/lib64/libc.so.6", O_RDONLY|O_CLOEXEC) = 3
read(3, "\177ELF\2\1\1\3\0\0\0\0\0\0\0\0\3\0>\0\1\0\0\0\300\250\3\0\0\0\0\0"..., 832) = 832
fstat(3, {st_mode=S_IFREG|0755, st_size=2164640, ...}) = 0
mmap(NULL, 8192, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0) = 0x7f68e4dae000
lseek(3, 808, SEEK_SET)                   = 808
read(3, "\4\0\0\0\5\0\0\0\1\0\0\0\0\0\0\0\0\2\0\0\0\0\0\0\0\300\4\0\0\0\0\0"..., 32) = 32
mmap(NULL, 4020448, PROT_READ|PROT_EXEC, MAP_PRIVATE|MAP_DENYWRITE, 3, 0) = 0x7f68e47c9000
mmap(0x7f68e4996000, 2093056, PROT_NONE) = 0
mmap(0x7f68e4b95000, 24576, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_FIXED|MAP_DENYWRITE, 3, 0x1cc000) = 0x7f68e4b95000
mmap(0x7f68e4b9b000, 14560, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_FIXED|MAP_ANONYMOUS, -1, 0) = 0x7f68e4b9b000
close(3)                                  = 0
arch_prctl(ARCH_SET_FS, 0x7f68e4dae000) = 0
mprotect(0x7f68e4b95000, 16384, PROT_READ) = 0
mprotect(0x600000, 4096, PROT_READ) = 0
mprotect(0x7f68e4daf000, 4096, PROT_READ) = 0
munmap(0x7f68e4dae000, 125831) = 0
getrandom("\x10\x0b\x5b\x2e\xcc\xf8\x3d\xc\x98\xa2", 8, GRND_NONBLOCK) = 8
brk(NULL) = 0x1516000
brk(0x1517000) = 0x1517000
brk(NULL) = 0x1517000
brk(0x1537000) = 0x1537000
openat(AT_FDCWD, "out.txt", O_RDONLY) = -1 ENOENT (No such file or directory)
--- SIGSEGV {si_signo=SIGSEGV, si_code=SEGV_MAPERR, si_addr=NULL} ---
+++ killed by SIGSEGV (core dumped) +++
Segmentation fault (core dumped)

A. Nigel is attempting to write to a file, but only opened it with read permissions.
B. Nigel compiled the program with make which used cc to compile it but the C compiler is clang.
C. Nigel cannot open out.txt because it doesn't exist.
D. The call to fopen returned a NULL pointer which was dereferenced by fprintf.
E. I do not want any marks for this question.

Page 10 of 18

## 第11页

Q22. What is gdb?  
A. A typo. You probably meant GCC the C compiler.  
B. The GNU Debugger: a program for figuring out what happens when programs run.  
C. A commandline interface to the Godbolt compiler explorer.  
D. The GNU Database: a modern relational database for running SQL commands.  
E. I do not want any marks for this question.  

Q23. When is a spreadsheet an appropriate tool to use to store important data?  
A. When you need to store large quantities of data.  
B. When you are doing double entry bookkeeping.  
C. When you are following a rigorous software engineering process.  
D. When you need to store nationally important data (such as for a national contact tracing system).  
E. I do not want any marks for this question.  

Q24. What is a composite key?  
A. A number added to a database table to uniquely identify rows.  
B. A key for a database table consisting of multiple attributes.  
C. A key for a database table consisting of multiple attributes of different types.  
D. The primary key for a database table.  
E. I do not want any marks for this question.  

Q25. How many attributes will a database table in 6NF have?  
A. 6NF places no restrictions on the number of attributes.  
B. 0  
C. 1  
D. <2  
E. I do not want any marks for this question.  

Q26. What is an INNER JOIN?  
A. A join where if a row can’t be joined to another row NULLs will be inserted.  
B. A join where the data will be glued together only on the inside (leaving a smooth exterior).  
C. A join where neither of the joining columns can be NULL.  
D. A join where the join condition must be a numeric comparison.  
E. I do not want any marks for this question.  

Page 11 of 18  
Turn Over/...

## 第12页

Q27. What does the following SQL query do:  
SELECT Movie.title  
FROM Movie  
WHERE Movie.lead = 'Keanu %'  
;  
A. It finds all of the films Keanu Reeves starred in.  
B. It searches for movies where the lead actor is Keanu %.  
C. It finds all of the films where the lead actor isn’t called Keanu.  
D. It searches for movies where the lead actor’s first name is Keanu.  
E. I do not want any marks for this question.  

Q28. What does the following SQL query do:  
SELECT Movie.title, Movie.revenue  
FROM Movie  
WHERE Movie.lead IS 'Keanu Reeves'  
ORDER BY Movie.revenue DESC  
LIMIT 3  
;  
A. It finds Keanu Reeves' top 3 films by revenue.  
B. It finds Keanu Reeves' bottom 3 films by revenue.  
C. It finds all of Keanus Reeves' films and sorts in terms of revenue.  
D. It finds 3 films staring Keanu Reeves (though which 3 is undetermined).  
E. I do not want any marks for this question.  

Q29. What is an SQL transaction?  
A. A series of queries that must be run in sequence and if any query fails then appropriate action taken.  
B. An SQL query made via a API for a different programming language.  
C. A single SQL query.  
D. Any operation which alters the state of the database.  
E. I do not want any marks for this question.  

Q30. Why might you not want to use a relational database and SQL?  
A. Your application is programmed in a different language.  
B. You are building a Track and Trace system.  
C. The data you want to store and queries you want to make are recursive in nature.  
D. The data you want to store needs to reside on a separate server.  
E. I do not want any marks for this question.  

Page 12 of 18

## 第13页

Q31. Consider the following Datalog program:
    sibling(A,B) :- parent(A, C), parent(B, C).
    parent(jo, john).
    parent(john, jean).
    parent(james, jo).
    parent(lou, john).
    parent(oliver, jo).
    parent(simon, jean).
    parent(flipsey, james).
Who is Jo's sibling?
    A. Lou
    B. Flipsey
    C. Simon
    D. James
    E. I do not want any marks for this question.

Q32. What is the command to read your system's documentation?
    A. help
    B. apropos
    C. man
    D. firefox https://openai.com/chatgpt/
    E. I do not want any marks for this question.

Page 13 of 18
Turn Over/Qu. continues ...

## 第14页

(cont.)

—Blank page—

Page 14 of 18
Qu. continues ...

## 第15页

(cont.)
—Blank page—
Page 15 of 18 Turn Over/Qu. continues ...

## 第16页

(cont.)
—Blank page—
Page 16 of 18
Qu. continues ...

## 第17页

(cont.)
—Blank page—
Page 17 of 18 Turn Over/Qu. continues ...

## 第18页

(cont.)

—Blank page—

Page 18 of 18
END OF PAPER
