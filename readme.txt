Anantha Rao
3-25-2025
LLM Agent for QA regarding national vulnerabilities database
---
This was the coding challenge I did. It uses the API from this website:
https://nvd.nist.gov/developers/vulnerabilities

... and the groq-llama LLM (using a GROQ API key) to make API calls based on user's
natural language inquiries, then responds with the LLM using the returned JSON.

Makes use of 'custom tools' from the LangChain Python package:
https://python.langchain.com/docs/introduction/

Essentially a question-answering LLM chatbot for questions about the National Vulnerability Database.

call 'nvd_agent.py' to run the script
