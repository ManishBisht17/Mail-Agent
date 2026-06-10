import json
import os
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

MEMORY_FILE = "chat_history.json"
MAX_MESSAGES = 41  # 1 system + 40 recent messages


def trim_messages(messages):
    """Keep system prompt and recent messages, never start mid tool-call."""
    if len(messages) <= MAX_MESSAGES:
        return messages

    trimmed = [messages[0]] + messages[-(MAX_MESSAGES - 1):]
    start = 1
    while start < len(trimmed) and not isinstance(trimmed[start], HumanMessage):
        start += 1
    return [trimmed[0]] + trimmed[start:] if start < len(trimmed) else [trimmed[0]]


def save_messages(messages):
    """Save messages to disk."""
    messages = trim_messages(messages)
    serialized = []
    for m in messages:
        if isinstance(m, SystemMessage):
            serialized.append({"type": "system", "content": m.content})
        elif isinstance(m, HumanMessage):
            serialized.append({"type": "human", "content": m.content})
        elif isinstance(m, AIMessage):
            entry = {"type": "ai", "content": m.content or ""}
            if m.tool_calls:
                entry["tool_calls"] = m.tool_calls
            serialized.append(entry)
        elif isinstance(m, ToolMessage):
            serialized.append({
                "type": "tool",
                "content": m.content,
                "tool_call_id": m.tool_call_id,
            })
    with open(MEMORY_FILE, "w") as f:
        json.dump(serialized, f, indent=2)


def load_messages():
    """Load messages from disk."""
    if not os.path.exists(MEMORY_FILE):
        return []
    with open(MEMORY_FILE, "r") as f:
        data = json.load(f)
    messages = []
    for m in data:
        if m["type"] == "system":
            messages.append(SystemMessage(m["content"]))
        elif m["type"] == "human":
            messages.append(HumanMessage(m["content"]))
        elif m["type"] == "ai":
            kwargs = {"content": m.get("content", "")}
            if m.get("tool_calls"):
                kwargs["tool_calls"] = m["tool_calls"]
            messages.append(AIMessage(**kwargs))
        elif m["type"] == "tool":
            messages.append(ToolMessage(m["content"], tool_call_id=m["tool_call_id"]))
    return trim_messages(messages)
