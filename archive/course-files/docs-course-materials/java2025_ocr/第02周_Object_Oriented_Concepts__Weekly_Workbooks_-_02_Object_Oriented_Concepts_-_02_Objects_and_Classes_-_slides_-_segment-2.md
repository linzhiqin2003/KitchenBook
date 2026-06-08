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