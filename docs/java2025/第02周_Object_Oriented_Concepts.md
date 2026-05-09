# 第02周：Object Oriented Concepts

> UoB Computer Science - Java 2025
> 提取自课件 PDF，用于 AI 出题知识库

---

## 📖 主讲课：Weekly Lectures 02 Key Language Constructs.md

# Key Object Oriented Language Constructs

COMSM0086

Dr Simon Lock & Dr Sion Hannuna

---

# Overview

The aim of today's session is to further explore some of the key OO concepts mentioned previously

Note: for your convenience, fragments of this lecture will appear embedded within each workbook section Allows you to refresh memory when attempting tasks

There are also additional slides/video in the workbooks Be sure to view these: some have not been seen before

---

# Warning

We are about to see a LOT of terminology !

You won't be expected to remember it all immediately
It will become more familiar over the next few weeks

Any terms in 'single quotes' are OFFICAL terminology
Anything in "double quotes" are my own informal words
(used to give you an intuitive feel for the concepts)

See the next slide for some examples...

---

# Classes

A 'Class' is a module of source code written in Java
For time being, think of it as a "fancy" struct from C

```java
class Counter
{
    // Code for class goes here !
}
```

We advise a 1-1 mapping between 'Class' and 'file'
Name of a class should match the name of the file
So the above would be in a file called Counter.java

---

# Objects and Instances

'Classes' are source code that you have written
A 'Class' describes a particular type of 'Object'

'Instances' of a class are created at run time
These live dynamic things are the 'Objects' in OOP

Process of creating live 'Objects' from 'Classes' is:
'Instantiation'

---

# Java Types

Java's 'Primitive' data types should be quite familiar (int, char, boolean, float etc. - note all lower case !)  
These primitives are just simple data (just like in C)

We can however ALSO use Classes as data types !  
These are more sophisticated: Data AND Behaviour

Java provides the concept of an 'array' (just like C)  
These can contain _either_ 'Primitives' _or_ 'Objects'  
Arrays are 'homogenous': all elements of same type  
(well, kinda ;o)

---

# Attributes

A Class has a number of data fields or 'Attributes'
These are global to (accessible within) that class
Importantly NOT (usually) global to whole program
This is that notion of 'Encapsulation'

For example:

```cpp
class Counter
{
    int count = 0;
}

---

# Methods

Classes have a bunch of "functions" called 'Methods'

```java
class Counter
{
    int count = 0;
    void increment() {
        count++;
    }
}
```

Such methods are "attached to" a particular Class
Methods are called ON a specific instance of a Class

```java
Counter cinemaSeatCounter;
cinemaSeatCounter.increment();

---

# Difference Between Functions & Methods

Methods are "tied to" a particular Class/Object
Functions are just "floating around" in namespace

In C you just call a function in isolation:
```
printf("Hello");
```

In Java you call a method ON a particular Object:
```
out.printf("Hello");
file.printf("Hello");
serial.printf("Hello");

---

# Standard Naming Conventions

Classes: camel case, starting with a capital
String, RallyCar, FlyingRobot, WarmBloodedAnimal

Objects/Instances: camel case, starting with lower case
colour, carCounter, termTimeAddress, fluffyBunny

Methods: camel case, starting with lower case
draw, incrementCounter, getAddress, strokeBunny

We don't use underscores (this isn't Python)

---

# Constructor Methods

Special methods exist to initialise instances of Class
These 'constructors' have same name as the Class

```java
class Counter
{
    int count;

    public Counter() {
        count = 0;
    }
}

Counter myCounter = new Counter();
```

Notice: no return type is defined for a constructor !
'public' so that it can be called from anywhere

---

# Multiple Constructors

We can write a simple constructor (default values):

```java
public Counter() {
    count = 0;
}
```

Or complex ones, where we pass in some value(s):

```java
public Counter(int startValue) {
    count = startValue;
}
```

Providing more than one method with the same name in this way is referred to as 'Overloading'

---

# Example Class

Java has a String class to store & manipulate text
Inside there's some kind of array to store characters
(That's Abstraction and Encapsulation in action !)

Also a bunch of methods that "do things to" String:
- length: returns number of characters in the text
- charAt: gives you the char at a particular position
- contains: tells you if string contains a sequence
- toLowerCase: converts string into lower case text
- substring: splits off a chunk of the string

---

# Example Objects

We can create Objects (instances) of the String class
Each with a different character sequence inside:
```java
String firstUnit = new String("COMSM0103");
String secondUnit = new String("COMSM0204");
```

There is (just for the String class) a shorthand:
```java
String thirdUnit = "COMSM0305";
```

Provided because creating Strings is soooo common

---

# Inheritance

Powerful feature to reuse & extend existing code

Take the String class for example...
Currently it is just plain text
But what if we wanted to add text styling ?
(Bold, Italics, Underline etc.)

We could 'extend' the basic String Class,
making use of all of the existing methods,
but also adding in some extra ones of our own...

---

# StyledString Class

```java
class StyledString extends String
{
    void setUnderlined(boolean underline) {
        // Some code goes in here !
    }

    void setItalics(boolean italic) {
        // Some code goes in here !
    }
}

---

# Overall Outcome

We've only added two new methods to StyledString:
- setUnderlined
- setItalics

But, because we are 'extending' String, we also get:
- length
- charAt
- contains
- toLowerCase
- etc.

All for free !

---

# Overriding

Adding features to a 'child' (the extending class)
Is often achieved by *replacing* an existing method
With *a new one* containing additional features

We write a method, with duplicate name & params
This replaces original method of the 'parent' class

This is called 'Overriding'
'Method in child class overrides the method of parent'

---

# Method 'Chaining'

If we are REALLY clever...

We can REUSE the method of 'superclass' (parent)

And then "tack on" the extra features at the end:

```java
public String toString()
{
    String text = super.toString();
    if(isUnderlined) text = "\033[4m" + text + "\033[0m";
    if(isItalics) text = "\033[3m" + text + "\033[0m";
    return text;
}
```

Note use of 'super' as a reference to the superclass

---

# Polymorphism

It is possible to "do things to" "families" of classes
Without caring exactly which class we are doing it to
For example, we can "do things to" ALL 3D shapes
(Such as getting volume, rotating in 3 axes etc.)
Without caring if it is a Sphere, Cube or Tetrahedron

```
Shape
   |
   |--- TwoDimensionalShape
   |      |--- Circle
   |      |--- Square
   |      |--- Triangle
   |
   |--- ThreeDimensionalShape
          |--- Sphere
          |--- Cube
          |--- Tetrahedron

---

# Polymorphism in Action

What if we don't know what kind of String to expect ?

It might be a String, StyledString, ColourString...

Don't want to write a different method for each type

Luckily we don't have to !

We can just write a "general purpose" method:

`public String correctSpelling(String text) ...`

And this will be able to operate on ANY kind of String
(Anything that is a String or any 'subclass' of String)

---

# Encapsulation

If this were C, we could just "reach in" and set the style boolean attributes like so:

```c
myString.isUnderlined = true;
myString.isItalics = true;
```

But this is very dangerous!
We don't know how the object uses these attributes
How can we be sure that it is safe to change them?

---

# DVD Collection Example

Imagine that you had a collection of DVDs
Your friends can come and ask to borrow one
You can keep track of who has which disc
(You might even record loans in a relational DB ;o)

But what would happen if people could just walk in,
and take them without even asking !
There would be chaos !!!
You wouldn't know where anything was :o(

---

# Accessor and Mutator methods

We may wish external objects to access internal data
But must ensure this is done in a controlled manner

Can be achieved by providing additional methods...
'Accessors' ("Getters") and 'Mutators' ("Setters"):

boolean isUnderlined = false;

void setUnderlined(boolean underline)... // Setter
boolean getUnderlined()...               // Getter
boolean isUnderlined()...               // Alternative

---

# Controlling Access

We can define attributes and methods to be:
- 'public' access from any location (avoid variables)
- 'private' only inside class in which they're defined
- 'protected' inside the class OR any subclass
(also from any class in the same package/folder)

If you don't specify any of the above, you will get:
"semi-protected" (let's NOT even go there just now)
Just use 'public' or 'private' (as appropriate) for now

---

This probably doesn't make much sense at the moment!
Things *should* become clearer during the workbook

Review video fragments of this lecture as needed
They are embedded in the workbook for this purpose!

At some point you'll be able to talk fluent "java-speak"
(and will wonder how you ever managed before ;o)

---

## 📋 任务简报：Weekly Briefings 02 Shapes Exercise.md

# Week 02 Practical Briefing

COMSM0086

Dr Simon Lock and Dr Sion Hannuna

---

# Overview

For each exercise we'll provide a Maven template
This week we use a template called "cw-shapes"

Avoids you having to do all the boring setup work
Means you can get on and focus on programming

There are features of Maven we haven't covered yet
Worth spending time exploring them in more detail
You may cover these again in 'Software Tools' !

---

# Maven Recap

Maven is a cross-language build environment
A bit like 'make', but a lot more sophisticated

Maven is very useful for managing dependencies
Not only for *specifying* required libraries...
...but also for *installing* them

You may have noticed a lot of text scrolling past ?
(especially the first time you ran 'mvnw compile')
That was Maven installing various libs and plugins

---

# Maven in More Detail

Core to Maven is the 'Project Object Model' file:
**POM**

This describes a project and its dependencies

Most IDEs support Maven POM files - including IntelliJ !
So you can open/import a Maven project seamlessly

Maven also defines various standards & conventions
Including structure and content of the project folder...

---

# 05/21

mvnw
mvnw.cmd
pom.xml
src
main
java
edu
uob
Circle.java
Colour.java
MultiVaria...
Rectangle.j
Shapes.java
Triangle.jav
TriangleVari
TwoDime...l
test
target

---

# Testing and Reporting

There is more to Maven than compiling & running
It supports various other development activities:
Code Analysis, Unit & Integration Testing, Reporting

In this unit we make extensive use of testing tools
Test Driven Development (TDD) is a key activity
So much so that it is touched on in all three units!
We'll revisit this topic in detail later in this briefing

---

# This Week's Workbook

But now let's take a look at this week's workbook
It's a fairly easy and straightforward set of tasks
It's all based around various 2 dimensional shapes
The main shape of interest will be the Triangle !

You may have attempted some of the tasks already
It won't hurt to do a quick recap of tasks completed
Chances are you won't have finished everything !

---

# Workbook: Task 1

This section mainly just introduces the workbook
Including a recap on a number of key OO concepts:

Abstraction
Encapsulation
Polymorphism
Inheritance
Class
Object

08/21

---

# Workbook: Task 2

Slides/video refresh memory on Objects & Classes

A few "fairly gentle" practical tasks to achieve:
- Add a constructor method to the Triangle class
- Add 3 parameters to constructor (side lengths)
- Store side lengths as int variables ('attributes')
- Write a method that returns the longest side

Then add a few lines of code to test above features

Create a few triangles to be sure everything works

---

# Workbook: Task 2 cont.

Add a 'toString' method that describes the triangle:

This is a Triangle with sides of length 4, 5, 7

Note that ALL Java Objects have a 'toString' method
It's good practice to override the default with your own
You should always try to return something descriptive
If you don't provide a 'toString' method, you just get:

edu.uob.Triangle@754dd69e

---

# Workbook: Task 3

Explores the topics of Inheritance & Polymorphism
Slides and Video fragments from previous lecture

"Introduce" Triangle into hierarchy (using 'extends')
Use polymorphism to store different shapes...
All in the same 'TwoDimensionalShape' variable !

Some additional "PRO" material for deeper insight
(referencing, avoiding duplication, inheritance)
From the UG unit - provided "for interest"

---

# Workbook: Task 4

Explores the topics of Abstraction & Encapsulation
Again, slides/video fragments from previous lecture

Add a 'Colour' variable to 'TwoDimensionalShape'
Important that 'Colour' is private (hidden inside)

Again, some optional "PRO" materials available
Find out about the subtleties of public/private

---

# Workbook: Task 5

Refresher slides on "getters" and "setters"
Officially called 'accessor' and 'mutator' methods

Add 'getColour' & 'setColour' methods to shape class
Add colour details to string returned from 'toString'

Question: Where is the best place to add this code ?
HINT: Which shapes can have a colour ?
HINT: Could you use 'overriding' and 'chaining' ?

---

# Workbook: Task 6

We provide an enum to represent triangle "variants":  
EQUILATERAL, ISOSCELES, SCALENE, RIGHT, FLAT etc.

Add code to constructor to work out which variant  
Store the result in a private attribute inside the class  

To start, focus on whether or not it is EQUILATERAL  
(You can consider other variants in a later task)

Write a 'getVariant' method that returns the attribute  
In order to allow other objects to access the variant

---

# Workbook: Task 7

Now work through the remaining types of triangle:
EQUILATERAL, ISOSCELES, SCALENE, RIGHT, ILLEGAL etc.

Add code to decide which type of Triangle it is
Order you consider variants in code IS important:
- Check "bad" variants first (ILLEGAL, IMPOSSIBLE)
- Then check "simple" variants (e.g. EQUILATERAL)
- Finally move on to check for "difficult" variants

---

# Workbook: Task 7 cont.

Rather than manually adding/removing test code
(In order to create test triangles and do printIns)
We will instead do something more systematic !
We have provided a JUnit test script:
TriangleTests
Drop this file into your project and then...
Use IntelliJ to run the test methods

@Test
void testEquilateral() { assertShapeVariant(TriangleVariant.EQUILATERAL,

---

# Workbook: Task 7 cont.

Just *reading* test script would be a little bit tedious:
TriangleTests

So I wrote a graphical test visualiser (just for fun !):
TriangleTestViewer

This was created using a platform called 'Processing'
(Popular Java-based audio/visual framework)

---

# Warning: Final Tests

Final couple of tests use some VERY large triangles
We must remember that data types are constrained
There is a limit to range of numbers an int can store
Also, float variables have limited precision (~7 DP)

## HINTS

Explore the variety of primitive data types in Java
Be selective about WHAT calculations you perform
Also think about the ORDER you perform them in

---

# Workbook: Task 8

At some point you'll need to test via the command line

project-folder

## Key Commands:

./mvnw clean

./mvnw compile

./mvnw test

---

# Broken Maven Project ?

project-folder

Need to ensure ./mvnw script is executable 'chmod'
Switching platforms can corrupt ./mvnw script
The hidden .mvn folder can be missing (redownload)
Mismatch between installed and POM version of java
Be aware of difference between 'mvn' and 'mvnw'

---

To work !

21/21

---

## 📝 练习册：Weekly Workbooks 02 Object Oriented Concepts 02 Objects and Classes slides segment 1.md

# Classes

A class is a "module" of a Java program
Typically 1-1 mapping between Class and file

```java
class Counter
{
    // Code for class goes here !
}
```

A Class describes a particular type of Object
Objects of that type are then created at run time
Objects are "instances" of Class that describes them

Convention is that Class names start with a capital

---

# Java Types

Sorry, but this next bit is a little confusing...
The _majority_ of data types in Java are Classes
The exception to this are "Primitive" types
(int, char, boolean, float etc)

Primitives are just simple data (the same as in C)
Everything else in Java is a Class !

Java provides the concept of an array (just like C)
These can contain either Primitives or Class types

---

# Attributes

A Class has a number of data fields or "Attributes"
These are global to (accessible within) the class
But importantly NOT global to the whole program
(Remember the notion of "Encapsulation" ?)

For example:

```cpp
class Counter
{
    int count;
}

---

# Methods

Each Class has a bunch of functions: "Methods"

```cpp
class Counter
{
    int count;
    void increment() {
        count++;
    }
}
```

Such Methods are "attached" to that Class

They are called "on" a specific instance of that Class

```cpp
Counter carCounter;
carCounter.increment();

---

# Difference Between Functions & Methods

Methods are tied to a particular object
Functions are just "floating around"

In C you just call a function in isolation:
```
printf("Hello");
```

In Java you call a method ON a particular Object:
```
out.print("Hello");
serial.print("Hello");
file.print("Hello");

---

# Constructor Methods

Special methods exist to create instances of a Class (Remember that such instances are called Objects) Constructors have the same name as the Class:

```java
class Counter
{
    int count;
    public Counter() {
        count = 0;
    }
}
Counter myCounter = new Counter();
```

Notice there is no return type with a constructor !

---

# Multiple Constructors

We can have simple constructors with default values:
```java
public Counter() {
    count = 0;
}
```

Or complex ones, where we passing in the settings:
```java
public Counter(int startValue) {
    count = startValue;
}
```

Providing more than one method with the same name like this is referred to as "Overloading"

---

## 📝 练习册：Weekly Workbooks 02 Object Oriented Concepts 02 Objects and Classes slides segment 2.md

# Example Class

Java has a String class to store & manipulate text
Inside there is an array attribute to store characters
And a bunch of methods to "do things to" the text:
- length: gives the number of characters in the text
- charAt: gives you the char at a particular position
- contains: tells you if string contains a sequence
- toLowerCase: converts string to lower case version
- substring: splits off a chunk of the string

All packaged up into a nice neat bundle - a Class !

---

# Example Objects

We can create Objects (instances) of the String class
Each with a different character sequence inside:
```java
String unitCode = new String("COMSM0103");
String unitCode = new String("COMSM0204");
```

There is (just for the String class) a shorthand:
```java
String unitCode = "COMSM0305";
```

Provided because creating Strings is so common

---

# Classes and Objects in Code

Methods of each Object operate on their own data
You don't want the "length" method of one String...
Telling you how long the text of another String is !

Similarly, with "substring":
```
String unitCode = new String("COMSM0103");
String unitName = "OOP with Java";
System.out.println(unitCode.substring(5,7));
```

What does the above code print out ?

Substring

---

## 📝 练习册：Weekly Workbooks 02 Object Oriented Concepts 03 Inheritance and Polymorphism deep segment 1.md

# Recap: REFERENCES

---

# Classes and Reference Types

- every object belongs to a class
- classes act like types; for instance, references to an object are given a particular type when we declare it:

```
Robot c3po = new Robot("C3PO");
```

the reference to ‘type’ Robot

here we specify the type of object the reference c3po can point to

the constructor called must then relate to the type we specified

```java
class Robot {
    String name;
    int numLegs;
    float powerLevel;

    Robot(String productName) {
        name = productName;
        numLegs = 2;
        powerLevel = 2.0f;
    }

    void talk(String phrase) {
        if (powerLevel >= 1.0f) {
            System.out.println(name + " says " + phrase);
            powerLevel -= 1.0f;
        } else {
            System.out.println(name + " is too weak to talk.");
        }
    }

    void charge(float amount) {
        System.out.println(name + " charges.");
        powerLevel += amount;
    }
}
```

→ What effects can we achieve by introducing sub-class relationships?

Object-Oriented Programming

---

# SUB-CLASSES

---

# Is one robot class enough?

- According to Wookieepedia, 3PO-series droids are “fluent in over six million forms of communication”, weigh around 77.6 kg, and have a maximal speed of 21km/hr

- So ... they have a lot of specific functionality and might be considered a special class of robot ...

Object-Oriented Programming

---

# Fighting Code Duplication

- **Problem**: you have written a class (e.g. Robot), which almost does what you want, but requires some extensions

- **Idea**: extend features from the existing class by creating a child class that automatically receives all features of the parent class (e.g. name, talk(),...) without writing code again

- **Implementation**: you define a new class (e.g. TranslationRobot) inheriting all features from the existing parent class, but add or adapt features so that the new class does exactly what you want

- **Result**: leads to DRY (do-not-repeat-yourself) code where each feature has a single code source

class Robot {
String name;
int numLegs;
float powerLevel;

Robot(String productName) {
name = productName;
numLegs = 2;
powerLevel = 2.0f;
}

void talk(String phrase) {
if (powerLevel >= 1.0f) {
System.out.println(name+" says "+phrase);
powerLevel -= 1.0f;
} else {
System.out.println(name + " is too weak to talk.");
}
}

void charge(float amount) {
System.out.println(name+" charges.");
powerLevel += amount;
}
}

parent class Robot provides all its features to the child class

‘extends’ signals inheritance from Robot class

public class TranslationRobot extends Robot {
// class has everything that Robot has implicitly
String substitute; //and more features

TranslationRobot(String substitute) {
this.substitute = substitute;
}

void translate(String phrase) {
this.talk(phrase.replaceAll("a", substitute));
}

@Override
void charge(float amount) { //overriding
System.out.println(name + " charges double.");
powerLevel = powerLevel + 2 * amount;
}
}

added method here

parent method is replaced here

---

# Usage of Inheritance

- a child class can provide new or alter old functionality by...
  (1) adding extra attributes
  (2) adding extra methods
  (3) replacing existing methods (known as overriding)

- inheritance renders classes more re-usable by making them ‘extendable’ and ‘adaptable’

- **WARNING**: Only use inheritance for specialisation, i.e. when there is an *is-a* relationship, not a *has-a* relationship (e.g. a Motor class should not be parent to a Robot class)

```java
class Robot {
    String name;
    int numLegs;
    float powerLevel;

    Robot(String productName) {
        name = productName;
        numLegs = 2;
        powerLevel = 2.0f;
    }

    void talk(String phrase) {
        if (powerLevel >= 1.0f) {
            System.out.println(name + " says " + phrase);
            powerLevel -= 1.0f;
        } else {
            System.out.println(name + " is too weak to talk.");
        }
    }

    void charge(float amount) {
        System.out.println(name + " charges.");
        powerLevel += amount;
    }
}

public class TranslationRobot extends Robot {
    // class has everything that Robot has implicitly
    String substitute; // and more features

    TranslationRobot(String substitute) {
        this.substitute = substitute;
    }

    void translate(String phrase) { // added method
        this.talk(phrase.replaceAll("a", substitute));
    }

    @Override
    void charge(float amount) { // overriding
        System.out.println(name + " charges double.");
        powerLevel = powerLevel + 2 * amount;
    }
}

public class InheritanceWorld {
    public static void main(String[] args) {
        TranslationRobot c3po = new TranslationRobot("e");
        c3po.translate("'This text is translated.'");
    }
}
```

Object-Oriented Programming

---

# CLASS HIERARCHIES

---

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

# The Class Hierarchy

- in single inheritance, as in Java, a class is derived from one direct super class only
- the resulting class hierarchy defines the inheritance relationship between all classes in a tree structure
- the root of the class hierarchy is the class Object
- every class in Java directly (implicitly, if it has no parent) or indirectly via multi-level inheritance extends (inherits from) the class Object

## java.lang
©1995-6, Charles L. Perkins

Object-Oriented Programming

---

## 📝 练习册：Weekly Workbooks 02 Object Oriented Concepts 03 Inheritance and Polymorphism slides segment 1.md

# Inheritance

Allows us to reuse & extend existing code

Take the String class for example...
Currently it is just plain text
But what if we wanted add text styling ?
(Bold, Italics, Underline etc.)

We can "extend" the basic String Class,
making use of all the existing methods,
but also adding in some of our own...

---

# StyledString Class

class StyledString extends String
{
    void setUnderlined(boolean underline)
    // Some code in here !
}
void setItalics(boolean italic)
// Some code in here !
}

---

# What we get

We have only added two new methods:
- setUnderlined
- setItalics

But because we have extended String, we get:
- length
- charAt
- contains
- toLowerCase
- etc.

All for free !

---

# Using StyledString

```java
public static void main(String args[])
{
    StyledString message = new StyledString("Hello");
    message.setUnderlined(true);
    message.setItalics(true);
    System.out.println(message);
}
```

run
StyledString

---

# Overriding

Adding features to a child (the extending class)
Is often achieved by replacing existing methods
With the new one containing additional features
This is called...
Overriding

---

# For example...

ALL classes have a method to get text for printing
We can "override" this in the StyledString class
And include special tags for styling:

"\033[4m" + text + "\033[0m";

The above is underlining
Don't worry - these codes aren't part of this unit!
(You don't need to know or understand them)

---

# Method Chaining

If we are really clever...
We can reuse the method of super (parent) class
And then tack on the extra features at the end:

```java
public String toString()
{
    String text = super.toString();
    if(isUnderlined) text = "\033[4m" + text + "\033[0m";
    if(isItalics) text = "\033[3m" + text + "\033[0m";
    return text;
}

---

# Polymorphism

What if we don't know what kind of String to expect ?

It might be a plain String or maybe a StyledString

Don't want to write a different method for each type

Luckily we don't have to !

We can just write a general purpose method:

```java
public void spellCheck(String text) ...
```

And this will be able to operate on ANY kind of String

(Any Object that is a String or sub-class of String)

---

## 📝 练习册：Weekly Workbooks 02 Object Oriented Concepts 04 Abstraction and Encapsulation deep segment 1.md

# Data Hiding

- you should routinely hide your attributes and methods as much as possible using private

- now that we’ve made our implementation of attributes private, there’s another benefit: we can change the implementation without changing the way objects access to our class (i.e. we may want to remove an attribute completely)

- using public makes elements globally accessible (also applicable to classes)

## class visibility

| Modifier | Package | World |
|----------|---------|-------|
| Public   | ✓       | ✓     |
| Default  | ✓       | ✗     |

removing a private attribute (such as noSides) has purely local consequences for the class only to resolve

```java
public class Polygon {
    private Position[] points;
    //private int noSides;

    Polygon(Position[] points) {
        this.points = points;
    }

    Position[] getPoints() {
        return points;
    }

    int getNoSides() {
        return points.length;
    }

    void setPoints(Position[] points) {
        this.points = points;
    }
}
```

removing the noSides attribute is now possible WITHOUT changing the ‘interface’ which this class exposes

some slide content used from N. Wu

Object-Oriented Programming | University of Bristol

---

## 📝 练习册：Weekly Workbooks 02 Object Oriented Concepts 04 Abstraction and Encapsulation slides segment 1.md

# Abstraction

Abstraction focuses on the "purpose" of an Object
Without concerning ourselves with how it does it

For most people, cars just get them from A to B
They aren't concerned with how all the parts work

We couldn't drive a car if we were concentrating
on what of the different bits were doing !

(Ask an editor what they think of a film ;o)

---

# Encapsulation

Encapsulation goes one step further...

Not only is understand internal workings unnecessary
They can't even be seen, accessed or manipulated

What about the car example ?
Ever tried to open an engine management system...

---

# Exotic Driver Bits

|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| +00 | +0 | +1 | +1 | +2 | +2 | +3 | +4 | -3 | -4 | -4.5 | -5 | -5.5 | -6 |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| -6.5 | -7 | -8 | +1 | +2 | +2 | +3 | +4 | 1.5 | 2 | 2.5 | 3 | 4 | 5 |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 5.5 | 6 | 7 | 8 | 1/16 | 5/64 | 3/32 | 7/64 | 1/8 | 9/64 | 5/32 | 3/16 | 7/32 | 1/4 |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 1 | 2 | 3 | 4 | 4 | 6 | 8 | 10 | 12 | 6 | 8 | 10 | 0 | 1 |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 2 | 2 | 3 | 1/8 | 5/32 | 3/16 | 1/4 | 5/16 | M5 | M6 | M8 | T8 | T9 | T10 |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| T15 | T20 | T25 | T27 | T30 | T40 | T45 | 2 | 2.5 | 3 | 4 | 5 | 6 | 5/64 |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 3/32 | 7/64 | 1/8 | 9/64 | 5/32 | T8H | T10H | T15H | T20H | T25H | T27H | T30H | T35H | T40H |  |  |  |  |  |  |

---

# Advantages of Encapsulation

One advantage of encapsulation is robustness...
No one can accidentally (or intentionally)
interfere with the internal workings of an Object

Another advantage is maintenance...
An object can more easily be upgraded or replaced
without changing any code which uses it
(As long as the interface stays the same !)

Also useful for work division in team development !

---

## 📝 练习册：Weekly Workbooks 02 Object Oriented Concepts 04 Abstraction and Encapsulation slides segment 2.md

# Private Variables

If this were C, we could just reach in and set the style booleans like so:

```c
myString.isUnderlined = true;
myString.isItalics = true;
```

But this is very dangerous !
If we don't know how the object uses them...
How can we know it is safe to change them ?

---

# DVD Collection

Imagine you had a collection of DVDs
People can ask to borrow one
You can keep track of who has which disk

But what would happen if people could just walk in,
and take them without asking !
There would be chaos !!!
You won't know where anything was :o(

---

# Accessor and Mutator methods

We may wish external objects to access internal data
But we need to achieve this in a controlled fashion

Can be achieved by providing additional methods...
Accessors ("Getters") and Mutators ("Setters"):

```
boolean isUnderlined = false;

void setUnderlined(boolean underline) ...
boolean getUnderlinedStatus() ...

---

# Public, Private and Protected

We actually have a lot of control over access:

## Attributes
- Public: Accessed from any location (usually bad !)
- Private: Only inside class in which they are defined
- Protected: Inside the class or any subclass

## Methods
- Public: Can be called from any location
- Private: Only inside class in which they are defined
- Protected: Inside the class or any subclass

---

## 📝 练习册：Weekly Workbooks 02 Object Oriented Concepts 05 Controlling Access deep segment 1.md

# Member Visibility

| Modifier | Class | Package | Subclass (outside package) | World |
| --- | --- | --- | --- | --- |
| Public | ✓ | ✓ | ✓ | ✓ |
| Protected | ✓ | ✓ | ✓ | ✗ |
| Default (no modifier) | ✓ | ✓ | ✗ | ✗ |
| Private | ✓ | ✗ | ✗ | ✗ |

methods usually default

main is public

attributes are usually private

notice that sub-classes outside the package have a special relationship with their parents if members are declared protected

slide content used from N. Wu

Object-Oriented Programming | University of Bristol

---

## 📝 练习册：Weekly Workbooks 02 Object Oriented Concepts 05 Controlling Access slides segment 1.md

# Providing Controlled Access: Getters and Setters

- getters and setters are what we name methods, which are used to access and mutate attributes (instead of direct access)
- they are also known as accessors and mutators
- often the getter is simply passing the underlying attribute (Please: No side effects!), and the setter is ensuring that all required invariants hold true
- it is important to think about whether it’s worth exposing a setter in the first place – is it really required?
- for instance, in our example, setting noSides directly would seem like a fundamentally bad idea

```java
class Polygon {
    Position[] points;
    int noSides;

    Polygon(Position[] points) {
        this.points = points;
        noSides = points.length;
    }

    Position[] getPoints() {
        return points;
    }

    void setPoints(Position[] points) {
        this.points = points;
        noSides = points.length;
    }
}
```

this getter method can be used as an alternative to access the underlying attribute points – in this basic case it simply passes on the attribute itself

this setter method allows the mutation of the points field and, most importantly, make sure that the overall state is consistent and our invariant ‘points.length == noSides’ holds true after the manipulation

Object-Oriented Programming | University of Bristol

---

## 📝 练习册：Weekly Workbooks 02 Object Oriented Concepts 06 Enumerations slides segment 1.md

# Enumerated Types

- Enumerated types (enums) in Java are way more versatile than enums in C
- Enums are a special type of class
  - You can declare fields and methods
  - In their most basic form they are very simple
  - Simple enum:

```java
public enum FoodGroup {
    CANDY, CANDYCANES, CANDYCORNS, SYRUP;
}

---

# Using Enums

```java
public class PoisonDetector {
    private final FoodGroup edible;

    private PoisonDetector (Food food) {
        if (food.isSweet()) {
            if (food.isPeppermint() && food.isStripey()) {
                edible = FoodGroup.CANDYCANES;
            } else if (food.isLiquid()) {
                edible = FoodGroup.SYRUP;
            } else if (food.looksLikeCorn()) {
                edible = FoodGroup.CANDYCORNs;
            } else {
                edible = FoodGroup.CANDY;
            }
        } else {
            edible = NULL;
        }
    }

    public FoodGroup canIEatIt() { return edible; }
}
```

NO!

---

# Easy Fix

## Add a default/error value to the enum

```java
public enum FoodGroup {
    CANDY, CANDYCANES, CANDYCORNs, SYRUP, DONOTEAT;
}
```

## Set this to the new default value instead of null

```java
public class PoisonDetector {
    private final FoodGroup edible;

    private PoisonDetector (Food food) {
        if (food.isSweet()) {
            if (food.isPeppermint() && food.isStripey()) {
                edible = FoodGroup.CANDYCANES;
            } else if (food.isLiquid()) {
                edible = FoodGroup.SYRUP;
            } else if (food.looksLikeCorn()) {
                edible = FoodGroup.CANDYCORNs;
            } else {
                edible = FoodGroup.CANDY;
            }
        } else {
            edible = FoodGroup.DONOTEAT;
        }
    }

    public FoodGroup canIEatIt() { return edible; }
}

---


## 🔑 核心知识点摘要

*（出题时参考以上各节详细内容，此处为快速索引）*

| 类型 | 文档 | 核心主题 |
|------|------|----------|
| 📖 主讲课 | Weekly Lectures 02 Key Language Constructs.md | |
| 📋 任务简报 | Weekly Briefings 02 Shapes Exercise.md | |
| 📝 练习册 | Weekly Workbooks 02 Object Oriented Concepts 02 Objects and Classes slides segment 1.md | |
| 📝 练习册 | Weekly Workbooks 02 Object Oriented Concepts 02 Objects and Classes slides segment 2.md | |
| 📝 练习册 | Weekly Workbooks 02 Object Oriented Concepts 03 Inheritance and Polymorphism deep segment 1.md | |
| 📝 练习册 | Weekly Workbooks 02 Object Oriented Concepts 03 Inheritance and Polymorphism slides segment 1.md | |
| 📝 练习册 | Weekly Workbooks 02 Object Oriented Concepts 04 Abstraction and Encapsulation deep segment 1.md | |
| 📝 练习册 | Weekly Workbooks 02 Object Oriented Concepts 04 Abstraction and Encapsulation slides segment 1.md | |
| 📝 练习册 | Weekly Workbooks 02 Object Oriented Concepts 04 Abstraction and Encapsulation slides segment 2.md | |
| 📝 练习册 | Weekly Workbooks 02 Object Oriented Concepts 05 Controlling Access deep segment 1.md | |
| 📝 练习册 | Weekly Workbooks 02 Object Oriented Concepts 05 Controlling Access slides segment 1.md | |
| 📝 练习册 | Weekly Workbooks 02 Object Oriented Concepts 06 Enumerations slides segment 1.md | |
