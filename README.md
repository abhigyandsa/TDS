# TDS Project 1 (LLM Agent)
## IIT Madras BS Programme. January 2025.
### - by Abhigyan Das

This project aims to create an llm agent and expose two api endpoints.
- run - this allows the user to pass a plain English task description via the url parameter ```task``` and have the llm parse and execute the task as described (or atleast attempt to).
- read - allows reading non-privileged files from the system to access output of run. Uses the ```file``` parameter.
