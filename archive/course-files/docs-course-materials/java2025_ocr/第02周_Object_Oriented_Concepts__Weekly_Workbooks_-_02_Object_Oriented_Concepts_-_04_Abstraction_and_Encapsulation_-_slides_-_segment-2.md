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