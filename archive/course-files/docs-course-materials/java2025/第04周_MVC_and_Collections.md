# 第04周：MVC and Collections

> UoB Computer Science - Java 2025
> 提取自课件 PDF，用于 AI 出题知识库

---

## 📖 主讲课：Weekly Lectures 04 Thinking in Objects.md

# Thinking in Objects

COMSM0086

Dr Simon Lock & Dr Sion Hannuna

---

# Aim of this Session

The aim of this session is to provide guidance on:
"How to *Think* in Objects"
(and stop thinking in terms of functions ;o)

Whilst at the same time encouraging you to:
"Harness the Power of Object Orientation"

---

# Why this ? Why now ?

You are familiar with fundamental programming (from your previous studies on the C unit in TB1)

So far this TB we've implemented trivial exercises Next workbook involves building a REAL application

Going from an abstract description of a problem... to a GOOD *Object Oriented* solution is NOT easy !

This is where the guidance in this session will help

---

# Identifying Classes

First challenge we face is identifying suitable Classes  
In order to partition code into various source files

A question that students often ask is:  
"How do I identify GOOD classes ?"

The truthful answer to this question is probably:  
"Practice and Experience"

However, this answer feels a bit like the old joke...

---

# Carnegie Concert Hall - New York

Lost Tourist: How do I get to Carnegie Hall ?

05/23

---

# Carnegie Concert Hall - New York

Lost Tourist: How do I get to Carnegie Hall ?
Passing Pianist: Practice !

06/23

---

# Some Real Help ?

But that answer isn't much help in learning OOP !

Identifying suitable classes is a DIFFICULT task
Involves knowledge, understanding and creativity

There is no "one right answer"...
But there are "good choices" & "not so good choices"

Here are a few simple tips for identifying classes...

---

# Identifying Suitable Classes

Collect key entities ('nouns') from 'problem domain'
Student, Triangle, Colour, Board, Player, Location

Collect key entities ('nouns') from 'solution domain'
LookupTable, NameValuePair, AddressServer, LinkedList

Collect key jobs/tasks/roles from BOTH domains
Include these as "doer" classes (my word ;o)
(they "do" things & their names often end in "er")

FileParser, DataLoader, CommandHandler, ReportGenerator

---

# Incremental Identification

Don't expect to identify ALL classes *in advance*
Some classes 'emerge' during iterative development

Be prepared to refactor project as code expands:
- Splitting classes when they get complex/incoherent
- Merging multiple classes when commonalities arise
- Creating additional class when new feature won't fit
- Wholesale restructuring when things turn ugly !!!
'Design Patterns' can help suggest suitable structure
(although we haven't really covered these yet ;o)

---

# Inheritance

Look out for opportunities to use inheritance!
BUT be careful NOT to overuse it!!!

Unit assignments are designed to involve inheritance
(so you can gain experience applying the concept)
Real-world opportunities for use are far less common

You'll frequently need to extend existing hierarchies
The need to create your own hierarchy is less common
(unless you are building frameworks for others to use)

---

# Illustrative Example

Let us consider a simple example application...
A graphical visualisation of GitHub groupwork:

Each project involves 3-5 student contributors
We can generate reports on contributor activity
(code commits, pull requests, change reviews etc.)

Reports are exported as separate JSON documents
These are then imported into our application
This then generates graphical representations

GitHub Activity -> JSON Reports -> Graphic Visuals

---

# 12/23

Viv (vv12345)

Una (uu12345)

Tom (tt12345)

---

# Implementation

First let us explore a function-oriented implementation
This was written in Java using the Processing platform
Makes good use of Processing graphics libraries !

YES

It is perfectly possible to write valid Java code,
that TOTALLY ignores Object Oriented constructs

Don't try to understand all the code (not important)
Just try to appreciate organisational structure !

MondrianFunctional

---

# Summary of Function Calling Patterns

setup >> scanForProjectReports

draw >> drawAllStudentsInGroup...
>> drawSingleStudent...
>> getValueOfMetric

keyPressed >> loadPreviousReport >> loadJSONObject

keyPressed >> loadNextReport >> loadJSONObject

---

# Reflection on the code

The code works fine and does the job as intended...
BUT it is NOT Object Oriented in structure:
- It has centralised control (one file controls all)
- There is limited delegation of responsibility
- It makes use of globals and much flow of data
- There are tight linkages between functions

Let's refactor this code to be more Object Oriented
(which, in the end, is what we are here to learn)
Also an opportunity to explore some OO concepts
Make use of Java "power" features along the way

---

# Analysis: Proposed Classes

There are two key entities from application domain:
- Project: Encapsulates details of a specific repository
- Student: Encapsulates details of individual students

A data structure for ALL projects would be useful:
- ProjectList: "array" of project objects (not strings!)

Also a "doer" class to scan for available reports:
- ProjectScanner: returns all reports in specified folder

MondrianObjectOriented

---

# Main Class

A main class exists to start up the whole application
This class is relatively simple - it just deals with:
- Setting up key parameters (window size, font etc.)
- Kicking off the scanner to look for project reports
- Drawing graphics (actually delegated to other classes)
- Handling of key presses from user (next/previous)

A very short source file (only about 25 lines)
Nice and simple - pretty easy to understand !

---

# OO Concepts: Student and Project Classes

## Delegated Responsibility
Both load JSON and populate their internal variables
Both classes are responsible for drawing themselves

## Abstraction and Encapsulation
Advanced features are "hidden away" inside classes
For example: just-in-time loading and caching of data:
```
if (name==null) loadProjectData();
text(name, 7, 18);

---

# OO Concepts: ProjectList Class

## Abstraction and Encapsulation
Internally deals with creating & managing iterators
Internally handles checking existence of next/prev

## Inheritance and Reuse
Extends and inherits methods from ArrayList
Adds 'getCurrent' method (not provided by ArrayList)

## Extension and Method Augmentation
Methods "wrapped" within more descriptive names
(e.g. "next" becomes "moveToNextProject")

---

# OO Concepts: ProjectScanner Class

A "doer" utility class to scan for project reports
Returns array of Project objects loaded from filesystem

## Abstraction and Encapsulation
Messy details of File IO "hidden away" inside class

## Cohesion
ProjectScanner class focuses only on low-level File IO
Could be expanded with other File IO features later ?

---

# A Few Additional Notes

Function-style methods are still useful in OO code (e.g. 'loadStudentData' and 'getValueOfMetric')
Sometimes function-orientation is a good approach !

We have embedded "doers" inside "key entities":
The Student class represents the Student entity...
...but also implements drawing & JSON data parsing

In a more complex application, we might choose
to split these out into a number of separate classes
Remember: Development is iterative and dynamic !

---

# Complexity

You could argue that we've increased complexity of the code by creating multiple additional class files (some classes are small and contain very little code)

On the positive side, code is logically organised...
It is clear where various features should be located

The whole application is currently quite simplistic (we removed some features from the *real* code)

After a few more iterations it could become complex
We'd soon be grateful for a well-organised structure

---

Try to employ some of these ideas
when writing your own code !

---

## 📋 任务简报：Weekly Briefings 04 OXO Briefing.md

# OXO Exercise Briefing

COMSM0086

Dr Simon Lock & Dr Sion Hannuna

---

# Before we begin: Shapes Exercise Recap

A few people asked to see sample solution of Shapes Simple exercise, but worth spending time reviewing

We won't be looking at every single line of code
A lot of it is fairly straightforward and uninteresting

A few novel features and notable characteristics
Let's focus on just those (in no particular order)...

---

# Overriding and Chaining

ALL 'TwoDimensionalShapes' will have a colour
Specific shapes however have different geometry
Where should we implement 'toString' method ?

```java
abstract class TwoDimensionalShape {
    private Colour shapeColour;

    public String toString() {
        return "This shape is " + shapeColour;
    }
}

class Triangle extends TwoDimensionalShape implements MultiVariantShape {
    public String toString() {
        return "Triangle with sides " + first + "," + second + "," + third + ". " + super.toString();
    }
}

---

# Multiple Constructors: With Chaining !

```java
class Triangle extends TwoDimensionalShape implements MultiVariantShape {
    private int first;
    private int second;
    private int third;
    private TriangleVariant variant;
    static int population;

    public Triangle(int first, int second, int third) {
        this.first = first;
        this.second = second;
        this.third = third;
        variant = identifyTriangleVariant();
        population++;
    }

    public Triangle(int first, int second, int third, Colour colour) {
        this(first, second, third);
        super.setColour(colour);
    }
```

04/27

---

# Triangle Variants

We already have a method to return the longest side
It's sometimes useful to know the shortest two sides
For example, when checking right-angled triangles:
$ \text{square of hypotenuse} == \text{sum of squares of other 2 sides} $

You could add 'getShortestSide' and 'getMedianSide'
OR store sides sorted by length (e.g. in an array)
I chose something different - trying to be clever...

---

# Variant Identification: One line each !

```java
int longestSide = getLongestSide(first, second, third);
// sumOfAllSides needs to be long to avoid int overflow problems
long sumOfAllSides = ((long)first) + ((long)second) + ((long)third);
// Check for "bad" variants first (otherwise we might classify it as "good" triangle first)
if((first<=0) || (second<=0) || (third<=0)) return TriangleVariant.ILLEGAL;
// Could have been `sumOfAllSides == longestSide*2` but risks overflowing due to large numbers
else if(sumOfAllSides/2.0 == longestSide) return TriangleVariant.FLAT;
// Could have been `sumOfAllSides < longestSide*2` but risks overflowing due to large numbers
else if(sumOfAllSides/2.0 < longestSide) return TriangleVariant.IMPOSSIBLE;
// Relatively straight-forward (and reliable) to check that all sides are equal
else if((first==second) && (second==third)) return TriangleVariant.EQUILATERAL;
// Isosceles check appears late - triangle might have two identical sides, but still be "bad"
else if((first==second) || (second==third) || (third==first)) return TriangleVariant.ISOSCELES;
// Checking for right-angle triangles is a bit complex, so "farm it out" to a separate method
else if(isRightAngle(first,second,third)) return TriangleVariant.RIGHT;
// Scalenes should be near the bottom because the test for them is a bit "loose"
else if((first!=second) && (second!=third) && (third!=first)) return TriangleVariant.SCALENE;
// Otherwise, we don't know what type it is (theoretically, we shouldn't actually get here !)
else return null;
```

06/27

---

# Right-Angles: avoiding square-root & overflow

```java
private boolean isRightAngle(int first, int second, int third) {
    int longestSide = getLongestSide(first, second, third);
    long firstSquared = ((long)first) * ((long)first);
    long secondSquared = ((long)second) * ((long)second);
    long thirdSquared = ((long)third) * ((long)third);
    long longestSquared = ((long)longestSide) * ((long)longestSide);
    return (- longestSquared + firstSquared + secondSquared + thirdSquared) == longestSquared;
}

private int getLongestSide(int a, int b, int c) {
    int largest = a;
    if(b>largest) largest = b;
    if(c>largest) largest = c;
    return largest;
}

---

Moving on to this week's exercise...

08/27

---

# OXO

Next TWO workbooks focus on a single application
Aim is to build a noughts-and-crosses (OXO) game
It's a fairly easy activity (easier than later ones ;o)
This is NOT an assessed exercise
Let's take a look at the key features...

---

# Model View Controller

We will often mention 'Design Patterns' in this unit
First pattern we encounter is 'Model-View-Controller'
Useful for structuring interactive UI applications
Approach is to split application into 3 'components':
- Model: the core application 'state' data
- View: the bit that the user sees (GUI or text)
- Controller: interprets events and makes decisions
This separation makes change and evolution easier

---

# MVC for OXO

## Model
Game State

## View
Playing Board

## Controller
Management & Rules

## OXOGame
User Input Handling

### Domain
### Rendering Logic
### Display
### Event Handling Logic

---

# Fill in the gaps

A Maven template project has been provided for you

Already implemented are:
- OXOModel: Game State from the OXO domain
- OXOView: Provides 'Rendering Logic' and 'Display'
- OXOGame: Main window (that receives user input)

OXOController is empty: your task is to complete it !
You must call methods of OXOModel to change state
You don't need to interface directly with OXOView
(it monitors OXOModel and updates automatically)

---

# What does Game State 'Model' consist of ?

- The set of players currently playing the game
- The "owner" of each cell in the game grid
- The player whose turn it currently is
- The number in-a-row required to win
- If the game has been drawn
- The winner of the game
(If there currently is one)

---

# OXOView

|     | 1   | 2   | 3   |
|------|-----|-----|-----|
| a    | X   |     |     |
| b    |     | O   |     |
| c    |     |     | X   |

14/27

---

# OXOGame

Key feature of Java: 'Write Once, Run Everywhere'
Main window looks *similar* on different platforms

Player X's turn
Player X's turn
Player X's turn

---

# Playing the Game

Players take it in turns to make their chosen move
Entering cell identifier into OXOGame GUI window
Consists of row letter and column number (e.g. b2)
Inputted cell ID then passed to OXOController via:
`public void handleIncomingCommand(String command)`
Your task: interpret identifier & update game state

run-demo

---

# Key Game Features

---

# Win Detection

There is no point playing, if no one actually wins!
It is the Controller's job to detect when a win occurs
It MUST be able to check for wins in ALL directions:
horizontally / vertically / diagonally

Note: win detection MUST work on grids of ANY size
Not just the standard 3x3 board!
The reason for this is...

---

# Dynamic Board Size

It would be nice to alter board size during a game
If it became clear a game was going to be a draw
(all blank cells have been used but no one has won)
Increasing the board size allows play to continue
This has implications for the storage of game state
You will need to update OXOModel so that it uses...

---

# 'ArrayList' (from 'Collections' package)

For a 3x3 game you must instantiate FOUR ArrayLists

---

# Next week

The NEXT workbook will focus on error handling
Namely: what if the user inputs a "bad" cell ID ?
Don't worry about this for the time being
Assume all user inputs are correct/acceptable

We'll also add some additional "fun" extensions !

---

# Automated Testing

Game is complex enough to need automated testing
(Manual testing quickly becomes slow and tedious)

As 'developers' it is YOUR job to write tests scripts
It is not "fun" and it is not particularly "rewarding"
However, it is responsibility of mature professionals

You have been provided with a skeleton test script
Populate this with a comprehensive set of test cases
Focus on testing OXOController (i.e. your code !)

ExampleControllerTests

---

# Warning: There are Lambdas !

Example test script contains some unusual syntax:

```assert(Exception.class, () -> handleIncomingCommand());
```

Lambda operator -> is something we have not actually covered yet

Operates like an inline function

Allows us to pass CODE "into" an already existing method

More on this NEXT week !

---

# Full Set of Test Cases

We have a (fairly) comprehensive set of test cases
However, we won't let you see these just yet ;o)
It's good to experience writing your own test cases

We'll release OUR test file near end of the exercise
You'll be able to check how well your code is written
(And how comprehensive YOUR tests cases were !)

---

# Note regarding 'Serialization'

Some classes we have provided in the project:
- implement the 'Serializable' interface and...
- have a private attribute called 'serialVersionUID'

```java
public class OXOController implements Serializable {
    @Serial private static final long serialVersionUID = 1;
}
```

GUI applications written in Java require the above so that the application can be stored ('serialized')

We won't be doing any serialization in this exercise
We still need these, or we'll get compiler warnings

---

To Work !

26/27

---

## 📝 练习册：Weekly Workbooks 04 MVC and Collections 02 Model View Controller slides segment 1.md

# Model-View-Controller: The Model

## Model

Data, logic  
business rules

### Domain

### Rendering Logic

### Display

### Event Handling Logic

slide content courtesy of N Wu

Object-Oriented Programming | University of Bristol

---

# Model-View-Controller: The View

## Model
Data, logic business rules

## View
User interface, text, checkboxes

## Domain

## Rendering Logic

## Display

## Event Handling Logic

slide content courtesy of N Wu

Object-Oriented Programming | University of Bristol

---

# Model-View-Controller: The Controller

## Model
Data, logic business rules

## View
User interface, text, checkboxes

## Controller
keystrokes, mouse movement and clicks

Rendering Logic
Display
Event Handling Logic
Domain

slide content courtesy of N Wu

Object-Oriented Programming | University of Bristol

---

## 📝 练习册：Weekly Workbooks 04 MVC and Collections 04 Dynamic Board Size deep segment 1.md

# Stacks of ‘Known Type’

- if a mistake is made with downcasting we can only see this problem at runtime
- the ‘downcasting problem’ was solved by the introduction of generics in Java 5
- generics allow the compiler to keep track of object types at compile time, rather than relying on the programmer
- with generics we can, using `<...>`, parameterise classes with types, which removes the need for uncontrolled downcasting

class ArrayStack<V> implements Stack<V> {
    Object[] stack;
    int size;
    final int N;

    ArrayStack() {
        N = 100;
        stack = new Object[N];
        size = 0;
    }

    public void push(V x) {
        assert (size < 100);
        stack[size] = x;
        size = size + 1;
    }

    public V pop() {
        assert (size > 0);
        @SuppressWarnings("unchecked")
        V result = (V) stack[size-1];
        size = size - 1;
        return result;
    }

    public V peek() {
        assert (size > 0);
        @SuppressWarnings("unchecked")
        V result = (V) stack[size-1];
        return result;
    }

    public boolean empty() {
        return (size == 0);
    }
}

interface Stack<V> {
    void push(V x);
    V pop();
    V peek();
    boolean empty();
}

classes and interfaces can be parameterised with types, which can be used as consistent, but unknown (when writing your class) types within them

these casts are now under control – we know the casts will always work locally since ‘push’ only allows objects of type V on the stack in the first place

cast-free!

class StackWorld {
    public static void main (String[] args) {
        ...
        Stack<Robot> stack = new ArrayStack<Robot>();
        stack.push(new Robot("C3PO"));
        stack.push(new TranslationRobot("a"));
        stack.push(new CarrierRobot());
        System.out.println(stack.pop().name);
        System.out.println(stack.pop().name);
        System.out.println(stack.peek().name);
    }
}

---

## 📝 练习册：Weekly Workbooks 04 MVC and Collections 04 Dynamic Board Size slides segment 1.md

# Object Stacks

- a stack allows elements to be put onto (push) and removed from (pop) the top of a list of elements
- an extra operation could be peek, that allows to get a reference to the top element without removal
- an operation empty could check if there are no elements on the stack
- the interface ObjectStack defines an interface for this behaviour for a list of Objects
- one can implement such a stack in many ways, e.g. using arrays as shown on the left

## Object-Oriented Programming | University of Bristol

```java
class ArrayObjectStack implements ObjectStack {
    Object[] stack;
    int size;
    int N;

    ArrayObjectStack() {
        N = 100;
        stack = new Object[N];
        size = 0;
    }

    public void push(Object x) {
        assert (size < 100);
        stack[size] = x;
        size = size + 1;
    }

    public Object pop() {
        assert (size > 0);
        Object result = stack[size-1];
        size = size - 1;
        return result;
    }

    public Object peek() {
        assert (size > 0);
        Object result = stack[size-1];
        return result;
    }

    public boolean empty() {
        return (size == 0);
    }
}
```

```java
interface ObjectStack {
    void push(Object x);
    Object pop();
    Object peek();
    boolean empty();
}
```

objects of class Object reside on this stack; since Object is super class to any class, this stack allows any objects (even mixed!) as elements of it

assertions make sure that any preconditions on running the method successfully hold - they can get erased during runtime

---

# Downcasting

- when retrieving objects from our ObjectStack we need to ‘turn them’ from type Object to the type we expect in order to access particular members – this is called ‘casting’

- it is implemented using the (TargetClass) notation in front of the object to be cast

class ArrayObjectStack implements ObjectStack {
    Object[] stack;
    int size;
    int N;

    ArrayObjectStack() {
        N = 100;
        stack = new Object[N];
        size = 0;
    }

    public void push(Object x) {
        assert (size < 100);
        stack[size] = x;
        size = size + 1;
    }

    public Object pop() {
        assert (size > 0);
        Object result = stack[size-1];
        size = size - 1;
        return result;
    }

    public Object peek() {
        assert (size > 0);
        Object result = stack[size-1];
        return result;
    }

    public boolean empty() {
        return (size == 0);
    }
}

interface ObjectStack {
    void push(Object x);
    Object pop();
    Object peek();
    boolean empty();
}

casting may create exceptions if we try to cast to a target that cannot be achieved

A Dog is not a Robot!

class StackWorld {
    public static void main (String[] args) {
        ObjectStack oStack = new ArrayObjectStack();
        oStack.push(new Robot("C3PO"));
        oStack.push(new TranslationRobot("a"));
        oStack.push(new CarrierRobot());
        //oStack.push(new Dog()); //will break the first cast!
        System.out.println(((Robot)oStack.pop()).name);
        System.out.println(((Robot)oStack.pop()).name);
        System.out.println(((Robot)oStack.peek()).name);
    }
}

cast of the object retrieved via peek to a Robot – the programmer is in charge to make sure the cast can be made

---

## 📝 练习册：Weekly Workbooks 04 MVC and Collections 04 Dynamic Board Size slides segment 2.md

# Java Collections

- a Collection is a container that groups multiple elements into a single unit
- the Java Collection framework (JCF) is one of the most important ones in all of Java's libraries, providing high performance implementations
- it uses generics to be flexible w.r.t. element types contained, and it is also polymorphically structured, so the same methods work on different collections

## Interfaces of the Collections Framework

```
<<interface>> Iterable<T>
       |
       v
<<interface>> Collection<E>
       |
       +-- <<interface>> Set<E>
       |       |
       |       +-- <<interface>> SortedSet<E>
       |
       +-- <<interface>> List<E>
       |
       +-- <<interface>> Queue<E>
       |       |
       |       +-- <<interface>> BlockingQueue<E>
       |
       +-- <<interface>> Map<K,V>
       |       |
       |       +-- <<interface>> SortedMap<K,V>
       |       |
       |       +-- <<interface>> ConcurrentMap<K,V>
```

Overview by Ray Toal

Object-Oriented Programming | University of Bristol

---

# The Collections Framework

<<interface>> Iterable<T>
    |
    |--- <<interface>> Collection<E>
            |
            |--- <<interface>> Set<E>
            |       |
            |       |--- <<interface>> SortedSet<E>
            |               |
            |               |--- TreeSet<E>
            |               |
            |               |--- HashSet<E>
            |               |       |
            |               |       |--- LinkedHashSet<E>
            |               |
            |               |--- EnumSet<E>
            |               |
            |               |--- CopyOnWriteArraySet<E>
            |
            |--- <<interface>> List<E>
                    |
                    |--- <<interface>> SortedSet<E>  <!-- 重复，应为 SortedList<E> 或其他，但图中如此 -->
                    |       |
                    |       |--- TreeSet<E>  <!-- 重复，应为 TreeList<E> 或其他，但图中如此 -->
                    |       |
                    |       |--- ArrayList<E>
                    |       |
                    |       |--- Vector<E>
                    |       |
                    |       |--- CopyOnWriteArrayList<E>
                    |
                    |--- <<interface>> Queue<E>
                            |
                            |--- <<interface>> BlockingQueue<E>
                                    |
                                    |--- PriorityBlockingQueue<E>
                                    |
                                    |--- DelayQueue<E>
                                    |
                                    |--- SynchronousQueue<E>
                                    |
                                    |--- ArrayBlockingQueue<E>
                                    |
                                    |--- LinkedBlockingQueue<E>
                            |
                            |--- PriorityQueue<E>
                            |
                            |--- ConcurrentLinkedQueue<E>
            |
            |--- <<interface>> Map<K,V>
                    |
                    |--- <<interface>> SortedMap<K,V>
                            |
                            |--- TreeMap<K,V>
                    |
                    |--- <<interface>> ConcurrentMap<K,V>
                            |
                            |--- ConcurrentHashMap<K,V>
                    |
                    |--- HashMap<K,V>
                            |
                            |--- LinkedHashMap<K,V>
                            |
                            |--- WeakHashMap<K,V>
                            |
                            |--- IdentityHashMap<K,V>
                            |
                            |--- EnumMap<K,V>
                            |
                            |--- Hashtable<K,V>

Overview by Ray Toal

Object-Oriented Programming | University of Bristol

---

# HashMap Interlude

Object-Oriented Programming | University of Bristol

---

# Example Usage: The List<T> Interface

## import of the right package
```java
import java.util.*;
```

## simple for-loop to iterate through the set
```java
for (Robot robot : list) {
    System.out.print(robot.name+',');
}
```

## construct list object (with type inference)
```java
List<Robot> list = new ArrayList<>();
```

## adding elements
```java
list.add(c3po);
list.add(new CarrierRobot());
list.add(1, new Robot("C4PO"));
```

## element removal
```java
Robot removed = list.remove(2);
```

## «interface» List<E>
| Method | Description |
|--------|-------------|
| `+ boolean add(int index, E)` | Adds the specified element at the specified position in this list. |
| `+ boolean addAll(int index, Collection<E>)` | Inserts all the elements in the specified collection into this list, starting at the specified position. |
| `+ void clear()` | Removes all elements from this list. |
| `+ boolean contains(Object o)` | Returns true if this list contains the specified element. |
| `+ boolean containsAll(Collection c)` | Returns true if this list contains all of the elements of the specified collection. |
| `+ E get(int index)` | Returns the element at the specified position in this list. |
| `+ int indexOf(Object o)` | Returns the index of the first occurrence of the specified element in this list, or -1 if this list does not contain the element. |
| `+ int lastIndexOf(Object o)` | Returns the index of the last occurrence of the specified element in this list, or -1 if this list does not contain the element. |
| `+ E remove(int index)` | Removes the element at the specified position in this list. |
| `+ E set(int index, E)` | Replaces the element at the specified position in this list with the specified element. |
| `+ Iterator<E> iterator()` | Returns an iterator over the elements in this list in proper sequence. |
| `+ ListIterator<E> listIterator()` | Returns a list iterator over the elements in this list (in proper sequence). |
| `+ List<E> subList(int fromIndex, int toIndex)` | Returns a view of the portion of this list between the specified fromIndex, inclusive, and toIndex, exclusive. |
| `+ int size()` | Returns the number of elements in this list. |
| `+ boolean isEmpty()` | Returns true if this list contains no elements. |

```java
class ListWorld {
    static void printList(List<Robot> list) {
        System.out.print("List is:");
        for (Robot robot : list) {
            System.out.print(robot.name+',');
        }
        System.out.println("");
    }

    public static void main(String args[]) {
        List<Robot> list = new ArrayList<>();
        Robot c3po = new Robot("C3PO");
        list.add(c3po);
        list.add(new CarrierRobot());
        printList(list);
        list.add(1, new Robot("C4PO"));
        printList(list);
        Robot removed = list.remove(2);
        System.out.println("Removed:"+removed.name);
        printList(list);
        System.out.println("C3PO in list?:"+list.contains(c3po));
        list.addAll(0,list);
        printList(list);
    }
}
```

List is:C3PO,Standard Model,
List is:C3PO,C4PO,Standard Model,
Removed:Standard Model
List is:C3PO,C4PO,
C3PO in list?:true
List is:C3PO,C4PO,C3PO,C4PO,

Object-Oriented Programming | University of Bristol

---


## 🔑 核心知识点摘要

*（出题时参考以上各节详细内容，此处为快速索引）*

| 类型 | 文档 | 核心主题 |
|------|------|----------|
| 📖 主讲课 | Weekly Lectures 04 Thinking in Objects.md | |
| 📋 任务简报 | Weekly Briefings 04 OXO Briefing.md | |
| 📝 练习册 | Weekly Workbooks 04 MVC and Collections 02 Model View Controller slides segment 1.md | |
| 📝 练习册 | Weekly Workbooks 04 MVC and Collections 04 Dynamic Board Size deep segment 1.md | |
| 📝 练习册 | Weekly Workbooks 04 MVC and Collections 04 Dynamic Board Size slides segment 1.md | |
| 📝 练习册 | Weekly Workbooks 04 MVC and Collections 04 Dynamic Board Size slides segment 2.md | |
