# 第07周：DB Exercise

> UoB Computer Science - Java 2025
> 提取自课件 PDF，用于 AI 出题知识库

---

## 📖 主讲课：Weekly Lectures 07 OXO Debrief.md

# OXO Debrief

COMSM0086

Dr Simon Lock & Dr Sion Hannuna

---

# Aim of this session

Our aim is to provide insight into the OXO exercise
By working through JUST ONE possible solution
(Note: other approaches might be equality valid)

It is problematic to produce an "ideal" solution
(We probably couldn't agree on one anyway ;o)

Aim to provide something simple & understandable
(Which will permit the discussion of various issues)

A sensible and achievable implementation of OXO
(rather than trying to show off how "clever" we are)

---

# Driving Design Principles

- Divide and Conquer: delegate clearly defined tasks
- Granularity: short methods to aid understandability
- Simplicity: avoid unnecessarily complex control flow
- Modesty: avoid sophisticated language constructs
- Nominative Clarity: give things appropriate names

## Overall aim:

Produce a solution that everyone can understand!
Short and simple (My OXOController is 190 lines)

---

# Recap of Features

Build OXO / Tic-Tac-Toe / noughts & crosses with:

- Command Parsing & Validation
- Cell Claiming
- Dynamic Board Size
- Extendable Number of Players
- Dynamic Win Threshold
- Automated Win and Draw Detection
- Game Reset

---

# Identified Classes

Main Class: OXOGame
MVC: OXOModel, OXOView, OXOController
Exceptions: OXOMoveException (and subclasses)
Player class: OXOPlayer
Test class: OXOTests

Didn't really feel the need for any additional classes

---

# ASCII字符表

| 32 | 48 | 64 | 80 | 96 | 112 |
|----|----|----|----|----|-----|
| 33 | 49 | 65 | 81 | 97 | 113 |
| 34 | 50 | 66 | 82 | 98 | 114 |
| 35 | 51 | 67 | 83 | 99 | 115 |
| 36 | 52 | 68 | 84 | 100 | 116 |
| 37 | 53 | 69 | 85 | 101 | 117 |
| 38 | 54 | 70 | 86 | 102 | 118 |
| 39 | 55 | 71 | 87 | 103 | 119 |
| 40 | 56 | 72 | 88 | 104 | 120 |
| 41 | 57 | 73 | 89 | 105 | 121 |
| 42 | 58 | 74 | 90 | 106 | 122 |
| 43 | 59 | 75 | 91 | 107 | 123 |
| 44 | 60 | 76 | 92 | 108 | 124 |
| 45 | 61 | 77 | 93 | 109 | 125 |
| 46 | 62 | 78 | 94 | 110 | 126 |
| 47 | 63 | 79 | 95 | 111 | 127 |

06/25

---

# Command Parsing and Validation

```java
command = command.toLowerCase();
if (command.length() != 2) throw new InvalidIdentifierLengthException(command.length());
int rowNumber = convertToRowNumber(command.charAt(0));
int colNumber = convertToColNumber(command.charAt(1));
int currentPlayerNumber = gameModel.getCurrentPlayerNumber();
claimBoardCell(gameModel.getPlayerByNumber(currentPlayerNumber), rowNumber, colNumber);

private static int convertToRowNumber(char rowChar) throws InvalidIdentifierCharacterException {
    if ((rowChar < 'a') || (rowChar > 'z')) throw new InvalidIdentifierCharacterException(RowOrColumn.R
    else return rowChar - 'a';
}

private static int convertToColNumber(char colChar) throws InvalidIdentifierCharacterException, Ou
{
    if (colChar == '0') throw new OutsideCellRangeException(RowOrColumn.COLUMN, 0);
    else if ((colChar < '1') || (colChar > '9')) throw new InvalidIdentifierCharacterException(RowOrCol
    else return colChar - '1';
}

---

# Claiming Cells

Again, let's try to keep everything clean and simple
A compact multi-part IF statement to check validity
Minimise cognitive load on developer (maybe YOU)
Appropriate exception thrown if command is invalid
The final branch claims the cell for the player

```java
public void claimBoardCell( OXOPlayer player, int rowNum, int colNum ) throws OXOMoveException
{
    if( rowNum>=gameModel.getNumberOfRows() ) throw new OutsideCellRangeException( RowOrColumn.ROW
    else if( colNum>=gameModel.getNumberOfColumns() ) throw new OutsideCellRangeException( RowOrCo
    else if( gameModel.getCellOwner( rowNum, colNum ) != null ) throw new CellAlreadyTakenException
    else gameModel.setCellOwner( rowNum, colNum, player );
}

---

# Dynamic Board Size

Replace 2D array: ArrayList of ArrayLists of Players
Create top level list ("cells") to hold all the rows
For each row in board, create a new list of players
Initialise all elements in each row to null (empty)

```java
private ArrayList<ArrayList<OXOPlayer>> cells;
public OXOModel(int numberOfRows, int numberOfColumns, int winThresh) {
    winThreshold = winThresh;
    cells = new ArrayList<ArrayList<OXOPlayer>>();
    for(int i=0; i<numberOfRows ;i++) {
        ArrayList<OXOPlayer> newRow = new ArrayList<OXOPlayer>();
        for(int j=0; j<numberOfColumns ;j++) newRow.add(null);
        cells.add(newRow);
    }
}

---

# Unlimited Number of Players

Make use of an extendable ArrayList to store players
When advancing to next player, check for wrap-around

```java
private ArrayList<OXOPlayer> players;

public int getNumberOfPlayers() {
    return players.size();
}

public void addPlayer(OXOPlayer player) {
    players.add(player);
}

if(currentPlayerNumber < gameModel.getNumberOfPlayers()-1) currentPlayerNumber++;
else currentPlayerNumber = 0;
gameModel.setCurrentPlayerNumber(currentPlayerNumber);

---

# Dynamic Win Threshold

Win threshold maintained *inside* OXOModel object
No COPIES of this value kept anywhere in the code
All references to threshold call the accessor method
When central value changes, all references will see

```java
private int winThreshold;

public void setWinThreshold(int winThresh) {
    winThreshold = winThresh;
}

public int getWinThreshold() {
    return winThreshold;
}

---

# Game Reset

Reinitialise ArrayList of ArrayLists of OXOPlayers
Reset player number, winner, game drawn
Don't bother resetting size of board or win threshold

```java
public void reset() {
    cells = new ArrayList<ArrayList<OXOPlayer>>();
    for(int i=0; i<numberofRows ;i++) {
        ArrayList<OXOPlayer> newRow = new ArrayList<OXOPlayer>();
        for(int j=0; j<numberofColumns ;j++) newRow.add(null);
        cells.add(newRow);
    }
    currentPlayerNumber = 0;
    winner = null;
    gameDrawn = false;
}

---

# Win Detection

Basic principle: Scan through the board, cell by cell
Keeping a count of consecutively claimed cells

Chose NOT to be clever (1 method for all directions)
Used separate (simpler) methods for each direction
Would probably be flagged for not using DRY code !

Horizontal and Vertical lines are relatively easy
Diagonal lines are however a LOT trickier to check

Let's take a look at how I did Vertical...

---

# Example: Vertical Win Detection

Scan down through each column, checking each cell
Compare owner of cell against owner of previous cell

```java
public OXOPlayer searchForVerticalWin()
{
    for(int colNumber=0; colNumber<gameModel.getNumberOfColumns(); colNumber++) {
        int consecutiveCount = 0;
        OXOPlayer ownerOfPreviousCell = null;
        for(int rowNumber=0; rowNumber<gameModel.getNumberOfRows(); rowNumber++) {
            OXOPlayer ownerOfCurrentCell = gameModel.getCellOwner(rowNumber, colNumber);
            if(ownerOfCurrentCell == null) consecutiveCount = 0;
            else if(ownersDiffer(ownerOfPreviousCell,ownerOfCurrentCell)) consecutiveCount = 1;
            else consecutiveCount++;
            if(consecutiveCount >= gameModel.getWinThreshold()) return ownerOfCurrentCell;
            ownerOfPreviousCell = ownerOfCurrentCell;
        }
    }
    return null;
}
```

| O | X | X |
|---|---|---|
|   | O | X |
| O |   | X |

---

# Diagonal Win Detection

Diagonal Win Detection MUCH harder to implement
Need to increment both x and y at the SAME time
Must also deal with two different directions of slope
Must work for ALL board sizes (not just basic 3x3)
Might not start in corners or go through centre cell

---

# A Novel Approach

Rather than trying to solve this difficult problem...
What if we TRANSFORM it into a simpler problem ?
(a problem that we *already* have a solution for ;o)

**SmartWinDetection**

This kind of intelligent pre-processing is powerful
Think laterally - don't just brute-force a solution
Try to make your life just that little bit easier

---

# Row Shifting/Unshifting: Versatile DRY code

```java
public void indentRows(Direction direction, Action action)
{
    int rowNumber = 0;
    int sizeOfIndent = 0;
    if(direction == Direction.DOWN) rowNumber = 0;
    if(direction == Direction.UP) rowNumber = this.getNumberOfRows()-1;
    while((rowNumber>=0) && (rowNumber<this.getNumberOfRows())) {
        for(int i=0; i<sizeOfIndent ;i++) {
            if(action == Action.ADD) this.getRow(rowNumber).add(0,null);
            if(action == Action.REMOVE) this.getRow(rowNumber).remove(0);
        }
        sizeOfIndent++;
        if(direction == Direction.DOWN) rowNumber++;
        if(direction == Direction.UP) rowNumber--;
    }
}
```

17/25

---

# Automated Draw Detection

Draw detection is relatively simple:
The game is drawn when ALL cells have been filled...
Provided that no player has won the game!

---

# Code Quality Considerations

Method and Variable names are "appropriate"

Methods are simple (not overly-complex) in terms of:
- Length of methods (Lines of Code)
- Level of nesting (Number of Indentations)
- Complexity of individual lines (Length of Line)

Made use of opportunity to "farm out" common code
(In order to control complexity and ensure DRYness)

Naturally, I kept an eye on structural design
(Cohesion, Coupling, Cyclic Dependencies etc.)

---

# Test "Script"

Test scripts often ignore code quality concerns
That's fine - they aren't really part of production code
Use of reusable methods can however reduce filesize

@Test
void testBigGame() throws OXOMoveException
{
    // Test for an actual 5-in-a-row horizontal win
    checkWinnerFor(new String[]{"b1","a1","b2","a2","b3","a3","b4","a4","b5"},5,5,5,0);
    // Test for an actual 5-in-a-row diagonal win
    checkWinnerFor(new String[]{"a1","a2","b2","a3","c3","a4","d4","a5","e5"},5,5,5,0);
}

---

# Want to see how well you did ?

We will make OUR test cases available via GitHub
Drop them into the 'test' folder in your OXO project
Run in IntelliJ or on command line with 'mvnw test'
Tests cover all the key features of the exercise
See how many test cases your code is able to pass !

---

Common Problems and Issues...

22/25

---

# Common Problems and Issues

- Broken encapsulation (direct access of internal state)
- State leakage (multiple inconsistent copies of data)
- Game continues (turns can be taken) even after win
- Unconstrained resize of board (add/remove row/col)
- Not all erroneous inputs detected and prevented
- Win not always detected (with expanded board size)
- Hardwired checking of playing letter (this isn't C !)
- Limited coverage of features by your own test cases

---

# Final Comments

Hope you enjoy a nice break during reading week!
Catch up with missed tasks from past workbooks

Once we are all back from the reading week break
We will release the FINAL non-assessed exercise

Your last chance to practice before the assignment

---

Questions ?

25/25

---

## 📋 任务简报：Weekly Briefings 07 DB Briefing.md

# OOP with Java - DB Briefing

COMSM0086

Dr Simon Lock & Dr Sion Hannuna

---

# The "DB" Exercise

Aim of this exercise is to build a database server...
...from the ground up !

A complex application for you to practice your Java
A chance to explore DB content from other units
As well as gain experience using a query language

This exercise does NOT contribute to your unit mark
(In previous years it would have, but not now !)

---

# Overview of Server Operation

Your database server must operate as follows:

1. Receive incoming requests from a client (conforming to a standard query language)
2. Interrogate & manipulate a set of stored records (maintained as a persistent collection of files)
3. Return an appropriate message back to the client (Success or Failure, with data - where relevant)

---

# Data Storage

A database consists of a number of 'tables'
Each 'table' consists of a number of 'columns'
Each 'table' contains 'rows' that store 'records'

The 'tables', their 'columns' and 'record' content
should be stored as TAB separated text files

example-table.txt
example-table.tab

---

# Record IDs

First (0th) column in a table is always called 'id'
Numerical value that uniquely identifies record/row
ID values are automatically generated by the server
The IDs acts as a primary key for each record
Relationships between records use ID as reference
Note that the ID of a record should NEVER change
(or you risk breaking any relationships stored !)
No "recycling" (don't reuse the IDs of deleted rows)

---

# Communication

A minimal skeleton server is provided for you (so you don't need to worry about networking)

Server listens on port 8888 and passes incoming messages to the 'handleCommand' method

Your task: implement 'handleCommand' internals !

For simplicity, assume only a single client connects (i.e. there is no need to handle parallel queries)

---

# Query Language

Clients communicate with server using "simple" SQL:

- USE: changes the database we are querying
- CREATE: constructs a new database or table
- INSERT: adds a new record (row) to a table
- SELECT: searches for records that match a condition
- UPDATE: change existing data contained in a table
- ALTER: add or remove the columns in a table
- DELETE: removes records that match a condition
- DROP: removes a specified table or database
- JOIN: performs an INNER JOIN on two tables

---

# Defining the Query Language

To help specify our simplified query language
We have provided an "augmented" BNF grammar
BNF

We hope that you appreciate this grammar
It embodies much analysis and specification work
It was a significant challenge to create and refine !

There is also a "transcript" of typical queries
Provides examples of queries you might expect to see
transcript

---

# Error Handling

Your parser should identify errors within queries:
- queries that do not conform to the BNF
- queries attempting "illegal" actions (see workbook)

Your response to the client must begin with either:
- [OK] for valid and successful queries
  (followed by the results of the query)
- [ERROR] if there is a problem with the query
  (followed by a human-readable message)

Use exceptions to handle errors *internally*
However these should NOT be returned to the user

---

# Testing

A command-line client has been provided for you
This is really just for demonstration purposes

Development should make use of automated testing
A template test script is found in the Maven project
Add all your automated JUnit tests there as usual

Testing should target the 'handleCommand' method
(Since this is where your code has been inserted)

---

# Importance of Testing

With the advent of Gen AI tools for code creation
Testing is becoming more and more important !
(We need to validate and verify generated code)

It is essential that you improve your testing skills
(This will be assessed in the final CW assignment !)
You had better start working on this ability NOW !

The Software Engineering unit will provide guidance
We will also do an "Effective Testing" session shortly

---

Questions ?

12/20

---

# SQL whitespace variability

As with any programming language (including Java)
SQL can contain extra whitespace and still be valid
Your interpreter needs to be able to cope with this

For example, let's consider this INSERT statement:

```
INSERT INTO marks VALUES('Steve',55,TRUE);
```

How many variants are there with 1 extra space ?
all-possible-variants
generate-variants-script

---

Dealing with these can be a bit tricky !
Would you like a few extra pointers ?
(Warning: May Contain Metaphors)

---

# How do you chop an onion ?

15/20

---

# The "Computer Scientist" Approach

Select the newest, "most cutting edge" knife
Cut onion into two halves (binary chop)
Iterate through columns first (slice)
Iterate through rows next (dice)
After each cut, return chopped
onions into a heap (or stack)
(to keep working area clear)

How does that sound ?

---

Oh dear me NO !

17/20

---

You need to pull the onion out of the ground first !

Then remove roots (and any remaining soil)
Chop off the green leaves
Remove the outer layers of skin
Maybe even give it a wash
Throw it away if it looks rotten !

Only THEN try to chop it

---

# The Problem

We had assumed that the onion was "ready to go"
But the farmer and seller have done a lot of work...

Washing, Head and Tailing, Grading, Filtering etc.

All before you get your hands on the onion

---

# How does this relate to parsing SQL ?!?

Don't just "dive in" and start "slicing and dicing"
Pre-processing will save you a LOT of time & effort

We can do simple filtering / cleaning / scrubbing
In order to "normalise" the incoming commands
Get them into a standard size/shape - like onions !

If everything is similar and consistent...
It will make writing a parser a WHOLE LOT easier

BasicTokeniser

---

## 📝 练习册：Weekly Workbooks 07 DB Exercise 03 Persistent Storage slides segment 1.md

# Overview

This lecture provides an intro to the Java File API
The Classes & Methods you need to read/write files

Everything you need is part of java.io package
So at the top of your code you should add:

```java
import java.io.*;
```

(Or import the individual classes if you prefer)

---

# The File Class

Everything is based around the "File" class
This is used to represent any file in the filesystem
Providing access to information about that file
As well methods to manipulate it

---

# Directories

Directories/folders are a special type of file in Java
This makes sense in some ways...
When you list the contents of a directory:

```java
File[] documents = documentFolder.listFiles();
```

You will get back a bunch of files
(Some of which will be subdirectories)

To check if a particular file is a directory, use:

```java
someFile.isDirectory();

---

# Exceptions

Pretty much anything we attempt to do to a file can cause exceptions to be generated

As a result, everything needs to be inside a "try" And we need to catch various exceptions, including:
- IOException
- FileNotFoundException

(As appropriate to the current situation)

---

# Filenames

When accessing a file, we identify it by filename
A String composed of the name & path of the file

For example:
```
String filename = "cv.txt";
```

Paths can be relative:
```
String filename = "../documents/cv.txt";
```

Or absolute:
```
String filename = "/user/bob/documents/cv.txt";

---

# Platform Independent Separator

The problem is that the following:

```java
String name = "email/cv.txt";
```

Would only work on OSX or Linux (not Windows)

Instead we should really use:

```java
String name = "email" + File.separator + "cv.txt";
```

This will work no matter which platform we run it on
(File.separator is replaced with the correct character)

---

# Checking if a file exists

Before we attempt to do anything to a file
We should make sure that file actually exists !

This is done by creating a new instance of File class
Passing it the name of the file we are interested in:
```java
String name = "email" + File.separator + "cv.txt";
File fileToOpen = new File(name);
```

We can then check to see if this file actually exists:
```java
if(fileToOpen.exists()) {
    // Do something to the file !
}

---

# LESSON LEARNT

A File Object doesn't represent an ACTUAL file
It only represents a POTENTIAL file !

---

# Creating new Files

If the file doesn't exist, then we should create it !
Done by asking the File instance to create the file:

```java
fileToOpen.createNewFile();
```

This returns a boolean (the success of the action)
It might be worth checking this !
(You might not have write permission to the folder)

---

# Creating new Directories

If we want to create a directory instead of a file
Then we need to use the "mkdir" method:

```java
String name = "email";
File emailFolder = new File(name);
emailFolder.mkdir();
```

Or "mkdirs" to create multiple levels of folder:

```java
String name = "docs" + File.separator + "email";
File emailFolder = new File(name);
emailFolder.mkdirs();

---

# Reading and Writing

Java provides various Helper Classes to aid with IO

Offering different alternatives to access file content

The one that we will focus on makes use of:
- FileReader: Class to read data from a File
- FileWriter: Class to write data to a File

---

# FileWriter

FileWriter allows us to write chars or Strings to a file:

```java
String name = "email" + File.separator + "cv.txt";
File fileToOpen = new File(name);
FileWriter writer = new FileWriter(fileToOpen);
writer.write("Hello\n");
writer.write('a');
writer.flush();
writer.close();

---

# FileReader

FileReader allows us to read chars from a file:

String name = "email" + File.separator + "cv.txt";
File fileToOpen = new File(name);
FileReader reader = new FileReader(fileToOpen);
char[] buffer = new char[10];
reader.read(buffer, 0, buffer.length);
reader.close();

---

# More Advanced Readers and Writers

Readers and Writers are quiet low-level
And are very much reminiscent of C code

Instead, we can use some more high-level classes:
- BufferedReader
- BufferedWriter

Lets look at BufferedReader in more detail...

---

# BufferedReader

BufferedReader can read in a whole line as a String:

String name = "email" + File.separator + "cv.txt";
File fileToOpen = new File(name);
FileReader reader = new FileReader(fileToOpen);
BufferedReader buffReader = new BufferedReader(reader);
String firstLine = buffReader.readLine();
buffReader.close();

---

# Other useful methods of the File Class

- delete
- renameTo
- setReadable
- setWritable
- list
- getName
- getPath
- getParent
- length

---


## 🔑 核心知识点摘要

*（出题时参考以上各节详细内容，此处为快速索引）*

| 类型 | 文档 | 核心主题 |
|------|------|----------|
| 📖 主讲课 | Weekly Lectures 07 OXO Debrief.md | |
| 📋 任务简报 | Weekly Briefings 07 DB Briefing.md | |
| 📝 练习册 | Weekly Workbooks 07 DB Exercise 03 Persistent Storage slides segment 1.md | |
