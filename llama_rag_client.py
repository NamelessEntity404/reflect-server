"""
Connects to the notes MCP server, retrieves relevant notes for a query,
and generates a response with Llama 3 (via Ollama) using a system prompt
that enforces the reasoning discipline this was built around: check
specifics before committing to a frame, pair credibility critiques with
independent grounding, flag genetic-fallacy risk, don't oversell
institutional remedies.

Install:
    pip install mcp ollama

Before running:
    ollama pull llama3
    ollama serve            # usually already running in the background

In one terminal:
    python notes_mcp_server.py

In another terminal:
    python llama_rag_client.py
"""

import asyncio
import json
import time
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import ollama

TRACE_LOG_PATH = "trace_log.jsonl"


def log_trace(query: str, notes_context: str, answer: str) -> None:
    """Append a structured record of this interaction for later audit."""
    record = {
        "timestamp": time.time(),
        "query": query,
        "retrieved_notes": notes_context,
        "response": answer,
    }
    with open(TRACE_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

SYSTEM_PROMPT = """\
Before committing to any psychological or legal framework for a stalking or \
abuse-related case, explicitly check it against the specific facts stated, \
including who initiated any separation. Do not present legal or institutional \
remedies (courts, police, restraining orders) without simultaneously noting \
documented failure rates and the risk that the process itself causes \
additional harm. When citing any source whose personal credibility is \
contested, state the underlying claim's independent evidentiary basis in the \
same response, not as a follow-up -- never let a credibility question about a \
messenger stand unaccompanied by the claim's separate support. Flag explicitly \
when reasoning risks the genetic fallacy (dismissing a true claim because of \
who is making it). Do not finalize a typology, mechanism, or diagnosis-style \
explanation on the first pass if disconfirming case-specific facts have not \
yet been actively solicited. Ground claims in the retrieved notes provided \
below where relevant, and say plainly when the notes do not cover something \
rather than guessing.
"""

SERVER_PARAMS = StdioServerParameters(
    command="python",
    args=["notes_mcp_server.py"],
)


async def get_relevant_notes(query: str) -> str:
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "search_notes", {"query": query, "top_k": 5}
            )
            return result.content[0].text if result.content else ""


def ask_llama(query: str, notes_context: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Relevant notes:\n{notes_context}\n\nQuestion: {query}",
        },
    ]
    response = ollama.chat(model="llama3", messages=messages)
    return response["message"]["content"]


async def main():
    print("Type a question (Ctrl+C to exit).")
    while True:
        query = input("\nAsk: ")
        notes_context = await get_relevant_notes(query)
        answer = ask_llama(query, notes_context)
        log_trace(query, notes_context, answer)
        print("\n" + answer)


if __name__ == "__main__":
    asyncio.run(main())
