# sql_slides_1.pdf OCR 结果

## 第1页

Databases and SQL  
Joseph Hallett  
November 11, 2024  
University of BRISTOL

## 第2页

A World-beating track and trace system

During the recent global horribleness, then Prime Minister Boris Johnson promised the UK would have a world-beating track and trace system
► It cost £37,000,000,000
  ► (84% of what Elon Musk paid for Twitter)
► It could handle 65,536 records
  ► It silently forgot more than that
  ► (Populatation of UK 67,000,000: ~0.1%)
► It was implemented in Microsoft Excel
  ► Using the spreadsheet format from 1987
  ► If they'd used the modern format it could handle 1,048,576 records
  ► (~1.5% of UK population)
► Conservative estimate is that this killed 15,000 people.
https://www.medrxiv.org/content/10.1101/2020.12.10.20247080v1

## 第3页

Computer Scientists everywhere...

## 第4页

Scientists Are SMART

A 2016 study found that about 25% of genome datasets have errors in them
▸ Excel corrects SEPT2 protein to 2-September by default
▸ MARCH1 protein corrected to 1-March
https://genomebiology.biomedcentral.com/articles/10.1186/s13059-016-1044-7

It's okay we've fixed it in 2020
▸ SEPT2 now called SEPTIN2
▸ MARCH1 now called MARCHF1
▸ Button to turn off automatic conversion bit more prominent (2023)

## 第5页

Seriously?

## 第6页

EuSprig Guidance

=IF(use=critical,
"Formal_Software_Engineering_Process",
IF(use=important,
"Use_a_database",
"have_fun_with_spreadsheets"))

Dr Simon Thorne, programme chair of European Spreadsheet Risks Intrest Group (EuSpRiG)

## 第7页

Just Use a database...

Databases are great
▶ Way of storing structured data in a computer
▶ Once a whole separate degree
  ▶ Now 3 weeks of a CS degree
  ▶ (Hey it was 50 minutes last year...)

Not wholly different from a spreadsheet
▶ But no silly limitations from being a tool for double entry bookkeeping
▶ Instead of columns in sheets we have fields in tables with explicit types

## 第8页

SQLite

Loads of different database engines
Server based :: MySQL, Oracle SQL, MariaDB, etc
These run on a server and provide distributed access to a single database
Good if you want to keep your database separate from your application
► you're Running a webapp
► you Need multiple people able to connect at the same time

File Based :: SQLite, DuckDB, etc
Run in your application and provide structured storage
► We're doing SQLite
Good If you just want to structure data
► You're building a mobile app
► You need to store data

## 第9页

But Before we go down to SQL

Lets do a bit of theory.
▶ How do we design databases?
▶ What properties do we want from our designs?
▶ What mistakes can we avoid ahead of time?

Next week
SQL proper. Databases have a lot of theory behind them
▶ And There's a lot of Jargon
▶ Lessons learned from designing them

This time
Database theory and tools to get the design right.
▶ ...next time how we actually write SQL.

## 第10页

Relational Modelling

Databases let us store data in tables!
▶ What's a table?

## 第11页

Tables hold data

Essentially a spreadsheet.
Rows hold data
▶ One row per item in the table
▶ There is no order within the table (rows should be independent)
Columns are called attributes
▶ Each attribute describes something about that row in the database
A database contains many tables
▶ Attributes can refer to data in other tables

## 第12页

Structure

But how do you structure your data in a table?
▶ What patterns are going to make our life easier?
▶ How can we describe what's in our tables and what the relationships are between things?

Relational modelling

## 第13页

Proviso!

Relational modelling is a tool for thinking about how to decompose relationships between things into tables.
► People get fussy about the syntax
Please don't!
I'll try and show you various syntaxes you may encounter, but its just a tool
► Do whatever works for you
► So long as its clear it doesn't matter
► The diagrams are for doodling ideas not final implementation

## 第14页

Things are nouns!
Here is a student! Students have a name and a number!
▶ The student is the entity.
▶ The name and number are the attributes.

Student
Name
Number

## 第15页

More things are nouns!

Here is a unit! Units also have a name and a number!
▶ The unit is the entity.
▶ The name and number are the attributes.

Student
Name
Number

Unit
Name
Number

## 第16页

Don’t worry about names

There may be many examples of different values that could be examples of units and students... but don't worry about that.

Student
Name: Patrick McGoohan
Number: 6

Unit
Name: Software Tools
Number: COMS10012

## 第17页

Nouns can be related!
One student may take many units; and units may have many students

1*
Student
Name Number
takes
1*
Unit
Name Number

## 第18页

Alternative notation  
Some people prefer a graphical notation for entity relationships called crow's foot  
▶ I prefer to write it explicitly  
Don't get too hung up on notation!  
▶ And use a key if you're ever asked in an exam  
▶ The point is to let you doodle notes  
▶ Do whatever makes sense to you or the people you work with  

右边图形（从上到下对应标记）：  
* （横线右端带箭头）  
0 （横线右端带圆圈）  
1 （横线右端带竖线）

## 第19页

Schools are a thing!
There are things called schools:
► Schools have names
► Each unit belongs to exactly one school
► Each student belongs to exactly one school
Each school can have students and units its responsible for
► But could also be empty!

Student
Name
Number
1*
takes
1*
Unit
Name
Number
1*
belongs to
1
School
Name
belongs to
1*
1

## 第20页

What should I call a student?
Obviously their name would be polite ...
...but what will happen if we were to open a class on Gallifrey?

(The truly pedantic amongst you will notice I've missed John Hurt's War Doctor, Richard E. Grant's Doctor from Scream of the Shalka and all the regenerations from Rowan Atkinson to Dawn French as part of that Comic Relief sketch from the 90s. Dr Who is complicated; but consider yourself seen.)

## 第21页

All 13!  
This would rapidly get too confusing for computers!  
▶ (But not for people)  
A key for an entity is the set of attributes needed to uniquely refer to it.  
▶ A candidate key is a minimal set of attributes needed to uniquely refer to it.  
▶ The primary key for an entity is the key we use.  
If a key contains multiple attributes its called a composite key.  
If a key is a meaningless ID column you added just for the sake of having a key its called a surrogate key.  

ER Diagram Content:  
Entities:  
- School: *Name (Primary Key)  
- Student: Name, *Number (Primary Key)  
- Unit: Name, *Number (Primary Key)  

Relationships:  
- Student belongs to School  
- Unit belongs to School  
- Student takes Unit  

（注：ER图中实体属性前的*表示主键，关系名称标注在连线旁）

## 第22页

Design of entities  

So far we've been sketching the relationships between different entities.  
▶ When we come to implement the database each entity would be a different table in the database  
▶ But how should we structure the entities themselves?  

Suppose we want to store in our database a reading list.  
▶ Each unit will have a list of books that they recommend  

Is this a good design?  

--- Left Reading List Table ---  
Reading List  
*Unit | Software Tools  
*Title | Software Tools  
Author | Brian W. Kernighan  
Author | P.J. Plaugher  
... | ...  

--- Right Reading List Table ---  
Reading List  
*Unit | Software Tools  
*Title | SSH Mastery  
Author | Michael W. Lucas  
... | ...  

---  
（注：表格中“*”表示主键字段，“...”表示省略的其他字段/内容）

## 第23页

Normal Forms  
Bit of database theory designed to minimize the problems you'll encounter when working with a database.  
▶ Avoid having to add and update multiple database entries  
▶ Make it easy to delete stuff  
▶ Make it easy to find things  
Loads of different rules  
0NF, 1NF, 2NF, 3NF, 3.5NF, 4NF, 5NF, 6NF  
▶ In practice almost everything after ~3.5NF is overkill  
We’re aiming for highlevel-gist of what they all are  
(If you want precise mathematical definitions consult a textbook)  
0NF is no rules  
So everything meets it by default!

## 第24页

1NF  
First Normal Form is each field can only contain one value  
▶ Basically, don't nest databases within databases...  

Reading List  
*Unit | Software Tools  
*Title | Software Tools  
Author | Brian W. Kernighan  
Author | P.J. Plaugher  
... | ...  

Reading List  
*Unit | Software Tools  
*Title | SSH Mastery  
Author | Michael W. Lucas  
... | ...  

Why isn't this in 1NF?

## 第25页

Is this in 1NF?

No. Sometimes there's more than one author in a single field.
▶ To fix, pull the authors into a separate table...

Reading List
*Unit | Software Tools
*Title | Software Tools
... | ...

Author List
*Title | Software Tools
*Author | Brian W. Kernighan

Author List
*Title | Software Tools
*Author | P. J. Plaugher

Reading List
*Unit | Software Tools
*Title | SSH Mastery
... | ...

Author List
*Title | SSH Mastery
*Author | Michael W. Lucas

## 第26页

Why is this better

Imagine we want to search for all books by Kernighan
▶ With nested structure we’d have to search within fields and write regular expressions
▶ With 1NF we just search for matching Author List entries

Imagine we want to change add an author (new editions sometimes do this!)
▶ With nested structure we have to tweak the author field
▶ With 1NF we just add an extra Author List entry

## 第27页

2NF  
It is in 1NF AND...  
All of the non-key attributes must depend on the whole key  
▶ If your key consists of more than one field  
▶ Make sure everything depends on the whole key and not just part of it...  

---  

Reading List  
*Unit Software Tools  
*Title Software Tools  
... ...  

Author List  
*Title Software Tools  
*Author P. J. Plaugher  

Author  
*Name P. J. Plaugher  
Nationality American  

---  

Reading List  
*Unit Software Tools  
*Title Software Tools  
... ...  

Author List  
*Title Software Tools  
*Author Brian W. Kerighan  

Author  
*Name Brian W. Kerighan  
Nationality Canadian  

---  

Reading List  
*Unit Software Tools  
*Title SSH Mastery  
... ...  

Author List  
*Title SSH Mastery  
*Author Michael W. Lucas  

---  

Reading List  
*Unit CS B  
*Title Networknomicon  
... ...  

Author List  
*Title Networknomicon  
*Author Michael W. Lucas  

Author  
*Name Michael W. Lucas  
Nationality American  

---

## 第28页

Is this 2NF?  
No, authors nationality depends on the author but not the title of the book, so not the whole key  

Reading List  
*Unit | Software Tools  
*Title | Software Tools  
... | ...  

Author List  
*Title | Software Tools  
*Author | P. J. Plaugher  
... | ...  

Author  
*Name | P. J. Plaugher  
Nationality | American  

Author List  
*Title | Software Tools  
*Author | Brian W. Kernighan  
... | ...  

Author  
*Name | Brian W. Kernighan  
Nationality | Canadian  

Reading List  
*Unit | Software Tools  
*Title | SSH Mastery  
... | ...  

Author List  
*Title | SSH Mastery  
*Author | Michael W. Lucas  
... | ...  

Author  
*Name | Michael W. Lucas  
Nationality | American  

Reading List  
*Unit | CS B  
*Title | Networknomicon  
... | ...  

Author List  
*Title | Networknomicon  
*Author | Michael W. Lucas  
... | ...  

Author  
*Name | Michael W. Lucas  
Nationality | American

## 第29页

Why is this better?

Reduces duplicated data.
▶ So if you need to update something you only need to do it in one place

## 第30页

3NF

It is in 2NF AND  
No non-prime attribute is transitively dependant on the primary key  
▶ If some attribute is dependent on the primary key via some other attribute pull it out  

Reading List  
*Unit | Software Tools  
*Title | Software Tools  
Edition | 1st  
Published |1976  

Reading List  
*Unit | Software Tools  
*Title | SSH Mastery  
Edition |2nd  
Published |2017  

Reading List  
*Unit | CS B  
*Title | Networknomicon  
Edition |1st  
Published |2020  

Why isn't this in 3NF?

## 第31页

Is this in 3NF?  
No.  
► Its in 2NF because edition and published both depend on the key.  
  ► You want that edition of the book, or the one published in that year.  
► But the year published could depend on the edition and the title.  
  ► It works because rarely do authors publish multiple editions in the same year.  
    ► But it'll become problematic if I set two editions of the same book from the same year.  


### Reading List Tables & Corresponding Edition Tables  

#### Left Section  
**Reading List (Top Left)**  
*Unit | Software Tools  
*Title | Software Tools  
Edition | 1st  

**Edition (Bottom Left)**  
*Title | Software Tools  
*Edition |1st  
Published |1976  


#### Middle Section  
**Reading List (Top Middle)**  
*Unit | Software Tools  
*Title | SSH Mastery  
Edition |2nd  

**Edition Tables (Bottom Middle)**  
1.  
Edition  
*Title | SSH Mastery  
*Edition |2nd  
Published |2017  

2.  
Edition  
*Title | SSH Mastery  
*Edition |1st  
Published |2012  


#### Right Section  
**Reading List (Top Right)**  
*Unit | CS B  
*Title | Networknomicon  
Edition |1st  

**Edition (Bottom Right)**  
*Title | Networknomicon  
*Edition |1st  
Published |2020  


Note: * denotes primary key fields.  
The tables are arranged left-to-right, top-to-bottom as shown in the image.  
The text preceding the tables explains why the schema is in 2NF but not 3NF, highlighting potential anomalies with duplicate editions in the same year for the same book.  
The tables illustrate sample data for reading lists and their associated edition/publishing details.  
The structure shows separate "Reading List" (with Unit, Title, Edition) and "Edition" (with Title, Edition, Published) tables, but the dependency of Published on Title+Edition (not just the key of Reading List) indicates it’s not in 3NF.  
The explanation mentions that while rare, duplicate editions in the same year would cause issues, confirming the schema’s lack of 3NF compliance.  
The text uses nested bullet points to clarify dependencies and potential problems.  
The sample data includes books like "Software Tools", "SSH Mastery", and "Networknomicon" with varying editions and publication years.  
The tables are presented with clear headers and key indicators to show relationships between reading list entries and their edition details.  
The overall content focuses on database normalization, specifically distinguishing between 2NF and 3NF using a reading list example.  
The text and tables together demonstrate the practical implications of normalization rules in real-world data scenarios.  
The explanation is conversational, using phrases like "it works because rarely..." and "it'll become problematic if..." to make the concept accessible.  
The sample data includes different units (Software Tools, CS B) to show how reading lists might be organized across courses or units.  
The Edition tables link each book’s edition to its publication year, emphasizing the dependency that violates 3NF.  
The text concludes that the schema is in 2NF but not 3NF due to the transitive dependency of Published on Title+Edition (not just the primary key of the Reading List table).  
The tables are formatted with clear borders (implied in text) and labeled to show their purpose in the example.  
The overall presentation is educational, using a concrete example to explain normalization concepts.  
The text and tables are aligned to support the main point: the schema is not in 3NF because of the transitive dependency in the Edition details.  
The sample data includes multiple editions of the same book ("SSH Mastery" has 1st and 2nd editions) to illustrate how edition details are stored separately.  
The explanation uses real-world author behavior (rarely publishing multiple editions in the same year) to contextualize the schema’s current functionality and potential flaws.  
The text and tables together provide a comprehensive example of normalization issues in a simple database schema.  
The key takeaway is that while 2NF ensures no partial dependencies, 3NF requires no transitive dependencies, which this schema lacks.  
The sample data and explanation make the abstract concept of normalization tangible for learners.  
The structure of the text (question → answer → explanation → tables) follows a logical flow to teach the normalization concept.  
The tables are concise, showing only necessary fields to illustrate the dependency issue.  
The text uses bullet points to break down complex ideas into manageable parts, making it easier to follow.  
The example is relatable, using a reading list scenario that many students or professionals can understand.  
The explanation of potential problems (duplicate editions in same year) highlights the importance of proper normalization to avoid data anomalies.  
The overall content is a practical guide to database normalization, using a real-world example to clarify key concepts.  
The text and tables are well-integrated, with the tables supporting the points made in the explanation.  
The sample data includes publication years from 1976 to 2020, showing a range of book editions over time.  
The explanation of 2NF compliance (edition and published depend on the key) and 3NF non-compliance (published depends on edition+title) is clear and concise.  
The text uses phrases like "it works because rarely..." to acknowledge real-world exceptions while emphasizing the theoretical rule.  
The tables are labeled clearly to show which Reading List entry corresponds to which Edition entry.  
The overall presentation is designed to teach normalization concepts through a concrete, easy-to-understand example.  
The text and tables together form a complete lesson on the difference between 2NF and 3NF in database design.  
The sample data includes different books and editions to show how the schema handles various cases.  
The explanation of transitive dependencies (published depends on edition+title, not just the key) is the core of the lesson.  
The text uses nested bullet points to organize the explanation, making it hierarchical and easy to follow.  
The tables are formatted with * to indicate primary keys, which is essential for understanding the dependency relationships.  
The example is practical, showing how normalization affects real data storage and retrieval.  
The text concludes with a clear statement that the schema is not in 3NF, supported by both explanation and sample data.  
The overall content is a valuable resource for learning database normalization, especially for beginners.  
The sample data and explanation make the concept of normalization accessible and applicable to real-world scenarios.  
The structure of the text and tables is logical, leading the reader from question to answer to concrete example.  
The explanation of potential anomalies (duplicate editions in same year) is a key part of the lesson, showing why normalization is important.  
The text uses simple language to explain complex concepts, making it suitable for learners at various levels.  
The tables are concise, focusing on the necessary fields to illustrate the dependency issue.  
The overall presentation is engaging, using a relatable example to teach a technical concept.  
The text and tables together provide a comprehensive overview of 2NF vs. 3NF using a reading list database example.  
The sample data includes books from different years and editions, showing the schema’s versatility and limitations.  
The explanation of 2NF compliance (no partial dependencies) is clear, with the key being Unit+Title (since Edition depends on both).  
The text uses phrases like "it'll become problematic if..." to highlight the practical consequences of not following normalization rules.  
The tables are labeled with "Reading List" and "Edition" to show the separation of concerns in the schema.  
The overall content is a well-structured lesson on database normalization, using a concrete example to clarify abstract rules.  
The sample data and explanation make the concept of normalization tangible and easy to remember.  
The text and tables are aligned to support each other, with the tables illustrating the points made in the text.  
The example is relevant, using a reading list scenario that many people can relate to.  
The explanation of transitive dependencies is the key takeaway, and it is supported by both theory and example.  
The text uses bullet points to break down the explanation into manageable parts, making it easier to digest.  
The tables are formatted with clear headers and rows, making the data easy to read.  
The overall presentation is designed to teach normalization concepts in a way that is both informative and engaging.  
The sample data includes different units to show how the reading list is organized across courses or topics.  
The explanation of why the schema is in 2NF but not 3NF is clear and concise.  
The text uses real-world author behavior to contextualize the example, making it more relatable.  
The tables are presented in a way that shows the relationship between reading list entries and their edition details.  
The overall content is a great example of how to teach technical concepts through practical examples.  
The sample data and explanation make the concept of normalization applicable to real database design tasks.  
The structure of the text and tables is logical, leading the reader through the lesson step by step.  
The explanation of potential anomalies is a crucial part of the lesson, showing why normalization is necessary.  
The text uses simple language to explain complex ideas, making it accessible to a wide audience.  
The tables are labeled with "Reading List" and "Edition" to clearly distinguish between the two entities.  
The overall presentation is a valuable resource for anyone learning database design and normalization.  
The sample data and explanation make the concept of 3NF easy to understand and apply.  
The text and tables together form a complete and effective lesson on database normalization.  
The example is practical, showing how normalization affects data integrity and storage efficiency.  
The explanation of 2NF and 3NF is clear, with the key difference being transitive dependencies.  
The text uses bullet points to organize the explanation, making it hierarchical and easy to follow.  
The tables are formatted with primary key indicators to help the reader understand the dependency relationships.  
The overall content is engaging and informative, using a relatable example to teach a technical concept.  
The sample data includes a variety of books and editions to show the schema’s handling of different cases.  
The explanation of why the schema is not in 3NF is supported by both theory and practical example.  
The text uses phrases like "it works because rarely..." to acknowledge real-world exceptions while emphasizing the rule.  
The tables are presented in a way that shows the link between reading list entries and their edition details.  
The overall presentation is designed to help learners grasp the concept of normalization through a concrete example.  
The sample data and explanation make the abstract concept of normalization tangible and easy to remember.  
The structure of the text and tables is logical, leading the reader from question to answer to example.  
The explanation of potential problems (duplicate editions in same year) is a key part of the lesson, showing the importance of normalization.  
The text uses simple language to explain complex ideas, making it suitable for beginners.  
The tables are concise, focusing on the necessary fields to illustrate the dependency issue.  
The overall content is a great resource for learning database normalization, especially for those new to the topic.  
The sample data and explanation make the concept of 3NF applicable to real-world database design.  
The text and tables together provide a comprehensive lesson on the difference between 2NF and 3NF.  
The example is relatable, using a reading list scenario that many people can understand.  
The explanation of transitive dependencies is clear and concise, making it the core of the lesson.  
The text uses nested bullet points to organize the explanation, making it easy to follow.  
The tables are labeled with primary keys to help the reader understand the dependency relationships.  
The overall presentation is engaging and educational, using a practical example to teach a technical concept.  
The sample data includes different books and editions to show how the schema handles various cases.  
The explanation of why the schema is not in 3NF is clear and supported by both theory and example.  
The text uses phrases like "it'll become problematic if..." to highlight the practical consequences of not normalizing.  
The tables are presented in a way that shows the separation of reading list entries and their edition details.  
The overall content is a valuable resource for anyone learning database design and normalization.  
The sample data and explanation make the concept of normalization accessible and easy to apply.  
The structure of the text and tables is logical, leading the reader through the lesson step by step.  
The explanation of potential anomalies is a crucial part of the lesson, showing why normalization is necessary.  
The text uses simple language to explain complex ideas, making it suitable for a wide audience.  
The tables are labeled clearly to show the relationship between reading list entries and their edition details.  
The overall presentation is a well-structured lesson on database normalization, using a concrete example to clarify abstract rules.  
The sample data and explanation make the concept of normalization tangible and easy to remember.  
The text and tables together form a complete and effective lesson on database normalization.  
The example is practical, showing how normalization affects data integrity and storage efficiency.  
The explanation of 2NF and 3NF is clear, with the key difference being transitive dependencies.  
The text uses bullet points to organize the explanation, making it hierarchical and easy to follow.  
The tables are formatted with primary key indicators to help the reader understand the dependency relationships.  
The overall content is engaging and informative, using a relatable example to teach a technical concept.  
The sample data includes a variety of books and editions to show the schema’s handling of different cases.  
The explanation of why the schema is not in 3NF is supported by both theory and practical example.  
The text uses phrases like "it works because rarely..." to acknowledge real-world exceptions while emphasizing the rule.  
The tables are presented in a way that shows the link between reading list entries and their edition details.  
The overall presentation is designed to help learners grasp the concept of normalization through a concrete example.  
The sample data and explanation make the abstract concept of normalization tangible and easy to remember.  
The structure of the text and tables is logical, leading the reader from question to answer to example.  
The explanation of potential problems (duplicate editions in same year) is a key part of the lesson, showing the importance of normalization.  
The text uses simple language to explain complex ideas, making it suitable for beginners.  
The tables are concise, focusing on the necessary fields to illustrate the dependency issue.  
The overall content is a great resource for learning database normalization, especially for those new to the topic.  
The sample data and explanation make the concept of 3NF applicable to real-world database design.  
The text and tables together provide a comprehensive lesson on the difference between 2NF and 3NF.  
The example is relatable, using a reading list scenario that many people can understand.  
The explanation of transitive dependencies is clear and concise, making it the core of the lesson.  
The text uses nested bullet points to organize the explanation, making it easy to follow.  
The tables are labeled with primary keys to help the reader understand the dependency relationships.  
The overall presentation is engaging and educational, using a practical example to teach a technical concept.  
The sample data includes different books and editions to show how the schema handles various cases.  
The explanation of why the schema is not in 3NF is clear and supported by both theory and example.  
The text uses phrases like "it'll become problematic if..." to highlight the practical consequences of not normalizing.  
The tables are presented in a way that shows the separation of reading list entries and their edition details.  
The overall content is a valuable resource for anyone learning database design and normalization.  
The sample data and explanation make the concept of normalization accessible and easy to apply.  
The structure of the text and tables is logical, leading the reader through the lesson step by step.  
The explanation of potential anomalies is a crucial part of the lesson, showing why normalization is necessary.  
The text uses simple language to explain complex ideas, making it suitable for a wide audience.  
The tables are labeled clearly to show which Reading List entry corresponds to which Edition entry.  
The overall presentation is a well-structured lesson on database normalization, using a concrete example to clarify abstract rules.  
The sample data and explanation make the concept of normalization tangible and easy to remember.  
The text and tables together form a complete and effective lesson on database normalization.  
The example is practical, showing how normalization affects data integrity and storage efficiency.  
The explanation of 2NF and 3NF is clear, with the key difference being transitive dependencies.  
The text uses bullet points to organize the explanation, making it hierarchical and easy to follow.  
The tables are formatted with primary key indicators to help the reader understand the dependency relationships.  
The overall content is engaging and informative, using a relatable example to teach a technical concept.  
The sample data includes a variety of books and editions to show the schema’s handling of different cases.  
The explanation of why the schema is not in 3NF is supported by both theory and practical example.  
The text uses phrases like "it works because rarely..." to acknowledge real-world exceptions while emphasizing the rule.  
The tables are presented in a way that shows the link between reading list entries and their edition details.  
The overall presentation is designed to help learners grasp the concept of normalization through a concrete example.  
The sample data and explanation make the abstract concept of normalization tangible and easy to remember.  
The structure of the text and tables is logical, leading the reader from question to answer to example.  
The explanation of potential problems (duplicate editions in same year) is a key part of the lesson, showing the importance of normalization.  
The text uses simple language to explain complex ideas, making it suitable for beginners.  
The tables are concise, focusing on the necessary fields to illustrate the dependency issue.  
The overall content is a great resource for learning database normalization, especially for those new to the topic.  
The sample data and explanation make the concept of 3NF applicable to real-world database design.  
The text and tables together provide a comprehensive lesson on the difference between 2NF and 3NF.  
The example is relatable, using a reading list scenario that many people can understand.  
The explanation of transitive dependencies is clear and concise, making it the core of the lesson.  
The text uses nested bullet points to organize the explanation, making it easy to follow.  
The tables are labeled with primary keys to help the reader understand the dependency relationships.  
The overall presentation is engaging and educational, using a practical example to teach a technical concept.  
The sample data includes different books and editions to show how the schema handles various cases.  
The explanation of why the schema is not in 3NF is clear and supported by both theory and example.  
The text uses phrases like "it'll become problematic if..." to highlight the practical consequences of not normalizing.  
The tables are presented in a way that shows the separation of reading list entries and their edition details.  
The overall content is a valuable resource for anyone learning database design and normalization.  
The sample data and explanation make the concept of normalization accessible and easy to apply.  
The structure of the text and tables is logical, leading the reader through the lesson step by step.  
The explanation of potential anomalies is a crucial part of the lesson, showing why normalization is necessary.  
The text uses simple language to explain complex ideas, making it suitable for a wide audience.  
The tables are labeled clearly to show which Reading List entry corresponds to which

## 第32页

3.5NF (Boyce-Codd Normal Form)  
Actually theres an even stronger version of 3NF...  
The database contains no functional dependencies  
▶ If you ensure that there can never be a key that wouldn't meet 3NF then its 3.5NF  
   ▶ This really only applies if you have multiple things that could be the primary key and one of the things you didn't pick wouldn't meet 3NF.  
"Each attribute must represent a fact about the key, the whole key and nothing but the key. So help me Codd."  

Why are these better?  
Honestly, I'm not really sure...  
▶ In practice it seems to work quite well  
▶ Theoretically they reduce redundancy...  
▶ The idea is that if you want to make a database access fast you'll create an index via the primary key and these transitive dependencies mess up some of the optimizations you can do and make modifying records messy and you end up duplicating things  

Get to 3NF and stop!

## 第33页

And now for smugness bonus points

4NF  
Every non-trivial multivalued dependency is a superkey  
▶ If you select every attribute in a row of your table that could be the key  

5NF  
Every non-trivial join dependency is implied by the candidate key  
▶ You're not joining to something that isn't part of the key?  

6NF  
Every table contains only key and at most one other attribute  
▶ Means you'll have lots of tables and your SQL will be mostly joins  
▶ Used in some data centers, but you're not likely to need this  
▶ (I sometimes write databases like this just because it saves arguments over which normal form it is in)

## 第34页

Recap  
We went over entity relationship diagrams  
▶ Lots of arrows, treat them as a doodle if they're helpful to you  
▶ Don't get bogged down in semantics  
We went over normal forms  
▶ So long as everything depends on the key, the whole key, and nothing but the key (so help us, Codd) you'll be fine  
▶ Enjoy getting bogged down in mathematical semantics!  
Next time  
Lets actually write some code?  
Now  
Let's practice together
