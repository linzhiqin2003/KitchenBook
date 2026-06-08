# Java Collections

- a Collection is a container that groups multiple elements into a single unit
- the Java Collection framework (JCF) is one of the most important ones in all of Java's libraries, providing high performance implementations
- it uses generics to be flexible w.r.t. element types contained, and it is also polymorphically structured, so the same methods work on different collections

## Interfaces of the Collections Framework

```
<<interface>> Iterable<T>
       |
       v
<<interface>> Collection<E>
       |
       +-- <<interface>> Set<E>
       |       |
       |       +-- <<interface>> SortedSet<E>
       |
       +-- <<interface>> List<E>
       |
       +-- <<interface>> Queue<E>
       |       |
       |       +-- <<interface>> BlockingQueue<E>
       |
       +-- <<interface>> Map<K,V>
       |       |
       |       +-- <<interface>> SortedMap<K,V>
       |       |
       |       +-- <<interface>> ConcurrentMap<K,V>
```

Overview by Ray Toal

Object-Oriented Programming | University of Bristol

---

# The Collections Framework

<<interface>> Iterable<T>
    |
    |--- <<interface>> Collection<E>
            |
            |--- <<interface>> Set<E>
            |       |
            |       |--- <<interface>> SortedSet<E>
            |               |
            |               |--- TreeSet<E>
            |               |
            |               |--- HashSet<E>
            |               |       |
            |               |       |--- LinkedHashSet<E>
            |               |
            |               |--- EnumSet<E>
            |               |
            |               |--- CopyOnWriteArraySet<E>
            |
            |--- <<interface>> List<E>
                    |
                    |--- <<interface>> SortedSet<E>  <!-- 重复，应为 SortedList<E> 或其他，但图中如此 -->
                    |       |
                    |       |--- TreeSet<E>  <!-- 重复，应为 TreeList<E> 或其他，但图中如此 -->
                    |       |
                    |       |--- ArrayList<E>
                    |       |
                    |       |--- Vector<E>
                    |       |
                    |       |--- CopyOnWriteArrayList<E>
                    |
                    |--- <<interface>> Queue<E>
                            |
                            |--- <<interface>> BlockingQueue<E>
                                    |
                                    |--- PriorityBlockingQueue<E>
                                    |
                                    |--- DelayQueue<E>
                                    |
                                    |--- SynchronousQueue<E>
                                    |
                                    |--- ArrayBlockingQueue<E>
                                    |
                                    |--- LinkedBlockingQueue<E>
                            |
                            |--- PriorityQueue<E>
                            |
                            |--- ConcurrentLinkedQueue<E>
            |
            |--- <<interface>> Map<K,V>
                    |
                    |--- <<interface>> SortedMap<K,V>
                            |
                            |--- TreeMap<K,V>
                    |
                    |--- <<interface>> ConcurrentMap<K,V>
                            |
                            |--- ConcurrentHashMap<K,V>
                    |
                    |--- HashMap<K,V>
                            |
                            |--- LinkedHashMap<K,V>
                            |
                            |--- WeakHashMap<K,V>
                            |
                            |--- IdentityHashMap<K,V>
                            |
                            |--- EnumMap<K,V>
                            |
                            |--- Hashtable<K,V>

Overview by Ray Toal

Object-Oriented Programming | University of Bristol

---

# HashMap Interlude

Object-Oriented Programming | University of Bristol

---

# Example Usage: The List<T> Interface

## import of the right package
```java
import java.util.*;
```

## simple for-loop to iterate through the set
```java
for (Robot robot : list) {
    System.out.print(robot.name+',');
}
```

## construct list object (with type inference)
```java
List<Robot> list = new ArrayList<>();
```

## adding elements
```java
list.add(c3po);
list.add(new CarrierRobot());
list.add(1, new Robot("C4PO"));
```

## element removal
```java
Robot removed = list.remove(2);
```

## «interface» List<E>
| Method | Description |
|--------|-------------|
| `+ boolean add(int index, E)` | Adds the specified element at the specified position in this list. |
| `+ boolean addAll(int index, Collection<E>)` | Inserts all the elements in the specified collection into this list, starting at the specified position. |
| `+ void clear()` | Removes all elements from this list. |
| `+ boolean contains(Object o)` | Returns true if this list contains the specified element. |
| `+ boolean containsAll(Collection c)` | Returns true if this list contains all of the elements of the specified collection. |
| `+ E get(int index)` | Returns the element at the specified position in this list. |
| `+ int indexOf(Object o)` | Returns the index of the first occurrence of the specified element in this list, or -1 if this list does not contain the element. |
| `+ int lastIndexOf(Object o)` | Returns the index of the last occurrence of the specified element in this list, or -1 if this list does not contain the element. |
| `+ E remove(int index)` | Removes the element at the specified position in this list. |
| `+ E set(int index, E)` | Replaces the element at the specified position in this list with the specified element. |
| `+ Iterator<E> iterator()` | Returns an iterator over the elements in this list in proper sequence. |
| `+ ListIterator<E> listIterator()` | Returns a list iterator over the elements in this list (in proper sequence). |
| `+ List<E> subList(int fromIndex, int toIndex)` | Returns a view of the portion of this list between the specified fromIndex, inclusive, and toIndex, exclusive. |
| `+ int size()` | Returns the number of elements in this list. |
| `+ boolean isEmpty()` | Returns true if this list contains no elements. |

```java
class ListWorld {
    static void printList(List<Robot> list) {
        System.out.print("List is:");
        for (Robot robot : list) {
            System.out.print(robot.name+',');
        }
        System.out.println("");
    }

    public static void main(String args[]) {
        List<Robot> list = new ArrayList<>();
        Robot c3po = new Robot("C3PO");
        list.add(c3po);
        list.add(new CarrierRobot());
        printList(list);
        list.add(1, new Robot("C4PO"));
        printList(list);
        Robot removed = list.remove(2);
        System.out.println("Removed:"+removed.name);
        printList(list);
        System.out.println("C3PO in list?:"+list.contains(c3po));
        list.addAll(0,list);
        printList(list);
    }
}
```

List is:C3PO,Standard Model,
List is:C3PO,C4PO,Standard Model,
Removed:Standard Model
List is:C3PO,C4PO,
C3PO in list?:true
List is:C3PO,C4PO,C3PO,C4PO,

Object-Oriented Programming | University of Bristol