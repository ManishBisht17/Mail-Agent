import ssl
ssl._create_default_https_context = ssl._create_unverified_context

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from tools import read_emails, send_email, label_email, summarize_email
import json

load_dotenv()

llm = ChatOpenAI(model="gpt-4o", temperature=0)
tools = [read_emails, send_email, label_email, summarize_email]
llm_with_tools = llm.bind_tools(tools)

tools_map = {
    "read_emails": read_emails,
    "send_email": send_email,
    "label_email": label_email,
    "summarize_email": summarize_email,
}

system = SystemMessage("You are a helpful Gmail assistant. Use tools to help the user manage their email.")

def run_agent(query: str):
    messages = [system, HumanMessage(query)]
    
    while True:
        response = llm_with_tools.invoke(messages)
        messages.append(response)
        
        if not response.tool_calls:
            return response.content
        
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            print(f"\n[Using tool: {tool_name} with {tool_args}]")
            
            result = tools_map[tool_name].invoke(tool_args)
            messages.append(ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"]
            ))

if __name__ == "__main__":
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        response = run_agent(user_input)
        print(f"\nAgent: {response}")