Anantha Rao
3-25-2025
LLM Agent for QA regarding national vulnerabilities database
---
This was the coding challenge I did for a startup in Seattle. It uses the API from this website:
https://nvd.nist.gov/developers/vulnerabilities

... and the groq-llama LLM (using a GROQ API key) to make API calls based on user's
natural language inquiries, then respond with the LLM using the returned JSON.

Makes use of 'custom tools' from the LangChain Python package:
https://python.langchain.com/docs/introduction/
