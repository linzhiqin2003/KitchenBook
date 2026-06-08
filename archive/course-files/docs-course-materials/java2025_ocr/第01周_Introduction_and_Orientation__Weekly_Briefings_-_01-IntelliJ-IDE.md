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