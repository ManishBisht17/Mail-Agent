import base64
import email as email_lib
from langchain.tools import tool
from gmail_auth import get_gmail_service

service = get_gmail_service()

@tool
def read_emails(max_results: int = 5) -> str:
    """Reads the latest unread emails from Gmail inbox."""
    results = service.users().messages().list(
        userId="me", labelIds=["INBOX", "UNREAD"], maxResults=max_results
    ).execute()

    messages = results.get("messages", [])
    if not messages:
        return "No unread emails found."

    summaries = []
    for msg in messages:
        data = service.users().messages().get(
            userId="me", id=msg["id"], format="full"
        ).execute()

        headers = {h["name"]: h["value"] for h in data["payload"]["headers"]}
        subject = headers.get("Subject", "No Subject")
        sender  = headers.get("From", "Unknown")
        snippet = data.get("snippet", "")
        summaries.append(f"ID: {msg['id']}\nFrom: {sender}\nSubject: {subject}\nSnippet: {snippet}\n")

    return "\n---\n".join(summaries)


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Sends an email. Args: to (recipient email), subject, body."""
    message = email_lib.message.EmailMessage()
    message["To"]      = to
    message["Subject"] = subject
    message.set_content(body)

    encoded = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(
        userId="me", body={"raw": encoded}
    ).execute()
    return f"Email sent to {to} with subject '{subject}'."


@tool
def label_email(message_id: str, label_name: str) -> str:
    """Adds a label to an email. Creates the label if it doesn't exist."""
    existing = service.users().labels().list(userId="me").execute().get("labels", [])
    label_id = next((l["id"] for l in existing if l["name"] == label_name), None)

    if not label_id:
        new_label = service.users().labels().create(
            userId="me", body={"name": label_name}
        ).execute()
        label_id = new_label["id"]

    service.users().messages().modify(
        userId="me", id=message_id, body={"addLabelIds": [label_id]}
    ).execute()
    return f"Label '{label_name}' added to message {message_id}."


@tool
def summarize_email(message_id: str) -> str:
    """Gets the full body of a specific email by its ID."""
    data = service.users().messages().get(
        userId="me", id=message_id, format="full"
    ).execute()

    parts = data["payload"].get("parts", [])
    body = ""
    for part in parts:
        if part["mimeType"] == "text/plain":
            body = base64.urlsafe_b64decode(part["body"]["data"]).decode()
            break

    headers = {h["name"]: h["value"] for h in data["payload"]["headers"]}
    return f"From: {headers.get('From')}\nSubject: {headers.get('Subject')}\n\nBody:\n{body[:2000]}"