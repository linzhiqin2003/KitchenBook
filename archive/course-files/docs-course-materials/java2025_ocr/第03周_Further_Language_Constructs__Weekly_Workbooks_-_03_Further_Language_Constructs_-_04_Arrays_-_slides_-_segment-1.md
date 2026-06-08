# Arrays in Focus: Creating, Initialising and Iterating

- arrays (in Java) are objects too...

```java
public class RobotArrays {
    public static void main (String[] args) {
        Robot[] robotsA = new Robot[3]; // instantiate array of references to 3 Robot objects
        System.out.println(robotsA[0]); // at start, array locations carry null
        robotsA[0] = new Robot("C3PO"); // initialise entry at index 0
        robotsA[1] = new Robot("C4PO"); // initialise entry at index 1
        robotsA[2] = robotsA[0];        // initialise with same reference as index 0
        Robot[] robotsB = {
            new Robot("C5PO"),
            robotsA[0],
            robotsA[1]
        };
        System.out.println(robotsB.length); // print size of array robotsB
        for (Robot robot : robotsB)         // loop through entries, assign current to robot
            System.out.println(robot.name); // print name of current element
    }
}
```

This is an Iterator using the “:” notation, which provides a reference “robot” to each object held in the array turn-by-turn (The reference is not a one to the array location itself, which is not an object.)

...beware, it is the wrath of the null that you need to defend against in your programming...