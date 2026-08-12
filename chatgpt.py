import json
import os
import re
from dotenv import load_dotenv
import logging
from openai import OpenAI
load_dotenv()
DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", os.getenv("OPENAI_MODEL", "gpt-4o"))
LIGHT_DEPLOYMENT = os.getenv(
    "AZURE_OPENAI_LIGHT_DEPLOYMENT",
    os.getenv("OPENAI_LIGHT_MODEL", "gpt-4o-mini"),
)
API_KEY = os.getenv("AZURE_OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
ENDPOINT = os.getenv(
    "AZURE_OPENAI_ENDPOINT",
    os.getenv("OPENAI_BASE_URL", ""),
)
logging.basicConfig(level=logging.INFO)


if ENDPOINT and not ENDPOINT.rstrip("/").endswith("/openai/v1"):
    ENDPOINT = f"{ENDPOINT.rstrip('/')}/openai/v1/"

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not API_KEY:
            raise RuntimeError("Set AZURE_OPENAI_API_KEY or OPENAI_API_KEY")
        if not ENDPOINT:
            raise RuntimeError("Set AZURE_OPENAI_ENDPOINT or OPENAI_BASE_URL")
        _client = OpenAI(api_key=API_KEY, base_url=ENDPOINT)
    return _client

SEARCH_QUERY_SYSTEM = """You are a search query generator for an academic paper search engine (CORE).

<task>
Convert the user's research question into a search query optimized for finding relevant academic papers.
</task>

<rules>
- Use grouping, AND and OR where appropriate to improve the accuracy
- Output ONLY the search query text — no explanations, labels, or quotation marks.
- Prioritize the most important concepts, remove generic terms.
- Keep the query under 80 words.
- Do not use search operators like site:, filetype:, or excessive boolean grouping.
</rules>"""

ANSWER_SYSTEM = """You are CORE-GPT, a research assistant that answers questions using only provided academic paper search results.

<task>
Write a concise, well-sourced answer to the user's question based solely on the search results provided.
</task>

<rules>
- Use ONLY information from the provided search results. Do not rely on outside knowledge.
- Try to connect the sources you are receiving to give a comprehensive and cohesive response,
- Avoid listing the various papers findings indipendently.
- Try to include all the sources if possible.
- If the search results do not contain enough information to answer, say so clearly.
- Write in a neutral, journalistic tone. Synthesize findings across sources; do not repeat text verbatim.
- Keep the answer under 160 words.
- Do not use filler phrases like "based on the provided search results", "in summary", or "overall".
- When different results refer to different entities with the same name, address each separately.
</rules>

<citation_format>
- Cite sources inline using [N] notation where N matches the source index (1-based).
- Only cite the most relevant sources that directly support each claim.
- Each source is provided as {"url": "...", "abstract": "...", "title": "..."}.
</citation_format>"""

COURSE_MATERIAL_SYSTEM = """You are CORE-GPT, a research assistant that creates undergraduate course reading lists from academic paper search results.

<task>
Create a structured course reading list for the given topic using only the provided search results.
</task>

<rules>
- Use ONLY information from the provided search results.
- If results are insufficient, say so clearly.
- Use a neutral, academic tone. Synthesize across sources without repeating text.
- Cite sources inline using [N] notation where N matches the source index (1-based).
- When different results refer to different entities with the same name, list them separately.
</rules>"""

GATE_SYSTEM = """You decide whether a user message should trigger an academic paper search on CORE.

<task>
Return exactly one word: SEARCH, DECLINE, FOLLOWUP.
</task>

<rules>
- SEARCH if the message is a research question, academic topic, or meaningful follow-up in a research conversation.
- DECLINE for greetings, chit-chat, off-topic requests (recipes, weather, jokes), or messages too vague to search.
- FOLLOWUP for questions inherent to the current search results.
- When conversation history shows an ongoing research discussion, lean toward SEARCH for short follow-ups.
- Output ONLY the word SEARCH or DECLINE.
</rules>"""


def _chat_completion(
    messages: list[dict],
    *,
    model: str | None = None,
    max_tokens: int = 4096,
    temperature: float = 0,
) -> str:
    response = _get_client().chat.completions.create(
        model=model or DEPLOYMENT,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content


def _normalize_query(text: str) -> str:
    text = text.replace("\n", " ").replace('"', " ")
    return re.sub(r"\s+", " ", text).strip()


def _format_context(messages: list[dict]) -> str:
    if not messages:
        return ""
    lines = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "").strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines)


def classify_query(message: str, messages: list[dict] | None = None) -> str:
    context = _format_context(messages or [])
    user_content = message
    if context:
        user_content = f"""<conversation_history>
{context}
</conversation_history>

<latest_message>
{message}
</latest_message>"""

    response = _chat_completion(
        [
            {"role": "system", "content": GATE_SYSTEM},
            {"role": "user", "content": user_content},
        ],
        model=LIGHT_DEPLOYMENT,
        max_tokens=8,
    )
    return response.strip().upper()


def generate_search_query(input_request: str, messages: list[dict] | None = None) -> str:
    context = _format_context(messages or [])
    user_content = input_request
    if context:
        user_content = f"""<conversation_history>
{context}
</conversation_history>

<latest_question>
{input_request}
</latest_question>"""

    prompt_messages = [
        {"role": "system", "content": SEARCH_QUERY_SYSTEM},
        {"role": "user", "content": user_content},
    ]
    return _normalize_query(_chat_completion(prompt_messages))


def generate_answer(
    input_request: str,
    search_results: list,
    messages: list[dict] | None = None,
) -> str:
    context = _format_context(messages or [])
    question_block = input_request
    if context:
        question_block = f"""<conversation_history>
{context}
</conversation_history>

<latest_question>
{input_request}
</latest_question>"""

    prompt_messages = [
        {"role": "system", "content": ANSWER_SYSTEM},
        {
            "role": "user",
            "content": f"""<question>
{question_block}
</question>

<search_results>
{json.dumps(search_results, indent=2)}
</search_results>""",
        },
    ]
    return _chat_completion(prompt_messages)


def generate_course_material(input_request: str, search_results: list) -> str:
    messages = [
        {"role": "system", "content": COURSE_MATERIAL_SYSTEM},
        {
            "role": "user",
            "content": f"""<topic>
{input_request}
</topic>

<search_results>
{json.dumps(search_results, indent=2)}
</search_results>""",
        },
    ]
    return _chat_completion(messages)
