# L4. Object Oriented Design

## What is OO Design?

Object-Oriented Software: structure software around objects and their interactions.

Objects, as real-world entities, contain state and behaviour.

Main constructs（主要构造）:

- Classes: blueprints for types of objects (e.g., Car) 蓝图
- Objects: individual instances for the given type (e.g., Ford Fusion with registration number AB25CDF )

## Why Design?

- Organise ideas
- Plan work

- Build understanding of the system structure and behavior
- Communicate with development team
- Help (future) maintenance team to understand

## OO Design Principles:

### Encapsulation 封装
- Encloses the data and behaviour of the objects within that object
  包含该对象内的数据和行为
- Prevents unauthorised access
  - Controlled access: object can be changed only by permitted methods
  - Protects data integrity 保护数据完整性

```java
//Partial example, not full class
public class Animal {
    private String name;

    public String getName() {
        return name;
    }
}
```

### Abstraction
- Focus on core concerns
- Leave out unnecessary detail
- Expose only the essential information
- Hide complexity of the class/object (i.e., how they are made)
  - Loose coupling: objects interact via abstract interfaces 松散耦合：对象通过抽象接口相互作用

```java
//Partial example, not full class
public abstract class Animal {
    private String name;
    public String getName() {

return name;
public abstract void makeSound();
}
++++++++++++++
class Cat extends Animal {
public void makeSound() {
System.out.println ("Meow!");
}
}
class Dog extends Animal {
public void makeSound() {
System.out.println ("Woof!");
}
}

## Inheritance 继承
- Inherit the properties and behaviour
- Reuse the code
  - Reduce re-writing
  - Reduce errors and inconsistency in code 减少代码中的错误和不一致

//Partial example, not full class
public abstract class Animal {
private String name;
public String getName() {
return name;
public abstract void makeSound();
}
++++++++++++++
class Cat extends Animal {
public void makeSound() {
System.out.println ("Meow!");
}
}

## Polymorphism 多态性

- Allows for substitution of sub-class for super-class 允许将子类转换为超类
- Behaviour belongs to the sub-classed object 行为属于子类对象
  - Dynamic method dispatch 动态方法派遣
  - Extensibility 可扩展性
  - Flexible and modular systems 灵活且模块化的系统

```java
//Partial example, not full class

public class Main {
    public static void main(String[] args) {
        Animal animal1 = new Dog();
        Animal animal2 = new Cat();

        animal1.makeSound(); // Output: Woof!
        animal2.makeSound(); // Output: Meow!
    }
}
```

## Composition

- Build an object from other objects
  - Reuse
  - Build incrementally 逐步构建

```java
//Partial example, not full class

class Legs {
    private int nuOfLegs;
    public Legs (int nuOfLegs) {this.nuOfLegs =nuOfLegs;}
    public void walk() {
        System.out.println ("Walking on" + nuOfLegs +"legs");
    }
}
++++•public class Animal { ...
    private Legs legs;
    ...

public void move() { System.out.print(name + " is
"); legs.walk(); }
}

## UML: Class Diagrams

## What Is a Class Diagram?

Static view of a system 系统的静态视图

## Class Diagrams

Class can be understood as a template (模版) for creating objects with own functionality

```plaintext
Class Name
Attributes
visibility, name, type
Methods
visibility, name, parameters,
return type
```

```plaintext
Patient
-x : name
-v : address
+getName () : String
+updateAddress(newY : String)
## Boolean checkAddress(y: String)
```

**Visibility:**
+ public # protected - private

## Notation for Attributes 属性符号

[visibility] name [: type] [multiplicity] [=value] [{property}]

- visibility
  - other package classes
  - - private : available only within the class
  - + public: available for the world
  - # protected: available for subclasses and other package classes

- ~ package: available only within the package
- [multiplicity], by default 1
- properties: readOnly, union, subsets<property-name>, redefined<property-name>, ordered, bag, seq, composite
- static attributes appear underlined 静态属性会被划线

## Notation for Operations 运算符号

`[visibility] name ([parameter-list]) : [{property}]`

- visibility
- method name
- formal parameter list, separated by commas 形式参数列表，用逗号分隔
  - direction name : type [multiplicity] = value [{property}]
  - static operations are underlined
- Examples:
  - display()
  - - hide()
  - + toString() : String
  - + createWindow (location: Coordinates, container: Container) : Window {readOnly}

## How do we find Classes: Grammatical Parse 语法解析

Classes

- Identify nouns from existing text 从现有文本中识别名词
- Narrow down to remove 缩小范围以去除
  - Duplicates and variations (e.g., synonyms) 重复与变体（例如，同义词）
  - Irrelevant 无关紧要
  - Out of scope 超出范围

## Structural Relationships in Class Diagrams 类图中的结构关系

## What Is an Association?

- The semantic relationship between two or more classifiers that specifies connections among their instances. 两个或多个分类器之间的语义关系，用于指定它们实例之间的连接。
- A structural relationship specifying that objects of one thing are connected to objects of another thing. 一种结构关系，规定一个事物的对象与另一个事物的对象相连。

```
Patient
Appointment
```

## What Is Multiplicity? (多重性)

- Multiplicity is the number of instances one class relates to ONE instance of another class. 多重性是指一个类与另一个类的一个实例之间的关联实例数。
- For each association, there are two multiplicity decisions to make, one for each end of the association. 对于每个关联，有两个多重决策，分别对应该关联的两个端。
    - For each instance of Patient, many or no Appointments can be made. 对于每个患者实例，可以安排多或不预约。
    - For each instance of Appointment, there will be one Patient to see. 每次预约都会有一位患者需要看诊。

```
Patient    1     0..*
Appointment
```

## Multiplicity: Example

Unspecified

Exactly One 1

Zero or More 0..*

Zero or More *

One or More 1..*

Zero or One (optional value) 0..1

Specified Range 2..4

Multiple, Disjoint Ranges 2, 4..6

Patient 1 Appointment

0..*

0..*

1

Treatment 0..* Products

0..6

What Is an Aggregation? 聚合

- A special form of association that models a whole-part relationship between the aggregate (the whole) and its parts. 这是一种特殊的联想形式，模拟了整体（整体）与其部分之间的整体关系。
- An aggregation is an “is a part-of” relationship. 聚合是一种“是”的一部

分“关系。
- Multiplicity is represented like other associations. 多重性与其他关联一样被表示。
```
Patient
Appointment
Whole
Aggregation
Part
```

## Aggregation: Shared vs. Non-shared

- Shared Aggregation
```
Multiplicity > 1
Whole
Part
```

- Non-shared Aggregation
```
Multiplicity = 1
Whole
Part
```

By definition, composition is non-shared aggregation. 根据定义，组合是非共享聚合。

## What Is Composition?

- A form of aggregation with strong ownership and coincident lifetimes 一种具有强烈所有权和巧合寿命的聚合形式
  - The parts cannot survive the whole/aggregate 这些部分无法承受整体或整体的

## What Is Navigability?

Indicates that it is possible to navigate from an associating class to the target class using the association 表示可以使用关联从关联类导航到目标类

## What Is Generalization?

- A relationship among classes where one class shares the properties and/or behavior of one or more classes.
- Defines a hierarchy of abstractions where a subclass inherits from one or more superclasses.
- Is an “is a kind of” relationship.

## Example: Inheritance

- One class inherits from another
- Follows the “is a” style of programming
- Class substitutability

```
Ancestor
Patient
- name
- address
- patientNumber
+ bookAppointment()
+ payForTreatment()
```

Superclass (parent)

Generalization Relationship

```
NHS Patient
```

```
Non-NHS Patient
```

Subclasses (children)

Descendants

## Abstract and Concrete Classes

- Abstract classes cannot have any objects
- Concrete classes can have objects

Discriminator

```
Patient
+ payForTreatment()
```

Abstract class

Abstract operation

Payment means

There are no direct instances of Patient

```
HNS Patient
+ payForTretment()
```

```
Non-NHS Patient
+ payForTretment()
```

All objects are either NHS or Non-NHS Patients

## Generalization vs. Aggregation

- Generalization and aggregation are often confused
  - Generalization represents an “is a” or “kind-of” relationship
  - Aggregation represents a “part-of” relationship

## UML: Sequence Diagrams

### Objects Need to Collaborate
- Objects are useless unless they can collaborate to solve a problem.
  - Each object is responsible for its own behavior and status.
  - No one object can carry out every responsibility on its own.
- How do objects interact with each other?
  - They interact through messages.
  - Message shows how one object asks another object to perform some activity.

### Sequence Diagrams: Basic Elements
- A set of participants arranged in time sequence
- Good for real-time specifications and complex scenarios

## Method for Analysis Sequence Diagrams

- for each scenario (high-level sequence diagram)
  - decompose to show what happens to objects inside the system
    → objects and messages
  - Which tasks (operation) does the object perform?
    → label of message arrow

### Sequence Diagram Legend

- **Who participates in the interaction?**
  - Actors and Objects

- **Vertical axis represents flow of time**

- **Message to / invocation of other object**
  - name represents the request made
  - may contain instantiated parameters

- **Return messages**
  - may contain return value
  - may be empty (void)

- **Life line represents existence of the object**

- **Message passing: synchronous or asynchronous arrowhead**

### Sequence Diagram Example

```
:aCustomer
:AppointmentBill
:Treatment
:Product
```

- checkAppointmentBill → :AppointmentBill
- getTreatmentPrice → :Treatment
- getProductPrice → :Product
- return → :Treatment
- return → :AppointmentBill
- calculatePrice() → :AppointmentBill
- return → :aCustomer

### Sequence Diagram Analysis

- **Who participates in the interaction?**
  - Actors and Objects

- **Vertical axis represents flow of time**

- **Message to / invocation of other object**
  - name represents the request made
  - may contain instantiated parameters

- **Return messages**
  - may contain return value
  - may be empty (void)

- **Life line represents existence of the object**

- **Message passing: synchronous or asynchronous arrowhead**

### Sequence Diagram Example (Detailed)

```
:aCustomer
:AppointmentBill
:Treatment
:Product
```

- checkAppointmentBill → :AppointmentBill
- getTreatmentPrice → :Treatment
- getProductPrice → :Product
- return → :Treatment
- return → :AppointmentBill
- calculatePrice() → :AppointmentBill
- return → :aCustomer

- Who is to trigger the next step?
  → return message or pass on control flow

## Sequence Diagrams
- Sequence Diagrams can model simple sequential flow, branching, iteration, recursion and concurrency
- They may specify different scenarios/runs
  - Primary
  - Variant
  - Exceptions

## Interaction frames: alt

## Interaction frames: loop

## Review

## What are the OO Design Principles?

There are five core OO Design Principles:

1. **Encapsulation** — Encloses the data and behaviour of an object within that object. It prevents unauthorised access and ensures data integrity by allowing an object to be changed only through permitted methods.

2. **Abstraction** — Focuses on core concerns and leaves out unnecessary detail. It exposes only essential information, hides the internal complexity of classes/objects, and promotes loose coupling by having objects interact via abstract interfaces.

3. **Inheritance** — Allows a class to inherit the properties and behaviour of another class. This promotes code reuse, reduces re-writing, and minimises errors and inconsistency.

4. **Polymorphism** — Allows a subclass to be substituted for a superclass. Behaviour belongs to the sub-classed object (dynamic method dispatch), enabling extensible, flexible, and modular systems.

5. **Composition** — Builds an object from other objects, enabling reuse and incremental construction of complex structures.

## What does a class diagram represent?

A class diagram represents a static view of a system. It models classes as templates for creating objects, showing each class's name, attributes (with visibility, name, and type), and methods (with visibility, name, parameters, and return type). It also shows the structural relationships between classes.

## Define association, aggregation, and generalization.

**Association** — A semantic relationship between two or more classifiers that specifies connections among their instances. It is a structural relationship specifying that objects of one class are connected to objects of another (e.g., a Patient has Appointments).

**Aggregation** — A special form of association that models a whole-part ("is a part-of") relationship between an aggregate (the whole) and its parts. It can be shared (a part belongs to multiple wholes) or non-shared. A stronger form called **Composition** is a non-shared aggregation where the parts cannot survive without the whole — they share the same lifetime.

**Generalization** — A relationship among classes where one class shares the properties and/or behaviour of one or more other classes. It defines a hierarchy of abstractions where a subclass inherits from a superclass, and represents an "is a kind of" relationship (e.g., NHS Patient and Non-NHS Patient are both kinds of Patient).

## How do you find associations?

The slides describe a Grammatical Parse approach: you identify associations by reading existing text descriptions of the system and looking for verbs and relationships between the nouns (which represent classes). You then narrow these down by removing duplicates, synonyms, irrelevant items, and anything out of scope. For instance, in the dental surgery example, words like "employs," "provides treatments to," and "allows patients to buy" would hint at associations between classes such as Dentist, Patient, and Treatment.

## What information does multiplicity provide?

Multiplicity specifies the number of instances one class relates to ONE instance of another class. For each association, two multiplicity decisions must be made — one for each end. Common notations include:

## NOTATION MEANING

| NOTATION | MEANING |
| --- | --- |
| 1 | Exactly one |
| 0..* or * | Zero or more |
| 0..1 | Zero or one (optional) |
| 1..* | One or more |
| 2..4 | Specified range |
| 2, 4..6 | Multiple, disjoint ranges |

For example: for each Patient, zero or many Appointments can be made; for each Appointment, there is exactly one Patient.

## What is the main purpose of a Sequence Diagram (SD)?

A Sequence Diagram's main purpose is to model how objects collaborate and interact with each other over time. Since no single object can carry out every responsibility on its own, objects must interact through messages — and SDs capture this. They are particularly good for real-time specifications and complex scenarios, and can model sequential flow, branching, iteration, recursion, and concurrency across different scenarios (primary, variant, and exception flows).

## What are the main concepts in a Sequence Diagram (SD)?

The main concepts are:

**Participants (Actors and Objects)** — The entities that take part in the interaction, arranged across the top of the diagram.

**Lifeline** — A vertical dashed line beneath each participant representing the existence of that object over time.

**Vertical time axis** — The vertical dimension represents the flow of time (top to bottom).

**Messages** — Horizontal arrows showing one object asking another to perform some activity. They carry a name representing the request and may contain parameters. Messages can be synchronous (filled arrowhead) or asynchronous (open arrowhead).

**Return messages** — Dashed arrows showing values or control being returned from a called object. They may carry a return value or be empty (void).

Interaction frames — Structural constructs such as alt (branching/conditional) and loop (iteration) that model more complex control flows within the diagram.
