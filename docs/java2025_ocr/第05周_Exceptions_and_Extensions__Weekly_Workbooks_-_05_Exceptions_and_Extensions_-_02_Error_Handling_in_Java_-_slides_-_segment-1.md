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