"""Generate concepts.json for the online review module."""
import json, os

chapters = []

def ch(id, title):
    chapters.append({"id": id, "title": title, "questions": []})

def q(text, marks, answer, mock=None):
    chapters[-1]["questions"].append({
        "id": len(chapters[-1]["questions"]) + 1,
        "question": text,
        "marks": marks,
        "mock": mock,
        "answer": answer if isinstance(answer, list) else [answer],
    })

# ═══ L1 ═══
ch("l1-introduction", "Introduction to Software Engineering")

q("List three reasons behind the 'Software Crisis'.", 3, [
    "Software is getting larger and larger.",
    "Software is getting more complex (complex domains, systems dependency).",
    "Time to market is shorter than ever.",
])

q("List six reasons why software projects fail.", 3, [
    "Poor requirements / over-ambitious requirements / unnecessary requirements.",
    "Over budget.",
    "Contract management issues.",
    "End-user training gaps.",
    "Operational management failures.",
    "Note: 'bad developers' is NOT the main problem.",
])

q("Define Software Engineering.", 2, [
    "Engineering: cost-effective solutions to practical problems by applying scientific knowledge to building things for people.",
    "SE: design, development, testing, and maintenance of software applications, applying engineering principles and programming knowledge to build solutions for end users.",
])

q("List five collaboration tools and techniques.", 2, [
    "Modelling and diagramming (to reach consensus on design).",
    "GitHub (sharing documents for collaboration).",
    "Kanban (task allocation and progress monitoring).",
    "Test-driven development (stop others breaking your code).",
    "Other techniques: experiment and explore.",
])

q("List the seven Software Development Tasks.", 3, [
    "Requirements Analysis", "Planning", "Design (high level and detailed)",
    "Development", "Testing", "Deployment", "Operation and Maintenance",
])

q("Name four examples of Software Development Life Cycles.", 2, [
    "Waterfall, Agile, V-Model, Spiral.",
])

q("List and briefly describe the five stages of the Waterfall SDLC.", 5, [
    "Requirements Definition: gathering functional and non-functional requirements.",
    "System and Software Design: deciding how parts interact, dividing work.",
    "Implementation and Unit Testing: parallel coding, versioning, automated testing, docs.",
    "Integration and System Testing: combining modules, verifying whole system.",
    "Operation and Maintenance: deploying, ongoing support, bug fixes.",
])

q("Define functional requirements and non-functional requirements.", 2, [
    "Functional: what the system should do — services, reactions to inputs, behaviours, what NOT to do.",
    "Non-functional: quality properties — security, ease of use, response time. Constraints on services, apply to whole system.",
])

q("Explain the difference between Verification and Validation. Give an example where software passes verification but fails validation.", 5, [
    "Verification: 'Are you building it right?' — checks compliance with specifications.",
    "Validation: 'Are you building the right thing?' — checks it meets actual user needs.",
    "Example: system built per spec (passes V) but spec didn't capture a real user need like mobile access (fails V).",
])

q("State three advantages and three disadvantages of the Waterfall model.", 3, [
    "Advantages: Simple to use; every phase has defined result and review; perfect for clear agreed requirements.",
    "Disadvantages: Software ready only after last stage; high risks and uncertainty; not suited for changing requirements; late integration.",
])

q("Define the Software Development Lifecycle (SDLC).", 2, [
    "A structured and iterative methodology used by development teams to build, deliver and maintain high-quality and cost-effective software systems.",
])

# ═══ L2 ═══
ch("l2-agile", "Agile Software Development")

q("What is Agile Software Development?", 1, [
    "Agile is a way of thinking about software development.",
])

q("State the four key values of the Agile Manifesto.", 4, [
    "Individuals and interactions over processes and tools.",
    "Working software over comprehensive documentation.",
    "Customer collaboration over contract negotiation.",
    "Responding to change over following a plan.",
])

q("List four things coders LIKE and four things coders DISLIKE.", 4, [
    "Like: writing quality code; ticking off to-do list; impressing clients with working software; (any above).",
    "Dislike: writing extensive documentation; committing to a final design in advance; being micromanaged; working to big immovable deadlines.",
])

q("List six Agile principles that satisfy clients' needs and six that satisfy coders' needs.", 6, [
    "Client: (1) highest priority = satisfying client with early/continuous delivery (2) embrace change even late (3) collaborate daily with client (4) face-to-face communication (5) deliver working software frequently (6) minimise unnecessary work.",
    "Coder: (1) steady sustainable pace (2) self-organising teams (3) teams reflect regularly (4) progress = working code (5) continuous attention to technical excellence (6) build teams around motivated individuals.",
])

q("[MOCK Q1] Describe the ethos underlying Extreme Programming. [5]\nBriefly describe five practices used in Extreme Programming. [5]", 10, [
    "Ethos: Simple design; Sustainable pace; Coding standards; Collective ownership; Whole team approach.",
    "Practices: Pair programming; Test driven; Small releases; Continuous integration; Refactoring.",
], mock="Q1")

q("Describe pair programming in detail: the two roles, key rules, and benefits.", 4, [
    "Helm: uses keyboard and mouse, does the coding.",
    "Tactician: thinks about implications and potential problems, recommends refactoring.",
    "Code not 'owned' by pair — anyone can change it. Pairings evolve at any time.",
    "All code is reviewed as written. Facilitates project communication.",
])

q("Explain TDD: core rules and three benefits.", 3, [
    "Rules: tests written before code; no test = no feature; tests informed by requirements.",
    "Benefits: code coverage (all code has ≥1 test); simplified debugging (failure = last change); system documentation (tests describe what code does).",
])

q("List and define the five key Scrum concepts.", 3, [
    "The Scrum: daily stand-up meeting of entire team.",
    "Scrum Master: team leader.",
    "Sprint: short rapid development iteration.",
    "Product Backlog: to-do list of jobs.",
    "Product Owner: the client or their representative.",
])

q("Describe the Kanban board: what it is, how it works, and typical columns.", 3, [
    "A flexible 'to do' list tool (originally post-it notes on whiteboard, now digital e.g. Jira).",
    "Issues progress through states from 'To do' to 'Done'.",
    "Columns: Backlog, Being Verified, Awaiting Integration, Done. Must have a 'Done' column.",
])

q("List four problems or limitations of Agile.", 4, [
    "Hard to draw up legally binding contracts — no full spec in advance.",
    "Good for greenfield but not effective for brownfield/legacy systems.",
    "Works for small co-located teams, challenging for large distributed development.",
    "Relies on developer knowledge — what if they're unavailable (holidays, illness, turnover)?",
])

# ═══ L3 ═══
ch("l3-requirements", "Requirements Engineering")

q("What are system requirements? Distinguish functional and non-functional.", 3, [
    "Requirements specify a system in terms of user observation, not implementation.",
    "Functional: what the system does — services, reactions, behaviours, what NOT to do.",
    "Non-functional: quality properties — constraints on services, apply to whole system (security, usability, performance).",
])

q("List five general problems that make requirements engineering necessary.", 3, [
    "Inconsistent terminology: people express needs in their own words.",
    "Conflicting needs for the same system.",
    "People frequently don't know what they want.",
    "Requirements change frequently.",
    "Relevant people/information may not be accessible.",
])

q("Requirements serve as three things. What are they?", 1, [
    "Communication mechanism, instructions, and acceptance criteria.",
])

q("What three properties must good requirements have?", 2, [
    "Unambiguous / Precise.",
    "Sufficiently accessible / Measurable.",
    "Understandable / Clear.",
])

q("What is the Onion Model? List at least six stakeholder roles.", 3, [
    "Template for identifying stakeholders, organized in concentric layers from product outward.",
    "Roles: Normal Operator, Functional Beneficiary, Champion, Sponsor, Purchaser, Developer, Maintenance Operator, Operational Support, Interfacing System Owner, Negative Stakeholder, Regulator, Politician, The Public.",
])

q("List seven methods for stakeholder identification.", 2, [
    "Clients; Documentation (org charts); Templates (onion model); Similar projects; Context analysis; Surrogate stakeholders; Negative stakeholders.",
])

q("Define an Epic and list its characteristics.", 2, [
    "High-level requirement (no detail), focused on business/user value, large/complex at scope, needs breakdown into smaller pieces grouped under it.",
])

q("Write the User Story template and give one example.", 2, [
    "As a <type of user>, I want to <some goal> so that <some reason>.",
    "Example: As a user with low vision, I want to resize text so that I can read comfortably.",
])

q("[MOCK Q2] How is INVEST used? What does each letter mean? [7]\nWhich 3 INVEST criteria does 'As a disabled user, I want to update the app settings so that I can use the app comfortably' fail? [3]", 10, [
    "INVEST evaluates quality of user stories (how well written).",
    "I=Independent (work separately), N=Negotiable (flexible), V=Valuable (clear user value), E=Estimable (estimate effort), S=Small (fits in sprint), T=Testable (clear done criteria).",
    "Fails: Small (it's an epic, many disability types), Estimable (unclear effort), Testable (unclear acceptance tests).",
], mock="Q2")

q("Write the Acceptance Criteria template and list the four qualities.", 2, [
    "Template: Given <context>, When <action>, Then <expected outcome>.",
    "Qualities: Clear, Testable, Measurable, Atomic.",
])

q("Explain the hierarchy: Initiative → Epic → User Story.", 3, [
    "Initiative: strategic objective, important business outcome, spans multiple epics and teams.",
    "Epic: large strategic goal, spans multiple sprints, needs breakdown.",
    "User Story: specific feature, completed within a single sprint.",
])

q("Explain the MoSCoW prioritization method.", 2, [
    "Must-Have (essential), Should-Have (important), Could-Have (nice to have), Won't-Have (out of scope at present).",
])

q("Explain the Value vs Effort prioritization matrix.", 2, [
    "High value + Low effort → do first. High value + High effort → do next.",
    "Low value + Low effort → do if time. Low value + High effort → avoid.",
])

q("List seven requirements elicitation techniques.", 2, [
    "Interviews, Observations, Surveys, Current documentation, Similar products, Co-design, Prototyping.",
])

q("List the non-functional requirements categories (top-level and sub-categories).", 3, [
    "Product requirements: efficiency, dependability, security, usability.",
    "Organizational requirements: environmental, operational, development.",
    "External requirements: regulatory, ethical, legislative (accounting, safety/security).",
])

q("What is a Use Case Model? What two parts does it consist of?", 3, [
    "Describes functional requirements in terms of use cases, links stakeholder needs to software requirements, serves as planning tool.",
    "Two parts: use-case diagrams (visual) and use-case specifications (text).",
])

q("What are the three benefits of a Use-Case Model?", 1, [
    "Communication, Identification, Testing.",
])

q("What is an Actor? List five properties.", 3, [
    "Anything that interacts with the system.",
    "Can be human, machine, or another system. Can actively interchange information. Can give or passively receive information.",
    "Actors are NOT part of the system — they are EXTERNAL.",
])

q("What is a Use Case?", 2, [
    "A set of use-case instances, each a sequence of actions the system performs that yields an observable result of value to a particular actor.",
    "Models a dialogue between actors and the system.",
])

q("What does a use-case specification contain?", 2, [
    "Description of flow of events (actor-system interaction), preconditions, postconditions, special requirements, key scenarios, subflows.",
])

q("Explain basic flow vs alternative flows in use cases.", 2, [
    "Basic flow: one successful scenario from start to finish.",
    "Alternative flows: regular variants, odd cases, exceptional/error flows. Many per use case.",
])

q("List the three checkpoints for validating use cases.", 2, [
    "Each use case is independent of the others.",
    "No use cases have very similar behaviours or flows.",
    "No part of the flow has already been modelled as another use case.",
])

q("[MOCK Q5] NiceHair hairdresser system:\n5.1 Write 2 epics + 3 user stories per epic [16]\n5.2 Write acceptance criteria for each [6]\n5.3 Key agile team roles? [3]", 25, [
    "Epic 1 — Product Catalog: (1) manager adds products (2) stylist searches by name/brand (3) owner updates pricing/availability.",
    "Epic 2 — Inventory: (1) manager sets min stock alerts (2) stylist checks availability (3) owner generates stock reports.",
    "Acceptance criteria: Given/When/Then for each story.",
    "Roles: Product Owner (vision, backlog), Scrum Master (processes, obstacles), Developers (code, test, deploy).",
], mock="Q5")

# ═══ L4 ═══
ch("l4-ood", "Object-Oriented Design")

q("What is Object-Oriented Software? Distinguish Classes from Objects.", 2, [
    "OO: structure software around objects and their interactions. Objects contain state and behaviour.",
    "Class = blueprint for types of objects (e.g. Car). Object = individual instance (e.g. Ford Fusion reg AB25CDF).",
])

q("List five reasons why we do design.", 2, [
    "Organise ideas; plan work; build understanding of structure/behaviour; communicate with dev team; help future maintenance.",
])

q("Define Encapsulation and explain why it matters.", 3, [
    "Encloses data and behaviour within the object.",
    "Prevents unauthorised access. Controlled access: changed only by permitted methods. Protects data integrity.",
    "Example: private String name; public getName() — name accessed only via getter.",
])

q("Define Abstraction and explain its benefit.", 2, [
    "Focus on core concerns, expose only essential info, hide complexity.",
    "Benefit: loose coupling — objects interact via abstract interfaces, not concrete implementations.",
])

q("Define Inheritance. State two benefits.", 2, [
    "Inherit properties and behaviour from another class ('is-a' relationship).",
    "Benefits: reuse code (reduce re-writing), reduce errors and inconsistency.",
])

q("Define Polymorphism. Give a brief example.", 2, [
    "Subclass substitution for superclass. Behaviour belongs to subclass (dynamic method dispatch). Enables extensibility.",
    "Example: Animal a = new Dog(); a.makeSound(); → 'Woof!' — subclass method called.",
])

q("Define Composition. Distinguish it from Aggregation.", 3, [
    "Composition: build from other objects, strong ownership, coincident lifetimes — parts can't survive the whole. Non-shared aggregation.",
    "Aggregation: whole-part ('part-of') where parts CAN exist independently. Can be shared.",
])

q("What does a UML Class Diagram represent? What does a class box contain?", 2, [
    "Static view of a system.",
    "Class box: Name, Attributes (visibility, name, type), Methods (visibility, name, params, return type).",
])

q("List the four visibility/access modifiers in UML.", 2, [
    "+ public (all), - private (class only), # protected (subclasses + package), ~ package (package only).",
])

q("Write the notation for attributes and operations in UML.", 2, [
    "Attributes: [visibility] name [: type] [multiplicity] [= value] [{property}]. Static = underlined.",
    "Operations: [visibility] name ([params]) [: return] [{property}]. Static = underlined.",
])

q("How do you find classes using the Grammatical Parse approach?", 2, [
    "Identify nouns from existing text (requirements, descriptions).",
    "Narrow down: remove duplicates/synonyms, irrelevant, out-of-scope.",
])

q("Define Association and Multiplicity.", 2, [
    "Association: semantic/structural relationship specifying connections among instances of classifiers.",
    "Multiplicity: number of instances one class relates to ONE instance of another. Two decisions per association (one at each end).",
])

q("List all multiplicity notations and meanings.", 3, [
    "1 = exactly one. 0..* or * = zero or more. 1..* = one or more.",
    "0..1 = zero or one (optional). 2..4 = specified range. 2,4..6 = multiple disjoint ranges.",
])

q("Explain Generalization vs Aggregation.", 2, [
    "Generalization: 'is a kind of' — subclass inherits from superclass.",
    "Aggregation: 'part of' — whole-part relationship, one object contains others.",
])

q("What is the difference between Abstract and Concrete classes?", 2, [
    "Abstract: cannot be instantiated (no direct objects). Serve as blueprints.",
    "Concrete: can be instantiated — all actual instances are of concrete classes.",
])

q("Define Navigability in class diagrams.", 1, [
    "Indicates it is possible to navigate from an associating class to the target class using the association.",
])

q("What is the purpose of a Sequence Diagram? List the key elements.", 3, [
    "Models how objects collaborate and interact over time through messages. Good for real-time specs and complex scenarios.",
    "Elements: Participants (actors/objects), Lifeline (vertical dashed line), Time axis (top→bottom), Messages (horizontal arrows), Return messages (dashed arrows). Sync vs async arrowheads.",
])

q("What interaction frames exist in SDs? What can SDs model?", 2, [
    "Frames: alt (branching/conditional), loop (iteration).",
    "SDs model: sequential flow, branching, iteration, recursion, concurrency. Primary/variant/exception scenarios.",
])

q("[MOCK Q6] ATM system design:\n6.1 Class diagram [5]\n6.2 Account: 2 attrs + 2 methods [4]\n6.3 Access modifiers and why [2]\n6.4 Two multiplicity examples [4]\n6.5 Encapsulation, abstraction, inheritance, polymorphism, aggregation/composition [10]", 25, [
    "6.1 Classes: ATM, Customer, Bank, Account, ATM Transactions, Current/Savings Account. Show attrs, methods, relationships, multiplicities.",
    "6.2 Attrs: number, balance. Methods: deposit(), withdraw().",
    "6.3 Attrs: private (-) for encapsulation/security. Methods: public (+) for accessibility, with validation.",
    "6.4 Customer→Account (1 to 1,2); Account→Transactions (1 to *).",
    "6.5 Encapsulation: private balance + public deposit()/withdraw(). Abstraction: Account could be abstract. Inheritance: Current/Savings inherit Account. Polymorphism: withdraw() differs per subclass. Aggregation: Bank contains ATM+Account+Customer.",
], mock="Q6")

# ═══ L5 ═══
ch("l5-project-management", "Project Management")

q("Describe the key practices in Agile Management, organized by three main roles.", 4, [
    "Iterative and incremental delivery via sprint cycles (2-4 weeks).",
    "Product Owner: Epics, User Stories, Backlog Grooming.",
    "Dev Team: CI/CD, Pair Programming, TDD.",
    "Scrum Master: daily stand-ups, sprint planning, reviews, retrospectives. Kanban: limiting WiP, transparency.",
])

q("Why is measurement central to quality? What is 'measurement'?", 3, [
    "Planning time/effort (team + customer), identifying testing focus, evaluating productivity.",
    "Measurement: attributing values to objects → basis for comparison → better decisions.",
])

q("Why is measurement difficult in Software Engineering?", 1, [
    "Most entities are difficult to measure reliably. Difficult to 'pin down' a single value.",
])

q("List the eight top-level quality characteristics in ISO/IEC 25010.", 4, [
    "Functional Suitability, Performance Efficiency, Compatibility, Usability,",
    "Security, Maintainability, Reliability, Portability.",
])

q("Compare Lines of Code (LoC) and Cyclomatic Complexity as white-box metrics.", 4, [
    "LoC: easy to compute, widely used, approximate size. But: ignores logical complexity, language-specific, not all lines equal.",
    "Cyclomatic Complexity: V(G) = E−N+2P. Measures independent paths through code. Better for logical complexity.",
])

q("Explain Story Points and how Planning Poker works.", 4, [
    "Story Points: informal size unit (1-10), derived collectively, 'Wisdom of Crowds'.",
    "Planning Poker: Fibonacci cards (1,3,5,8,13,20...), reveal simultaneously, discuss divergence, max 3 rounds.",
])

q("Define Team Velocity and how it's used.", 2, [
    "Story points completed per sprint, derived from previous sprints (average).",
    "Estimates: time to complete project; target stories per sprint.",
])

q("What do Burn-Down Charts show? How do feedback loops work?", 2, [
    "Plot remaining work (story points) vs time, showing estimated vs actual lines.",
    "After each sprint compare estimate vs actual → discuss in retrospective → continuous improvement.",
])

q("[MOCK Q3] Describe the key characteristics of Sprint Retrospective:\nPurpose, Attendees, Outcome, When It Happens, What Is Discussed.", 10, [
    "Purpose: inspect process, reflect on team performance, identify improvements.",
    "Attendees: dev team + Scrum Master (PO optional).",
    "Outcome: actionable items for improving team processes.",
    "When: end of sprint, after or separate from sprint review.",
    "Discussed: what went well, what didn't, blockers, how to improve collaboration/productivity.",
], mock="Q3")

q("Describe Sprint Review: Purpose, Focus, Attendees, Output, Key Question.", 5, [
    "Purpose: inspect product increment, gather stakeholder feedback.",
    "Focus: the product and deliverables.",
    "Attendees: dev team, PO, SM, stakeholders, customers, users.",
    "Output: feedback on product, potential backlog changes.",
    "Key Q: 'Does the product meet stakeholder expectations?'",
])

q("List all Scrum framework categories: Roles, Ceremonies, Artifacts, Agreements.", 4, [
    "Roles: Product Owner, Scrum Master, Team.",
    "Ceremonies: Sprint Planning, Daily Scrum, Sprint Review, Sprint Retrospective.",
    "Artifacts: Product Backlog, Sprint Backlog, Working Software.",
    "Agreements: Working Agreement, Definition of Ready, Definition of Done.",
])

q("Compare Sprint Review and Sprint Retrospective.", 5, [
    "Review: inspects PRODUCT; all stakeholders attend; output = backlog changes; 'does it meet expectations?'",
    "Retro: inspects PROCESS; dev team + SM only; output = improvement actions; 'how can we work better?'",
])

# ═══ L7 ═══
ch("l7-hci-evaluation-part-one", "HCI Evaluation Part One")

q("What is the Think Aloud evaluation technique?", 2, [
    "Users are asked to verbalise what they are thinking and doing as they perform a task using the software.",
    "Provides insights into user experience; can identify navigation problems or content for improvement; used iteratively or on a finished product.",
])

q("List the benefits and drawbacks of Think Aloud.", 3, [
    "Benefits: cheap, relatively easy, provides insight into user experience, low participant numbers, fits most SDLCs.",
    "Drawbacks: relies on verbalisation (subjective, not objective), social desirability bias — participants may say what they think is the 'right answer'.",
])

q("Describe how to plan and carry out a Think Aloud evaluation.", 4, [
    "Planning: decide research questions, write tasks, decide participant count and session length (15-60 min).",
    "Carrying out: facilitator runs the session, 1-2 observers take notes. Explain there is no right answer. Ask participant to complete tasks uninterrupted. If user goes silent, prompt: 'what are you thinking?'",
    "Analysis: combine observer notes, organise into meaningful categories (features that helped, features with problems, additional features wanted), count frequency to identify biggest issues.",
])

q("What is a heuristic? What is heuristic evaluation?", 2, [
    "Heuristic: a generalisation or rule of thumb; experienced-based strategies for quick decisions (may not be optimal).",
    "Heuristic evaluation: an inspection method conducted WITHOUT users — experts inspect a design to find usability problems against a set of usability principles. Analytical evaluation (based on principles) vs empirical evaluation (observing users).",
])

q("List Nielsen's 10 principles of heuristic evaluation.", 5, [
    "1. Visibility of system status (feedback)",
    "2. Match between system and real world (conventions)",
    "3. User control and freedom (emergency exits, undo/redo)",
    "4. Consistency and standards",
    "5. Error prevention",
    "6. Recognition rather than recall",
    "7. Flexibility and efficiency of use (accelerators, shortcuts)",
    "8. Aesthetic and minimalist design",
    "9. Help users recognise, diagnose and recover from errors",
    "10. Help and documentation",
])

q("Explain 'Visibility of system status' with an example.", 2, [
    "The design must clearly communicate its state. Feedback should be presented quickly after user actions.",
    "Do not show blank screens or static loading messages. Example: password strength indicator shown as password is entered.",
])

q("Explain 'Match between system and real world' with an example.", 2, [
    "System should use familiar terminology. Controls should follow real-world conventions. Information in natural, logical order.",
    "Example: iTunes organised as a Library (music, movies, TV) with a Store underneath — mirrors real-world library concept.",
])

q("Explain 'User control and freedom'.", 1, [
    "Users need 'emergency exits' to leave unwanted states. Support undo/redo and clear navigation. Provide breadcrumbs showing current location.",
])

q("Explain 'Recognition rather than recall'.", 1, [
    "Minimise user's memory load. Make objects, actions, options visible. User should not have to remember info from one part of dialogue to another. Instructions should be visible or easily retrievable.",
])

q("Explain 'Aesthetic and minimalist design'. What four visual design principles apply?", 2, [
    "Dialogues should not contain irrelevant or rarely needed info. Every extra unit of info diminishes relative visibility of relevant info.",
    "Four principles: Contrast, Repetition, Alignment, Proximity (CRAP).",
])

q("How do you run a heuristic evaluation? How many evaluators are needed?", 3, [
    "3-5 evaluators each do independent evaluation. Sometimes a facilitator records comments.",
    "Facilitator can answer evaluators' questions (unlike user testing). Can be done on paper prototypes. Typically lasts 1-2 hours.",
    "Expert goes through interface several times: first for overall feel, second for specific elements. Evaluators produce list of usability problems: which principle was violated and how.",
])

q("List benefits and drawbacks of heuristic evaluation.", 2, [
    "Benefits: cheap, relatively easy, instant gratification (lists available immediately), low participants, fits most SDLCs, very cost effective (benefit-cost ratio 48:1).",
    "Drawbacks: important issues may get missed, might identify false issues, many trivial issues often identified (seems overly critical), experts have biases.",
])

q("What are the key differences between Think Aloud (empirical) and Heuristic Evaluation (inspection)?", 3, [
    "Facilitator role: empirical — observe users and let them struggle; inspection — facilitator answers expert questions.",
    "Participants: empirical needs more users; inspection needs only 3-5 experts.",
    "Data analysis: empirical requires analysing observations after; inspection provides 'instant gratification' with a clear list of issues and heuristics broken.",
])

# ═══ L8 ═══
ch("l8-hci-evaluation-part-two", "HCI Evaluation Part Two")

q("What are questionnaires used for in HCI? List tips for good questionnaires.", 2, [
    "Used to collect demographic data and user opinions. Can evaluate designs and understand user requirements. Can be used at scale with low resources.",
    "Tips: use validated questionnaires (measure what they claim). Avoid leading questions. Keep number feasible (question fatigue).",
])

q("Describe the NASA TLX: purpose, 6 subscales, and scoring.", 5, [
    "Purpose: estimates a user's perceived workload when using a system. Gold standard for measuring subjective workload. Developed by Sandra Hart (NASA).",
    "6 subscales: Mental Demand, Physical Demand, Temporal Demand, Performance, Effort, Frustration. Five scales go Low→High; Performance goes Perfect→Failure.",
    "Scoring: each dimension rated on a line with 21 tick marks (0-100 in steps of 5). Score = (tick number - 1) × 5.",
    "With weights: 15 paired comparisons determine dimension weights (0-5 each, sum=15). Weighted score = sum(rating × weight) / 15. Range 0-100.",
    "Without weights ('raw TLX'): sum of 6 ratings / 6. Simpler to administer, mixed evidence on sensitivity difference.",
])

q("Describe the SUS questionnaire: purpose, structure, scoring, and threshold.", 4, [
    "System Usability Scale: 'quick and dirty' reliable usability measure. Created by John Brooke (1986). 10 items, 5-point Likert scale (Strongly Disagree to Strongly Agree).",
    "Items alternate: odd items are positive (1,3,5,7,9), even items are negative (2,4,6,8,10).",
    "Scoring: odd items = scale position - 1; even items = 5 - scale position. Each item contributes 0-4. Sum × 2.5 = total (range 0-100).",
    "SUS score > 68 = above average usability. < 68 = below average. Individual item scores are not meaningful alone.",
])

q("Explain 'within-subjects' vs 'between-subjects' study design.", 4, [
    "Within-subjects (repeated measures): every participant evaluates BOTH conditions (e.g., both site 1 and site 2).",
    "Between-subjects: one group evaluates condition A, a different group evaluates condition B.",
    "Within-subjects advantages: fewer participants needed; reduces impact of individual differences (participants are their own control).",
    "Within-subjects disadvantage: learning effect (skills gained from one evaluation carry over to next).",
    "Between-subjects advantages: less time per participant; no learning effects.",
    "Between-subjects disadvantage: need more participants (each gives only one data point); participants must be comparable.",
])

q("Which statistical test is used for within-subjects data? Which for between-subjects?", 2, [
    "Within-subjects: Wilcoxon Signed Rank Test. Ideal for Likert/scale data (SUS, NASA TLX). Minimum 5 users.",
    "Between-subjects: Mann-Whitney U Test.",
    "Both: use significance level α = 0.05 (95% certainty that difference is real). Test statistic must be ≤ critical value for significance.",
])

# MOCK Q4
q("[MOCK Q4] NHS chatbot (text vs speech interface):\n4.1a) Describe two evaluation designs and justify. [6]\n4.1b) Instrument for measuring usability. [4]\n4.1c) Statistical test and significance level. [3]\n4.2a) One empirical method with details. [4]\n4.2b) One inspection method with details. [4]\n4.2c) Two key differences between empirical and inspection. [4]", 25, [
    "4.1a) Within-subjects: every user tests both text and speech (controls individual differences). Between-subjects: separate groups for each. Within-subjects preferred — participants vary in speech experience, each acts as own control. Counter learning effects by randomising order.",
    "4.1b) SUS: 10 items, 5 of each type (positive/negative), measured on Likert scales. Score = (sum of contributions) × 2.5. Usability indicated by score > 68.",
    "4.1c) Within-subjects → Wilcoxon Signed Rank Test. Between-subjects → Mann-Whitney U Test. Significance level α = 0.05.",
    "4.2a) Think Aloud: facilitator explains tasks, participants verbalise thoughts, 2 observers record. Data grouped into categories (challenges, likes, suggestions).",
    "4.2b) Heuristic evaluation: facilitator explains tasks, expert evaluates against Nielsen's heuristics, records issues and which heuristic was broken. Data available immediately.",
    "4.2c) Differences: (1) facilitator role — empirical: observe and let struggle; inspection: answer expert questions. (2) participants — empirical needs more users; inspection needs 3-5 experts. (3) data — empirical requires post-analysis; inspection gives instant list.",
], mock="Q4")

# ═══ L9 ═══
ch("l9-software-quality-and-testing", "Software Quality and Testing")

q("List six reasons why software quality is relevant.", 3, [
    "Reputation (poor quality damages business). Cost (poor quality = expensive to develop/maintain, leads to technical debt).",
    "Software certification (e.g., DO-178B/C for aircraft). Organisational certification (e.g., CMM, ISO 9001).",
    "Legality (ALARP — As Low As Reasonably Practicable). Moral/ethical codes of practice (ACM ethical guidelines).",
])

q("Describe the three perspectives of software quality.", 2, [
    "Subjective / 'fitness for use' (Juran): quality perceived by individual user (GUI aesthetics, missing functionality). Focus on vital few objectives.",
    "Objective / 'conformance to requirements' (Crosby): measurable product properties (documentation, bug count, compliance). Achieved by disciplined specification.",
    "Practical: what quality means to your specific team and clients.",
])

q("List the four steps towards software quality.", 2, [
    "Use a standard development process. Use a coding standard (industry compliance, consistent quality, security, reduce costs).",
    "Define and monitor metrics (defect + complexity metrics — high complexity → more defects).",
    "Identify and remove defects: conduct manual reviews, use testing.",
])

q("What are the key elements of the testing process?", 4, [
    "System Under Test (SUT): the system/unit being tested. Can be white-box (access to source code and runtime state) or black-box (only interface/API). May be reactive or deterministic. Must be isolated from live system.",
    "Specification: idealised behaviour (UML, formal spec, or user stories/test cases in agile). A concrete spec enables systematic test generation; without it, testing is ad-hoc.",
    "Test Cases: executions of SUT. Input (or sequence of inputs). Should cumulatively cover every distinctive facet of behaviour. An ideal test set exposes any deviation from spec.",
    "Test Oracle: decides whether output is correct (assertion in code, or human user). Oracle problem: no comprehensive spec, many test cases, complex outputs make manual validation prohibitive.",
])

q("Compare White-Box and Black-Box testing.", 3, [
    "White-box: access to internals (source code, runtime state, execution tracking). Uses code to measure coverage and drive test generation.",
    "Black-box: no access to internals (may have access but don't use it). Only knows interface — parameters, functions/methods, specification document.",
    "White-box measures coverage objectively; black-box tests from user/interface perspective.",
])

q("List five white-box coverage metrics and explain Statement and Branch coverage.", 4, [
    "Statement, Branch, Def-Use/Dataflow, MC/DC, Mutation coverage.",
    "Statement coverage = (statements executed / total statements). If a faulty statement is always buggy when executed, it will be detected.",
    "Branch coverage = (branches executed / total branches). Subsumes statement coverage — every branch (true/false) must be executed.",
    "DO-178B/C: non-critical → statement coverage; safety-critical → MC/DC coverage.",
])

q("Describe the Equivalence Partitioning (EP) method for black-box testing.", 4, [
    "1. Decompose program into functional units (smaller = more rigorous tests, easier debugging).",
    "2. Identify inputs and outputs for each unit.",
    "3a. Identify categories: classify inputs into valid and invalid.",
    "3b. Define partitions: value ranges/characteristics per category (e.g., 0≤exam≤75 valid, >75 invalid, alphabetic invalid).",
    "3c. Identify constraints between categories (not all can combine).",
    "3d. Write test specifications: pair each equivalence class with test inputs and expected outputs.",
])

q("Explain Boundary Value testing.", 2, [
    "Errors most frequently occur at edge cases.",
    "Test: just below boundary, at the boundary, just above the boundary.",
])

q("What is JUnit? List four types of assertions.", 2, [
    "JUnit: Java testing framework using assertions to verify code. Reports failures when assertions don't hold.",
    "assertEquals(expected, actual), assertTrue(condition), assertFalse(condition), assertThat(value, matchingFunction).",
])

# ═══ L10 ═══
ch("l10-sustainability", "Software Engineering for Sustainability")

q("Explain four negative effects of ICT on sustainability: induction, obsolescence, rebound effects, risks.", 4, [
    "Induction: ICT creates new demand for resources (e.g., cloud computing → more storage use).",
    "Obsolescence: designing products for new sales, not supporting existing products (e.g., new iPhone models make older ones undesirable/unsupported).",
    "Rebound effects: efficiency improvements lead to increased overall consumption instead of net savings (e.g., route planning apps make car travel more attractive → increase traffic).",
    "Risks: unexpected sustainability challenges (e.g., 5G → increased demand for rare earth elements; AI → 'baked in' biases and unemployment).",
])

q("What three things can software do for sustainability?", 3, [
    "Optimisation: reduce waste via sensors and smart planning (e.g., plant watering based on humidity, satnav route optimisation).",
    "Substitution: replace physical with digital (e.g., in-person → video conferencing, CD → music streaming).",
    "Behaviour change: transition to sustainable production and consumption patterns (e.g., use renewables during peak generation, feedback on environmental impact when shopping, take-back functions).",
])

q("What is SusAF (Sustainability Awareness Framework)?", 2, [
    "A question-based framework for building awareness of potential sustainability effects of a software solution.",
    "Aims to enable discussion to make sustainability-conducive requirements decisions.",
])

q("List the five dimensions of sustainability and give two topics per dimension.", 5, [
    "Social: Sense of Community, Trust, Inclusiveness and Diversity, Equality, Participation and Communication.",
    "Individual: Health, Lifelong Learning, Privacy, Safety, Agency.",
    "Environmental: Material and Resources, Energy, Biodiversity and Land Use, Soil/Atmospheric/Water Pollution, Logistics and Transportation.",
    "Economic: Value, Customer Relationship Management, Supply Chain, Governance and Processes, Innovation and R&D.",
    "Technical: Maintainability, Usability, Extensibility and Adaptability, Security, Scalability.",
])

q("How does sustainability awareness impact Agile practices? Give four examples.", 4, [
    "Lack of stakeholder demand → SusAF shows win-win options (increase sustainability + reduce costs).",
    "Sustainability not in product backlog → SusAF formulates sustainability-focused requirements to integrate.",
    "Sustainability criteria missing in testing/CI → once in backlog, testing/acceptance criteria follow.",
    "Lack of retrospective focus → formal sustainability requirement ensures discussion in retrospectives.",
])

q("Describe the sustainability cloud process (AWS shared responsibility model).", 2, [
    "AWS responsible for sustainability OF the cloud (infrastructure, data centers, electricity, cooling).",
    "Customer responsible for sustainability IN the cloud (data design, software design, code efficiency, platform deployment, scaling).",
    "Process: identify targets → evaluate options → prioritise and plan → test and validate → deploy → measure results and replicate.",
])

# ═══ L11 ═══
ch("l11-privacy-by-design", "Privacy by Design")

q("List the 8 principles of Data Protection (GDPR).", 4, [
    "1. Fairly and lawfully processed (consent, contractual/legal obligations, public interest).",
    "2. Processed for limited purposes.",
    "3. Adequate, relevant, and not excessive.",
    "4. Accurate and kept up to date.",
    "5. Not kept longer than necessary.",
    "6. Processed in accordance with the data subject's rights.",
    "7. Secure.",
    "8. Not transferred to countries without adequate protection.",
])

q("List the 7 principles of Privacy by Design.", 4, [
    "1. Preventive not remedial: anticipate and prevent privacy risks before they happen.",
    "2. Privacy as the default setting: personal data automatically protected.",
    "3. Privacy embedded into design: engineered from the start, not added later.",
    "4. Full functionality: no trade-off between privacy and other interests (e.g., innovation).",
    "5. End-to-end protection: data protected at every stage (collection, use, storage, deletion).",
    "6. Visibility and transparency: operations remain open and accountable.",
    "7. Respect for user privacy: user interests as core focus, strong defaults, clear notices, user-friendly options.",
])

q("Why should we practice Privacy by Design? List three reasons.", 2, [
    "1. Reduce risk of data breaches.",
    "2. Build trust with users.",
    "3. Align with GDPR/similar regulation compliance.",
])

q("Describe Privacy by Design Technique 1: Use of Personas.", 3, [
    "Users can browse using pre-defined representative personas to explore outcomes without providing real personal data.",
    "Data is only collected when the user actively decides to proceed for a specific purpose.",
    "Operationalises the GDPR rule: 'do not collect any data unless there is a clearly defined goal/purpose for it.'",
    "Reduces conflicts around data sharing — users see data collected for specific purposes and accept it.",
])

q("Describe Privacy by Design Technique 2: Inform and Give Choice.", 2, [
    "Before data collection, clearly present: what data is needed, why, and the benefit to the user.",
    "User chooses whether to share. Only relevant data for their chosen option is collected.",
    "Enforces GDPR: 'process data only for limited purposes', collected data is 'adequate, relevant, and not excessive'.",
])

q("List and explain Hoepman's 8 Privacy Design Strategies.", 4, [
    "Minimise: collect only data needed for processing.",
    "Hide: collected/processed data should not be in plain sight.",
    "Separate: distribute or isolate data during storage/processing.",
    "Aggregate: store/process personal data at the highest possible aggregation level.",
    "Inform: notify data subjects whenever personal data is processed.",
    "Control: data subjects should control collection, storage, and processing.",
    "Enforce: implement and enforce privacy policies compatible with legal requirements.",
    "Demonstrate: data controller should be ready to demonstrate compliance.",
])

q("What is GDPR and what motivates Privacy-focused Software Development?", 2, [
    "GDPR: General Data Protection Regulation — regulates how organisations collect, store, and process personal data.",
    "Motivation: privacy concerns in software adoption, data-hungry business models not accounting for human needs. The false 'privacy-utility trade-off' claim (less data = less utility) is challenged.",
])

# ═══ Output ═══
total_q = sum(len(c["questions"]) for c in chapters)
total_m = sum(q["marks"] for c in chapters for q in c["questions"])

out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
    "..", "courses", "software-engineering", "review", "concepts.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump({"chapters": chapters, "total_questions": total_q, "total_marks": total_m}, f, ensure_ascii=False, indent=2)
print(f"{total_q} questions, {total_m} marks → {out}")
