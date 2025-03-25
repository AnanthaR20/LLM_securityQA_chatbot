"""
Script written by: Anantha Rao
Last Modified: 2-16-2025
Attribution Note: "This product uses the NVD API but is not endorsed or certified by the NVD."
"""
import os,re,random, getpass, requests
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

"""Initialize Environment Variables for API keys"""
if not os.environ.get("GROQ_API_KEY"):
  os.environ["GROQ_API_KEY"] = getpass.getpass("Enter API key for groq LLM: ")
if not os.environ.get("NVD_API_KEY"):
    os.environ["NVD_API_KEY"] = getpass.getpass("Enter API key for NVD: ")

# Helper fn
def date_info_present(query:str):
    """Checks to see if query string contains any mention of date-related words"""
    date_related = [
        "january",'february','march','april',
        'may','june','july','august','september',
        'october','november','december',' jan',' feb',
        ' mar','apr',' jun',' jul',' aug',' sep',' sept',' oct',
        ' nov',' dec','month','year',"week"," day ",
        "today","tomorrow","yesterday"]
    
    for i in date_related:
        if i in query.lower():
            return True
    if re.search(r"\d{4}-\d{2}-\d{2}",query):
        return True
    
    return False

# Helper fn
def valid_datetime_diff(dateRangeStart:str,dateRangeEnd:str):
    """Checks if paramaters are formatted as YYYY-MM-DD.
    Also, given that it is formatted correctly, it checks to see if
    the date range violates the 120 day limit for the NVD API.
    """
    format_checker = re.compile(r"\d{4}-\d{2}-\d{2}")
    if not format_checker.match(dateRangeStart) or not format_checker.match(dateRangeEnd):
        return False
    
    year_s = int(dateRangeStart[0:4])
    year_e = int(dateRangeEnd[0:4])
    mon_s = int(dateRangeStart[5:7])
    mon_e = int(dateRangeEnd[5:7])
    day_s = int(dateRangeStart[8:10])
    day_e = int(dateRangeEnd[8:10])

    cond0 = (year_e > year_s) or (mon_e > mon_s) or (day_e > day_s)
    cond1 = mon_e - mon_s <= 2 and year_e == year_s
    cond2 = mon_e - mon_s <=-10 and year_e - year_s == 1
    if cond0 and (cond1 or cond2):
        return True
    else:
        return False


"""Define Custom Tool"""
@tool("api-tool",parse_docstring=True)
def nvd_api(cveId:str,dateRangeStart:str,dateRangeEnd:str,keywords:str) -> str:
    """
    Calls the NVD API to get data-based answers related to the NVD security and vulnerability database.

    Args:
        cveId: cve identification number. Formatted as 'CVE', '-', 4 digits, '-', 5 digits
        dateRangeStart: the starting date among date-related words in the query. Formatted YYYY-MM-DD
        dateRangeEnd: the ending date among date-related words in the query. Formatted YYYY-MM-DD
        keywords: 1 to 3 key words specifying a particular set of vulnerabilities or exposuresor the name of a company, software, or product. keywords are separated by a space.
    """
    
    """Assemble API URL to call"""
    url_stem = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    url_params = ""
    if dateRangeStart == "" or dateRangeEnd == "" or not valid_datetime_diff(dateRangeStart,dateRangeEnd):
        url_params = "?cveId=" +cveId+ "&keywordSearch="+keywords
    else:
        url_params = "?cveId=" +cveId+ "&keywordSearch="+keywords+"&lastModStartDate="+dateRangeStart+"T00:00:00-08:00&lastModEndDate="+dateRangeEnd+"T23:59:59-08:00"
    
    url = url_stem + url_params
    response = requests.get(url,headers={"apiKey":os.environ["NVD_API_KEY"]})
    
    """Handle Server Response"""
    if response.ok:
        """Consider groq llm API limits"""
        API_max_char_limit = 18000
        sample_size = 10

        """Take a random sample of CVEs when more than one returned"""
        j = response.json()
        all_CVEs= j['vulnerabilities']
        sample_CVEs = []
        if len(all_CVEs) >= sample_size:
            random_subset = random.sample(range(0,len(all_CVEs)),sample_size)
            for i in random_subset:
                sample_CVEs.append(all_CVEs[i])
        elif len(all_CVEs) > 0:
            sample_CVEs = all_CVEs
        else:
            """Return the mostly-empty JSON and a custom message"""
            return j | {"message":"There are no vulnerabilities that match that query"}

        """LLM should have more context about each vulnerability when it can. Thus, context-size is based on sample size"""
        context_size = int((API_max_char_limit-1000)/len(sample_CVEs))
       
        """Create a list of context-strings for each of the sample CVEs"""
        sample_CVEs_as_context_strings = [str(v)[0:context_size] for i,v in enumerate(sample_CVEs)]

        """Return dictionary of sample CVEs"""
        return {
            "message": f"There are {len(sample_CVEs)} CVEs in this sample",
            "numSamples": len(sample_CVEs),
            "totalResults": j['totalResults'],
            "version": j["version"],
            "timestamp": j["timestamp"],
            "vulnerabilities": sample_CVEs_as_context_strings
        }
    
    else:
        """Return a message in case API call fails"""
        if response.status_code != 404:
            print(f"NVD API responded with code: {response.status_code}")
        return {"message":f"NVD API responded with code:{response.status_code}. Either wait a couple seconds or query needs rewording"}


"""Initialize chat history and chat models"""
human_readable_chat_history = []
chat_history = []
model = init_chat_model("llama3-8b-8192", model_provider="groq")
m = model.bind_tools([nvd_api])

"""Command Line Interface for answering questions"""
while (True):
    """Reset list of Message Objects for LLM to use for current iteration of questions"""
    q_a = [] 

    """Prompt user for question"""
    query = input("What questions do you have regarding the NVD? (Type 'q' to quit)\n")
    if query == 'q':
        break
    if query == "":
        continue
    print("--------------------")
    print("Let me look through the records. This should take less than a minute...\n")    
    
    """Get AIMessage() then log all Messages into q_a"""
    llm_params = m.invoke(query)
    human_readable_chat_history.append(query)
    q_a.append(HumanMessage(query))
    q_a.append(llm_params)

    """Run Tool Calls"""
    for tool_call in llm_params.tool_calls:
        selected_fn = {"api-tool":nvd_api}[tool_call['name']]

        """Prevent LLM from hallucinating arguments that are not asked about"""
        """Validate dates the LLM extracted """
        for arg in tool_call['args']:
            if 'date' in arg and date_info_present(query):
                continue
            if tool_call['args'][arg].lower() not in query.lower():
                tool_call['args'][arg] = ""

        print("While I comb through the database, here's a summary for you of how I'm interpreting your query:\n")
        print(tool_call['args'])
        tool_msg = selected_fn.invoke(tool_call)
        """Add ToolMessage to q_a"""
        q_a.append(tool_msg)

    """Invoke model for answer to the question"""
    llm_answer = model.invoke(q_a)
    print(llm_answer.content)

    """Log Answers in history"""
    chat_history.append(q_a)
    human_readable_chat_history.append(llm_answer.content)

    """Prompt user to continue or not"""
    prompt = input("Any other questions? (Type 'y' or 'n')\n")
    if prompt == 'y':
        print("--------------------\n\n\n\n\n")
        continue
    else:
        break


"""Offer Chat history"""
q = input("Would you like a copy of the chat history? (Type 'y' or 'n')")
print("\n\n\n------------------------------")
if (q == 'y'):
    for i,v in enumerate(human_readable_chat_history):
        if i % 2 == 0:
            print(f"\n***You: {v}")
        else:
            print(f"***Chatbot: {v}")
print("------------------------------")