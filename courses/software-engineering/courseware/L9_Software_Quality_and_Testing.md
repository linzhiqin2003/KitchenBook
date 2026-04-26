# L9. Software Quality and Testing

## Why is Software Quality relevant?

- Reputation Software developers and their organisations rely on reputation. A poor quality product (or family of products) can be enormously damaging for business. Software bugs can have immediate impacts on custom, especially in customer-facing industries. The automotive software problems with Volkswagen have led to an enormous amount of negative publicity, which has a direct impact on sales.

- Cost of Product and Maintenance/Limiting Costs of Product and Maintenance Cost is an overriding factor in software development. Poor quality software tends to be expensive to develop and to maintain, which can have a detrimental effect on business. Poor software quality can lead to technical debt, where the organisation in charge of the software needs to invest a disproportionate amount of resources into maintaining and running the software to make up for (and to try and remedy) poor design and implementation decisions.

- Software Certification Depending on the domain of the software (e.g. in Aircraft or Rail), the development and use of software might be restricted, and dependent on obtaining some form of certification. For example, software in modern civilian aircraft often has to be certified to the DO178 standard, which requires the extensive use of software quality assurance procedures throughout the software development lifecycle.

- Organisational Certification The organisational procedures and structures that are employed for software development can have a huge bearing on the quality of the software they produce. There are various ways by which to categorise the

extent to which an organisation employs good practice. International certification procedures and standards such as CMM and ISO90017 exist, so that software development organisations can advertise their “capability” to develop high quality software.

- **Legality（合法性）** Depending on the country, there may be overriding legal obligations that apply to organisations that use software. For example, in the UK, organisations have to demonstrate that the risk posed by their technology (this includes software) is “As Low As Reasonably Practicable” or “ALARP”. In other words, every “practicable” measure must have been taken to demonstrate that (in our case) the software system does not pose a risk to its users.

- **Moral / ethical codes of practice（道德/伦理规范）** Even in cases where a software system is not covered by industrial certification and legislation, and where its failure is not necessarily business or safety-critical, there can remain a moral obligation to the users. Professional organisations such as the American Computer Society (ACM) have explicit ethical guidelines and codes of practice, with statements such as “Software engineers shall act consistently with the public interest”. This clearly implies that they ought to do whatever possible to maximise the quality of their software and to prevent it from containing potentially harmful bugs.

## Software Quality is Multi-dimensional

- Subjective or “fitness for use”: as perceived by an individual user (e.g., aesthetics of GUI, missing functionality...) 主观或“适宜使用”：由个别用户感知（例如，图形界面的美观、缺失功能等）

- Objective or “conformance to requirements”: can be measured as a property of the product (e.g., detailed documentation, number of bugs, compliance with regulations ....) 目标或“符合要求”：可以作为产品的属性来衡量（例如，详细文档、漏洞数量、法规合规情况等）。

- Practical: what does it mean to your team and your clients?

- Fitness for use: Joseph Juran embodied the idea that the quality of product revolves around its fitness for use. He argued that, ultimately, the value of a product depends on the customer’s needs. Crucially, it forces the product developers to focus on those aspects of the product that are especially crucial (the vital few objectives) as opposed to the useful many. 使用适宜性：约瑟夫·朱兰体现了产品的质量取决于其适用性。他认为，最终产品的价值取决于客户的需求。关键是，它迫使产品开发者专注于产品中那些特别关键的方面（关键的少数目标），而非有用的众多目标。

- Conformance to Requirements: Phil Crosby embodied a different tone. He defined quality as “conformance to requirements”. His opinion was that quality can be achieved by the disciplined specification of these requirements, by setting

goals, educating employees about the goals, and planning the product in such a way that defects would be avoided. 符合要求：菲尔·克罗斯比体现了不同的基调。他将质量定义为“符合要求”。他认为，通过对这些要求的有纪律性地规范，设定目标、教育员工这些目标，以及以避免缺陷的方式规划产品，才能实现质量。

## Steps Towards Software Quality

- Use a standard development process
- Use a coding standard
  - Compliance with industry standards (e.g., ISO, Safety, etc.)
  - Consistent code quality
  - Secure from start
  - Reduce development costs and accelerate time to market 降低开发成本，加快上市时间
- Define and monitor metrics (defect metrics and complexity metrics)
  - High complexity leads to higher number of defects
- Identify and remove defects
  - Conduct manual reviews
  - Use Testing

## Testing process: key elements and relationships

## ppt底部注释

## System under Test (SUT)
This is the system (or unit/function) being tested. It seeks to implement the specification.

- The SUT can either be a white-box system, where we have complete access to the source code and the run-time state (e.g. the call-stack), or a black-box system, where we only have access to the external interface or API (depending on the type of system). It can also be a mixture of the two; for example, library routines might be provided in the form of closed source components, whilst the source code for the main core of the system is available for analysis.
The system might be reactive where the input / output behaviour at one stage is affected by previous inputs (e.g. a GUI), or it might process inputs in a single batch and return to its initial state. This matters from a testing perspective, because in the reactive case, the test inputs have to be formulated as sequences.

- The system might be deterministic, where it always returns the same answer for a given input. It might however also be non-deterministic, where the same input can elicit different outputs (perhaps because of randomised internal behaviour, or other factors beyond control such as thread-scheduling).

- It is commonly important to ensure that the SUT is an isolated version of the “live” system.

Specification A specification represents the idealised behaviour of the system under test. Depending on the development context, this might be embodied as a comprehensive, rigorously maintained document (e.g. a set of UML diagrams or a Z specification). Alternatively, if developed in an agile context, it might be a partial intuitive description captured in a selection of user stories, test cases, and documented as comments in the source code.

- The nature of the specification has an obvious bearing on testing. If a concrete, reliable specification document exists and there is a shared understanding of what the system is supposed to do, this can be used as the basis for a systematic test-generation process. If this is not the case, then testing becomes a more ad-hoc and dependent upon the intuition and experience of the tester.

Test cases The test cases correspond to the executions of the SUT. In practical terms a test case corresponds to an input (or a sequence of inputs) to the system.

- Test cases should ideally cumulatively execute every distinctive facet of software behaviour. An ideal test set (collection of test cases) should be capable of exposing any deviation that the SUT makes from the specification. If it can be shown to do this, the test set is deemed to be adequate.

Test Oracle Executing the test cases alone will not determine whether the SUT conforms to the specification or not. This decision – whether or not the output of a test is correct or not – is made by a test oracle. In practice, an oracle might be an assertion in the source code that is checked during the test execution, or it might be the human user, deciding whether or not the behaviour is acceptable.

- Test oracles are notoriously difficult to produce. There is in practice rarely an explicit, comprehensive, up to date specification that can be used as a reference. A successful software has usually been developed over the course of decades by a multitude of developers, which means that, ultimately, there is rarely a definitive record of how exactly the system should behave. What’s more, there may be tens of thousands of test cases, each of which might produces complex outputs, which can make the task of manual validation of the outputs prohibitively time consuming. These issues are collectively referred to as the oracle problem.

White Box Testing

- Access to software ”internals”:

  - Source code
  - Runtime state
  - Can keep track of executions. 可跟踪执行

- White box testing exploits (利用) this to
  - Use code to measure coverage
    - Many different ways
  - Drive generation of tests that maximise coverage

```c
int tri_type(int a, int b, int c) {
    int type;
    if (a > b)
    { int t = a; a = b; b = t; }
    if (a > c)
    { int t = a; a = c; c = t; }
    if (b > c)
    { int t = b; b = c; c = t; }
    if (a + b <= c)
        type = NOT_A_TRIANGLE;
    else {
        type = SCALENE;
        if (a == b && b == c)
            type = EQUILATERAL;
        else if (a == b || b == c)
            type = ISOSCELES;
    }
    return type;
}
```

## White-Box Testing

- Coverage Metrics:
  - Statement coverage
  - Branch coverage
  - *Def-Use or Dataflow coverage *
  - MC/DC (Modified Condition / Decision Coverage)
  - *Mutation coverage...*
- Prescribed metrics, e.g., DO178-B/C standard for civilian aircraft software
  - non-critical - statement coverage
  - safety-critical - MC/DC coverage
- Statement coverage: The proportion of executable statements in the program that have been executed.

- Branch coverage: The proportion of all of the logic-branches in the source code (e.g. outcomes of IF, WHILE, or FOR statements) to have been executed.
- Def-Use or Dataflow coverage: The source code is analysed to extract the def-use relations, which relate statements at which a variable is defined (i.e. instantiated and given a value) to subsequent statements using that definition. The test-goal is to cover all of the possible def-use relations.

%% 下面的没打印 %%

## Statement Coverage
- Test inputs should collectively have executed each statement 测试输入应集体执行每个语句
- If a statement always exhibits a fault when executed, it will be detected 如果一个语句在执行时总是表现出错误，那么它将被检测到
  Computed as:
  $$Coverage = \frac{Statements\ executed}{Total\ statements}$$

## Branch Coverage
- Test inputs should collectively have executed each branch
- Subsumes statement coverage
- Computed as:
  $$Coverage = \frac{Branches\ executed}{Total\ branches}$$

## Black Box Testing
- No access to “internals”
  - May have access, but don’t want to
- We know the interface
  - Parameters
  - Possible functions / methods
- We may have some form of specification document

## Testing Challenges
- Many different types of input
- Lots of different ways in which input choices can affect output
- An almost infinite number of possible inputs & combinations（组合）

## Equivalence Partitioning (EP) Method 等价划分方法
- Identify tests by analysing the program interface 通过分析程序接口识别测试

1. Decompose program into “functional units” 将程序分解为“功能单元”
2. Identify inputs / parameters for these units
3. For each input
    - Identify its limits（界限） and characteristics（特征）
    - Define “partitions” - value categories
    - Identify constraints（约束） between categories
    - Write test specification（规范）

## EP – 1. Decompose into Functional Units
- Dividing into smaller units is good practice
    - Possible to generate more rigorous（严谨的） test cases.
    - Easier to debug if faults（故障） are found.
- E.g.: dividing a large Java application into its core modules / packages
- Already a functional unit for the Grading Component（组件） example

## EP – 2. Identify Inputs and Outputs
- For some systems this is straightforward（简单）
    - E.g., the Triangle program:
        - Input: 3 numbers,
        - Output: 1 String
    - E.g., Grading Component
        - Input: 2 integers: exam mark and coursework mark
        - Output: 1 String for grade
- For others less so. Consider the following:
    - A phone app.
    - A web-page with a customised add component.

## EP – 3.a Identify Categories

## EP: 3.b Define “Partitions” - value categories

- Significant value ranges / value-characteristics of an input

| CATEGORY | DESCRIPTION | PARTITION |
|----------|-------------|-----------|
| Valid | EM_1 valid exam mark | $0 \leq$ Exam mark $\leq 75$ |
|  | CM_1 valid coursework mark | $0 \leq$ Coursework mark $\leq 25$ |
| Invalid | EM_2 invalid exam mark | Exam mark > 75 |
|  | EM_3 invalid exam mark | Exam mark < 0 |
|  | EM_4 invalid exam mark | alphabetic |
|  | EM_5 invalid exam mark | real number |
|  | CM_2 invalid coursework mark | Coursework mark > 25 |
|  | CM_3 invalid coursework mark | Coursework mark < 0 |
|  | CM_4 invalid coursework mark | alphabetic |
|  | CM_5 invalid coursework mark | real number |

## EP – 3.c Identify Constraints between Categories

- Not all categories can combine with each other（相互组合）

## EP – 3. d Write Test Specifications (规范)

For EM2, EM3, EM4: each 5 pairs, as shown for EM1 and EM5

## Example: Inputs and Expected Outputs

The test cases corresponding to partitions derived from the input exam mark are:

| CATEGORY        | CONDITION                  |
|-----------------|---------------------------|
| valid exam mark | EM_1                      | $0 \leq$ Exam mark $\leq 75$ |
| invalid exam mark | EM_2                    | Exam mark > 75               |
| invalid exam mark | EM_3                    | Exam mark < 0                |
| invalid exam mark | EM_4                    | alphabetic                   |
| invalid exam mark | EM_5                    | real number                  |
| valid coursework mark | CM_1               | $0 \leq$ Coursework mark $\leq 25$ |
| invalid coursework mark | CM_2            | Coursework mark > 25         |
| invalid coursework mark | CM_3            | Coursework mark < 0          |
| invalid coursework mark | CM_4            | alphabetic                   |
| invalid coursework mark | CM_5            | real number                  |

| TEST CASE | 1 | 2 | 3 |
| --- | --- | --- | --- |
| Input (exam mark) | 44 | -10 | 93 |
| Input (c/w mark) | 15 | 15 | 15 |
| total mark (as calculated) | 59 | 5 | 108 |
| Partition tested (of exam mark) | 0 ≤ e ≤ 75 | e < 0 | e > 75 |
| Exp. Output | 'B' | 'FM' | 'FM' |

## Boundary Values 边界价值

- Most frequently errors occur in "edge" cases
  - Test just under boundary value 略低
  - Test just above the boundary value 稍高
  - Test the boundary value

## How do we go about using this?

- Testing applied in Java unit
- Use JUnit
  - uses “Assertions” to test the code
  - Allow us to state what should be the case 请允许我们说明应该是什么情况
  - If assertions do not hold, JUnit’s logging mechanisms reports failures 如果断言不成立，JUnit的日志机制会报告失败
  - Various types of assertion are available, e.g., assertEquals( expected, actual ); assertTrue( condition ); assertFalse( condition ); assertThat( value, matchingFunction )

## Review (AI回答)

### What is Software Quality?

Software quality is multi-dimensional and can be understood from three perspectives:

- Subjective ("fitness for use") — As perceived by an individual user. This includes things like the aesthetics of a GUI or missing functionality that a user expects.

- Objective ("conformance to requirements") — A measurable property of the product, such as detailed documentation, number of bugs, or compliance with regulations.
- Practical — What quality means specifically to your team and your clients in their context.

Quality matters for a number of important reasons: it affects reputation, the cost of the product and its maintenance, software and organisational certification, legality, and adherence to moral and ethical codes of practice. The ISO/IEC 25010 standard provides a formal quality model covering multiple characteristics.

Steps towards achieving software quality include: using a standard development process and coding standards, defining and monitoring metrics (defect and complexity metrics), conducting manual reviews, and — crucially — using testing.

## What are the key elements and relationships for test specifications?

Based on the slides (referencing Staats, Whalen & Heimdahl, 2011), the key elements of a test specification in the context of Equivalence Partitioning (EP) are:

1. Functional Units — The system is first decomposed into smaller, testable units. This makes it easier to generate rigorous test cases and to debug when faults are found.

2. Inputs and Outputs — For each functional unit, the inputs (parameters) and expected outputs are clearly identified.

3. Categories — Inputs are classified into valid and invalid categories (e.g., valid exam mark, invalid exam mark).

4. Partitions — Each category is further divided into partitions — ranges or value characteristics of an input (e.g., $0 \leq \text{Exam mark} \leq 75$, $\text{Exam mark} > 75$, alphabetic input, real number input).

5. Constraints between Categories — Not all categories can be combined with each other. Constraints identify which combinations are valid or meaningful for test cases.

6. Test Specification (Input–Output Pairs) — Each equivalence class (EM) is paired with each coverage target (CM), producing a set of concrete test cases with defined inputs and expected outputs. For each EM, 5 pairs are defined across the CMs.

7. Boundary Values — Since errors most frequently occur at edge cases, tests should cover just below, at, and just above each boundary value.

## How do we carry out white-box testing?

White-box testing requires access to the software's internals, specifically:

- The source code
- The runtime state
- The ability to track executions

White-box testing uses this access to measure coverage and drive the generation of tests that maximise coverage. The key coverage metrics used are:

| COVERAGE METRIC | DESCRIPTION |
| --- | --- |
| Statement Coverage | Every statement in the code is executed at least once |
| Branch Coverage | Every branch (true/false) of each decision is executed |
| Def-Use / Dataflow Coverage | Tracks how variables are defined and used across paths |
| MC/DC (Modified Condition/Decision Coverage) | Each condition independently affects the outcome |
| Mutation Coverage | Checks whether tests can detect deliberately introduced faults |

Coverage requirements are context-dependent. For example, under the DO-178B/C standard for civilian aircraft software: non-critical systems require statement coverage, while safety-critical systems require the stricter MC/DC coverage.

## How do we carry out black-box testing?

Black-box testing involves no access to (or deliberate ignorance of) the software's internals. The tester only knows the interface — the parameters, possible functions/methods, and any specification document.

The primary method taught in the slides is Equivalence Partitioning (EP), carried out in the following steps:

**Step 1 — Decompose into Functional Units** Break the program into smaller, independently testable components.

Step 2 — Identify Inputs and Outputs Clearly define what the inputs are (e.g., two integers: exam mark and coursework mark) and what the expected output is (e.g., a grade string).

Step 3a — Identify Categories Classify inputs into valid and invalid categories for each input parameter.

Step 3b — Define Partitions For each category, define the specific value ranges or characteristics (e.g., $0 \leq$ Exam mark $\leq 75$ for valid; Exam mark $> 75$, Exam mark $< 0$, alphabetic, or real number for invalid).

Step 3c — Identify Constraints Determine which category combinations are meaningful or permissible in test cases.

Step 3d — Write Test Specifications Pair each input equivalence class (EM) with each coverage member (CM) to produce concrete input–output test pairs. For 5 EMs and 5 CMs this yields 25 test specifications.

Boundary Value Testing is then applied on top of EP: for each partition boundary, tests are written for the value just below, exactly at, and just above the boundary, since this is where errors most frequently occur.

In practice, these tests are implemented using tools such as JUnit in Java, using assertions like `assertEquals(expected, actual)`, `assertTrue(condition)`, and `assertFalse(condition)` to verify correctness automatically.
