# L11. Privacy by Design

## Data Protection

8 Principles of Data Protection:

Any company storing "personal data" must make sure it is:

- fairly and lawfully processed (consent, contractual and legal obligations, public interest, ...) 公平合法处理（同意、合同和法律义务、公共利益等）
- processed for limited purposes;
- adequate, relevant and not excessive;
- accurate and, where necessary, kept up to date;
- not kept longer than necessary;

- processed in accordance with the data subject's rights;
- secure;
- not transferred to countries without adequate protection

## Privacy by Design: Principles

1. Preventive not remedial: anticipate and prevent privacy risks before they happen. 预防性而非补救性
2. Privacy as the default setting: Personal data is automatically protected. Users do not have to do anything extra.
3. Privacy embedded into design: Engineered form the start, not added on later.
4. Full functionality: No trade-off in privacy vs other interests like innovation. 在隐私与创新等其他利益之间没有权衡。
5. End-to-end protection: Data is protected at every stage: collection, use, storage, and deletion. 端到端保护
6. Visibility and transparency: Operations remain open and accountable（负责任）.
7. Respect for user privacy: Keep user interests as core focus, provide use strong default settings, clear notices, and user-friendly options.

## Why Practice Privacy by Design ?

1. Reduce risk of data breaches（泄露）
2. Build trust with users
3. Align with GDPR/similar regulation compliance 与GDPR或类似法规合规保持一致

## Privacy – Focused Software Development

A software design approach that engages with the user’s needs and expectations early on, considers their concerns, and articulates the need for sensitive data collection during the software’s use. 一种软件设计方法，能够在早期就关注用户的需求和期望，考虑他们的关切，并在软件使用过程中明确表达敏感数据收集的需求。

## Motivation

- Privacy concerns in adopting software solutions.

- Business models – data hungry, not accounting for（考虑） human needs
- The General Data Protection Regulation (GDPR)
- No real Privacy-utility trade-off（隐私与实用权衡）:
  - Claim: the less personal data is collected by a software application the less utility users receive from that software.

## Collect data only if ACTUALLY using the system for the specific purpose

## Give information on the work and finance without data collection?××

- Technique 1: Use of Personas
  - Trial the “user journey” of the persona.
  - See the purpose for which data is shared and accept to share own data
  - Operationalize（落实） the GDPR rule stating “do not collect any data unless there is a clearly defined goal/purpose for it.”
  - Persona-based development technique does not only elicit（引导） and inform software designers/engineers about what privacy concerns various user groups want to adhere to（遵守）, but to also enable users to “walk in the persona’s shoes”:
    - Persona-style users have an opportunity to trial the “user journey” of the persona similar to themselves.
    - Reduces the conflicts around personal data sharing as the purpose for which it is shared is accepted as necessary by the user.
    - Operationalizes the GDPR rule stating “do not collect any data unless there is a clearly defined goal/purpose for it”: user sees the data collected and processed for a specific purpose, the developer is free of the additional burden of explaining data collection and processing needs when such a user proceeds to adopt the given software for their fully personalized use. 落实 GDPR规则：“除非有明确的目标/目的，否则不要收集任何数据”：用户看到为特定目的收集和处理的数据，开发者无需额外解释数据收集和处理需求，当用户采用该软件进行完全个性化使用时。
- Technique 2: Inform on Data Needed and Benefits

Get only data for the finance and grant (资助) options that are ASKED FOR by the user

## On Techniques: Inform and Give Choice

- Check out what option are available.
- Consider implications (影响) of data sharing per option.
- Choose what is best for you as a user.
- Enforces the GDPR rules stating “process data only for limited purposes”; collected data is “adequate, relevant and not excessive” and is processed per data subjects “... rights”

## Hoepman’s Privacy Design Strategies

| Minimize | personal data processing should be minimal, and collection should only focus on the data that is needed for processing. |
| --- | --- |
| Hide | collected and processed data should not be in plain sight. |
| Separate | data should be distributed or isolated, whether during storage or processing stage. |
| Aggregate | personal data should be stored or processed at the highest possible aggregation level. |
| Inform | data subject should be informed timely whenever personal data is processed. |
| Control | data subjects should be in control over data collection, storage and processing. |
| Enforce | contractual and legal policies (i.e., privacy policy) that is compatible with legal requirements should in place and enforced. |
| Demonstrate | data controller should be ready to demonstrate compliance. |

## Review (AI回答)

### What is GDPR for?

The General Data Protection Regulation (GDPR) exists to regulate how organisations collect, store, and process personal data. It operationalises a set of 8 core data protection principles, requiring that any company storing personal data ensures it is:

1. Fairly and lawfully processed — with proper consent or legal basis
2. Processed for limited purposes — only used for clearly defined goals
3. Adequate, relevant and not excessive — no unnecessary data collected
4. Accurate and kept up to date
5. Not kept longer than necessary
6. Processed in accordance with the data subject's rights
7. Secure
8. Not transferred to countries without adequate protection

In the context of software development, GDPR motivates Privacy by Design because it directly challenges data-hungry business models and requires developers to justify why each piece of personal data is collected. It also addresses the false assumption that less data collection necessarily means less utility for the user.

## What is the key focus of Privacy by Design?

Privacy by Design (PbD) is defined as the proactive engineering of privacy protection into the design and operation of software, systems, and business practices — right from the start, rather than adding privacy as an afterthought.

Its seven foundational principles are:

| PRINCIPLE | MEANING |
| --- | --- |
| Preventive, not remedial | Anticipate and prevent privacy risks before they occur |
| Privacy as the default | Personal data is automatically protected — users need not take extra action |
| Privacy embedded into design | Engineered from the start, not bolted on later |
| Full functionality | No trade-off between privacy and other values like innovation |
| End-to-end protection | Data protected at every stage: collection, use, storage, and deletion |
| Visibility and transparency | Operations remain open and accountable |
| Respect for user privacy | User interests are the core focus, with strong defaults and clear notices |

The overarching reason to practise PbD is to reduce the risk of data breaches, build trust with users, and align with GDPR compliance.

## Which techniques of practising PbD do you recall?

The slides present two core techniques and one broader strategic framework:

### Technique 1 — Use of Personas

Rather than collecting real user data upfront, the system allows users to browse using pre-defined representative personas to explore outcomes (e.g., what home improvements would cost for someone in a similar situation). Real personal data is only collected if the user actively decides to proceed for a specific purpose. This operationalises the GDPR rule: "do not collect any data unless there is a clearly defined goal."

### Technique 2 — Inform on Data Needed and Give Choice

Before any data is collected, the system clearly presents: what data is required, why it is needed, and what the benefit to the user will be. The user then chooses whether to share their data, and only the data relevant to their chosen option is collected. This enforces the GDPR principles of limited purpose and data minimisation, and respects the data subject's rights.

## Hoepman's 8 Privacy Design Strategies (a broader framework):

| STRATEGY | DESCRIPTION |
| --- | --- |
| Minimise | Collect only what is strictly needed |
| Hide | Collected data should not be in plain sight |
| Separate | Distribute or isolate data during storage and processing |
| Aggregate | Store/process data at the highest possible aggregation level |
| Inform | Notify data subjects whenever their data is processed |
| Control | Give data subjects control over their data |
| Enforce | Implement and enforce legally compatible privacy policies |
| Demonstrate | Be ready to demonstrate compliance to regulators |

## Can you give an example of PbD for a running app context?

Consider a running/fitness tracking app that monitors routes, pace, and location. Here is how PbD principles and techniques would apply:

### Minimise & Default Privacy

By default, the app does not share routes or location history with third parties. GPS tracking is only active during a run, not in the background.

Use of Personas (Technique 1) — A new user can explore features (e.g., "see what a 5K training plan looks like") by browsing a sample persona's data, without creating an account or providing any personal data upfront.

Inform and Give Choice (Technique 2) — Before enabling social sharing features (e.g., sharing run maps with friends), the app clearly explains: "This will share your GPS route and timestamps. This data will be stored for 30 days." The user then explicitly opts in — and only that specific data is collected.

Aggregate — Instead of storing precise GPS coordinates for every second, the app stores aggregated summaries (total distance, average pace, general area), reducing personal data exposure.

End-to-end Protection — Route data is encrypted both during transmission and at rest, and is automatically deleted after a user-defined retention period.

This example demonstrates that PbD does not reduce the utility of the app — users still get personalised training plans and progress tracking — but privacy is built in from the ground up rather than treated as an afterthought.
