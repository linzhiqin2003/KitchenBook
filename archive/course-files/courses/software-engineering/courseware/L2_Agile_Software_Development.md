# L2. Agile Software Development

Agile software development, including: extreme programming（极限编程）; test-driven development; scrum; and Kanban

## What is Agile Software Development?

- Agile is a way of thinking about software development
  软件开发的思维方式

## Four key values for software development

- Individuals and interactions over processes and tools 重视个体和互动胜于流程和工具
- Working software over comprehensive documentation 可运行的软件胜于详尽的文档
- Customer collaboration over contract negotiation 重视客户协作而非合同谈判
- Responding to change over following a plan 应对变化胜于遵循计划

## Agile was created by coders for coders

- Coders like
  - Writing quality code
  - Ticking things off their to do list 完成他们待办事项清单上的任务

- Impressing clients by showing them working software
- Coders dislike
  - Writing extensive documentation 撰写详细文档
  - Committing to a final design in advance 提前确定最终设计
  - Being micromanaged 被过度管理
  - Working to big, immovable deadlines 应对巨大且无法移动的最后期限

## Twelve agile principles

| SATISFY CLIENTS' NEEDS | SATISFY CODERS' NEEDS |
|------------------------|------------------------|
| The highest priority is satisfying the client (by delivering working software early and continuously) | Work at a steady, sustainable pace (no heroic efforts) 保持稳定可持续的工作节奏（不要过度努力） |
| Embrace change (even late in the development cycle) 接受变化（即使在开发周期的后期） | Rely on self-organising teams |
| Collaborate every day with the client | Teams reflect regularly on their performance 团队定期反思他们的表现 |
| Use face to face communication | Progress is measured by the amount of working code produced 进步是通过产生的可运行代码量来衡量的 |
| Deliver working software frequently 经常交付可运行的软件 | Continuous attention to technical excellence 持续关注技术卓越 |
| Minimise the amount of unnecessary work | Build teams around motivated individuals |

## Agile Methods

Popular methods include:

- Extreme Programming (XP) (the two co-creators were signatories of the manifesto) 极限编程（XP）（两位共同创始人是宣言的签署者）
- Test-driven development (creator was a signatory) 测试驱动开发（创始人是签署人）
- Kanban

- Scrum (the two co-creators were signatories)

## Extreme Programming Ethos 极限编程精神（样卷已有）

- Simple design: use the simplest way to implement features
- Sustainable pace: effort is constant and manageable 可持续的节奏：努力是稳定且可控的
- Coding standards: teams follow an agreed style and format
- Collective ownership: everyone owns all the code 集体所有制：每个人都拥有所有代码
- Whole team approach（全队参与）: everyone is included in everything

## Extreme Programming Practices（样卷已有）

- Pair programming: two heads are better than one
- Test driven: ensure the code runs correctly
- Small releases: deliver frequently and get feedback from the client
- Continuous integration: ensure the system is operational（可运行）
- Refactor: restructure the system when things get messy 重构：当系统变得混乱时进行重组

## Pair programming in more detail

Code is written by two programmers on one machine:

- The helm uses the keyboard and mouse and does the coding 舵手使用键盘和鼠标进行编码
- The tactician thinks about implications and potential problems 策略家考虑影响和潜在问题
- Communication is essential for pair programming to work
- Pair programming facilitates project communication 结对编程促进项目沟通
- The pair doesn’t "own" that code - anyone can change it

- Pairings can (and should) evolve at any time 配对可以（也应该）随时演变
- All code is reviewed as it is written 所有代码在编写时都会被审查
- The tactician is ideally positioned to recommend refactoring 战略家处于理想位置，可以建议重构

## Test-driven development in more detail

- Tests are written before any code and they drive all development
- A programmer’s job is to write code to pass the tests
- If there’s no test for a feature, then it is not implemented
- Tests are informed by the requirements of the system 测试由系统的要求驱动

## The benefits of test-driven development

- Code coverage 代码覆盖率

  We can be sure that all code written has at least one test because if there were no test, the code wouldn’t exist

- Simplified debugging

  If a test fails, then we know it must have been caused by the last change

- System documentation 系统文档

  Tests themselves are one form of documentation because they describe what the code should be doing

## Scrum

Scrum is a project management approach

Some key concepts are:

- The Scrum – a stand-up daily meeting of the entire team 整个团队的每日立会
- Scrum Master - team Leader

- Sprint - a short, rapid development iteration 冲刺——一次短期快速的开发迭代
- Product Backlog（产品待办事项清单） - To do list of jobs that need doing
- Product Owner - the client (or their representative)（或其代表）

## Kanban Board

- It's basically a flexible “to do” list tool 它基本上是一个灵活的“待办事项”工具
- Issues progress through various states from ”To do” to “Done” 问题会从“待办”状态逐步推进到“已完成”状态
- It was originally implemented as post-it notes on a whiteboard 它最初是作为白板上的便条纸实现的
- Various digital tools now fulfil the same function e.g. Jira 各种数字工具现在实现相同的功能，例如Jira

## Columns

- you might have columns for:
  - Backlog 待办事项
  - Being Verified 正在验证
  - Awaiting integration 等待整合
- Do what works for your team but make sure you have a “Done” column

## Problems with Agile

- Hard to draw up legally binding contracts because a full specification is never written in advance 很难制定具有法律约束力的合同，因为完整的规范从未提前写好
- Good for green-field development when you have a clean slate and are not constrained by previous work. However, it’s not so effective for brownfield development which involves improving and maintaining legacy systems. 对于全新开发来说非常适合，因为你有一个干净的起点，并且不受之前工作的限

制。然而，对于棕地开发（涉及改进和维护遗留系统）来说，它的效果不太明显。
- Works well for small co-located teams, but what
about large distributed development? 适合小型集中团队，但对于大型分布式开发呢?
- Relies on the knowledge of developers in the team
but what if they aren’t around (holidays, illness,
turnover)? 依赖团队中开发人员的知识，但如果他们不在（休假、疾病、人员流动）怎么办
