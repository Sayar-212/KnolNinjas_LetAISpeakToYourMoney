import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv
from google.adk.agents import Agent


# Load Gemini API key from .env
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Load JSON from MCP folder
def load_fi_mcp_json(file_path: str) -> dict:
    with open(file_path, 'r') as f:
        return json.load(f)    

# Tool 2: Convert CSA Trust Report to JSON
def convert_trust_report_to_json(report: str) -> dict:
    result = {}

    # Extract sections with regex
    result["agent"] = re.search(r"Agent:\s*(.*)", report).group(1).strip()
    result["action"] = re.search(r"Action:\s*(.*)", report).group(1).strip()

    # Sources Used
    sources = re.findall(r"\d+\.\s*(http[^\n]+)", report)
    result["sources_used"] = sources

    # Source Trust
    trust = re.search(r"Sources:\s*(✅ Trustable|❌ Unverified)", report)
    result["sources_trust"] = trust.group(1).strip() if trust else "❓ Unknown"

    # Rules Referenced
    rules = re.findall(r"-\s*(.+)", report.split("Rules Referenced:")[1].split("Data Analyzed:")[0])
    result["rules_referenced"] = [r.strip() for r in rules]

    # Data Analyzed
    data_block = report.split("Data Analyzed:")[1].split("Reason:")[0]
    data_lines = re.findall(r"-\s*(.+?):\s*(.+)", data_block)
    result["data_analyzed"] = {k: v for k, v in data_lines}

    # Reason
    reason = re.search(r"Reason:\s*\n(.*?)\n\s*\nStatus:", report, re.DOTALL)
    result["reason"] = reason.group(1).strip() if reason else ""

    # Status
    status = re.search(r"Status:\s*(✅ Approved|❌ Not Approved)", report)
    result["status"] = status.group(1).strip() if status else "❓ Unknown"

    return result

# Define the CSA Agent (ADK style)
root_agent = Agent(
    name="CSA",
    model="gemini-2.0-flash",
    description="Compliance and Security Agent that audits outputs of other agents from Fi MCP data",
    instruction="""
You are CSA - the Compliance and Security Agent for Project Arthasashtri.Building trust for agents that sources are legal and trustable .

Your job is to analyze any agent's response coming from Fi MCP output JSON and generate a **clear, transparent trust report** for users.

Instructions:
- Accept JSON data that contains:
  - agent (str): Name of the agent
  - action (str): What the agent did
  - decision (str): Final decision taken by the agent
  - sources (list): URLs or source strings used by the agent
  - used_fields (dict): Important data or values referred to
  - financial_rule_refs (list): Financial rule codes or names that were referenced

Your main job is to help users trust every agent's response by:
- Showing the sources used 
- Validating the sources are trustable or not via search
- Validating the data used
- Explaining the decision in simple terms in points
- Verifying compliance with financial rules
- Displaying the links to MCP or external docs


Format your output exactly like this:

Agent: CSA

Action: [Agent Action Summary]  
 
Sources Used:  
1. [URL 1]  
2. [URL 2]  
...  

 
Sources: ✅ Trustable or ❌ Unverified  


Rules Referenced:  
- [Rule 1]  
- [Rule 2]  
...  


Data Analyzed:  
- key1: value1  
- key2: value2  
...  


Reason:  
[Short human-readable explanation in bullet points or paragraph]  
 

Status: ✅ Approved or ❌ Not Approved  


Think step-by-step:
- Read all fields from JSON input
- Validate each source for trustworthiness
- Cross-check rule references
- Summarize used fields
- Explain reasoning in plain English
- Decide final status: Approved or Not Approved

Please use the tool for above output with no change `convert_trust_report_to_json` to convert the above into JSON format.

give final output of `convert_trust_report_to_json` format ..
""",
    tools=[load_fi_mcp_json,convert_trust_report_to_json]
)