# 第01周：Introduction and Orientation

> UoB Computer Science - Java 2025
> 提取自课件 PDF，用于 AI 出题知识库

---

## 📖 主讲课：Weekly Lectures 01 Introduction to Unit.md

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

---

## 📋 任务简报：Weekly Briefings 01 IntelliJ IDE.md

# Getting Started with IntelliJ

COMSM0086

Dr Simon Lock and Dr Sion Hannuna

---

# Overview

- Downloading and installing IntelliJ IDE
- Dealing with User Agreement and Licensing
- Opening an existing template project
- Installing the Java Development Kit (JDK)
  (including compiler, runtime and libraries)
- Running your first Java program !

Note: We will skim through these slides quite quickly now
Work through them at your own pace in practical session

---

# Do you need to install ?

You don't HAVE to install IntelliJ on your laptop
The lab machines are fully installed and set up:
/opt/idea/2025/bin/idea.sh
License Server: http://ls-jetbrains.bris.ac.uk:8080

## HOWEVER

Many people choose to work on their own machines
Just so they can work from home (and at any time)

If you do decide to install, here are a few tips...

---

# Download from JetBrains

Make sure you get the download for your platform!
(Website *should* autodetect to the right version)

Windows macOS Linux

![IntelliJ IDEA Ultimate Logo](https://example.com/logo.png)

IntelliJ IDEA Ultimate

The Leading Java and Kotlin IDE

[Download](#) .dmg

Free 30-day trial

ℹ️ Select an installer for Intel or Apple Silicon

Version: 2023.3.2  
Build: 233.13135.103  
20 December 2023

- [System requirements](#)
- [Installation instructions](#)
- [Other versions](#)
- [Third-party software](#)

```java
// Convert regular functions to @Link MultivariateDifferentiableFunction
public static MultivariateDifferentiableFunction toDifferentiable(final MultivariateFunction f) {
    return new MultivariateDifferentiableFunction() {
        @Override
        public double value(final double[] point) {
            return f.value(point);
        }

        @Override
        public DerivativeStructure value(final DerivativeStructure[] point) {
            // set up the input parameters
            final double[] dPoint = new double[point.length];
            for (int i = 0; i < point.length; ++i) {
                dPoint[i] = point[i].getValue();
                if (point[i].getOrder() > 1) {
                    throw new NumberIsTooLargeException(point[i].getOrder(), 1, true);
                }
            }
            // evaluate regular functions
        }
    };
}

---

# Alternative Approach

IntelliJ might be available through your platform's Package Manager (if it has one !)

IDEA Ultimate
Source Snap Store (Snap)

IDEA Ultimate
jetbrains✓
★★★★ (192)

Install

05/33

---

Install as normal (for your platform) !

06/33

---

# User Agreement

First time you run IntelliJ, you'll see User Agreement
Tick the box and click continue if you are happy !

## JETBRAINS USER AGREEMENT

Version 1.4, effective as of September 22, 2021

IMPORTANT! READ CAREFULLY:

THIS IS A LEGAL AGREEMENT. BY CLICKING ON THE “I AGREE” (OR SIMILAR)
BUTTON THAT IS PRESENTED TO YOU AT THE TIME OF YOUR FIRST USE OF
THE JETBRAINS SOFTWARE, SUPPORT, OR PRODUCTS, YOU BECOME A PARTY
TO THIS AGREEMENT, YOU DECLARE YOU HAVE THE LEGAL CAPACITY TO
ENTER INTO SUCH AGREEMENT, AND YOU CONSENT TO BE BOUND BY ALL THE
TERMS AND CONDITIONS SET FORTH BELOW.

### 1. PARTIES

1.1. “JetBrains” or “we” means JetBrains s.r.o., having its principal place of
business at Na Hrebenech II 1718/10, Prague, 14000, Czech Republic, registered
in the Commercial Register maintained by the Municipal Court of Prague, Section
C, File 86211, ID No.: 265 02 275

☑ I confirm that I have read and accept the terms of this User Agreement

Exit Continue

---

# Register for an Educational License

https://jetbrains.com/community/education/#students

Apply with
University email address ISIC/ITIC membership Official document

Status:
- I'm a student
- I'm a teacher

Level of study
Undergraduate

Is Computer Science or Engineering your major field of study?
- Yes
- No

Email address:
University email address, e.g. js@mit.edu

I certify that the university email address provided above is valid and belongs to me.

---

# License Settings

"Log In to JetBrains" if you have an educational license
"Start Trial" if you haven't yet registered with JetBrains

IntelliJ IDEA
Activate

Plugins

AI Assistant
Activate to enable

Code With Me
Activate to enable

Log in...

Proxy settings

Activate IntelliJ IDEA Start trial View plans and pricing

Get license from:
JetBrains Account Activation code License server

Log In to JetBrains Account... Register...

Exit

---

# Final Step for Educational License

Make sure you click the "Activate" button!

IntelliJ IDEA
Active until October 1, 2024

Plugins

AI Assistant
Activate to enable

Code With Me
Active until October 1, 2024

Simon Lock

Proxy settings
Activate plugin to enable paid functions

Activate IntelliJ IDEA
Start trial
View plans and pricing

Get license from:
JetBrains Account
Activation code
License server

Active license: Licensed to Simon Lock, For educational use only
Subscription is active until 01/10/2024

Activate
Cancel
Refresh license list

Continue

---

And that should provide you with
the same software as on the lab machines

Once you have the IDE installed...
How do we go about compiling and running code ?

---

# Welcome Screen

Most of the time on this unit you'll need "Open"
This is because we provide blank template projects
(Although you do get to practice creating a new project)

Welcome to IntelliJ IDEA
Create a new project to start from scratch.
Open existing project from disk or version control.

New Project  Open  Get from VCS

---

# Typical Project Template

Find and open the FOLDER containing the pom.xml file

```
Favorites
Recents
Applications
Desktop
Documents
Downloads

Locations
iCloud Drive
Green
Blue
Purple
```

| Name     | Kind          | Date Added      |
|----------|---------------|-----------------|
| mvnw     | Unix Ex...ble File | 6 Dec 2023 at 01:54 |
| mvnw.cmd | Document      | 6 Dec 2023 at 01:54 |
| pom.xml  | XML text      | 6 Dec 2023 at 01:54 |
| src      | Folder        | 6 Dec 2023 at 01:54 |
| target   | Folder        | 6 Dec 2023 at 01:54 |

New Folder Cancel Open

---

# Do You Trust Us ?

Be careful with projects from other sources !

## Trust and Open Project 'cw-shapes'?

IntelliJ IDEA provides features that may execute potentially malicious code from this folder.

If you don't trust the source, preview the project in the safe mode to only browse its code.

- Trust projects in ~/Development/Weekly Workbooks/01 Introduction to OOP/IntelliJ Template

Don't Open Preview in Safe Mode Trust Project

---

# Project Structure

A successfully opened project looks something like this:

```
Project
├── cw-shapes ~/Desktop/cw
│   ├── .idea
│   ├── .mvn
│   ├── src
│   ├── target
│   │   ├── mvnw
│   │   ├── mvnw.cmd
│   │   └── pom.xml
│   ├── External Libraries
│   └── Scratches and Consoles
```

Search Everywhere Double ⇧
Go to File ⇧⌘O
Recent Files ⇧E
Navigation Bar ⇧↑
Drop files here to open them

cw-shapes > src > main > java > edu > uob > Shapes

---

# Open the Main Class

Let's explore the project view to find the main class
In this project, the main class is a file called 'Shapes'

Project ▼
cw-shapes ~/Desktop/cw-shapes
> .idea
> .mvn
src
> main
> java
> edu.uob
Circle
Shapes
Triangle

Shapes.java ×
1 package edu.uob;
2
3 public class Shapes {
4
5 // TODO use this class as then entry pc
6 public static void main(String[] args)
9 }

---

# "Project JDK is not defined"

IntelliJ is just an IDE - is has no built-in compiler !
Lab machines have Java Development Kit installed
If working on your own laptop, YOU must install it

```
Project ▼  ◯  ◇  ×  :  —
Circle
Colour
MultiVariantShape
Rectangle
Shapes
Triangle
TriangleVariant
TwoDimensionalShape
```

```
Shapes.java
Project JDK is not defined  Setup SDK

1   package edu.uob;  ⚠️ 2  ⚠️ 1  ^  v
2   1 usage
3   public class Shapes {
4
5   // TODO use this class as then
6   public static void main(String[] args) {
```

17/33

---

# Project Settings (File > Project Structure !!!)

Need to select a JDK to use to compile & run project
Could use an existing JDK (if you have one installed)
Or download a new one from list of those available...

Project Settings
Project
Modules
Libraries
Facets
Artifacts
Platform Settings
SDKs
Global Libraries

Project
Default settings for all modules. Configure these parameters for each module on the m

Name: cw-shapes

SDK:
<No SDK>
Download JDK...
Add JDK...

Language level:

Compiler output:

directories for

---

# Download JDK

Select JDK to automatically download & install
Lowest Common Denominator: Lab has Java 17
(That's where we are going to mark your code !)
Best to choose: Eclipse Temurin (AdoptOpenJDK)

Version: 17
Vendor: Eclipse Temurin (AdoptOpenJDK HotSpot) 17.0.9

Cancel Download

---

# Installation Location

Keep a note of location where IntelliJ will install JDK
You'll need this later (to compile on command line)
On Mac OSX the location will be something like:
~/Library/Java/JavaVirtualMachines/temurin-17.0.9

Version: 17
Vendor: Eclipse Temurin (AdoptOpenJDK HotSpot) 17.0.9
Location: ~/Library/Java/JavaVirtualMachines/temurin-17.0.9

Cancel Download

---

# Be Patient !

It takes a while for the JDK to download and install
Don't worry, only happens once (when you first install)
Keep an eye on how things are going on progress bar:

Indexing JDK 'temurin-17'

---

# Using an Existing JDK

If you already have a JDK installed, you can use that
This will save you having multiple versions installed
It *might* be listed in dropdown, if not click "Add JDK"

Project Settings
Project
Modules
Libraries
Facets
Artifacts
Platform Settings
SDKs
Global Libraries

Project
Default settings for all modules. Configure these parameters for each module on the m
Name: cw-shapes
SDK: 
Language level:
Compiler output: 

<No SDK>
Download JDK...
Add JDK...

---

# Hunting down Existing JDK

IntelliJ is clever and will usually find installed JDKs
I installed JDK using 'Homebrew' package manager
Homebrew is good at hiding installed software ;o)
So I needed to manually hunt around to find the JDK

| Name | Size | Kind | Date Added |
| --- | --- | --- | --- |
| local | -- | Folder | 6 Dec 2023 at 08:43 |
| bin | -- | Folder | 6 Dec 2023 at 08:45 |
| etc | -- | Folder | 6 Dec 2023 at 09:53 |
| opt | -- | Folder | 6 Dec 2023 at 09:53 |
| 0mq | 24 bytes | Alias | 6 Dec 2023 at 12:36 |
| openjdk | 21 bytes | Alias | 2 Jan 2024 at 20:29 |

---

# JDK Version

The version I have installed is more recent than 17
However, we can limit language features used to 17
Prevents use of newer features that won't work in lab

## Project

Default settings for all modules. Configure these parameters for each module on the module page as needed.

Name: cw-shapes

SDK: 21 version 21.0.1 Edit

Language level: 17 - Sealed types, always-strict floating-point semantics

---

# REMEMBER

Labs machines ALREADY have a JDK installed
(so you won't need to follow the previous steps)
You only need to install JDK on your OWN laptop

Back to the Project...

---

# Ready to Run !

With the main class open in the editing panel...
You should now see the green "run" button at the top

26/33

---

# Success !

Might take a while for IntelliJ to compile & run the code
It has to build a lot of files the first time around
If everything worked OK, you should see...

Hello world!
Process finished with exit code 0

---

# Command Line

Although we will be using IntelliJ *most* of the time
It is useful to also be able to use the command line

Coursework will be marked on the command line
It's essential that you check your code runs there !

In order to be able to compile and run your code
You must tell command line where to find the JDK...

---

# OSX and Linux Environment Variables

Add two environment variables to your shell config file
(~/.profile on OSX or ~/.bashrc on linux)

JAVA_HOME must point to your installed JDK folder

You must also prepend the JDK *bin* folder to $PATH

```
export JAVA_HOME="/usr/local/opt/openjdk/"
export PATH="/usr/local/opt/openjdk/bin:$PATH"

---

Please note that:
/usr/local/opt/openjdk/
Is the location of MY installation of the JDK
YOURS is going to be somewhere different !
(wherever IntelliJ said it was going to put it)

---

# Windows Environment Variables

Environment Variables in Windows are set differently
Using a graphical interface in "System Preferences"
See separate guide to setting up JDK on windows

## User variables

| Variable | Value |
|----------|-------|
| Path     | C:\Program Files (x86)\Common Files\Oracle\Java\javapath;C:\Wi... |
| TEMP     | C:\Users\ AppData\Local\Temp |
| TMP      | C:\Users\ AppData\Local\Temp |

New... Edit... Delete

---

# Testing Your Environment

Open a fresh terminal or command prompt and type:
```
java -version
```

If everything worked, you'll see something like:

```
Last login: Wed Jan 3 23:34:17 on ttys000
~$ java -version
openjdk version "21.0.1" 2023-10-17
OpenJDK Runtime Environment Homebrew (build 21.0.1)
OpenJDK 64-Bit Server VM Homebrew (build 21.0.1, mixed mode, sharing)
~$

---

And now to work !

33/33

---

## 📝 练习册：Weekly Workbooks 01 Introduction and Orientation 03 Hello World slides segment 1.md

# Hello World

Here is the traditional "Hello World" in Java:

```java
class HelloWorld
{
    public static void main(String[] args)
    {
        System.out.println("Hello World!");
    }
}
```

Lots of stuff in there !
Some of it looks a bit similar to C ?
We'll address most of this in later lectures

---

## 📝 练习册：Weekly Workbooks 01 Introduction and Orientation extras maven.md

# The Maven Build System

## Features of build systems

Any build system needs to provide a core set of features which should include the following:

- Artefact generation - we want our executable program at the end, just like in Make
- Unified testing - we need a unified way to run some tests on our code, we'll dive into more details on what testing is about next week
- Dependency resolution - modern software development is all about not reinventing the wheel, Maven provides a simple and declarative way of getting wheels invented by someone else on the internet (license permitting of course!)

You many be wondering, why can't we just stick with IntelliJ's project structure? From the outset, it seems to support adding dependencies and you can run your program with relative ease. However, IntelliJ's project structure is not portable; you can't run your project on another computer unless it has IntelliJ installed.

Let's discuss how Maven provides the portable aspect in the follow sections.

## Convention over configuration

One of the most important aspect of Maven is that it requires a specific file structure and a specific set of files for your project work; the core philosophy of Maven is convention over configuration.

Per convention, Maven projects uses this directory structure:

```
├── .mvn - Maven wrapper binaries
├── mvnw - Maven wrapper for *nix
├── mvnw.cmd - Maven wrapper for Windows
├── pom.xml - Maven "Project Object Mode", or build configuration (mandatory)
├── README.md - include any other files for humans, maven don't care about these
└── src - source directory, contains all (only) source file (essentially mandatory)
    ├── main - application sources (essentially mandatory)
    │   ├── java - java source files
    │   └── resources - resources needed by other source files (optional)
    └── test - test sources (optional)
        ├── java - java test sources
        └── resources - resources needed by tests only
```

**Note**: Changing the overall directory structure will almost certainly cause the project to not compile, as expected.

Maven will perform compilation tasks with respect to this directory structure and handle all the intricacies of setting the classpath for you (it's more complicated than it should be because of how each platform handles paths).

Notice the mvnw, mvnw.cmd, and .mvnw entries, those are not part of the standard maven project. Those files are a wrapper files that delegate commands to the real maven executable and in cases where maven is missing, download and install it. We will revisit the use of these files in later sections.

## The Project Object Model

Residing in the project root is the pom.xml file. This file describes the current project in XML, here's a sample pom.xml file:

```xml
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">

---

<modelVersion>4.0.0</modelVersion>

<groupId>com.mycompany.app</groupId>
<artifactId>my-app</artifactId>
<version>1.0-SNAPSHOT</version>
<packaging>jar</packaging> <!-- we want a jar file as the executable -->

<name>My Project</name> <!-- your project name here -->

<dependencies>
  <dependencies>
    <!-- specify your dependencies here -->
    <dependency>
      <groupId>org.junit.jupiter</groupId>
      <artifactId>junit-jupiter</artifactId>
      <version>5.8.2</version>
      <scope>test</scope>
    </dependency>
    <dependency>
      <groupId>org.junit.platform</groupId>
      <artifactId>junit-platform-suite</artifactId>
      <version>1.8.2</version>
      <scope>test</scope>
    </dependency>
  </dependencies>
</dependencies>

</project>

---

The file is divided into several section:

## Maven Coordinates

The maven coordinate looks like following:

```xml
<groupId>com.mycompany.app</groupId>
<artifactId>my-app</artifactId>
<version>1.0-SNAPSHOT</version>
<packaging>jar</packaging>
```

It is used for others to find your project or for you to reference your own projects.

- groupId - a name to identify which group this package is from. By convention, it should be the root Java package name of the project.
- artifactId - the project name but without spaces or special characters.
- version - the version number of the project, can be any arbitrary string

As we'll be developing software for our own use, we can make something up here.

## Dependencies

Maven projects can include other projects as a dependency. For example, in a later task we will be using a development tool call JUnit. In the following Maven fragment, we include JUnit as a dependency:

```xml
<dependencies>
  <dependency>
    <groupId>org.junit.jupiter</groupId>
    <artifactId>junit-jupiter</artifactId>
    <version>5.8.2</version>
    <scope>test</scope>
  </dependency>
</dependencies>
```

---

<dependency>
    <groupId>org.junit.platform</groupId>
    <artifactId>junit-platform-suite</artifactId>
    <version>1.8.2</version>
    <scope>test</scope>
</dependency>
</dependencies>

All the required class/resources for JUnit will be downloaded and be ready to use in our project. Maven will also download additional dependencies that JUnit itself requires.

You don't need to worry about the operation of JUnit at this stage - we will introduce it properly later on in this unit (and probably in your other units as well!)

## Available libraries

If you're interested in what sort of libraries is available for use, you can search for dependencies to use on sites such as these:

*   [mvnrepository](https://mvnrepository.com/)
*   [The Central Repository](https://search.maven.org/)

There are other root level tags that specify build plugins and reports which we won't go into for this unit, you can read more about them [here](https://maven.apache.org/guides/index.html).

As this isn't a course focused on DevOps or build systems, we will only use Maven as a tool to help everyone compile and build your Java project in a controlled and predictable way. Using Maven has the added advantage that TAs can better help you in case there are configuration problems.

---


## 🔑 核心知识点摘要

*（出题时参考以上各节详细内容，此处为快速索引）*

| 类型 | 文档 | 核心主题 |
|------|------|----------|
| 📖 主讲课 | Weekly Lectures 01 Introduction to Unit.md | |
| 📋 任务简报 | Weekly Briefings 01 IntelliJ IDE.md | |
| 📝 练习册 | Weekly Workbooks 01 Introduction and Orientation 03 Hello World slides segment 1.md | |
| 📝 练习册 | Weekly Workbooks 01 Introduction and Orientation extras maven.md | |
