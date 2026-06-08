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