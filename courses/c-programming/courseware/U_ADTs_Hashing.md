ADTs: Hashing  
● To keep records of employees we might index (search) them by using their National Insurance number:  
xx-###-###-###-x  
● There are 17.6 billion combinations (around 2³⁴).  
● Could use an array of 17.6 billion entries, which would make searching for a particular entry trivial!  
● Especially wasteful since only our (5000) employees need to be stored.  
● Here we examine a method that, using an array of 6000 elements, would require 2.1 comparisons on average.  
● A hash function is a mapping, h(K), that maps from key K, onto the index of an entry.  
● A black-box into which we insert a key (e.g. NI number) and out pops an array index.  
● As an example lets use an array of size 11 to store some airport codes, e.g. PEK, BRS, FRA.

Hashing: Airport Codes  
• In a three letter string X₂X₁X₀ the letter 'A' has the value 0, 'B' has the value 1 etc.  
• One hash function is:  
h(K) = (X₂*26² + X₁*26 + X₀) %11  
• Applying this to "DCA":  
h("DCA") = (3*26² + 2*26 + 0) %11  
h("DCA") = (2080) %11  
h("DCA") = 1  
• Inserting "PHL", "ORY" and "GCM":  
A hash table (indices 0 to 10) contains:  
- PHL at index4  
- GCM at index6  
- ORY at index8  
• However, inserting "HKG" causes a collision.  
A hash table indicates HKG collides with PHL (located at index4).

Hashing: Collisions
● An ideal hashing function maps keys into the array in a uniform and random manner.
● Collisions occur when a hash function maps two different keys onto the same address.
● It’s very difficult to choose ‘good’ hashing functions.
● Collisions are common - the von Mises paradox. When 23 keys are randomly mapped onto 365 addresses there is a 50% chance of a collision.
● The policy of finding another free location if a collision occurs is called open-addressing.
● If a collision occurs then keep stepping backwards (with wrap-around) until a free location is encountered.

Double Hashing  
● This simple method of open-addressing is linear-probing.  
● The step taken each time (probe decrement) need not be 1.  
● Open-addressing through use of linear-probing is a very simple technique, double-hashing is generally much more successful.  
● A second function p(K) decides the size of the probe decrement.  
● The function is chosen so that two keys which collide at the same address will have different probe decrements, e.g.:  
  ρ(K) = MAX(1, ((X₂ * 26² + X₁ * 26 + X₀)/11)%11)  
● Although "PHL" and "HKG" share the same primary hash value of h(K) = 4, they have different probe decrements:  
  p("PHL") = 4  
  p("HKG") = 3

Hashing: Primes and Chaining  
- If the size of our array, M, was even and the probe decrement was chosen to be 2, then only half of the locations could be probed.  
(Array indices: 0,1,2,3,4,5,6,7,8,9; dashed arrows point to positions 0,2,4,6,8)  
- Often we choose our table size to be a prime number and our probe decrement to be a number in the range 1... M − 1.  
Open-addressing is not the only method of collision reduction. Another common one is separate chaining.  
(Array indices: 0,1,2,3,4,5,6,7,8,9,10; Position 4: PHL → HKG → NULL; Position5: GCM; Position7: ORY)

A Practical Hash Function
#include <stdio.h>
int hash(unsigned int sz, char *s);
int main(void)
{
    char str[] = "Hello World!";
    // Hash modulus 7919
    printf("%d\n", hash(7919, str));
    return 0;
}
/*
Modified Bernstein hashing
5381 & 33 are magic numbers required by the algorithm
*/
int hash(unsigned int sz, char *s)
{
    unsigned long hash = 5381;
    int c;
    while(c = (*s++)){
        hash = 33 * hash + c;
    }
    return (int)(hash%sz);
}
Execution :
5479
Has similarities to the implementation of rand():
int rand_r(unsigned int* seed);
int main(void)
{
    unsigned int seed = 0;
    printf("%d\n", rand_r(&seed));
    return 0;
}
/* This algorithm is mentioned in the ISO C standard,
here extended for 32 bits. */
int rand_r(unsigned int* seed)
{
    unsigned int next = *seed;
    int result;
    next *= 1103515245;
    next += 12345;
    result = (unsigned int) (next / 65536) % 2048;
    next *= 1103515245;
    next += 12345;
    result <<= 10;
    result += (unsigned int) (next / 65536) % 1024;
    next *= 1103515245;
    next += 12345;
    result <<=10;
    result += (unsigned int) (next /65536) %1024;
    *seed = next;
    return result;
}
Execution :
1012484

Cuckoo Hashing  
- We have two tables, each with their own hash function.  
- We only need to check two cells when searching.  
- On collision, the existing item is 'cuckooed' out of it's cell into the other table.  
Empty: copied farandoles into table 0(4)  
Empty: copied bronze into table 0(12)  
Empty: copied auscultatory into table 0(5)  
Empty: copied bifer into table 0(13)  
Empty: copied steepgrass into table 0(6)  
Empty: copied prevised into table 0(7)  
Empty: copied oomph into table 0(8)  
Empty: copied succour into table 0(10)  
empodium: copied auscultatory from table 0(5)  
empodium: so cuckooed out table 0(5)  
interquarreled: so cuckooed out bronze from table 0(12)  
Empty: copied bronze into table 1(5)  
ranseur: copied cuckooed empodium from table 0(5)  
Empty: copied empodium into table 1(4)  
Empty: copied megalodon into table 0(11)  
geosynchronous: so cuckooed out megalodon from table 0(11)  
Empty: copied megalodon into table 1(14)  
Empty: copied osmeteria into table 0(14)  
Table getting full -> rehashed old sz =16  
Left Table:  
0  
1  
2  
3  
4:farandoles  
5:ranseur  
6:steepgrass  
7:prevised  
8:oomph  
9  
10  
11:geosynchronous  
12:interquarreled  
13:bifer  
14:osmeteria  
15  
Right Table:  
0  
1  
2  
3  
4:empodium  
5:bronze  
6  
7  
8  
9  
10:auscultatory  
11  
12  
13  
14:megalodon  
15