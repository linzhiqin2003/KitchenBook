# 第10周：STAG Assignment

> UoB Computer Science - Java 2025
> 提取自课件 PDF，用于 AI 出题知识库

---

## 📖 主讲课：Weekly Lectures 10 Visitor Pattern.md

Department of Computer Science
University of Bristol

COMSM0086 – Object-Oriented Programming

# POLYMORPHISM
## AND VISITOR

Sion Hannuna | sh1670@bris.ac.uk
Sion Lock | simon.lock@bris.ac.uk

---

# Object-Oriented Programming

“Polymorphism is very useful for practical programming because it allows the uniform manipulation of objects of different, but related sub-classes using methods of a common super-class.”

Jürgen Winkler

---

# RECAP: ABSTRACT CLASSES

---

# Abstract Classes, Abstract Methods

- to prevent us from making instances of a class we apply the abstract keyword to the class
- abstract classes are often ones that are purely conceptual without any instances (e.g. a mammal, a generic Shape, an AbstractRobot)

```java
abstract class AbstractRobot extends Robot {
    abstract void greet(AbstractRobot other);
    abstract void greet(TranslationRobot other);
    abstract void greet(CarrierRobot other);
}
```

- no instance of AbstractRobot is ever allowed
- abstract methods provide no implementation in the class, however, sub-classes may provide implementations

- usually an abstract class contains abstract methods, that is methods which are declared, but supply no implementation (any non-abstract sub-class is forced to implement all these methods)
- a class with one or more abstract methods must be declared abstract itself

Object-Oriented Programming

---

# RECAP: POLYMORPHISM

---

# Recap: Sub-Classing & Polymorphism

- a sub-class can be understood as a sub-type that supports both inheritance (i.e. sub-classes receive all features for free from the parent) and polymorphism (i.e. features of sub-classes can be used in place of a feature of a class)

‘extends’ signals inheritance from Robot class

SUB-CLASS = SUB-TYPE with INHERITANCE + POLYMORPHISM

a reference can point to an object of a sub-class of the reference type

Object-Oriented Programming

---

# RECAP: DOUBLE / MULTIPLE DISPATCH

---

# Double Dispatch

- if we want to make the selection of method dynamic in more than one type we need to implement multiple dispatch
- Java does not explicitly supply a single mechanism for it
- however, we can be cunning and utilise single dispatch twice
- to do this, we need to dynamically dispatch on a receiver as before, but also turn the otherwise static parameter of the call into a dynamic receiver itself within the method that is dynamically dispatched

## AbstractRobot.java
```java
abstract class AbstractRobot extends Robot {
    abstract void greet(AbstractRobot other);
    abstract void greet(TranslationRobot other);
    abstract void greet(CarrierRobot other);
}
```

## CarrierRobot.java
```java
class CarrierRobot extends AbstractRobot {
    ...
    void greet(TranslationRobot other) {
        talk("'Hello from a TranslationRobot to a CarrierRobot.'");
    }
    void greet(CarrierRobot other) {
        talk("'Hello from a CarrierRobot to another.'");
    }
    void greet(AbstractRobot other) {
        other.greet(this);
    }
}
```

## TranslationRobot.java
```java
public class TranslationRobot extends AbstractRobot {
    ...
    void greet(TranslationRobot other) {
        talk("'Hello from a TranslationRobot to another.'");
    }
    void greet(CarrierRobot other) {
        talk("'Hello from a CarrierRobot to a TranslationRobot.'");
    }
    void greet(AbstractRobot other) {
        other.greet(this);
    }
}
```

## DispatchWorld.java
```java
class DispatchWorld {
    public static void main (String[] args) {
        AbstractRobot c3po = new TranslationRobot("e");
        AbstractRobot c4po = new TranslationRobot("o");
        AbstractRobot c5po = new CarrierRobot();
        AbstractRobot c6po = new CarrierRobot();
        c3po.greet(c4po);
        c5po.greet(c4po);
        c4po.greet(c5po);
        c5po.greet(c6po);
    }
}
```

different options are selected during runtime

2nd dispatch dynamically using the incoming parameter

1st dispatch dynamically on receiver

---

# VISITORS

( ... A FIRST MEETING WITH THE ‘PATTERN’ FAMILY ... )
( ... STANDARD SOLUTIONS TO COMMON PROBLEMS ... )

---

# How is the Visitor Pattern useful?

The Visitor Pattern facilitates the addition of new operations to existing object structures without modifying those structures (maybe look up open closed principle).

A visitor class is created that implements all of the appropriate specializations.

The visitor takes the instance reference as input, and implements the goal through double dispatch.

Object-Oriented Programming

---

# A Version of the Visitor Pattern

abstract class: italic font symbolises class or method without direct instances or implementation, respectively

association: Client has a direct reference to the target

composition: an Element may have multiple sub-Elements

The Visitor Pattern represents an operation to be performed on elements of an object structure. Visitor lets you define a new operation without changing the classes of the elements on which it operates.

inheritance: ConcreteVisitorB is a specific type of Visitor

## Visitor
void visit(ConcreteElement1)
void visit(ConcreteElement2)

## ConcreteVisitorA
void visit(ConcreteElement1)
void visit(ConcreteElement2)

## ConcreteVisitorB
void visit(ConcreteElement1)
void visit(ConcreteElement2)

## Client

## Element
void accept(Visitor)

## ConcreteElement1
void accept(Visitor)

## ConcreteElement2
void accept(Visitor)

---

# Toy example – mammals getting visited

For this example, try and recognise the various elements of the visitor pattern and understand their interactions

- Visitor (abstract superclass)
  - Concrete Visitor(s)
- Element (abstract superclass)
  - Concrete Element(s)
- Client (coordinates things in this example)

## CODE WALK THROUGH

Object-Oriented Programming

---

# Real world example – cash back offers

A bank offers 3 types of credit card which offer annual subscription fees vs cashback offers: as trade-offs

|  | Bronze (free) | Silver (£250) | Gold (£500) |
|---|---|---|---|
| Fuel | 1% | 2% | 3% |
| Tesco | 0.5% | 1% | 2.5% |
| Cycle republic | 0% | 1% | 5% |

Based on: https://youtu.be/TeZqKnC2gvA

Object-Oriented Programming

---

# Real world example – cash back offers

Consider what classes you will have for the pattern's components:

- Visitor
  - Concrete Visitor(s)
- Element
  - Concrete Element(s)
- Client

|       | Bronze (free) | Silver (£250) | Card (£500) |
|-------|---------------|--------------|-------------|
| Fuel  | 1%            | 2%           | 3%          |
| Tesco | 0.5%          | 1%           | 2.5%        |
| Cycle republic | 0%        | 1%           | 5%          |

## CODE WALK THROUGH

Based on: https://youtu.be/TeZqKnC2gvA

Object-Oriented Programming

---

# Example: A Binary Tree that can be visited...

- consider the following situation:
  - we have a target object structure (for instance a binary Tree where every node is either a Leaf or a Fork with references to two Tree objects)
  - other objects, known as clients, would like to perform operations that require information from possibly all sub-objects of the target structure (for instance summing up values from all the leaves of the tree structure)
  - however, we would like any operations to be defined independently from the object structure itself
  - the operations should therefore be encapsulated in a separate object (which we shall call the Visitor)

```
abstract class Tree { // the client
abstract void accept(Visitor v);
}

class Fork extends Tree {
Tree l;
Tree r;
...
}

class Leaf extends Tree {
int value;
...
}

abstract class Visitor {
abstract void visit(Fork t);
abstract void visit(Leaf t);
}
```

all Tree objects know how to accept a Visitor object

all Visitor objects know how to visit all types of trees

---

# The Tree-side of Things ... that can be visited ...

- we need an abstract class Tree that is parent to two non-abstract specialisations of Tree: the Fork and Leaf classes
- we also demand that all trees should accept a Visitor object (by calling its visit method with itself as parameter)

```java
abstract class Tree {
    abstract void accept(Visitor v);
}
```

```java
class Fork extends Tree {
    Tree l;
    Tree r;

    Fork(Tree l, Tree r) {
        this.l = l;
        this.r = r;
    }

    @Override
    void accept(Visitor v) {
        v.visit(this);
    }
}
```

```java
class Leaf extends Tree {
    int value;

    Leaf(int value) {
        this.value = value;
    }

    @Override
    void accept(Visitor v) {
        v.visit(this);
    }
}
```

any Tree object must be able to accept a Visitor object, non-abstract sub-classes MUST implement this method

being a Fork object means to hold references to two Tree objects

being a Leaf object means to have a value

accepting a visitor object means to call its visit method handing this as parameter

---

# VisitorWorld: Interaction of the Tree and the Visitor

- we also have an abstract Visitor object that knows how to visit Fork and Leaf objects
- a particular, non-abstract SumVisitor implements visit
- now we can message a Tree to accept a SumVisitor...

```java
abstract class Visitor {
    abstract void visit(Fork t);
    abstract void visit(Leaf t);
}
```

```java
class VisitorWorld {
    public static void main (String[] args) {
        Tree l1 = new Leaf(1);
        Tree l2 = new Leaf(2);
        Tree l3 = new Leaf(3);
        Tree n12 = new Fork(l1, l2);
        Tree tree = new Fork(n12, l3);
        SumVisitor visitor = new SumVisitor();
        tree.accept(visitor);
        System.out.println("total: " + visitor.total);
    }
}
```

```java
class Leaf extends Tree {
    int value;

    Leaf(int value) {
        this.value = value;
    }

    @Override
    void accept(Visitor v) {
        v.visit(this);
    }
}
```

```java
class SumVisitor extends Visitor {
    int total;

    @Override
    void visit(Fork fork) {
        fork.l.accept(this);
        fork.r.accept(this);
    } // forward to sub-trees

    @Override
    void visit(Leaf leaf) {
        total += leaf.value;
    }
}
```

```java
abstract class Tree {
    abstract void accept(Visitor v);
}
```

#3) visitor handles the visits

#4) we access the result in the attribute total of the visitor object

#1) we ask a tree to accept our visitor, dynamic dispatch on the tree sub-type

#2) a specific tree accepts by forwarding (dynamic dispatch) to the specific visitor

---

# Different Visitors – No Change to the Tree Classes ...

## Visitor.java
```java
abstract class Visitor {
    abstract void visit(Fork t);
    abstract void visit(Leaf t);
}
```

## SumVisitor.java
```java
class SumVisitor extends Visitor {
    int total;

    @Override
    void visit(Fork fork) {
        fork.l.accept(this);
        fork.r.accept(this);
    } // forward to sub-trees

    @Override
    void visit(Leaf leaf) {
        total += leaf.value;
    }
}
```

## ProdVisitor.java
```java
class ProdVisitor extends Visitor {
    int total = 1;

    @Override
    void visit(Fork fork) {
        fork.l.accept(this);
        fork.r.accept(this);
    } // forward to sub-trees

    @Override
    void visit(Leaf leaf) {
        total *= leaf.value;
    }
}
```

## VisitorWorld.java
```java
class VisitorWorld {
    public static void main (String[] args) {
        Tree l1 = new Leaf(1);
        Tree l2 = new Leaf(2);
        Tree l3 = new Leaf(3);
        Tree n12 = new Fork(l1, l2);
        Tree tree = new Fork(n12, l3);
        SumVisitor sumV = new SumVisitor();
        ProdVisitor prodV = new ProdVisitor();
        tree.accept(sumV);
        tree.accept(prodV);
        System.out.println( "sum: " + sumV.total + " prod: " + prodV.total );
    }
}
```

## Leaf.java
```java
class Leaf extends Tree {
    int value;

    Leaf(int value) {
        this.value = value;
    }

    @Override
    void accept(Visitor v) {
        v.visit(this);
    }
}
```

## Fork.java
```java
class Fork extends Tree {
    Tree l;
    Tree r;

    Fork(Tree l, Tree r) {
        this.l = l;
        this.r = r;
    }

    @Override
    void accept(Visitor v) {
        v.visit(this);
    }
}
```

## Tree.java
```java
abstract class Tree {
    abstract void accept(Visitor v);
}
```

### FLEXIBLE: we can define numerous different specialisations of Visitor, all providing different operations (e.g. sums, products..) on our Tree object structure WITHOUT changing the Tree class or any of its sub-classes

### NEAT: calling any operation on a Tree object can be achieved by letting a Tree object accept a Visitor object that implements the operation

### no change!

### no change!

### no change!

---

# Decoupling of Operations and Data Structures!

## Operations

abstract class Visitor {
    abstract void visit(Fork t);
    abstract void visit(Leaf t);
}

Visitor.java

class SumVisitor extends Visitor {
    int total;

    @Override
    void visit(Fork fork) {
        fork.l.accept(this);
        fork.r.accept(this);
    } // forward to sub-trees

    @Override
    void visit(Leaf leaf) {
        total += leaf.value;
    }
}

class ProdVisitor extends Visitor {
    int total = 1;

    @Override
    void visit(Fork fork) {
        fork.l.accept(this);
        fork.r.accept(this);
    } // forward to sub-trees

    @Override
    void visit(Leaf leaf) {
        total *= leaf.value;
    }
}

ProdVisitor.java

## Data Structures

class Leaf extends Tree {
    int value;

    Leaf(int value) {
        this.value = value;
    }

    @Override
    void accept(Visitor v) {
        v.visit(this);
    }
}

Leaf.java

class Fork extends Tree {
    Tree l;
    Tree r;

    Fork(Tree l, Tree r) {
        this.l = l;
        this.r = r;
    }

    @Override
    void accept(Visitor v) {
        v.visit(this);
    }
}

Tree.java

abstract class Tree {
    abstract void accept(Visitor v);
}

## VisitorWorld

class VisitorWorld {
    public static void main(String[] args) {
        Tree l1 = new Leaf(1);
        Tree l2 = new Leaf(2);
        Tree l3 = new Leaf(3);
        Tree n12 = new Fork(l1, l2);
        Tree tree = new Fork(n12, l3);
        SumVisitor sumV = new SumVisitor();
        ProdVisitor prodV = new ProdVisitor();
        tree.accept(sumV);
        tree.accept(prodV);
        System.out.println("sum: " + sumV.total +
                           " prod: " + prodV.total);
    }
}

Operations do not need to know how the data structure is actually implemented, or how it is traversed; they only need to know how to visit its components.

Data Structures do not need to know anything about the operations that are performed over them. They could be developed independently.

---

# THE VISITOR PATTERN

---

# ‘Visitor Pattern’ Emerges

## Visitor.java
```java
abstract class Visitor {
    abstract void visit(Fork t);
    abstract void visit(Leaf t);
}
```

## SumVisitor.java
```java
class SumVisitor extends Visitor {
    ...
    @Override
    void visit(Fork fork) {
        ...
    }
    @Override
    void visit(Leaf leaf) {
        ...
    }
}
```

## ProdVisitor.java
```java
class ProdVisitor extends Visitor {
    ...
    @Override
    void visit(Fork fork) {
        ...
    }
    @Override
    void visit(Leaf leaf) {
        ...
    }
}
```

## VisitorWorld.java
```java
class VisitorWorld {
    ...
}
```

## Tree.java
```java
abstract class Tree { // the client
    abstract void accept(Visitor v);
}
```

## Leaf.java
```java
class Leaf extends Tree {
    ...
    @Override
    void accept(Visitor v) {
        v.visit(this);
    }
}
```

## Fork.java
```java
class Fork extends Tree {
    ...
    @Override
    void accept(Visitor v) {
        v.visit(this);
    }
}
```

‘user client’ knows both the tree and the visitor

The Visitor Pattern represents an operation to be performed on elements of an object structure. Visitor lets you define a new operation without changing the classes of the elements on which it operates.

various different non-abstract visitors possible, all inherit from Visitor

various different non-abstract types of Tree may exist, all of which must implement the accept method

---

# USEFUL JAVA FEATURES

---

# Variadic Arguments

- in Java, methods can have a variable number of arguments (thus, the method has indefinite arity)
- these variadic methods can be made to accept zero or more arguments of a given type using the ... notation
- the arguments are provided to the methods as an array
- this is very useful for passing dynamically structured data into methods

method takes a single argument of type String

```java
class Robot {
    ...
    void talk(String phrase) {
        if (powerLevel >= 1.0f) {
            System.out.println(name + " says " + phrase);
            powerLevel -= 1.0f;
        } else {
            System.out.println(name + " is too weak to talk.");
        }
    }

    void talk(String first, String... strings) {
        this.talk(first);
        for (String string : strings) {
            this.talk(string);
        }
    }

    void charge(float amount) {
        System.out.println(name + " charges.");
        powerLevel = powerLevel + amount;
    }
}
```

overloaded method takes variable number of arguments of type String

```java
class VariadicRobotWorld {
    public static void main(String[] args) {
        Robot c3po = new Robot("C3PO");
        c3po.charge(10);
        c3po.talk("'A single hello, Java!'");
        c3po.talk("'Hello again, Java.'",
                "'Hey again!'",
                "'Still talking!'");
    }
}
```

method 'talk' can now be called with one or any number of String arguments

Object-Oriented Programming

---

# Enumeration Classes

- if you define a class using enum instead of class, the first statement must be a fixed list of constants of that class

- constants are the only objects (and can be used via Side.NOUGHT etc), but are guaranteed never to be duplicated, so you can use == for direct comparison

- constants are handled as auto-instantiated objects, you can reference them, even use a constructor for their initialisation

```java
public enum Side {
    NOUGHT("O"), CROSS("X");

    String symbol;

    Side(String symbol) {
        this.symbol = symbol;
    }

    public String symbol() {
        return symbol;
    }

    public Side other() {
        return this == NOUGHT ? CROSS : NOUGHT;
    }
}
```

```java
class SideWorld {
    public static void main (String[] args) {
        Side sideA = Side.NOUGHT;
        Side sideB = Side.CROSS;
        Side sideC = Side.CROSS;
        System.out.println(sideA==sideB); //false
        System.out.println(sideC==sideB); //true
        System.out.println(sideA.symbol()); //O
        System.out.println(sideB.symbol()); //X
        System.out.println(sideA.other().symbol()); //X
    }
}
```

enumeration of the constants with calls to the constructor

comparison using == is possible

enums are just objects

Object-Oriented Programming

---

# To Do

- recap content and check out the unit website
- write, compile, run and understand all the tiny programs from the lectures so far

Use the forum, we are there for you!

Object-Oriented Programming

---

## 📋 任务简报：Weekly Briefings 10 STAG Briefing.md

# Introduction to Final Assignment

COMSM0086

Dr Simon Lock and Dr Sion Hannuna

---

# Simple Text Adventure Game (STAG)

---

# Overview

Final exercise is worth 70% of unit assessment

The aim of this assignment is to build...

A general-purpose socket-server game-engine
(for text adventure games)

If you are unfamiliar with the genre, take a look at:
https://tinyurl.com/zork-game

---

# Game Server

The main class is a server that listens on port 8888
Server accepts incoming commands from clients
It then processes command & changes game state
Returning a suitable response back to the client

After processing command server closes connection
Then listens for the next connection on port 8888
Don't panic: this is provided for you in the template

---

# Standard "Built-in" Gameplay Commands

- "inventory" (or "inv" for short): lists all of the artefacts currently in the possession of the player
- "get": picks up a specified artefact from current location and adds it to the player's inventory
- "drop": puts down an artefact from player's inventory and places it into the current location
- "goto": moves the player to a new location (only if there is a valid path to that location)
- "look": describes the current location, including all entities in that location and paths to other locations

---

# Demo of Server in Action

RunGameServer

In order to connect to the server
We have also provided you with a GameClient:

RunGameClient

You won't need to alter the client code !
It is really just there so you can play the game

---

# With this server, you can play ANY game !

But how is this possible ?

Gameplay is defined by providing two separate 'game configuration' files to the game engine:

- Entities: structural layout and relationships
- Actions: dynamic behaviours of the game

Before considering the content of each of these files
Let us discuss 'Entities' and 'Actions' at high level...

---

# Different Types of Entity

- Character: A creature/person involved in game
- Player: A special kind of character (the user !)
- Location: A room or place within the game
- Artefact: A physical "thing" within the game (these things CAN be collected by the player)
- Furniture: A physical "thing", part of a location (these things CANNOT be collected by the player)

---

# The Location Class

Locations are complex entities in their own right
They can contain the following optional elements:

- Paths to other Locations (these can be one-way!)
- Characters that are currently at that Location
- Artefacts currently present in that Location
- Furniture that belongs in the Location

---

# Actions

Dynamic behaviours are represented as 'Actions'
Each action may have the following elements:

- A set of possible 'trigger' key phrases
(ANY of which can be used to initiate an action)

- A set of 'subject' entities that must be available
(ALL of which be present to perform the action)

- A set of 'consumed' entities that are removed
(ALL of which are "eaten up" by the action)

- A set of 'produced' entities that are created
(ALL of which are "generated" by the action)

---

# Example Actions

The previous description of 'Actions' is probably a little hard to understand !

Let's look at some examples by way of illustration They are represented using a language called XML (the same language used by the Maven POM file !)

actions.xml

---

# Entity Files

Rather than also representing entities using XML
We will use an alternative language called 'DOT'
(It's good to experience a range of languages)

DOT is a language used for representing graphs
(which is basically what a text adventure game is !)

entities.dot

Sorry about the file extension - it's not my choice !

---

# Visualising DOT files

The BIG bonus of using DOT files is that...

There are tools available for rendering them (GraphViz)

We can SEE structure of the 'entities' within the game:

```
cellar      elf
storeroom   log

cabin       potion      trapdoor

forest      key         tree

---

# Online Editor and Visualiser

https://dreampuf.github.io/GraphvizOnline/

20%20%20%20%20%20tree%20%5Bdescription%20%3D

14/32

---

# Parsers

You've already gained experience writing parsers
We don't really want to "go over old ground"
So we will be using two existing parsing libraries !

There is considerable educational value in
learning to use existing libraries and frameworks

This can get lost in a desire to learn fundamentals
But not on this unit !

---

# Which parsers ?

For parsing DOT files, you should use 'JPGD':
http://www.alexander-merz.com/graphviz/doc.html
Library _should_ already be embedded in maven project

And the Java API for XML Processing 'JAXP':
http://oracle.com/java/technologies/jaxp-introduction.html
Core library that _should_ be available to your project

See "test" folder for examples of these parsers in use

---

# Command Interpreter Flexibility

Just as with the DB server, the STAG server must be able to cope with various command variabilities:

- Varying case: all command are case-insensitive
- Varying word order: triggers/subjects in any order
  unlock door with key
  use key to unlock door
- Decorated commands: extra "unnecessary" words
  please unlock the door using the key, thanks !
- Partial commands: some subjects not mentioned
  unlock door

Full details of all these are contained in workbook

---

# Correctness and Certainty

Your server should block "badly formed" commands

## Extraneous Entities

Stated by user, but not defined as a subject of action

open door with key and axe

## Ambiguous Commands

Command matches more than one possible action

open with key

(if there are two things that can be opened with a key)

---

# Player Identification

Incoming commands always begin with a username (to identify which player has issued that command)

A typical incoming message might take the form of:
simon: open door with key

This allows the game to support multiple players !

Server does NOT need to deal with authentication (that would add to the complexity of assignment)

---

# Marking Process

A special set of "custom" game configuration files will be used to assess your engine during marking. It is therefore essential your code is able to load in files in the same format as the examples provided !

Test scripts will be used to automatically test your game engine to ensure it is operating correctly. It is therefore essential that you adhere to the "built-in" commands detailed previously !

---

# Your own test cases

As we have discussed previously on this unit
Effective and comprehensive testing is essential !
It becomes EVEN more important with AI code gen
(so we can be sure that generated code is correct)

For this reason, YOUR test cases will be marked:
- The extent to which tests cover required features
- Checking system does not enter erroneous states

---

# How do we identify "poor" testing ?

---

# Assessing your test cases (3 ways)

We first ensure that your tests cover all YOUR code (Whitebox testing ensuring all your code is "exercised")

How do we know that you have written "good" tests? (not just a set of "easy" cases that YOUR code passes) We'll run YOUR tests against a "known good" solution (Blackbox testing another solution - UNSEEN codebase)

Remember "a successful test is one that finds a fault"? We also run your tests against a "known bad" solution To see how many faults YOUR tests are able to detect!

---

# Code Quality

Your code quality will be assessed during marking
Adhere to guidelines outlined in the quality lecture
Refer to any feedback you have received previously
(if you submitted OXO or DB for code quality analysis)

Last year approx a third of students received a penalty
For those that did, the average penalty was only 2%
Our aim here is not really to penalise students
But rather to get you to improve your code quality !

---

# Collusion

This is an individual assignment, not group activity
Automated checkers used to flag possible collusion
If markers feel collusion has indeed taken place...
Incident is referred to academic malpractice panel

May result in a mark of zero for assignment
or even the entire unit (if it is a repeat offence)

---

# Derived Code

We'll use analysis tools to determine "derived" code
Material that was "found" online or generated by AI

Any derived code will be discounted during marking
You'll only receive credit for code YOU have written

---

More detail on derivation detection ?

27/32

---

# Mashup Coursework Submissions

The notion of a "mashup" codebase is nothing new
It does not rely on availability of effective AI tools
Students have been creating mashup work for years
borrow a bit of code from here, borrow a bit from there

Modern AI tools just make process quicker & easier
Students often don't even realise they are doing it !
But that's what you get when you Gen AI some code

---

# Addressing this Problem

Aim of unit is to assess YOUR programming skills

We aren't going to be able to do that if you are:
- "Reusing" bits and pieces from online solutions
- "Generating" chunks of code using AI tools

If we could *detect* code that has been "derived"...
We could factor it out during the marking process:
you don't get marks for code you didn't write

This would allow us to give credit where credit's due

---

# Implementing this Approach

We have a library of 500 solutions to the assignment
ALL submissions of ALL students from previous years

Many are available online (as part of code portfolios)
These will be part of the training set used by AI tools

These 500 solutions also borrow from online examples
(which provides us with even broader sampling)

All we do is compare YOUR code with this training set
The more similarities that are found...
The more "derivative" your submission has become

---

I know what you are thinking...

There is BOUND to be some level of similarly
Some standard boilerplate code that everyone has
Or some convergent algorithm that everyone uses

That's fine, we expect this kind of thing to happen
We will be using a variety of filters and thresholds
The aim being to factor out "natural" commonality

Also human-in-the-loop to catch any false-positives

---

# REMEMBER

You will only be rewarded for code that YOU write
Any "derived" code ("found" items or AI generated)
Will be discounted during the marking process
(resulting in a reduced final mark)

---


## 🔑 核心知识点摘要

*（出题时参考以上各节详细内容，此处为快速索引）*

| 类型 | 文档 | 核心主题 |
|------|------|----------|
| 📖 主讲课 | Weekly Lectures 10 Visitor Pattern.md | |
| 📋 任务简报 | Weekly Briefings 10 STAG Briefing.md | |
