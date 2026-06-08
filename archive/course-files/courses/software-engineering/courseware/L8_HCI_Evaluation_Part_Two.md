# L8. HCI Evaluation Part Two

## Questionnaires - defined
- Questionnaires involve asking people to answer questions either on paper or digitally e.g. on a webpage or app
- They can be used at scale with low resource requirements
- They generate a collection of demographic data and user opinions 他们生成一组人口统计数据和用户意见
- They can be used to evaluate designs and for understanding user requirements

## Questionnaires - tips
- It is difficult to produce your own questionnaires
- If you do, then ensure that you are asking a feasible（切实可行的） number of questions (question fatigue（疲劳） is a thing)
- Watch out for leading questions e.g. “Why did you have difficulty with the navigation on our app?”
- It is best to use existing questionnaires that have been validated i.e. they measure what they claim to be measuring
- I’ll now introduce you to two widely used questionnaires, starting with the NASA TLX

## NASA TLX
- The NASA Task Load Index (TLX) is a questionnaire that estimates a user’s perceived workload（感知的工作量） when using a system.
- Workload is a complex construct but essentially means the amount of effort people have to exert（付出）, both mentally and physically, to use a system.
- It was developed by Sandra Hart of NASA’s human performance group and Lowell Staveland of San Jose University.
- The focus is on measuring the “immediate often unverbalized impressions that occur spontaneously”（重点是测量“自发产生的即时且常常未被言说的印象”） (Hart and Staveland, 1988). These are difficult or impossible to observe objectively.
- Originally the NASA TLX questionnaire was developed for use in aviation but it’s

since been used in many different domains, including air traffic control, robotics, the automotive industry, healthcare, website design and other technology fields.

- Since it was introduced in 1988, it has had over 8000 citations.
- It is viewed as the gold standard for measuring subjective workload.
- Originally it was developed as a paper and pencil questionnaire but there are also free apps for iOS and Android
- The NASA TLX uses a multi-dimensional rating procedure that derives an overall workload score based on a weighted average of ratings on six subscales（采用多维评级程序，基于六个子量表的加权平均来推导整体工作负荷得分）: 
  - Mental Demand 精神需求
    - how much mental and perceptual（感知的） activity was required?
  - Physical Demand
    - how much physical activity was required?
  - Temporal Demand
    - how much time pressure did the user feel due to the rate at which tasks occurred（由于任务发生的速度）?
  - Performance 性能
    - how successfully did the user think they accomplished the task?
  - Effort
    - how hard did the user have to work (mentally and physically) to accomplish their level of performance?
  - Frustration 挫败感
    - how insecure, discouraged or irritated did the user feel in the task? 感到多么不安全、沮丧或恼火?

Note that five of the scales go from 'Very Low' to 'Very High'

Only the Performance scale goes from 'Perfect' to 'Failure'

| Mental Demand | How mentally demanding was the task? | Performance | How successful were you in accomplishing what you were asked to do? |
| --- | --- | --- | --- |
| Very Low |  | Perfect | Failure |
| Physical Demand | How physically demanding was the task? | Effort | How hard did you have to work to accomplish your level of performance? |
| Very Low |  | Very Low | Very High |
| Temporal Demand | How hurried or rushed was the pace of the task? | Frustration | How insecure, discouraged, irritated, stressed, and annoyed were you? |
| Very Low |  | Very Low | Very High |

NASA TLX Scoring 1

- Users answer the NASA TLX after they have completed a task. This is necessary as asking them to complete it during a task is typically not possible. However, it may mean that users forget details of the perceived workload.
- The questionnaire is scored in a two step process:
  - a. Identifying the relative importance of the 6 dimensions on a user's perceived workload
  - b. Rating each of the 6 dimensions on a scale (量表)

NASA TLX Relative weighting of dimensions 1

- A user reflects (反思) on the task they've been asked to perform and is shown each paired combination of the six dimensions to decide which is more related to their personal definition of workload as related to the task. 用户会反思自己被要求执行的任务，并展示六个维度的每一个配对组合，以决定哪个更符合他们对工作量的定义。
- This means a user considers 15 paired comparisons. For example, they need to decide whether Performance or Frustration "represents the more important contributor to the workload for the specific task you recently performed." 这意味着用户需要考虑15个配对比较。例如，他们需要决定绩效还是挫败感“代表你最近完成的具体任务中工作量中更重要的贡献”。
- Each time a dimension is selected as more important it receives a score of 1. The total score is the weight of the dimension and ranges from 0 to 5. 每当某个维度被选为更重要时，该维度得分为1。总分是维度权重，范围为0到5。
- The sum of the weights should be 15.

NASA TLX Relative weighting of dimensions 2

- The relative weighting of the six dimensions is often not measured or used.
- Not measuring the relative weighting makes the NASA TLX simpler to administer. 不测量相对权重使NASA TLX的管理更为简单。
- Several studies have compared raw TLX scores to weighted TLX scores and have found mixed results (some showing better sensitivity when removing weights, others showing no difference, and others showing less sensitivity).
- When the dimensions are not rated the method is called the ‘raw TLX score’×

## NASA TLX Rating the dimensions 1

- Users mark their score on each of the six dimensions.
- Each dimension consists of a line with 21 equally spaced tick marks, which divide the line from 0 to 100 in increments of 5. If a user marks between two ticks then the value of the right tick is used. 每个维度由一条带有21个等距刻度标记的线组成，这些刻度以5为单位将0到100的行分。如果用户在两个勾之间做标记，则使用右勾的值。
- The score on a dimension is calculated as the tick number (1, 21) – 1 multiplied by 5. 维度得分计算为刻数（1，21）– 1乘以5。

## NASA TLX Rating the dimensions 2

- For example, the images show the rating on a paper questionnaire (top) and on a mobile app (bottom)
- The fifth tick mark is selected, so the rating score is: $(5 - 1) * 5 = 20$

LOW
HIGH
Low
High

## NASA TLX What do the scores tell us?

- If the weights are used then the individual ratings on each of the dimensions are multiplied by their respective weights, summed and divided by 15, resulting in an aggregate perceived workload score for a task ranging from 0 – 100. 如果使用权重，则将每个维度的评分乘以各自的权重，再加总后除以15，得到任务的总感知工作量得分范围为0至100。
- If the weights are not used then the individual ratings on each of the six dimensions can be summed and divided by 6, resulting in an aggregate perceived workload score ranging from 0 – 100. 如果不使用权重，则可以将六个维度的各个评分相加并除以6，得到0至100的综合工作量感知得分。
- The individual ratings on the 6 dimensions also give some insight in to where the workload is coming from. This can be helpful for developers hoping to improve their design. 六维度上的个人评分也反映了工作量的来源。这对希望改进设计的开发者非常有帮助。

## NASA TLX Validity 有效性

- Hart and Staveland validated that the sub-scales measure different sources of workload. 验证了子量表衡量不同工作量源。
- Subsequent independent studies have also found that the NASA TLX is a valid measure of subjective workload (Rubio et al, 2004; Xiao et al, 2005).

## System Usability Survey (SUS) 系统可用性调查 (SUS)

- The System Usability Scale (SUS) provides a ‘quick and dirty’, reliable tool for measuring usability.
- It was created by John Brooke in 1986.
- It consists of a 10 item questionnaire with five response options for each item ranging from Strongly agree to Strongly disagree.
- It enables the evaluation of a wide variety of products and services, including hardware, software, mobile devices, websites and applications.

## System Usability Survey (SUS) - benefits

- SUS has become an industry standard, with references in over 1300 articles and publications.
- The noted（显著的）benefits of using SUS include:
  - It is a very easy questionnaire to administer to participants
  - It can be used on small sample sizes with reliable results
  - The SUS has been validated and shown to effectively differentiate between usable and unusable systems 区分可用和不可用系统

## System Usability Survey (SUS) - scale

- To use the SUS, participants are asked to score each of the 10 items with one of five responses that range from Strongly Agree to Strongly disagree i.e. using a five point Likert scale 使用五分李克特量表

## System Usability Survey (SUS) – scoring

- The SUS is given to users when they have completed using the system which is being evaluated
- They score each of the 10 items by marking one of the five boxes
- The SUS yields a single number representing a composite measure of the overall usability of the system being studied. SUS给出一个单一数字，代表所研究系统整体可用性的综合衡量。
- Note that scores for individual items are not meaningful on their own. 单个项目的分数本身并不具有意义。

1. I think that I would like to use this system frequently

2. I found the system unnecessarily complex

3. I thought the system was easy to use

4. I think that I would need the support of a technical person to be able to use this system

5. I found the various functions in this system were well integrated

6. I thought there was too much inconsistency in this system

7. I would imagine that most people would learn to use this system very quickly

8. I found the system very cumbersome to use

9. I felt very confident using the system

10. I needed to learn a lot of things before I could get going with this system

| Strongly disagree | Strongly agree |
|-------------------|----------------|
| 1                 | 2              | 3              | 4              | 5              |
|                   |                |                |                |                |
| 1                 | 2              | 3              | 4              | 5              |
|                   |                |                |                |                |
| 1                 | 2              | 3              | 4              | 5              |
|                   |                |                |                |                |
| 1                 | 2              | 3              | 4              | 5              |
|                   |                |                |                |                |
| 1                 | 2              | 3              | 4              | 5              |
|                   |                |                |                |                |
| 1                 | 2              | 3              | 4              | 5              |
|                   |                |                |                |                |
| 1                 | 2              | 3              | 4              | 5              |
|                   |                |                |                |                |
| 1                 | 2              | 3              | 4              | 5              |
|                   |                |                |

- To calculate the SUS score, first sum the score contributions from each item. Each item's score contribution will range from 0 to 4. 计算SUS分数时，首先将每项的分数贡献相加。每个项目的得分贡献范围为0到4。
- For items 1,3,5,7,and 9 (the odd numbered items) the score contribution is the scale position minus 1. For items 2,4,6,8 and 10 (the even numbered items) the contribution is 5 minus the scale position. 对于第1、3、5、7和9题（奇数题目），得分贡献为量表位置减去1。对于第2、4、6、8和10题（偶数题目），贡献为5减去量表位置。
- Multiply the sum of the scores by 2.5 to obtain the overall score. 将分数之和乘以2.5得到总分。
- SUS scores have a range of 0 to 100. SUS分数范围为0到100。
- Based on research, a SUS score above 68 would be considered above average and an SUS score below 68 is below average. 根据研究，SUS分数高于68被视为高于平均水平，低于68则低于平均水平。

## Statistical testing

- You might get a user to rate the SUS of two different designs and want to know if one design is significantly better than the other.
- Similarly, you might want to know if two levels of difficulty in your game are significantly different, so you get a user to rate the workload of both levels.
- To determine whether the differences in scores are significantly different we can use a statistical test
- There are many statistical tests but I am going to show you two that will be useful for your project.
- The first is the Wilcoxon Signed Rank Test and it is ideal for analysing data from Likert and other scales e.g. the NASA TLX and SUS.
- It is used when one user carries out two evaluations e.g. rates the workload of your game at two different difficulty levels. This is known as a 'within subjects' or 'repeated measures' study design. 当一名用户进行两次评估时，例如对游戏的工作量在两个不同难度级别进行评级。这被称为“受试者内”或“重复测量”研究设计。
- It is a good test when you have small numbers of users – the minimum is 5; however, it’s better at identifying significant differences when you have larger numbers of users.
- Make a table where each row represents a user’s scores and each column a separate evaluation score. 做一个表格，每行代表用户的分数，每列代表独立的评估分数。
- I’ve shown the results of three users evaluating the workload of a game at two

difficulty levels using the NASA TLX. 我展示了三位用户使用NASA TLX在两个难度级别下评估游戏工作负载的结果。

- Remember for this test you need a minimum of 5 users and ideally more

| USER ID | WORKLOAD LEVEL 1 | WORKLOAD LEVEL 2 |
|---------|------------------|------------------|
| U1      | 25               | 67               |
| U2      | 32               | 56               |
| U3      | 18               | 43               |

- Enter the data into the online calculator: https://www.statology.org/wilcoxon-signed-rank-test-calculator/

- Look up the calculated W test statistic in the table of critical values 查阅临界值表中的计算出的W检验统计量

- To do this you need to know N, which is the number of users, and the significance level, which we will set at 0.05

- This means that if a significant difference is found then it is 95% certain that this is a real difference rather than due to randomness in the data you have collected 这意味着如果发现显著差异，那么有95%的把握是真实存在的，而不是你收集的数据中的随机性

- We use an alpha value aka significance level of 0.05 我们使用α值，即显著水平 0.05

- We find the row that corresponds to our number of users aka n – let's imagine we collected data from 10 users 我们找到对应用户数的行，也就是n——假设我们收集了10个用户的数据

- The critical value is in the cell where the alpha value column and number of users row intersect (8 in this case)

- The W test statistic generated by the online calculator needs to be equal to or less than the critical value, otherwise there is no significant difference 在线计算器生成的W检验统计量必须等于或小于临界值，否则无显著差异

ALPHA VALUE
n 0.005 0.01 0.025 0.05 0.10
5 - - - - 0
6 - - - 0 2
7 - - 0 2 3
8 - 0 2 3 5
9 0 1 3 5 8
10 1 3 5 8 10
11 3 5 8 10 13
12 5 7 10 13 17
13 7 9 13 17 21
14 9 12 17 21 25
15 12 15 20 25 30
16 15 19 25 29 35
17 19 23 29 34 41
18 23 27 34 40 47
19 27 32 39 46 53
20 32 37 45 52 60

- If we compare two sets of results generated by two different groups e.g. the SUS scores of experienced gamers and novice gamers after playing the same video game, then this type of study is known as a 'between-subjects' study design. 如果我们比较两组不同组生成的结果，例如经验玩家和新手玩家玩同一游戏后的 SUS 分数，这种研究被称为“受试者间”研究设计。
- We use a different statistical test to determine whether there is a significant difference between the SUS scores of the novice（新手） and experienced gamers
- This is known as the Mann-Whitney U test. There is also an online calculator for this test and the calculation process is similar to Wilcoxon signed ranks test.
- You can read about the Mann-Whitney U test here: https://www.statology.org/ mann-whitney-u-test/

## Summary of within-subjects and between-subjects study designs

- Imagine we want to test two alternative versions of a website: site 1 and site 2

- A within-subjects study design would ask every participant to evaluate both site 1 and site 2
- A between-subjects study design would get one group of participants to evaluate site 1 and a different group of participants to evaluate site 2

## Advantages and disadvantages of within-subjects study designs

- The two main advantages of a within-subjects study design are that you need fewer participants and it reduces the impact of participants' individual differences as all participants do all evaluations 受试者内研究设计的两个主要优点是需要更少的参与者，并且由于所有参与者都参与所有评估，减少了参与者个体差异的影响
- The disadvantages of a within-subjects study design are that participants can gain knowledge and skills from completing one part of the evaluation and use them doing another part of the evaluation aka a 'learning effect'. 受试者内研究设计的缺点是，参与者可能通过完成评估的一部分获得知识和技能，却能将其用于评估的另一部分，即“学习效应”。

## Advantages and disadvantages of between-subjects study designs

- The two main advantages of a between-subjects study design are that

participants spend less time doing the evaluations (e.g. they only evaluate one website) and there are no learning effects 受试者间研究设计的两个主要优点是：参与者在评估上花费的时间更少（例如他们只评估一个网站），且没有学习效应

- The main disadvantage of a between-subjects study design is that you need more participants because each participant only provides one data point 受试者间研究设计的主要缺点是需要更多参与者，因为每个参与者只提供一个数据点

- It is important that participants are comparable otherwise differences might be due to participant individual differences, rather than due to differences in what is being evaluated. 参与者的可比性非常重要，否则差异可能源于参与者个体差异，而非评估内容的差异。
