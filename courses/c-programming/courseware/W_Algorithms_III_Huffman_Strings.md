Algorithm: Huffman Compression  
● Often we wish to compress data, to reduce storage requirements, or to speed transmission.  
● Text is particularly suited to compression since using one byte per character is wasteful - some letters occur much more frequently.  
● Need to give frequently occurring letters short codes, typically a few bits. Less common letters can have long bit patterns.  
● To encode the string "BABBAGE":  
3/7 (B), 2/7 (A), 1/7 (E), 1/7 (G)  
● Keep a list of characters, ordered by their frequency

Huffman Compression II  
● Use the two least frequent to form a sub-tree, and re-order (sort) the nodes :  
● A = 10, B = 0, E = 110, G = 111  
● String stored using 13 bits.

Algorithm: Rabin-Karp String Searching  
- The task of searching for a string amongst a large amount of text is commonly required in word-processors, but more interestingly in massive Biological Databases e.g. searching for amino acids in protein sequences.  
- How difficult can it be? Don't you just do a character by character brute-force search?  
  Master String: AAAAAAAAAAAAH  
  Substring : AAAAAAH  
  Substring : AAAAAAAH  
  Substring : AAAAAAAH  
- If the master string has m characters, and the search string has n characters then this search has complexity: O(mn)  
- Recall that to compute a hash function on a word we did something like:  
  h("NEILL") = (13 × 26^4 + 4 × 26^3 + 8 × 26^2 + 11 × 26 + 11) % P  
  where P is a big prime number.  
- This can be expanded by Horner's method to:  
  (((((13 × 26) + 4) × 26) + 8) × 26) + 11) × 26 + 11) % P  
（注：纯文本中以上标形式呈现的指数用"^"替代，如26⁴→26^4；乘号统一用"×"表示，与原图一致。）

Rabin-Karp II  
- For a large search string, overflow can occur. We therefore move the mod operation inside the brackets:  
  (((((((13 × 26) + 4)%P × 26) + 8)%P × 26) + 11)%P × 26 + 11)%P  
- We can compute a hash number for the search string, and for the initial part of the master string.  
- When we compute the hash number for the next part of the master, most of the computation is common, we just need to take out the effect of the first letter and add in the effect of the new one.  
- One small calculation each time we move one place right in the master.  
- Complexity O(m + n) roughly, but need to check that two identical hash numbers really has identified two identical strings.  
```c
#include <string.h>
#include <assert.h>
#define Q 33554393
#define D 26
#define index(C) (C - 'A')
int rk(char *p, char *a);
int main(void)
{
    assert(rk("STRING", 
        "A STRING EXAMPLE CONSISTING OF ...") == 22);
    return 0;
}
int rk(char *p, char *a)
{
    int i, dM = 1, h1=0, h2=0;
    int m = strlen(p);
    int n = strlen(a);
    for (i=1; i<m; i++) dM = (D*dM)%Q;
    for (i=0; i<m; i++){
        h1 = (h1*D + index(p[i]))%Q;
        h2 = (h2*D + index(a[i]))%Q;
    }
    // h1 = search string hash, h2 = master string hash
    for (i=0; h1!=h2; i++){
        h2 = (h2 + Q - index(a[i])*dM) % Q;
        h2 = (h2*D + index(a[i+m])) % Q;
        if (i>n-m) return n;
    }
    return i;
}
```

Algorithm : Boyer-Moore String Searching
The Boyer-Moore algorithm uses (in part) an array flagging which characters form part of the search string and an array telling us how far to slide right if that character appears in the master and causes a mismatch.
Execution :
A STRING SEARCHING EXAMPLE CONSISTING OF ...
STING
    STING
        STING
- With a right-to-left walk through the search string we see that the G and the R mismatch on the first comparison.
- Since R doesn't appear in the search string, we can take 5 steps to the right.
- The next comparison is between the G and the S. We can slide the search string right until it matches the S in the master.

Boyer-Moore II
Execution:
A STRING SEARCHING EXAMPLE CONSISTING OF ...
          |   |   |   |   |
        STING
          STING
              STING
                STING
                  STING
- Now the C doesn't appear in the master and once again we can slide a full 5 places to the right.
- After 3 more full slides right we arrive at the T in CONSISTING.
- We align the T's, and have found our match using 7 compares (plus 5 to verify the match).