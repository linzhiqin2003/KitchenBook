# L10. Software Engineering for Sustainability

## Induction, Obsolescence, Rebound Effects, Risks 诱导、过时、反弹效应与风险

- Induction effect: ICT（信息通信领域技术） creates new demand for resources
  - E.g., cloud computing leads to more storage use.
- Obsolescence: designing products for new sales（新型号） driving the technological innovation and not supporting existing products
  - iPhones release new models, making older ones ‘undesirables’, or not supported for new software.
- Rebound Effects: efficiency improvements through ICT lead to increased overall

consumption instead of net savings.

- Route planning apps aim to reduce traffic flows, but end up making car travel more attractive and increase traffic instead.
- Risks – unexpected sustainability challenges from ICT development
  - 5G telecoms reading to increased demand on rare earth elements (稀土) and waste; AI use leading to ‘baked in’ (根深蒂固的) biases and unemployed in some jobs...

## ICT as Enabler for Sustainable Society

### What can Software do for Sustainability?

- Optimisation
  - E.g. plant watering based on humidity sensor – reduce water waste; from maps to satnav – optimise root planning/travel time...
- Substitution (替代)
  - E.g., in-person to video conferencing; CD to music streaming...
- Behaviour Change: transition to sustainable patterns of Production and Consumption
  - E.g.: Production – start energy use activities when renewables are generating, like mid-day in sunny climates
  - Consumption – feedback on environmental impact of product choice when shopping; reuse/take back functions on e-shops...

### Software requirements – key to sustainability

“Requirement: necessary (or desired) function, attribute, capability, characteristic, or quality of a system for it to have value and utility (效用) to a customer or other stakeholder”

## SuSAF: Sustainably Awareness Framework

A question-based framework for building awareness of potential sustainability effects of a software solution which aims to enable discussion so as to make sustainability-conducive requirements decisions

基于问题的框架，旨在提升对软件解决方案潜在可持续影响的认知，旨在促进讨论，从而做出有利于可持续发展的需求决策

## Dimensions of Sustainability
- Individual
- Social
- Technical
- Economic
- Environmental、

## What can Software do for Sustainability?
- Optimisation
- Substitution
- Behaviour Change: transition to sustainable patterns of Production and Consumption

## Tool: Sustainability Awareness Framework

Sustainability Dimensions and Topics: Social, Environmental, Economic, Technical, Individual

Guiding Questions: For each sustainability dimension, questions in plain text, examples, reminders and checkboxes.

5 Topics Coved by Questions

SusAF Sustainability Awareness Framework

Discussion Notes
Summary of Discussion Notes: Identifying chain-of-effects Reflection on impact of widespread and long-term use.

Sustainability Awareness Diagram (SusAD): Visualisation tool, breaks down graph into the five interrelated dimensions of sustainability.

## Sustainability Dimensions and Topics

## Sustainability Awareness Diagram

## CATEGORY TOPICS
Social (1) Sense of Community; (2) Trust; (3) Inclusiveness and Diversity; (4) Equality; (5) Participation and Communication;
Individual (1) Health; (2) Lifelong learning; (3) Privacy; (4) Safety; (5) Agency;
Environmental (1) Material and Resources; (2) Soil, Atmospheric and Water Pollution; (3) Energy; (4) Biodiversity and Land Use; (5) Logistics and Transportation;
Economic (1) Value; (2) Customer Relationship Management (CRM); (3) Supply chain; (4) Governance and Processes; (5) Innovation and R&D;
Technical (1) Maintainability; (2) Usability; (3) Extensibility and Adaptability; (4) Security; (5) Scalability;

## Sustainability Awareness Diagram

Figure 1. Simplified SusAD diagram for AirBnB system

## Sustainability Awareness Framework (SusAF)

- Individual: Health, lifelong learning, ...
- Social: Sense of community, trust (信任), inclusiveness (包容性), ...
  - Trust: "Can the system change the trust between users and the business that owns the system."
  - Inclusiveness and diversity: "Does the system include users with different background, age groups, education levels, etc."
- Environment: Material & resources, energy, ...
- Economic: Value, CRM, supply chain, ...
- Technical: Maintainability, usability, security, ...

## Summary of discussion in notes

| TOPIC               | KEY POINTS - SOCIAL DIMENSION                             |
|---------------------|-----------------------------------------------------------|
| SENSE OF COMMUNITY  | rent rooms → personal contact → start friendship → better sense of community |
|                     | rating system → welcome and helpful                       |
|                     | high use → change house dynamics → children affected      |
|                     | high use → door codes → less personal contact             |
|                     | structural changes to properties                           |
|                     | high use → long-term renters forced out                   |

## Sustainability Requirements - > User Stories

### Rating for Contractor selection:

1. As a **householder**, I want to select contractors rated on basis of their **distance** from my home, so that those working on my home are local tradespeople.
2. ... **types of materials** they use when retrofitting properties, so that I can choose the workmen that use materials suited to my home and health.
3. ...**discounts** they provide for the work, so that I can select the best offered price.
4. As a newly starting **contractor**, I want to be able to provide **discounts** on martials I use ...

## User Privacy:

1. As a householder-app-user I want to keep my financial, personal, and home details private so that no 3rd party app has no access to my bank account details.

2. As a householder-app-user I want to choose which specific government grant eligibility is checked for me, so that I maintain data on topics of my choice private. (E.g., do not check health-based eligibility as I do not want to disclose it).

3. xxxxxx

## What about Product Backlog?

| BACKLOG ITEM               | TESTING METRICS                                                                 |
|----------------------------|---------------------------------------------------------------------------------|
| User Authentication (Login/Sign-up) | - Success Rate: Percentage of successful login/sign-up attempts without errors. Target: > 95%.<br>- Security: Ensure passwords are encrypted, and user data is handled securely (e.g., SSL).<br>- Load Time: Time taken to load the authentication page. Target: < 2 seconds.<br>- Error Handling: Verify that invalid login attempts (e.g., wrong password) provide clear error messages. |
| Product Detail Page        | - Accuracy: Ensure correct product data (description, price, images) is displayed.<br>- Image Load Time: Time taken for product images to fully load. Target: < 1 second per image.<br>- Responsiveness: Test the page across different devices and screen sizes. |
| Environmental Impact of the App | - Energy Efficiency: Measure energy consumption during dashboard use. Target: < 10% CPU usage.<br>- Eco-Friendly Property Listings: number of eco-friendly properties listed. |

## What about Sprints? Add Metrics for all features!

## Sustainability Awareness Impacts Software Architecture

## Takeaways and discussion:

- SusAF as a Systems Thinking activity: Potentially high cost vs. few guiding questions
- Systems vs Software Requirements Engineering: Need to look at wider socio-economic system
- Requirements Engineers as leads for Sustainability Engineering: timely consideration helps fostering informed choices

| BACKLOG ITEM | TESTING METRICS |
| --- | --- |
| User Authentication (Login/Sign-up) | - Success Rate: Percentage of successful login/sign-up attempts without errors. Target: > 95%.<br>- Security: Ensure passwords are encrypted, and user data is handled securely (e.g., SSL).<br>- Load Time: Time taken to load the authentication page. Target: < 2 seconds.<br>- Error Handling: Verify that invalid login attempts (e.g., wrong password) provide clear error messages.<br>- Data Privacy: Ensuring that user data is not misused or leaked. GDPR Compliance: Ensure personal data handling is compliant==<br>- Energy Efficiency: Authentication should not require more that 10% average CPU usage. |
| Product Detail Page | - Accuracy: Ensure correct product data (description, price, images) is displayed.<br>- Image Load Time: Time taken for product images to fully load. Target: < 1 second per image.<br>- Responsiveness: Test the page across different devices and screen sizes.<br>- Accessibility: Ensure the page is accessible to users with disabilities (e.g., vision impairments) - compliance with WCAG standards==<br>- Energy Consumption: Optimizing image sizes to reduce load time and energy use. Measure file size reductions using image compression techniques. Target: > 30% reduction. |

Software Architecture: “fundamental organisation of software system embodied in its components, their relationships to each other and to the environment, and the principles guiding its design and evolution.”

## Issues that Impact Architectural Decisions

Nonfunctional product characteristics

Software compatibility

Architectural influences

Product lifetime

Number of users

Software reuse

## Sustainability of and in AWS

Customer is responsible for sustainability in the cloud

AWS is responsible for sustainability of the cloud

"...you can build architectures that maximize efficiency and reduce waste"

Data Design & Usage

Software Application Design

Platform Deployments and Scaling

Data Storage

Code Efficiency

Utilization & Scaling

Servers

Cooling

Water

Waste

AWS Global Infrastructure

Data Centers

Electricity Supply

Building Materials

## Sustainability in the Cloud: Process

Identify target improvements

Evaluate specific options

Prioritise and plan improvements

Test and validate an improvement

Deploy changes to production

Measure results and replicate success

## Takeaways and discussion:

- Sustainability is a crosscutting concern: affects all layers and other concerns
- Sustainability drives architecturally significant decisions
- Software Engineers have to consider Sustainability at all development stages and across the stack
