# coby
Simple build system that is specifically design for C++20 modules.
To build a project, it needs two things, a rule file and a target file.
The rule file consists of python functions which returns the correct command to run for each rule.
The target file describes the different targets and what rule to use for them. The dependency between modules
can either be decided automatically with automatic=true for the target or manually with deps=[target1,target2]
