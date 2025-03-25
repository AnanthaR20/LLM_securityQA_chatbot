import os,re,sys,getpass, requests
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage

os.environ['LANGSMITH_TRACING']='true'
os.environ['LANGSMITH_ENDPOINT']="https://api.smith.langchain.com"
# os.environ['LANGSMITH_API_KEY']= getpass.getpass("Type langsmith api key")
os.environ['LANGSMITH_PROJECT']="pr-blank-evidence-53"
if not os.environ.get("GROQ_API_KEY"):
  os.environ["GROQ_API_KEY"] = getpass.getpass("Enter API key for Groq: ")

model = init_chat_model("llama3-8b-8192", model_provider="groq")

messages = [
    SystemMessage("Break the following down into sequential requests"),
    HumanMessage("How many errors were there between Jan and Feb last year?"),
]

# print(model.invoke(messages))
"""----- On Prompt Templates now -----"""
from langchain_core.prompts import ChatPromptTemplate

system_template = "Translate the following from English into {language}"

prompt_template = ChatPromptTemplate.from_messages(
    [("system", system_template), ("user", "{text}")]
)

"""----- Using Tools -----"""
from langchain_core.tools import tool
@tool("division-tool")
def divide(a:float,b:float):
  """Divide two numbers, where 'b' is the dividend 
  and 'a' is the divisor"""
  return b/a


""" ----- Using Structured Tools -----"""
from pydantic import BaseModel,Field
from langchain_core.tools import StructuredTool

class CalculatorInput(BaseModel):
  a:int = Field(description = "first number")
  b:int = Field(description = "second number")

def multiply(a:int,b:int) -> int:
  """Multiply two integers"""
  return a * b

calc = StructuredTool.from_function(
  func = multiply,
  name = "Calculator",
  description = "multiply two integers together",
  args_schema = CalculatorInput
)


url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
# response = requests.get(url)
# 



