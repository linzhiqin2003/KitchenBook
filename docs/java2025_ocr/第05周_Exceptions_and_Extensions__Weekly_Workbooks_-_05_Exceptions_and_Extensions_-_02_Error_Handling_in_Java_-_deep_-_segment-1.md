# Sketching Inheritance Relationships

This notation borrows from the Unified Modelling Language (UML), which is an established standard for modelling systems, particularly object-oriented ones...

UNIFIED MODELING LANGUAGE

a class is represented by a box with three sections: 1) the class name, 2) the attributes, and 3) the methods

inheritance is represented by a (triangular) arrow from child to parent class

multi-level inheritance

Why could a class with no new features be a valid and useful child class?

if no new features are introduced, a section can be left empty

Robot
String name
int numLegs
float powerLevel
void talk(String)
void charge(float)

TranslationRobot
String substitute
void translate(String)

GermanTranslationRobot

CarrierRobot
void carry()