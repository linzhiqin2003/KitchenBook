# Instance vs Class Variables

Sometimes we need a single variable for all Objects
For example, a "population" counter to keep track
of how many StyledStrings we've created

Clearly we can't use an Object variable
(we'd have one inside every StyledString)

What we need is a single "Class" variable
This is implemented using the "static" keyword:
```
static int populationSize = 0;
```

This is tied to the Class, not the Objects !

---

# Using Class Variables

When using a Class variable, we access it via the Class name, rather than an Object name:

```java
class StyledString extends String
{
    static int populationSize = 0;

    public StyledString(String text) {
        super(text);
        StyledString.populationSize++;
    }

    public int getPopulationSize() {
        return StyledString.populationSize;
    }
}