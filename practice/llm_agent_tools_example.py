"""
Script written by: Anantha Rao
Last Modified: 2-16-2025
"""
import os,re,sys,getpass, requests
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

"""Initialize Environment Variables for API keys"""
if not os.environ.get("GROQ_API_KEY"):
  os.environ["GROQ_API_KEY"] = getpass.getpass("Enter API key for Groq: ")
if not os.environ.get("NVD_API_KEY"):
    os.environ["NVD_API_KEY"] = getpass.getpass("Enter NVD API Key: ")

chat_history = []
q_a = []

"""Define Custom Tools"""
@tool("division-tool",parse_docstring=True)
def divide(a:float,b:float):
    """Divide two numbers.
   
    Args:
        a: The Dividend
        b: the Divisor
    """
    return a/b if b != 0 else 0

@tool("addition-tool",parse_docstring=True)
def add(a:float,b:float):
    """Add two numbers and return their sum.
   
    Args:
        a: First number 
        b: Second number
    """
    return a + b

@tool("multiplication-tool",parse_docstring=True)
def multiply(a:float,b:float) -> float:
    """Multiply two numbers
   
    Args:
        a: First number
        b: Second number
    """
    return a*b

model = init_chat_model("llama3-8b-8192", model_provider="groq")
m = model.bind_tools([divide,add,multiply])

query = "What is 5+9? Also, yo what is 5x5 and then tell me what 5/5 is!"
q_a.append(HumanMessage(query))
llm_msg = m.invoke(query)
q_a.append(llm_msg)

for tool_call in llm_msg.tool_calls:
    selected_fn = {"addition-tool":add,"multiplication-tool":multiply,"division-tool":divide}[tool_call['name']]
    tool_msg = selected_fn.invoke(tool_call)
    q_a.append(tool_msg)

chat_history.append(q_a)
# print(m.invoke(chat_history[-1]).content)