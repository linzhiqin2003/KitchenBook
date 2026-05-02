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

# ═══ Output ═══
total_q = sum(len(c["questions"]) for c in chapters)
total_m = sum(q["marks"] for c in chapters for q in c["questions"])

out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
    "..", "courses", "software-engineering", "review", "concepts.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump({"chapters": chapters, "total_questions": total_q, "total_marks": total_m}, f, ensure_ascii=False, indent=2)
print(f"{total_q} questions, {total_m} marks → {out}")
