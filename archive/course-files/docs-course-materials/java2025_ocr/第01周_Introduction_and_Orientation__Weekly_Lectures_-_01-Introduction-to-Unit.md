# Object Oriented Programming with Java

COMSM0086

Introduction and Orientation

---

# Meet The Team - Unit Directors

Simon

Sion

---

# Aim of this Unit

Our main focus will be on programming with Java
An essential element of which is 'Object Orientation'
(which is why the unit is called 'OOP with Java' !)

Object Orientation is a MAJOR concept in Comp Sci
It is not "owned" by Java - other technologies use it

OO is a total paradigm shift (quite literally)
There is more to learning a language than syntax !

---

# WARNING

Note that this unit is NOT JUST about "Coding"
(i.e. implementing a specification you've been given)

It is NOT JUST a re-run of TB1 programming units
(just using a different programming language)

It takes a broader perspective on 'Development'
(Analysis, Spec., Design, Testing, Maintenance etc.)

This unit uses tools from the 'Software Tools' unit
As well as processes & practices from 'Software Eng'

---

# TB1
## TB2
## Project
05/28

---

# Weekly Workbooks

Teaching centers around series of weekly workbooks
These contain various practical tasks to work through

Workbooks take a 'problem led' approach:
Tasks provide a reason/motivation for your learning

Templates/code examples are provided as needed
Lecture video fragments are integrated inline
"Content WHERE you need it, WHEN you need it"

---

# Sandwich ?

This unit is designed to have a "sandwich" structure

Self study: gain initial understanding of workbook

Lab session: one-on-one help to resolve problems

Self study: complete remaining workbook tasks

Don't expect...

To get everything done just

during the practical session !

---

# Weekly Practical Briefing

Each week there is a practical briefing session that:
- Explores the intricacies of the workbook
- Explains any essential concepts
- Introduces any key skills and tools needed
- Provides an opportunity for Q&A

Briefing takes place Monday at 10:00 in MBV 2.11
Duration will vary (depending on complexity of topic)
But that's fine, since briefing will flow straight into...

---

# Weekly Practical Lab

2 hour (approx) practical, starting at around 11:00
(starts after the weekly briefing has finished !)

You'll need to do some pre-processing of materials
Practical shouldn't be first time you open workbook !
(the top slice of bread in "the sandwich")

Opportunity to get one-on-one help and advice
With a team of skilled teaching assistants to help

---

Zik
Alex
Mahesh
Fred
Wallace

---

# Weekly Theory Lectures

Theory Lectures: Thursday 12:00 in Chemistry LT2
In these sessions we will go "deep" and "broad"... 

## Deep
Delve into complex low-level features of Java & OOP

## Broad
Situate unit within context of Software Development
(Analysis, Spec., Design, Testing, Maintenance etc.)

---

# Integrated Development Environment

Use of modern dev. environments is a key skill
NOW is right time to introduce this kind of tool !
On this unit we will be using the IntelliJ IDE

IntelliJ is already installed on the lab machines
You may wish to installing it on your own computer
We'll provide guidance on how to do this shortly

For this unit, you will need *at least* Java 17

---

# Assessments

There will be 2 assessed activities for this unit:
- 3 week practical exercise (starting in week 10)
- Written exam (sat during summer exam period)

Weighting will be 70:30 (coursework:exam)
Resit assessments may be offered over summer

---

Questions ?

14/28

---

# Java

Java is a very popular programming language
Used for large servers, desktop applications,
mobile devices, embedded processors etc.

It has very little in common with 'JavaScript' !
Other than a partially similar name
(and some common syntax)

Object Orientation is core - hence our interest

---

# What is Java like ?

Java is *a little bit* like C (syntax is quite similar)

There are however some important differences:

- No explicit pointers (no * or &) yay !!!
- Automated memory management (no malloc/free)
- No seg faults (you'll get 'exceptions' instead)
- Support for various Object Oriented constructs
- Greater platform independence (more shortly)

---

# Hello World

Here is the traditional 'Hello World' in Java:

```java
class HelloWorld
{
    public static void main(String[] args)
    {
        System.out.println("Hello World!");
    }
}
```

Some of it looks very similar to C
But there is lots of new stuff in there as well !

---

# Write Once, Run Anywhere

Power feature: Java runs the same on ALL platforms
Windows, OSX, Linux, Unix, BSD etc
(Except Android Java - which is VERY different !)

Source code compiled to cross-platform 'bytecode'
(halfway between source and binary executable)

Bytecode is then *interpreted* at runtime (kinda ;o)
This runs inside a standardised 'Virtual Machine'
This abstracts over the low-level detail of host OS

---

# C Programming - in Theory

Source Code
Compiler
OSX Executable
Linux Executable
Win Executable
OSX
Linux
Windows

---

# C Programming - in Practice

OSX
Source Code

Linux
Source Code

Windows
Source Code

Compiler

Compiler

Compiler

OSX Executable

Linux Executable

Win Executable

OSX

Linux

Windows

---

# Java Programming - in Theory & Practice !

Java Source Code
Java Compiler
Java Byte Code
Java Virtual Machine
Java Virtual Machine
Java Virtual Machine
OSX
Linux
Windows

21/28

---

# Performance

C has a reputation for being fast!
Java for being a little bit more "leisurely"
(Due to the overhead of bytecode interpretation)

HOWEVER

Almost all Java Virtual Machines use 'JIT' compilers
Convert bytecode to native executable AT RUNTIME
'Just-In-Time' to be executed (hence the name)

So performance difference is now fairly marginal

---

# What type of language ?

C is a procedural/imperative language
("do this and then do that")
With Functional Decomposition as main paradigm:
Functions DELEGATE work to sub-functions

Java is also a procedural/imperative language
But its INTENDED paradigm is Object Orientation:
Objects COLLABORATE together to achieve objective

Difference might seem subtle, but impact is great !

---

# Functional Decomposition (what C is)

Main function is broken down into smaller functions
Forms a tree, with data flowing around everywhere
Although effective programs can be written this way
They tend to be 'monolithic' ("big and frightening")
Also 'brittle' (resistant to long-term evolution)

---

# Object Orientation

Program written as decentralised cooperating pieces
Each piece (Object) looks after its own internal data
Collaborate with each other to get the job done
Scales well to larger projects (if done properly !)
Works effectively for large teams (if done properly !)

---

# What are Classes and Objects?

We've mentioned them in passing already
but what exactly ARE 'Classes' and 'Objects' ?

**CLASSES**: modules that divide up the source code
(Normally each file contains just a single Class)

**OBJECTS**: structures that divide up running program
(Each Object encloses its own state and data)

Classes can be viewed as a template (cookie cutter)
from which we can 'instantiate' live Objects

---

# Key Characteristics of Object Orientation

Abstraction: sophistication, but with simple interface
Encapsulation: inner working locked away out-of-sight
Inheritance: hierarchies of Classes share behaviours
Polymorphism: like Classes can be treated the same

Yes, these are all very vague, high-level descriptions
But we'll explore them all in more detail next week!

---

Let's take a look at that First Workbook

https://github.com/drslock/JAVA2025

Clone whole repo to your local computer
Then view _either_ the README _or_ index.html

README
index