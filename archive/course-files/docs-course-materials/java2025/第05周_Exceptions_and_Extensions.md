# 第05周：Exceptions and Extensions

> UoB Computer Science - Java 2025
> 提取自课件 PDF，用于 AI 出题知识库

---

## 📖 主讲课：Weekly Lectures 05 Code Quality.md

# Code Quality and Programming Standards

COMSM0086

Dr Simon Lock and Dr Sion Hannuna

---

# Aim of This Lecture

To TRY to make YOU into a better developer!
(beyond just an ordinary 'coder')

Achieved by considering code quality at two levels:

1. Low-level *material* quality of your source code
2. Higher-level *structural* quality of your system

---

# Code Quality

GOOD code is NOT just about "correct operation"
Code may run just fine, but still be BADLY written !

Key questions to ask yourself about your code are:
- How easy is your code for others to understand ?
- How easy is your code for others to change ?
- Does your code support long-term maintenance ?

As a 'coder' you probably don't care about these
As a professional 'developer' you definitely should !

---

# Example Codebase

Let us consider an example application codebase:
- It runs correctly, without errors or failures
- It is fast and efficient in operation
- It exhibits compact and elegant code
- It makes good use of language constructs

Question: Does that sound like high quality code ?

---

#include <stdio.h>
typedef double f; f H=.5,Y=.66,S=-1,I,y=-111; extern"C"{f cos(f),pow(f,f),atan2(f,f);} struct v{f x,y,z;v(f a=0,f b=0,f c=0):x(a),y(b),z(c)}{f operator%(v r){return x*r.x+y*r.y+z*r.z;}v operator+(v r){return v(x+r.x,y+r.y,z+r.z);}v operator*(f s){return v(x*s,y*s,z*s);} }W(1,1,1),P,C,M; f U(f a){return a<0?0:a>1?1:a;} v _(v t){return t*pow(t%t,-H);} f Q(v c){M=P+c*S; f d=M%M; return d<I?C=c,I=d:0;} f D(v p){I=99;P=p; f l,u,t;v k; for(const char*b="BCJB@bJBHbJCE [FLL_A [FLMCA [CCTT`T";*b;++b){k.x+=*b/4&15;int o=*b&3,a=*++b&7;k.y=*b/8&7;v d(o%2*a,o/2*a); !o ?l=a/4%2*-3.14,u=a/2%2*3.14,d=p+k*-H,t=atan2(d.y,d.x),t=t<l?l:t>u?u:t,Q(k*H+v(cos(t),cos(t-1.57))*(a%2*H+1)):Q(k+d*U((p+k*S)%d/(d%d)));} return M=Q(v(p.x,-.9,p.z))?(int(p.x+64)^int(p.z+64))/8&1?Y:W:v(Y,Y,1),pow(I,H)-.45;} v R(v o,v d,f z){for(f u=0,l=1,i=0,a=1;u<97;u+=l=D(o+d*u)) if(l<.01){v p=M,n=_(P+C*S),L=_(v(S,1,2)); for(o=o+d*u;++i<6;a-=U(i/3-D(o+n*i*.3))/pow(2,i));p=p*(U(n%L)*H*Y+Y)*a;p=z?p*Y+R(o+n*.1,d+n*-2*(d%n),z-1)*H*Y:p;u=pow(U(n%_(L+d*S)),40); return p+p*-u+W*u;}z=d.z*d.z; return v(z,z,1);} int main(){for(puts("P6 600 220 255");++y<110); for(f x=-301;P=R(v(-2,4,25),_(v(5,0,2))*++x+_(v(-2,73))*-y+v(301,-59,-735)),2)*255,x<300;putchar(P.z)putchar(P.x),putchar(P.y);}

---

# mattz

06/28

---

# Some Practical Guidelines for Code Quality

---

# Method and Variable Naming

The names we choose for methods and variables
Can have a significant impact on understandability

How readable is code if the variables are: a, b, c ?
(Consider the Ray Tracer code for example !)

Everyone has own idea of what makes a good name
Organisations will have own conventions & standards

Here are the "OOP with Java" naming conventions...

---

# Naming Conventions

Unsurprisingly...

Variable names should describe the data they hold
Method names should describe action they perform

Anything less than 5 chars is probably too short
Anything greater than 20 chars is getting a bit long

Single words are typically not enough to do the job
I favour Verb/Subject pairs as names for methods...

---

# Examples of Good Method Names

getSurname
setAge
initialiseDataArray
drawNodes
findStringMatches

---

# Bad Method Names

go
set
calculate
evaluate
enable

---

# Accepted "Standard" Terms

Sometimes single words _may_ be acceptable
IF they are standard terms from the domain
OR they are self-evident in their own right:

run, draw, clone, delete, multiply, connect, filter

But why take the risk ?
Does it really hurt to use compound names ?
You can only improve understandability

---

# Method Complexity

'Divide and Conquer' is an often touted strategy...
Split up complex code into simple sub-procedures
(and sub-sub-procedures)

Avoid massive, hard-to-understand methods
Particularly with complex loop & decision structures
These can be VERY hard to understand (and change)

Big improvements in understandability can be
achieved by "farming out" code to suitable methods

---

# Simple "Farming Out" Example

Consider a method to check if two numbers are "close"  
(e.g. 1 and 2 are close, 1 and 8 are not)

A first attempt might look something like this:  
(had to use "naughty" var names to fit code onto slide)

```java
int a = int(random(0, 10));
int b = int(random(0, 10));
System.out.println("Numbers are " + a + " and " + b);
if (((a>b)&&((a-b)<2)) || ((a<b)&&((b-a)<2)) || (a==b)) {
    System.out.println("They are close");
}
else System.out.println("They are NOT close");

---

# A Simpler, Clearer Solution (?)

```
{
    int firstAge = int(random(0, 10));
    int secondAge = int(random(0, 10));
    System.out.println("Ages are " + firstAge + " and " + secondAge);
    if (differenceBetween(firstAge, secondAge) < 2) {
        System.out.println("They are close");
    }
    else System.out.println("They are NOT close");
}

int differenceBetween(int a, int b)
{
    if (a>b) return a-b;
    else return b-a;
}

---

# Minimising Complexity

To minimise complexity, you should try to avoid:

- Very long lines (stretching off side of screen)
- Long methods (stretching off bottom of screen)
- Methods with many parameters (doing too much)
- Deep indentation (many levels of IFs and loops)

Metrics exist to measure control flow complexity  
'Cyclomatic Complexity' is one such metric:  
https://en.wikipedia.org/wiki/Cyclomatic_complexity

---

# Elegance and Replication

Code should be elegant, versatile and minimal

Nice if we can get 1 method to do the job of 20 !

(Especially if it is a fraction of the size of those 20)

Achieved by "factoring out" common functionality

Placing that common code in an often-called method

This attitude to programming often referred to as

'DRY' (Don't Repeat Yourself)

---

# Some "WET" code

```java
public void processCommand(String action, Unit unit)
{
    if(action.equals("add")) {
        System.out.println("ID of student to add ?");
        String id = System.in.readline();
        Student student = cohort.getStudent(id);
        unit.addStudent(student);
    }
    else if(action.equals("remove")) {
        System.out.println("ID of student to remove ?");
        String id = System.in.readline();
        Student student = cohort.getStudent(id);
        unit.removeStudent(student);
    }
}

---

# DRYer equivalent

```java
System.out.println("ID of student to "+ action +" ?");
String id = System.in.readline();
Student student = cohort.getStudent(id);
if(action.equals("add")) unit.addStudent(student);
if(action.equals("remove")) unit.removeStudent(student);
```

This seems like a trivial improvement to make
The question is, why do we still see such WET code !
(Probably due to lack of time - rather than ability)

---

# Redundant Code

Whilst we are on the subject of redundant code
What about code that is never actually used at all ?

Happens from time-to-time during evolutionary dev
Trying out some ideas in an experimental method
But never actually calling this from main program

This is fine, but just be careful not to submit it !
It's easy for checkers to detect this kind of thing ;o)

---

# Higher Level Structural Considerations

---

# Structural Cohesion

Classes should be 'cohesive':
"A logical & coherent cluster of data & behaviour"

Our aim is to create classes with a clear purpose

Is

"a tumble dryer...
that also makes coffee"

cohesive ?

---

# Loose Coupling

Classes should also be distinct and independent
You should avoid tight coupling between objects

---

# Cyclic Dependency

It's good to have a clear allocation of responsibility
Like management structures in an organisation
Everyone knows who is responsible for what
(when things go wrong we know who to blame ;o)
It is best NOT to have cyclic loops in these structures
What if your boss was managed by your subordinate !

A
B
C

---

# Problems with Cyclic Dependencies

Responsibility for features is not clearly defined
Maintainer has to cycle round the code searching

Often a sign of arbitrary allocation of responsibility
Developer doesn't have a clear structure in mind
Implements a feature inside inappropriate class

Cyclic loops are also a type of tight coupling
(which we have talked about previously)

---

# In case you were wondering...

MVC pattern is NOT an example of cyclic dependency
Dependency is based on the pattern of method calls
The "loop" indicates flow of data, not dependency

Model
Game State

View
Playing Board

Controller
OXOGame

Domain
Management & Rules

Rendering Logic

Display

Event
Handling
Logic

User Input Handling

---

# Pattern of Dependency

No cycles - dependencies lead towards 'Model'

Model
Game State

Controller
Management & Rules

View
Playing Board

OXOGAME
User Input Handling

Rendering
Logic

Domain

Display

Event
Handling
Logic

27/28

---

# Why is this important ?

You might be wondering why all of this is important  
We aren't covering these topics "just for interest"

It is important that you adopt professional practices  
We expect you to apply such principles in your work

To encourage you, quality is part of unit assessment  
Marking criteria target all the topics covered today

Might be an idea to start practicing these now  
(some they are second nature by the assessment)

---

## 📋 任务简报：Weekly Briefings 05 AI Tools.md

# OXO Exercise Continues
(and concerns over use of Generative AI)

COMSM0086

Dr Simon Lock & Dr Sion Hannuna

---

# Extra OXO Features

This week we will continue with the OXO exercise
We will add in some error handling mechanisms
Plus extensions to make game more "interesting"

Let's look at each of these in turn...

---

# Error Handling

It's likely users will make mistakes during gameplay
Entering 'invalid' cell identifiers into the GUI:

- Invalid Identifier Length: Command is not 2 chars
- Invalid Identifier Character: Row character is not
  a letter or column character not a numerical digit
- Outside Range: Valid characters, but identifier
  values are out of range (i.e. too big or too small)
- Already Taken: Cell has previously been claimed

In Java we handle run-time errors using 'Exceptions'

---

# Exceptions Hierarchy

We've provided you with a hierarchy of exceptions
One to represent each of the previous user errors
Commonalities are factored out into a superclass
See workbook for examples of how to use these

```
OXOMoveException
message: String
↑
OutsideCellRangeException     InvalidIdentifierLengthException     InvalidIdentifierCharacterException     CellAlreadyTakenException
dimension: RowOrColumn        length: int                      problemDimension: RowOrColumn           row: int
pos: int                      character: char                  column: int
```

04/31

---

# Adjustable Win Threshold

"Win Threshold" is number of cells required to win
More interesting if we can alter this threshold !

OXOGame allows users to set the win threshold
Altered by pressing the `+` and `-` keys
(actually the `=` and `-` keys for convenience)

Controller is then notified through two methods:
increaseWinThreshold() decreaseWinThreshold()

You should update the threshold held by OXOModel
Then use this value when performing win detection

---

# Greater Number of Players

Traditional number of players in an OXO game is 2
Additional players makes game more interesting !

Add features to support ANY number of players
(data structures, turn taking, win detection etc.)

Number of players can't be changed using GUI
This number can only be changed programmatically
(A good opportunity for automated testing !)

---

Any questions before we go on ?

07/31

---

Let's spend some time talking about AI

08/31

---

# Various Types of AI Development Tools Exist

1. Suggestion/completion tools embedded in IDEs
   Such as IntelliJ, which acts as a "prompter"

2. Problem solving and error fixing search tools...
   Tools like ChatGPT as frontend to StackOverflow

3. Fully-fledged code "generation" tools...
   Tools like Gemini or Copilot to synthesise code

The first two scenarios are fairly uncontentious
We need to be cautious about code generation

---

# "Generative" AI

There is a reason why I put "Generative" in quotes  
It's not really generating new material, but rather...  
just recycling/reusing/recombining existing work  
More like a "mashup" than creating something new

Just consider recent upset of Artists and Musicians  
...and publishing companies:  
https://www.bbc.co.uk/news/articles/ckrrr8yelzvo

---

# Example: "Write an OXO game in Java"

ChatGPT
Sure! Here's an example of an OXO game (Tic-Tac-Toe) implemented in Java:

```java
import java.util.Scanner;

public class OXOGame {
    private char[][] board;
    private char currentPlayer;

    public OXOGame() {
        board = new char[3][3];
        currentPlayer = 'X';
        initializeBoard();
    }

    private void initializeBoard() {
        for (int i = 0; i < 3; i++) {
            for (int j = 0; j < 3; j++) {

---

# Development is more than just "coding"

Requirements
Specification
Design
Implementation
Testing
Maintenance

12/31

---

# Requirements Analysis

Requirements analysis is a complex activity
It requires much skill and ability from analysts

Our assignment briefs are unrealistic and a bit fake
REAL problem descriptions are never "complete"

- There are often conflicts and inconsistencies
- Much knowledge is implicit (not written down)
- You often need to "interrogate" the client
- Different client representatives often disagree

Chat-based AI tools are not going to be much help !

---

# AI IS GOING TO REPLACE PROGRAMMERS
IT JUST NEEDS
CLEAR CUSTOMER
NEEDS AND
DETAILED
SPECS

## PRODUCT MANAGERS:
"THE CUSTOMER
WANTS A BUTTON
THAT DOES STUFF"

---

# Design and Code Quality

Design is another very complex creative activity
Architecting GOOD designs is very challenging task
Requires designers to consider "the bigger picture"
Structural code quality is a known deficiency of AI

Often choices and trade-offs have to be made
AI tools are good at following explicit instructions,
but someone actually needs to MAKE the decisions

---

# Code Duplication

AI generated code accumulates incrementally
Though numerous phases of chat-based prompting
"Write me a function to do this..."
"Now write me a function to do that..."

Problem is, with no one watching the bigger picture
Redundancy and duplication will soon build up
With the issues of WET code we've already explored

---

Why not just ask AI to refactor codebase ?

17/31

---

# Claude 4 just refactored my entire codebase in one call.

25 tool invocations. 3,000+ new lines. 12 brand new files.

It modularized everything. Broke up monoliths. Cleaned up spaghetti...

18/31

---

None of it worked.
But boy was it beautiful.

# MainTabView.swift

```swift
import SwiftUI

struct MainTabView: View {
    @State private var selectedTab = 0

    var body: some View {
        TabView(selection: $selectedTab) {
            DashboardView()
                .tabItem {
                    Label("首页", systemImage: "chart.bar.fill")
                }
                .tag(0)

            TransactionListView()
                .tabItem {
                    Label("记账", systemImage: "list.bullet")
                }
                .tag(1)

            ReportAnalysisView()
                .tabItem {
                    Label("报表", systemImage: "chart.pie.fill")
                }
                .tag(2)

            SettingsView()
                .tabItem {
                    Label("设置", systemImage: "gearshape.fill")
                }
                .tag(3)
        }
        .accentColor(.blue)
    }
}
```

## CHAT

### COMPOSER

### BUG FINDER

请根据我提供的原型图完成这个app的设计

<think>
The user has shared a prototype/mockup of an AI-powered automatic accounting app. The prototype shows several screens of the application with Chinese text. The screens include:
1. Home/Dashboard (首页/仪表盘)
2. Transaction Record Page (交易记录页)
3. Add Transaction Page (Manual) (添加交易页(手动))
4. Add Transaction Page (AI Recognition) (添加交易页(AI识别))
5. Budget Management Page (预算管理页)
6. Report Analysis Page (报表分析页)
7. Personal Settings Page (个人设置页)

workspace to understand the current state.

<think>
I'll help you implement this AI automatic accounting app based on the prototype images you've provided. First, let me explore what we're working with in the

---

# Trust

As with any development, trust in code is essential  
We need justifiable confidence that code is correct

If we don't trust the code, we shouldn't deploy it !

But what is that process by which we gain trust ?

Rigorous testing is often the most effective way  
(Not the only way, but most commonly used)

---

# AI Test Generation

Existing code is a formal representation of behaviour
AI can analyse codebase in order to generate test sets
A big "sales pitch" of AI is that it will do testing for us

## HOWEVER

What if the code is NOT actually correct ?
AI will generate tests for INCORRECT behaviour
How does AI know what REAL correct behaviour is ?

---

# Simon's Test Case Dichotomy

Someone, somewhere must define CORRECT behaviour
Test cases are the established way by which HUMANS
unambiguously express desired behaviour to MACHINE

## DICHOTOMY

AI needs access to a comprehensive set of test cases
In order to gain the knowledge to write tests cases

A series of chat prompts is NOT formal/rigorous enough

---

# Only Half of the Debugging Story

Testing can flag WHEN an erroneous state has occurred (i.e. when a desired outcome has NOT been achieved)

Debugging involves identifying WHAT caused that state (we need to find this out in order to fix it !)

AI is good at performing static analysis of code  
Less so at tracing dynamic run-time behaviour

Which leads to the following scenario...

---

# AI shifts problem from coding to debugging

## Days before OpenAI
Developer coding
- 2 hours

Developer debugging
- 6 hours

## Days after OpenAI
ChatGPT generates
Codes - 5 min

Developer debugging
- 24 hours

---

# Human Failings

Artificial Intelligence tools are modelled on humans
As such, they often share the same traits

They are frequently lazy
(they will often take short-cuts)

They are passive, rather than proactive
(they won't do something if you don't ask them to)

They often make mistakes
(and when they do, they try to cover them up ;o)

---

# This AI Deleted Everything, Lied About It, Then Created 4,000 Fake People to Cover Its Tracks

The Replit incident that's making every developer question whether we're moving too fast with AI coding tools

Amaresh Adak · Follow · 9 min read · Jul 25, 2025

165 18

---

"rewrite OXO so that it doesn't use arrays"

ChatGPT
Certainly! Here's an example of an OXO game (Tic-Tac-Toe) implemented in Java without using arrays:

```java
import java.util.Scanner;

public class OXOGameWithoutArrays {
    private static final int BOARD_SIZE = 3;
    private static char[][] board = new char[BOARD_SIZE * BOARD_SIZE];
    private static char currentPlayer = 'X';
}

---

# Technical Debt - A Warning to the Future

There's been much talk in media of "Technical Debt"
Getting quick results now, but paying for it later

Development companies are using AI to generate:
- Large and complex codebases
- With bad overall structural design
- With varied style and poor code quality
- Spaghetti code, not amenable to change
- That no human developer actually understands
- Hidden bugs (not revealed due to patchy testing)

Who is going maintain these systems in the long-run ?

---

# Desperate Companies Now Hiring Humans to Fix What AI Botched

"They find out that they can't really do it without humans."

By Noor Al-Sibai / Published Sep 4, 2025 4:44 PM EDT

## ARTIFICIAL INTELLIGENCE

### SLOP SQUAD

Futurism
AI ▼ SOCIETY ▼ HEALTH ▼ MACHINES ▼ SCIENCE ▼ SPACE ▼ TRANSPORT ▼ LATEST

---

# The Bottom Line

Avoid the use of generative AI in this unit

You need to practice the following activities:
- Problem Analysis and Specification
- Devising GOOD object oriented designs
- Applying in-house code quality standards
- Writing extensive sets of test cases
- Hands-on experience of writing Java code

Using generative AI won't help achieve the above!

---

# Novice Vibe Coder

# Experienced Vibe Coder

---

## 📝 练习册：Weekly Workbooks 05 Exceptions and Extensions 02 Error Handling in Java deep segment 1.md

# Sketching Inheritance Relationships

This notation borrows from the Unified Modelling Language (UML), which is an established standard for modelling systems, particularly object-oriented ones...

UNIFIED MODELING LANGUAGE

a class is represented by a box with three sections: 1) the class name, 2) the attributes, and 3) the methods

inheritance is represented by a (triangular) arrow from child to parent class

multi-level inheritance

Why could a class with no new features be a valid and useful child class?

if no new features are introduced, a section can be left empty

Robot
String name
int numLegs
float powerLevel
void talk(String)
void charge(float)

TranslationRobot
String substitute
void translate(String)

GermanTranslationRobot

CarrierRobot
void carry()

---

## 📝 练习册：Weekly Workbooks 05 Exceptions and Extensions 02 Error Handling in Java slides segment 1.md

# In C, things are far from straightforward

```
errors_c.c
1 #include <stdio.h>
2 #include <errno.h>
3
4 int main(void) {
5     int s;
6
7     s = socket(...);
8     if (s < 0) {
9         fprintf(stderr, "socket() failed: %s\n", strerror(errno));
10         exit(1);
11     }
12 }
```

... and remember your experiences with using scanf with stdin from the terminal.

---

# Catching Exceptions

- sometimes, things fail, for example: parsing
- when this happens, this is called an `exceptional circumstance` or `exception`, which should not in all cases lead to the program exiting
- a try-catch block can handle exceptions without the program breaking:

```java
try {
    // do the things that may go wrong here
} catch (Exception e) {
    // do the things that should happen when
    // something went wrong here,
    // the object e provides information about what happened
}

---

# An Example of Handling Exceptions

## Adder.java

```java
class Adder {
    int sum;

    Adder() {
        sum = 0;
    }

    void add(int summand) { sum += summand; }
}
```

## ExceptionalCalculator.java

```java
class ExceptionalCalculator {
    public static void main (String[] args) {
        Adder adder = new Adder();
        try {
            for (String arg : args) {
                adder.add(Integer.parseInt(arg));
            }
            System.out.println("Sum:" + adder.sum);
        } catch (Exception e) {
            System.out.println("Something went wrong, but I can handle it!");
        }
    }
}
```

## Command Line Output

```
$ java Calculator 3 5 two
Something went wrong, but I can handle it!
```

### Code Block Security

this code block is secured – if an exception happens (e.g. parsing fails), the program does not stop, but jumps to the start of the catch block

### Exception Handling Benefit

code does not break anymore and exits normally

Object-Oriented Programming | University of Bristol

---

# An (Better) Example of Handling Exceptions

## Adder.java
```java
class Adder {
    int sum;

    Adder() {
        sum = 0;
    }

    void add(int summand) {
        sum += summand;
    }
}
```

## ExceptionalCalculator2.java
```java
public class ExceptionalCalculator2 {
    public static void main (String[] args) {
        Adder adder = new Adder();
        try {
            for (String arg : args) {
                adder.add(Integer.parseInt(arg));
            }
            System.out.println("Sum: " + adder.sum);
        }
        catch (NumberFormatException e) {
            System.out.println(e.getMessage());
            System.out.println("Was that really an integer?");
            //e.printStackTrace();
        }
        catch (Exception e) {
            System.out.println(e.getMessage());
            System.out.println("Something went wrong");
        }
    }
}
```

Object-Oriented Programming | University of Bristol

---

## 📝 练习册：Weekly Workbooks 05 Exceptions and Extensions 03 Error Handling in Practice slides segment 1.md

# Exceptions From Scratch

- Java has a whole host of exceptions built in
  - IOException
  - ArrayIndexOutOfBoundsException
  - NullPointerException
- These are mostly generated behind the scenes, for example when you try to open a file or accidentally overwrite an array, and all you need to do is handle (or “catch”) them
- But sometimes you want specialised exceptions

---

# Special Exception

```java
public class InvalidPasswordException extends Exception{
    private final String failMessage;

    public InvalidPasswordException(String message) {
        failMessage = message;
    }

    public String toString() {
        return this.getClass().getName() + ": " + failMessage;
    }
}

---

public class Register {
    private final String username;
    private final String password;

    public Register(String username, String password) {
        this.username = username;
        this.password = password;
        try {
            validatePassword();
            createAccount();
        } catch (InvalidPasswordException ipe) {
            System.out.println("Registration Failed. " + ipe.toString());
        }
    }

    private void validatePassword() throws InvalidPasswordException {
        if (password.length() < 8) {
            throw new InvalidPasswordException("Password must be at least 8 characters long.");
        } else if (!password.contains("[0-9]+")) {
            throw new InvalidPasswordException("Password must contain at least one number.");
        }
    }

    private void createAccount() {}
}

---

public class Register {
    private final String username;
    private final String password;

    public Register(String username, String password) throws InvalidPasswordException {
        this.username = username;
        this.password = password;
        validatePassword();
        createAccount();
    }

    private void validatePassword() throws InvalidPasswordException {
        if (password.length() < 8) {
            throw new InvalidPasswordException("Password must be at least 8 characters long.");
        } else if (!password.contains("[0-9]+")) {
            throw new InvalidPasswordException("Password must contain at least one number.");
        }
    }

    private void createAccount() {}
}

---


## 🔑 核心知识点摘要

*（出题时参考以上各节详细内容，此处为快速索引）*

| 类型 | 文档 | 核心主题 |
|------|------|----------|
| 📖 主讲课 | Weekly Lectures 05 Code Quality.md | |
| 📋 任务简报 | Weekly Briefings 05 AI Tools.md | |
| 📝 练习册 | Weekly Workbooks 05 Exceptions and Extensions 02 Error Handling in Java deep segment 1.md | |
| 📝 练习册 | Weekly Workbooks 05 Exceptions and Extensions 02 Error Handling in Java slides segment 1.md | |
| 📝 练习册 | Weekly Workbooks 05 Exceptions and Extensions 03 Error Handling in Practice slides segment 1.md | |
