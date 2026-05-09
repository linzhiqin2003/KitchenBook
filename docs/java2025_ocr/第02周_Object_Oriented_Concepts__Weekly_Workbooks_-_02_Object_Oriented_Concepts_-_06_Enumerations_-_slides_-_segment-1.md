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