import os
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from tools import read_emails, send_email, label_email, summarize_email
from memory import save_messages, load_messages

load_dotenv()

tools = [read_emails, send_email, label_email, summarize_email]

tools_map = {
    "read_emails": read_emails,
    "send_email": send_email,
    "label_email": label_email,
    "summarize_email": summarize_email,
}

SYSTEM_PROMPT = (
    "You are a helpful Gmail assistant. Use tools to help the user manage their email. "
    "Be concise and friendly. When listing emails, format them clearly."
)

messages = load_messages()
if not messages:
    messages = [SystemMessage(SYSTEM_PROMPT)]

_llm_with_tools = None


def _get_llm():
    global _llm_with_tools
    if _llm_with_tools is None:
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError(
                "OPENAI_API_KEY not set. Add it to your .env file to chat with the agent."
            )
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        _llm_with_tools = llm.bind_tools(tools)
    return _llm_with_tools


def reset_conversation():
    global messages
    messages = [SystemMessage(SYSTEM_PROMPT)]
    save_messages(messages)


def run_agent(query: str) -> dict:
    """Run the agent and return structured response with tool usage info."""
    llm_with_tools = _get_llm()
    messages.append(HumanMessage(query))
    tools_used = []

    while True:
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            save_messages(messages)
            return {"content": response.content, "tools_used": tools_used}

        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tools_used.append({"name": tool_name, "args": tool_args})
            result = tools_map[tool_name].invoke(tool_args)
            messages.append(ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"],
            ))


if __name__ == "__main__":
    print("Email Agent ready! Type 'exit' to quit. Type 'clear' to reset memory.\n")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        if user_input.lower() == "clear":
            reset_conversation()
            print("Memory cleared!\n")
            continue
        result = run_agent(user_input)
        print(f"\nAgent: {result['content']}\n")
