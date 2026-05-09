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