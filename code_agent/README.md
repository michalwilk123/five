The puspose of the code_agent is to provide a runtime for Script

Script is a JSON object that is long and multistep prompt that can be for example used to
generate a project from scratch

The Script is an abstract prompt representation. It can be used for anything.
In this project it is used as a massive prompt to represent the whole programming project from scratch

The main difference between Script and regular prompt is that the Script is executed by the
LLM element after element. It can be nested and be really complex, allowing for detailed project generation.
