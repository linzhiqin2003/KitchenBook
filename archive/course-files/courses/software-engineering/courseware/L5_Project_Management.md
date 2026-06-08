# L5. Project Management

## Agile Management – Key Practices

- Iterative and incremental (增量) delivery (交付)
  - Sprint cycles (e.g. 2-4 weeks)
  - Key roles and responsibilities:
    - Product Owner
      - Epics, User Stories, Backlog Grooming (积压整理).
    - Development Team,
      - Continuous Integration/Delivery, Pair Programming, Test-Driven Development
    - Scrum Master
      - Daily stand-ups, sprint planning, sprint reviews, and retrospectives 回顾
    - Kanban: limiting Work in Progress, transparency (透明) of progress

## Measurement is Central to Quality 衡量是质量的核心

- How to plan for the project time and effort?
  - For the team?
  - For the customer?
- Which software/part of it needs more time for testing?
- Which developer should get a bonus payment for productivity?....

## What is “Measurement”?

- Attributing values to objects. 赋予对象价值。
  - The fuel efficiency of a car (gallons per mile)
  - The number of goals scored by a footballer

- The cost of a house
- Can use these values as basis for comparison 可以将这些数值作为比较基础
  - What is the cheapest house?
  - Who is the best goal scorer?
- Can use these measurements and comparisons to make better decisions.
  - Which car should I buy (e.g., given five candidate cars)
  - Which striker （前锋）should I put in my team?

## Measurement is Difficult in Software Engineering

- Most entities are difficult to measure reliably 大多数实体都难以可靠测量
- Difficult or impossible to “pin down” a single value 很难或不可能“确定”一个单一的数值
- Quality Models: ISO/IES25010

- Functional Suitability
  - Functional Completeness
  - Functional Correctness
  - Functional Appropriateness
- Performance Efficiency
  - Time Behaviour
  - Resource Utilisation
  - Capacity
- Compatibility
  - Co-existence
  - Interoperability
- Usability
- Appropriateness
- Realisability
- Learnability
- Operability
- User Error Protection
- User Interface Aesthetics
- Accessibility
- Integrity
- Non-repudiation
- Authenticity
- Accountability
- Maintainability
  - Modularity
  - Reusability
  - Analysability
  - Modifiability
  - Testability
- Reliability
  - Maturity
  - Availability
  - Fault Tolerance
  - Recoverability
- Security
  - Confidentiality
- Portability
  - Adaptability
  - Installability
  - Replaceability

## Usual Metrics: Size and Complexity 常用指标：规模与复杂度

- After development ...
  - How much effort will it require for maintenance?
  - Where should we direct testing effort?
  - How much effort was required for development?
  - Metrics are based upon source code (“white box”)
- Before development has started ...
  - How much programming effort will module X require?

- What will be the estimated cost of the final product?
- Metrics are based upon requirements / specification (“black box”)

## White Box Complexity Metrics

- Number of lines in a file (or a group of files)
  - Easy to compute
  - Easy to understand and interpret
  - Often sufficient for an approximate measure of size
  - Widely used (perhaps the most widely used) metric
  - Comments
  - What is a line?
  - Blank lines
  - Not all “lines” are equal
  - Ignores logical/ architectural complexity
  - Highly language-specific 高度依赖语言
- Cyclomatic Complexity 环形复杂性
  - Calculated from the control flow graph:
    $$
    V(G) = E - N + 2P
    $$
    E – number of edges;
    N – number of nodes;
    P – number of procedures (usually 1)
  - Number of independent paths through the code
  - Independent path – any path that introduces at least one new statement/condition 独立路径——任何引入至少一个新语句/条件的路径

## Black Box Complexity Metrics

### Estimating Agile Projects

Desired features（所需功能）→ Estimate size → Derive duration（确定持续时间）→ Schedule

### Story Points (Size Estimation)

- An informal, agile unit of “size measurement”
  - Usually an estimate from 1-10
- Derive（推导） an estimate from the whole team at sprint planning meetings
- Based on the idea of the “Wisdom of the Crowds” 基于“群众智慧”的理念
  - The collective estimate of groups (i.e., of effort required for a story) is better than the estimate of an individual 对群体的集体估计（即为一个故事所需的 effort）比对单个人的估计更好

## Planning Poker
- The whole team is involved
- Each member is given a set of numbered cards
- Numbers follow the Fibonacci sequence
  - 1,3,5,8,13,20,...
    - Larger tasks become harder to estimate in exact terms
    - Low values - trivial to implement
    - High values - difficult to implement
- Each member is also given a “?” card
- Cycle repeats for a maximum of 3 iterations (to avoid infinite loops!)

## Team Velocity
- Number of (estimated) story points implemented per sprint.
- Can be derived from previous sprints.
  - e.g., Average points implemented from previous x sprints.
- Can be used to estimate:
  - Time required to complete project.
  - Target number of stories that can be completed in a sprint.

## Burn Charts

## Feedback Loops

Estimate
Actual

30
22.5
15
7.5
0

Start Monday Tuesday Wednesday Thursday Friday

## Feedback Loops – Sprint Review（默写）

## SPRINT 1
## SPRINT 2
## SPRINT 3
## SPRINT 4
## SPRINT 5

Retrospective 1
Retrospective 2
Retrospective 3
Retrospective 4

Roles: Product Owner, Scrum Master, Team
Ceremonies: Sprint Planning, Daily Scrum, Sprint Review, Sprint Retrospective
Artifacts: Product Backlog, Sprint Backlog, Working Software
Agreements: Working Agreement, Definition of Ready, Definition of Done

24 Hours
Daily Stand-Up

Product
Backlog

Sprint
Backlog

Build/Test the
Sprint Backlog
(2 Weeks)

Sprint
Retrospective

Sprint
Review

Working
Product
Increment

Sprint Planning

## Feedback Loops – Sprint Retrospective（样卷）

| Purpose | To inspect the product increment and gather feedback from stakeholders. |
| --- | --- |
| Focus | Focuses on the product and deliverables completed during the sprint. |
| Attendees | Development team, Product Owner, Scrum Master, stakeholders, customers, users. |
| Output/Outcome | Feedback on the product, potential changes to the product backlog or requirements. |
| When It Happens | At the end of the sprint, before the next sprint starts. |
| Duration | Typically 1-2 hours, depending on the sprint length and amount of work delivered. |
| What Is Discussed | - What was completed during the sprint.<br>- Demonstration of the increment.<br>- Feedback from stakeholders.<br>- Any changes to priorities or new requirements. |
| Key Question | "Does the product meet stakeholder expectations, and what adjustments are needed?" |
| Goal | To get stakeholder feedback and adapt the product based on it. |
| Artifacts or Tools | - Product backlog<br>- Sprint backlog<br>- Potential product increment demo |
| Example Questions Asked | - What value did we deliver in this sprint?<br>- Are stakeholders satisfied with the current progress?<br>- What changes are needed to the product or backlog? |

| Purpose | To inspect the process, reflect on team performance, and identify improvements. |
| --- | --- |
| Focus | Focuses on the process, team collaboration, and workflow improvements. |
| Attendees | Development team and Scrum Master (Product Owner may join but is not required). |
| Output/Outcome | Actionable items aimed at improving team processes in future sprints. |
| When It Happens | At the end of the sprint, immediately after or separate from the sprint review. |
| Duration | 30-60 minutes for short sprints (longer for longer sprints). |
| What Is Discussed | - What went well during the sprint.<br>- What didn't go well.<br>- Team challenges and blockers.<br>- How to improve collaboration and productivity. |
| Key Question | "How can we improve the way we work as a team?" |
| Goal | To drive continuous improvement within the team's process and collaboration. |
| Artifacts or Tools | - Retrospective boards (e.g., Start/Stop/Continue, Mad/Sad/Glad)<br>- Actionable items list |
| Example Questions Asked | - What should we start doing, stop doing, or continue doing?<br>- Were there any blockers, and how can we prevent them?<br>- How was team collaboration? |

## Review

### What are the key practices in Agile Management? (AI生成)

The key practices in Agile Management are organised around three main roles:

**Iterative & Incremental Delivery** — Work is structured into sprint cycles (typically 2–4 weeks), delivering functional increments of the product continuously.

**Product Owner practices** include writing Epics and User Stories, maintaining and grooming the Product Backlog, and prioritising requirements.

**Development Team practices** include Continuous Integration/Delivery, Pair Programming, and Test-Driven Development (TDD).

Scrum Master practices include facilitating Daily stand-ups, Sprint Planning, Sprint Reviews, and Sprint Retrospectives.

Kanban is also used to limit Work in Progress (WiP) and maintain transparency of progress across the team.

## How can we measure complexity? (AI生成)

The slides describe two categories of complexity measurement:

### White Box Metrics (used after development, based on source code):

- **Lines of Code (LoC)** — The simplest and most widely used metric. It is easy to compute and interpret, and gives an approximate measure of size. However, it has significant limitations: it ignores logical/architectural complexity, is highly language-specific, and not all lines are equal in effort or value.

- **Cyclomatic Complexity** — A more sophisticated metric calculated from the control flow graph using the formula: $V(G) = E - N + 2P$, where $E$ = number of edges, $N$ = number of nodes, and $P$ = number of procedures. It measures the number of independent paths through the code, giving a better picture of logical complexity than LoC alone.

### Black Box Metrics (used before development, based on requirements/specifications):

- **Story Points** — An informal agile unit of size estimation (usually 1–10), derived collectively by the whole team at sprint planning, based on the "Wisdom of the Crowds" principle.

- **Planning Poker** — A structured team estimation technique where each member selects a card from a Fibonacci-sequence deck (1, 3, 5, 8, 13, 20...) to represent their effort estimate. Diverging estimates are discussed and the process repeats for up to 3 iterations until consensus is reached.

## Why do we use black box options? (AI生成)

We use black box metrics because they allow us to estimate complexity and effort before development has started, when no source code yet exists to analyse. At this early stage, we only have requirements and specifications to work from. Black box methods like Story Points and Planning Poker help answer critical planning questions such as: How much programming effort will a module require? and What will be the estimated cost of the final product? They also leverage the "Wisdom of the Crowds" — collective team estimates tend to be more accurate than any individual estimate alone. Furthermore, they

avoid the pitfalls of white box metrics (like LoC) which can be gamed or misinterpreted.

## What mechanisms does Agile Development use for feedback? (AI生成)

Agile uses two primary structured feedback loops at the end of each sprint:

### 1. Sprint Review

- **Purpose**: To inspect the product increment and gather feedback from stakeholders.
- **Focus**: The product — what was built and delivered during the sprint.
- **Attendees**: Development team, Product Owner, Scrum Master, stakeholders, customers, and users.
- **Output**: Feedback on the product, potential changes to the backlog or requirements.
- **Key Question**: "Does the product meet stakeholder expectations, and what adjustments are needed?"
- **Duration**: Typically 1–2 hours.

### 2. Sprint Retrospective

- **Purpose**: To inspect the process, reflect on team performance, and identify improvements.
- **Focus**: Team collaboration, workflow, and internal processes — not the product.
- **Attendees**: Development team and Scrum Master (Product Owner is optional).
- **Output**: Actionable improvement items for future sprints (e.g., using Start/Stop/Continue or Mad/Sad/Glad boards).
- **Key Question**: "How can we improve the way we work as a team?"
- **Duration**: 30–60 minutes for short sprints.

Together, these two mechanisms ensure continuous improvement at both the product level (Sprint Review) and the process level (Sprint Retrospective).
