# L3. Requirements Engineering

## Requirements

System requirements specify a system, not in terms of system implementation, but in terms of user observation. Requirements record description of the system features and constraints.

系统需求是根据用户观察来指定系统，而不是系统实现。需求记录系统特性和约束的描述。

- Functional requirements specify user interactions with the system, they say what the system is supposed to do:
  - Statements of services the system should provide 系统应提供的服务声明
  - How the system should react to particular inputs
  - How the system should behave in particular situations
  - May also state what the system should NOT do 也可以说明系统不应该做的事情

- Non-functional requirements specify other system properties, they say how the functional requirements are realised: 非功能需求规定了其他系统属性，它们说明了功能需求的实现方式：
  - Constraints ON the services or functions offered by system 系统所提供的服务或功能的约束
  - Often apply to whole system, not just individual features 通常适用于整个系统，而不仅仅是单个特征

## Why do we need Requirements Engineering?

## General Problems and Requirements Engineering

- Inconsistent terminology: people express needs in their own words
  术语不一致：人们用自己的话表达需求
- Conflicting needs for the same system
- People frequently don't know what they want (or at least can't explain !)
- Requirements change quite frequently
- Relevant people/information may not be accessible

Requirements are communication mechanism 需求包括通信机制

Requirements are instructions 需求就是指令

Requirements are acceptance criteria 要求是验收标准

- To be able to fairly assess whether the team have produced something that matches what you asked for, the thing that you asked for must be:
  - Unambiguous / Precise 明确/精确
  - Sufficiently accessible / Measurable 足够可及/可衡量
  - Understandable / Clear

## Analysing Requirements

Identify stakeholders involved with the system 识别系统相关的利益相关者

## The Onion model

The Wider Environment

The Containing System

The System

The Product or Service

Functional Beneficiary

Politician

Functional Beneficiary

Normal Operator

Champion

Sponsor

Purchaser

Developer

Interfacing System Owner

Negative Stakeholder

Regulator

Operational Support

Maintenance Operator

The Public

## Stakeholders

- Identification
  - Clients
  - Documentation, e.g., organisation chart 文档，例如组织结构图
  - Templates (e.g., onion model) 模板（例如，洋葱模型）
  - Similar projects 类似项目
  - Analysing the context of the project 分析项目背景
  - Surrogate stakeholders (e.g., legal, unavailable at present, mass product users) 替代利益相关者（例如，合法的、目前无法获得的、大规模产品用户）
  - Negative stakeholders

Identify top-level user needs/concerns (e.g., as NFRs or initiatives/epics) 识别顶级用户需求（例如NFR或倡议/史诗）

## Identify Epics

- High level requirement (no detail)
- Focused on business or user value
- Large and/or complex at scope 规模大或复杂
- Needs to be broken down into smaller pieced to implement 需要拆分成更小的部分来实施

- The pieced are grouped under that epic 这些作品被归入那个史诗
- Examples:
  - Enhance visual accessibility 提升视觉可及性
  - Implement alternative input methods
  - Build accessibility settings options 构建无障碍设置选项
- All part of an Initiative: “Increase usability for disabled users” 这一切都是倡议的一部分：“提升残障用户的可用性”

Break down needs (requirements) into individual stories (smaller steps) / Refine requirements 将需求拆分为单个故事/细化需求

## Break into “User Stories” - Template （重点）

公式：As a < type of user >, I want to < some goal > so that < some reason >.

For my epic: Enhance visual accessibility（视觉无障碍性）：

- As a user with low vision, I want to resize（调整）text so that I can read comfortably.
- As a colour-blind user, I want to customise the colour scheme（配色方案）so that I can see all content regardless of colour perception（感知）.
- As a user, I want sufficient contrast（足够的对比度）between text and background so that I can read all sections of the app.

## INVEST for Good User Stories（样卷）

INVEST is used to evaluate the quality of user stories, i.e., or how well a user story is written.

- Independent: Can be worked on separately from other stories.
- Negotiable: Flexible and open to discussion.
- Valuable: Delivers clear value to the user.
- Estimable: Can be estimated for effort.
- Small: Small enough to complete within a sprint.
- Testable: Has clear criteria to determine if it’s done.

## Acceptance Criteria for User Stories

Template:

Given <initial context or precondition>, when <action or event>, then <expected outcome>.

- Clear: easy to understand and unambiguous（明确的）.
- Testable: should be able to test to verify that it is met.
- Measurable（可衡量）: can be measured quantitatively or qualitatively.
- Atomic: each criteria is independent, can be checked by itself.

## Example Acceptance Criteria

As a user with low vision, I want to resize text so that I can read comfortably.

- Text resizing: Given I am on the website or application, when I navigate to the accessibility settings, then I should see an option to adjust text size (e.g., small, medium, large, extra large).
- No impact on non-text elements: Given I resize the text to any size, when I view non-text elements (e.g., images or icons), then they should not distort or change in size（不应变形或改变尺寸）.
- Default reset option（重置为默认值）: Given I have resized the text to a different size, when I want to return to the default size, then I should see and be able to use a "Reset to Default" option in the accessibility settings.

## Initiative vs Epic vs User Story

| INITIATIVE | EPIC | USER STORY |
| --- | --- | --- |
| A strategic objective for the company, with important business outcome. 该公司的战略目标，具有重要的业务成效。 | A large, strategic goal. 一个宏大的战略目标。 | A specific feature or functionality. 某项特定功能。 |
| Spans multiple epics and teams/departments. 涉及多个项目和团队/部门。 | Spans multiple sprints. 跨越多 个冲刺周期。 | Completed within a sprint. |
| Example: “Improve experience of disabled users.” | Example: “Enhance visual accessibility.” | Example: "As a user with low vision, I want to resize text so that I can read comfortably." |

## Prioritise User Stories: what to implement?

- Considering on:
  - User needs
  - Business value
  - Technical considerations 技术考量
- MoSCoW:
  - Must-Have（必备）: : essential （必不可少）
  - Should-Have（应有）: important
  - Could-Have（可选）: nice to have （有则更好）
  - Won’t-Have（暂不考虑）: out of scope at present （目前不在范围之内）
- Value vs Effort:
  - High value, Low effort (do first)
  - High value, High effort (do next)
  - Low value, Low effort (do if there is time)
  - Low value, High Effort (avoid)

## Non-functional Requirements（非功能性需求）

Non-functional requirements

Product requirements

Organizational requirements

External requirements

Efficiency requirements

Dependability requirements

Security requirements

Regulatory requirements

Ethical requirements

Usability requirements

Environmental requirements

Operational requirements

Development requirements

Legislative requirements

Performance requirements

Space requirements

Accounting requirements

Safety/security requirements

Specify atomic requirements (e.g., formal specification) 明确原子需求（例如，正式规范）（非重点）

Not detailed in this course, e.g.:

- Structured language
- Formal methods

## Requirements Elicitation Techniques 需求获取技术

- Interviews
- Observations
- Surveys
- Current documentation
- Similar products and solutions
- Co-design 共同设计
- Prototyping 原型制作

Some UML: use cases (use case diagram, use case description) 一些 UML：用例（用例图、用例描述）

## What is a use-case model?

- System behavior is how a system acts and reacts. Use cases describe the interactions between the system and (parts of) its environment.
- Describes the functional requirements of a system in terms of use cases 以用例描述系统的功能需求
- Links stakeholder needs to software requirements
- Serves as a planning tool
- Consists of (包含) actors and use cases

## A use-case model is comprised of (一个用例模型包括) :

- Use-case diagrams (visual representation)
- Use-case specifications (text representation) 用例规范（文本表示）

## Use-case diagram

- Shows a set of use cases and actors and their relationships 展示了一组用例、参与者及其关系
- Defines clear boundaries of a system 定义系统的明确边界
- Identifies who or what interacts with the system
- Summarizes the behavior of the system

Use-case diagram

The System

Actor 1

Use case 1

Use case 2

Use case 3

Actor 2

Actor 3

## What Are the Benefits of a Use-Case Model?

- Communication
- Identification
- Testing

## Major Concepts in Use-Case Modeling

- An actor represents anything that interacts with the system.
- A use case describes a sequence of events, performed by the system, that yields an observable result of value to a particular actor. 用例描述系统执行的一系列事件，为特定参与者产生可观测的价值结果。
- Association: Shows that a use case is initiated by an actor.

## Use-case specification 用例规范

- A requirements document that contains the text of a use case, including:
  - A description of the flow of events describing the interaction between actors and the system 描述事件流，描述行为者与系统之间的交互
  - Other information, such as:
    - Preconditions 前提条件
    - Postconditions 后期条件
    - Special requirements
    - Key scenarios 关键情景
    - Subflows 子流程

## Outline each use case 列出每个用例

An outline captures use case steps in short sentences, organized sequentially

## Use Case Name
## Brief Description
### Basic Flow
1. First step
2. Second step
3. Third step
### Alternative Flows
1. Alternative flow 1
2. Alternative flow 2
3. Alternative flow 3

Number and name the steps
Structure the basic flow into steps
Identify alternative flows

替代流程（Alternative Flows）描述系统在异常或分支情况下的处理方式

## Flows of events (basic and alternative) 事件流（基础和替代）
- A flow is a sequence of steps
- One basic flow
  - Successful scenario from start to finish 从头到尾的成功剧本
- Many alternative flows
  - Regular variants 常规变体
  - Odd cases 奇特案例
  - Exceptional (error) flows 异常（错误）流

## Checkpoints for use cases 用例检查点
- Each use case is independent of the others 每个用例彼此独立
- No use cases have very similar behaviors or flows of events
- No part of the flow of events has already been modeled as another use case 事件流程中没有任何部分被建模为另一个用例

## What Is an Actor?
- Actors represent roles a user of the system can play. 参与者代表系统用户可以扮演的角色。
- They can represent a human, a machine, or another system.
- They can actively interchange information with the system. 他们可以主动与系统

交换信息。
- They can be a giver of information. 他们可以传递信息。
- They can be a passive recipient of information. 他们可以被动接收信息。
- Actors are not part of the system.
  - Actors are EXTERNAL. 外在的

## What Is a Use Case?

Defines a set of use-case instances, where each instance is a sequence of actions a system performs that yields an observable result of value to a particular actor. 定义了一组用例实例，每个实例是系统执行的一系列动作，为特定演员产生可观测的价值结果。
- A use case models a dialogue between one or more actors and the system 用例模拟了一个或多个参与者与系统之间的对话
- A use case describes the actions the system takes to deliver something of value to the actor
  用例描述系统为向行为方提供有价值内容所采取的行动

## Use Cases and Actors

- A use case models a dialog between actors and the system. 用例模拟了参与者与系统之间的对话。
- A use case is initiated by an actor to invoke a certain functionality in the system. 一个用例由参与者发起，用于调用系统中的某个功能。

## What is a use-case scenario?

- An instance of a use case 一个用例实例
- An ordered set of actions from the start of a use case to one of its end points 从用例开始到终点的有序动作集合

## What are models for? (Review) （AI生成）

Based on the slides, a use-case model serves several purposes: it describes the functional requirements of a system in terms of use cases, links stakeholder needs to software requirements, serves as a planning tool, and consists of actors and use cases. More specifically, models are used for Communication (between end users, domain experts, and developers), Identification (of system interactions and requirements), and Testing

(providing a basis for test plans).

## What is system behavior? (Review) (AI生成)

The slides define system behavior as "how a system acts and reacts." Use cases are the mechanism used to describe the interactions between the system and (parts of) its environment.

## What is an actor? (Review) (AI生成)

An actor represents anything that interacts with the system. Key properties of actors include:

- They can represent a human, a machine, or another system.
- They can actively interchange information with the system.
- They can be a giver of information or a passive recipient of information.
- Critically, actors are NOT part of the system — they are EXTERNAL.

## What is a use case? (Review) (AI生成)

A use case defines "a set of use-case instances, where each instance is a sequence of actions a system performs that yields an observable result of value to a particular actor." In other words, a use case models a dialogue between one or more actors and the system, describing the actions the system takes to deliver something of value to the actor. It is initiated by an actor to invoke a certain functionality.

## What is a role? (Review) (AI生成)

The slides explain this through the concept of actors: "Actors represent roles a user of the system can play." A single person can play multiple roles. For example, in the slides, "Louis acts as a student" in one use case (Enroll for a Course) and "Louis acts as a customer" in another (Deposit Funds) — the same person plays different roles depending on the context.

## How do we know if our requirements are of good quality? (Review) (AI生成)

The slides give two complementary frameworks:

For requirements in general, they must be:

- Unambiguous / Precise
- Sufficiently accessible / Measurable
- Understandable / Clear

For user stories specifically, the INVEST criteria apply:

- Independent – can be worked on separately
- Negotiable – flexible and open to discussion
- Valuable – delivers clear value to the user
- Estimable – can be estimated for effort
- Small – completable within a sprint
- Testable – has clear criteria to determine if done

Acceptance criteria for each story must also be Clear, Testable, Measurable, and Atomic.
