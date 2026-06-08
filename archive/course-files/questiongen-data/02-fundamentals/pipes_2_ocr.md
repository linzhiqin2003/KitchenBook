# pipes_2.pdf OCR 结果

## 第1页

Pipes 2
COMS10012 / COMSM0085
Software Tools

## 第2页

redirects

## 第3页

redirect  
$ cat infile | sort > outfile  
infile  
cat  
sort  
outfile

## 第4页

redirect
$ sort < infile > outfile
infile
sort
outfile

## 第5页

redirect

$ COMMAND > FILE  
FILE  
overwrites

$ COMMAND >> FILE  
FILE  
appends to

5

## 第6页

error redirect

$ COMMAND > FILE 2> FILE2
$ COMMAND > FILE 2>&1

not:
$ COMMAND 2>&1 > FILE

ignore output:
$ COMMAND > /dev/null

## 第7页

files vs streams

A program that uses a standard stream can be told to use a file instead by

• PROGRAM < FILE (standard input)
• PROGRAM > FILE (standard output)
• PROGRAM 2> FILE (standard error)

7

## 第8页

files vs streams

A program that expects a filename can be told to use standard input/output instead by:

• using the filename -(single dash), if the program supports it
• using the filename /dev/stdin etc., if your OS supports it

8

## 第9页

Filenames with dashes  
Filenames starting with dashes are generally considered bad.  
If you really want to address one (e.g. you created one by mistake), use e.g.  
$ cat ./ -  
$ rm ./ -f

## 第10页

advanced

## 第11页

tee  
$ ls | tee FILE  
tee: takes a filename as argument and writes a copy of input to it, as well as to stdout  
11

## 第12页

pagers  
$ 1s | less  

less is a pager: it displays text on your screen, one page at a time.  

• Up/Down arrows scroll,  
• Space/Enter advance a page,  
• / (forward slash) opens a search,  
• q quits.  

This takes direct control of the screen (terminal).  

12

## 第13页

sed

$ echo "Hello World" | sed -e 's/World/Universe/'
Hello Universe

sed stands for stream editor – it can change text using a regular expression as it passes from input to output.

s/ONE/TWO/ [g] replaces the first match for ONE (all matches, with /g) with TWO. Regular expressions are supported.

13

## 第14页

need a file, want a pipe  
If PROGRAM wants a file to read from, how can I pipe something in?  

$ PROGRAM <(SOMETHING)  

$ cat <(echo "Hi")  
Hi  

$ echo <(echo "Hi")  
/dev/fd/63  

14

## 第15页

subshell
$ cat <(echo "Hi")
echo
/dev/fd/...
cat

## 第16页

subshell to argument

$ COMMAND $(SOMETHING)

$ echo $(echo Hi | sed -e s/Hi/Hello/)
Hello

old-fashioned way, with backticks:
$ COMMAND `SOMETHING`

16
