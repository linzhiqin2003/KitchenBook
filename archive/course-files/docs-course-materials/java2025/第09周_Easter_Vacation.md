# 第09周：Easter Vacation

> UoB Computer Science - Java 2025
> 提取自课件 PDF，用于 AI 出题知识库

---

## 📖 主讲课：Weekly Lectures 09 Double Dispatch.md

Department of Computer Science
University of Bristol

COMSM0086 – Object-Oriented Programming

# POLYMORPHISM AND DOUBLE DISPATCH

Sion Hannuna | sh1670@bris.ac.uk
Simon Lock | simon.lock@bris.ac.uk

---

# DOUBLE DISPATCH

---

# READY!

---

# What is double and / or multiple dispatch?

Dispatch based on two or more types

- Single dispatch:
  - mammal.makeNoise();
    - Resolves mammal to its underlying type and calls its makeNoise method rather than mammal's

- Double dispatch:
  - (mammal1 & mammal2).makeNoise();
    - Depends on which mammals are interacting!

- Why might you do this?

Object-Oriented Programming

---

# What is multiple dispatch?

Dispatch based on two or more types

- Single dispatch:
  - `mammal.makeNoise();`
    - Resolves mammal to its underlying type and calls its makeNoise function rather than mammal's

- Double dispatch:
  - `(mammal1 & mammal2).makeNoise();`
    - Depends on which mammals are interacting!

- Why might you do this?
  - Collision detection in games (for example)

Object-Oriented Programming

---

# Multiple Dispatch – the Big Switch

```c
#define rock 1
#define paper 2
#define scissors 3

typedef struct entity {
    unsigned int ID;
    void * data;
} Entity;

void collision(Entity * e1, Entity * e2)
{
    switch (e1->ID) {
    case rock:
        switch (e2->ID) {
            case rock: /*DRAW*/
            case paper: /*ENTITY 2 WINS*/
            case scissors: /*ENTITY 1 WINS*/
        }
    case paper:
        switch (e2->ID) {
            case rock: /*ENTITY 1 WINS*/
            case paper: /*DRAW*/
            case scissors: /*ENTITY 2 WINS*/
        }
    case scissors:
        switch (e2->ID) {
            case rock: /*ENTITY 2 WINS*/
            case paper: /*ENTITY 1 WINS*/
            case scissors: /*DRAW*/
        }
    }
}
```

Object-Oriented Programming

---

# Criticisms of the Big Switch

- Good
  - Code is relatively easy to step through

- Bad
  - Adding/removing types is a big job which will not be verified by a compiler
  - Need a type field for all types and have to keep track of all types
  - Switch statements tend to grow and show up as code replication throughout the project

Object-Oriented Programming

---

# Multiple Dispatch – Function pointer / dispatch table

```c
#define rock 0
#define paper 1
#define scissors 2

typedef struct entity {
    unsigned int ID;
    void * data;
} Entity;

typedef void (*collReso) (Entity * e1, Entity * e2);

void rock_rock(Entity * e1, Entity * e2);
void rock_paper(Entity * e1, Entity * e2);
void rock_scissors(Entity * e1, Entity * e2);
void paper_rock(Entity * e1, Entity * e2);
void paper_paper(Entity * e1, Entity * e2);
void paper_scissors(Entity * e1, Entity * e2);
void scissors_rock(Entity * e1, Entity * e2);
void scissors_paper(Entity * e1, Entity * e2);
void scissors_scissors(Entity * e1, Entity * e2);

void collision(Entity * e1,Entity * e2,collReso colTbl[][3])
{
    collReso cr = colTbl[e1->ID][e2->ID];
    cr(e1, e2);
}
```

```c
int main()
{
    Entity e1, e2;
    collReso colTbl[3][3];

    colTbl[0][0] = rock_rock;
    colTbl[0][1] = rock_paper;
    colTbl[0][2] = rock_scissors;
    colTbl[1][0] = paper_rock;
    colTbl[1][1] = paper_paper;
    colTbl[1][2] = paper_scissors;
    colTbl[2][0] = scissors_rock;
    colTbl[2][1] = scissors_paper;
    colTbl[2][2] = scissors_scissors;

    e1.ID = 0;
    e2.ID = 2;

    collision(&e1, &e2, colTbl);

    return 0;
}
```

Object-Oriented Programming

---

# Criticisms of Function table

- Good
  - Tables are disentangled from code.
  - Table modification has less side-effects with regards to the code which uses them (in contrast to the switch statement approach).

- Bad
  - Debugging / stepping through is awful
  - Still require type field for all types

Object-Oriented Programming

---

# How can we do this in Java?

You might be tempted to do something like this (it won't work):

```java
public class Runner {
    public static void main (String [] args){
        Mammal mDolphin = new Dolphin();
        Mammal mLion = new Lion();

        mDolphin.makeNoise(mLion);
    }
}
```

And then update the mammal class and its children to provide overloaded functions for each scenario ...

Object-Oriented Programming

---

# How can we do this in Java?

```java
public abstract class Mammal {
    public void stateAttributes() {
        System.out.println("Warm blood, 3 inner
    }
    public abstract void makeNoise();
    public abstract void makeNoise(Dog d);
    public abstract void makeNoise(Lion l);
    public abstract void makeNoise(Dolphin d);
}

public class Dolphin extends Mammal{
    @Override
    public void makeNoise() {
        System.out.println("squeek click");
    }
    @Override
    public void makeNoise(Dog d) {
        System.out.println("Dolphin interacting with dog");
    }
    @Override
    public void makeNoise(Dolphin d) {
        System.out.println("Dolphin interacting with dolphin");
    }
    @Override
    public void makeNoise(Lion l) {
        System.out.println("Dolphin interacting with lion");
    }
}
```

But it wont work because each function is expecting a particular type of mammal: call parameters, even if they are references, are treated as static ...

Object-Oriented Programming

---

# Double dispatch in Java

Mammals and their children (done)
Rock paper scissors (done)

Object-Oriented Programming

---

# Criticisms of OO Approach

- Good
  - Many errors caught at compile time
  - Avoids the issues inherent to switch-based solutions
- Bad
  - Hard to understand - especially for those unfamiliar with Visitor design pattern
  - It is an object oriented solution which violates many object oriented ideas
  - breaks encapsulation - function call interacts with more than one type

Object-Oriented Programming

---

# Multiple Dispatch (Robot example)

- if we want to make the selection of method dynamic in more than one type we need to implement multiple dispatch
- Java does not explicitly supply a single mechanism for it
- however, we can be cunning and utilise single dispatch recursively
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
        talk("Hello from a TranslationRobot to a CarrierRobot.");
    }
    void greet(CarrierRobot other) {
        talk("Hello from a CarrierRobot to another.");
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
        talk("Hello from a TranslationRobot to another.");
    }
    void greet(CarrierRobot other) {
        talk("Hello from a CarrierRobot to a translationRobot.");
    }
    void greet(AbstractRobot other) {
        other.greet(this);
    }
}
```

## DispatchWorld.java

```java
class DispatchWorld {
    public static void main(String[] args) {
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

## 📋 任务简报：Weekly Briefings 09 DB Debrief.md

# Object Oriented Programming with Java

COMSM0086

DB Exercise Debriefing

---

# Looking for the "Correct" Solution ?

There isn't really one single "correct" solution
But there are "good" and "not-so-good" approaches

This notion of "goodness" is a slippery concept
Open to interpretation, but typically involves:

- A reasonable (logical/extensible) structure
- Appropriate material code quality attributes
- Behaves as intended (passes the tests !)
- Operates "efficiently enough" to be usable

---

# DBServer

## QueryParser

## DBInterrogator

## FileParser

## Database

## Table

## Row

## Query

## ResultSet

## OutputFormatter

03/12

---

# Query Inheritance Hierarchy

All the possible query type have their own class
All query types inherit from a abstract super class
Each class can parse and perform that query type

Query
Use Query
Create Query
Select Query
Insert Query

---

# Sion's Preferred Architecture

SELECT name FROM actors WHERE age > 10

Tokenizer
Token nextToken()

Maybe use regular expressions for a subset of this

[CT: "SELECT"]
[ID: "name"]
[KW: "FROM"]
[ID: "actors"]
[KW: "WHERE"]
[ID: "age"]
[OP: ">"]
[INT: "10"]

Parser
DBcmd parse()

BNF for this one - regular expressions will not work

Abstract Syntax TREE (AST)

Code generator or interpreter

DBServer

...

Parser builds subclass of DBcmd as it parses. This is returned to DBServer which passes a reference to itself as an argument to the method used to execute the command. The context given by parsing the BNF, combined with Token types facilitates error handling and command building

---

# Sion's Preferred Architecture

| DBcmd |
| --- |
| List<Condition> conditions; |
| List<String> colNames; |
| List<String> tableNames; |
| String DBname; |
| String commandType; |
| ... ? |
| String query(DBServer s) |

Abstract class DBcmd has uninitialized attributes for the superset of attributes required by all commands and one abstract method which is implemented by all concrete commands which extend it

Potentially mutates DBserver state and returns result of query

| SelectCMD |
| --- |
| String query(DBServer s) |

| AlterCMD |
| --- |
| String query(DBServer s) |

| InsertCMD |
| --- |
| String query(DBServer s) |

| UpdateCMD |
| --- |
| String query(DBServer s) |

...

---

# Code Quality Feedback

We have set up a submission point on Blackboard
If upload your DB project code here by Friday 1pm
You'll receive an email summary of quality analysis

Report highlights ALL issues detected in your code
(Some points raised are more serious than others)

It's useful however to be made aware of all issues
The best way to continuously improve your code!

---

# Most commonly encountered issues

- Overly complex methods, as measured by:
  - Cyclomatic Complexity (see quality lecture)
  - Depth of Nesting (indentation)
  - Sheer length of methods (Lines of Code)
- Replication and Duplication (unDRY code)
- Breaking encapsulation (public attributes)
- Unnecessarily long IF/CASE statement blocks

---

# Testing: "Behaves as intended"

Our test cases cover as much behaviour as possible
Whilst trying to keep the test set small and tight
Our test cases are split into the following "clusters":
- Basic & Compound SELECT
- UPDATE, DELETE and JOIN
- Illegal Names & Illegal Actions
- Malformed Queries & Unknown Entities
- Case insensitivity & Whitespace Variability
- General Server Robustness (miscellaneous!)

---

# Run Our Test Cases

We will release all of our test cases via GitHub
(When we feel that the time is right !)

Run them against your code, see how many you pass
If you fail our tests, your own cases were incomplete

Ask why you overlooked those areas of behaviour ?
How might you improve your own tests in future ?
Could you be more systematic in your approach ?

---

# Efficiency

Efficiency was not explicitly part of this exercise
Hard to assess without employing large datasets
Even then, devising suitable metrics is problematic
(Hard to determine what java is doing internally !)

This topic is not covered to any extent in this unit
(Not really enough time to consider algorithmics)
Something to bare in mind when designing solutions
Especially important creating non-trivial systems

---

# Importance of this Discussion

At the very end of this unit there will be...
A BIG assessed exercise (70% of the unit mark)

It is important to gain feedback on your work NOW
(so you can reflect on your performance and improve)

You don't really want the first feedback you get...
To be AFTER the one (and only) assessed exercise !

---


## 🔑 核心知识点摘要

*（出题时参考以上各节详细内容，此处为快速索引）*

| 类型 | 文档 | 核心主题 |
|------|------|----------|
| 📖 主讲课 | Weekly Lectures 09 Double Dispatch.md | |
| 📋 任务简报 | Weekly Briefings 09 DB Debrief.md | |
