from chatgpt import classify_query, generate_answer, generate_search_query
from core import search_works
from query_gate import GateOutcome, GateResult, heuristic_gate
import re
from flask import Flask, jsonify, render_template, request
import urllib.parse
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

app = Flask(__name__, template_folder="templates", static_folder="static")

DECLINE_MESSAGE = (
    "I can only help with research questions about academic papers in CORE. "
    "Try asking something like: \"What are the limitations of bibliometrics?\" "
    "or \"Are COVID vaccines effective?\""
)


def evaluate_gate(message: str, messages: list[dict] | None = None) -> GateResult:
    result = heuristic_gate(message, messages)
    if result.outcome != GateOutcome.UNDECIDED:
        return result

    chat_type = classify_query(message, messages)
    if "SEARCH" in chat_type:
        return GateResult(GateOutcome.SEARCH, "Lightweight model approved search.", "model")
    elif "FOLLOW" in chat_type:
        return GateResult(GateOutcome.FOLLOWUP, "Lightweight model approved followup.", "model")
    return GateResult(GateOutcome.DECLINE, "Lightweight model declined search.", "model")


def replace_url_to_link(value):
    # Replace url to link
    urls = re.compile(r"((https?):((//)|(\\\\))+[\w\d:#@%/;$()~_?\+-=\\\.&]*)", re.MULTILINE | re.UNICODE)
    value = urls.sub(r'<a href="\1" target="_blank">\1</a>', value)
    # Replace email to mailto
    urls = re.compile(r"([\w\-\.]+@(\w[\w\-]+\.)+[\w\-]+)", re.MULTILINE | re.UNICODE)
    value = urls.sub(r'<a href="mailto:\1">\1</a>', value)
    return value


def clearup_response(answer, search_results):
    cleared_answer = re.sub(r"\[\$(\d+)", r"[\1]", answer)
    url_matched = re.findall(r"\[[url:]?(https://core.ac.uk/works/\d+)\]", answer)
    logging.info(url_matched)
    if url_matched:
        count = 1
        for result in search_results:
            logging.info(result)
            if result['url'] in url_matched:
                cleared_answer = cleared_answer.replace(f"[{result['url']}]", f"[{count}]")
                count += 1
    return cleared_answer


def render_response(answer, search_results, titles, search_query):
    i = 0
    references = "<ol>"
    search_query_for_web = urllib.parse.quote(f"{search_query}")
    logging.info(search_results)
    for a in search_results:
        references += f" <li> {a['url']} - {titles[i]}</li>"
        i += 1
    references += "</ol>"
    core_link = f"<br><a href='https://core.ac.uk/search?q={search_query_for_web}'>See more in CORE</a>"
    return replace_url_to_link(clearup_response(answer, search_results)) + replace_url_to_link(references) + core_link


def render_json_response(answer, search_results, titles, search_query):
    i = 1
    references = {}
    search_query_for_web = urllib.parse.quote(f"{search_query}")
    logging.info(len(search_results))
    for a in search_results:
        references[i] = a
        i += 1
    core_link = f"https://core.ac.uk/search?q={search_query_for_web}"
    answer = clearup_response(answer, search_results)
    logging.info(len(answer), len(references))
    logging.info("render_json_response")
    return {
        "answer": answer,
        "results": references,
        "see_more": core_link
    }


def run(input_request, messages: list[dict] | None = None):
    search_query = generate_search_query(input_request, messages)
    logging.info(f"Searching core with: {search_query}")

    titles, search_results = search_works(search_query)

    if len(search_results) == 0:
        return "Not enough CORE results"

    answer = generate_answer(input_request, search_results, messages)

    return render_response(answer, search_results, titles, search_query)


def run_json(input_request: str, messages: list[dict] | None = None) -> dict:
    search_query = generate_search_query(input_request, messages)
    logging.info(f"Searching core with: {search_query}")

    titles, search_results = search_works(search_query)
    logging.info(len(titles), len(search_results))
    if len(search_results) == 0:
        return {
            "answer": "Not enough CORE results for this query.",
            "results": {},
            "see_more": None,
            "search_query": search_query,
        }

    answer = generate_answer(input_request, search_results, messages)
    payload = render_json_response(answer, search_results, titles, search_query)
    logging.info("run_json")
    payload["search_query"] = search_query
    return payload


def followup_json(input_request: str, messages: list[dict] | None = None) -> dict:

    answer = generate_answer(input_request, [], messages)
    payload = render_json_response(answer, [], [], [])
    payload["search_query"] = messages[-1]["content"]
    return payload

def _normalize_messages(raw_messages: list | None) -> list[dict]:
    if not raw_messages:
        return []
    normalized = []
    for item in raw_messages:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if role in ("user", "assistant") and isinstance(content, str) and content.strip():
            normalized.append({"role": role, "content": content.strip()})
    return normalized


def chat(input_request: str, messages: list[dict] | None = None) -> dict:
    messages = _normalize_messages(messages)
    gate = evaluate_gate(input_request, messages)
    updated_messages = messages + [{"role": "user", "content": input_request}]

    if gate.outcome == GateOutcome.DECLINE:
        updated_messages.append({"role": "assistant", "content": DECLINE_MESSAGE})
        return {
            "action": "decline",
            "gate": gate.source,
            "reason": gate.reason,
            "message": DECLINE_MESSAGE,
            "messages": updated_messages,
        }

    if gate.outcome == GateOutcome.FOLLOWUP:
        result = followup_json(input_request, messages)
        updated_messages.append({"role": "assistant", "content": input_request})
        return {
            "action": "search",
            "gate": gate.source,
            "reason": gate.reason,
            "message": result["answer"],
            "answer": result["answer"],
            "results": result["results"],
            "see_more": result["see_more"],
            "search_query": result["search_query"],
            "messages": updated_messages,
        }

    result = run_json(input_request, messages)
    updated_messages.append({"role": "assistant", "content": result["answer"]})
    return {
        "action": "search",
        "gate": gate.source,
        "reason": gate.reason,
        "message": result["answer"],
        "answer": result["answer"],
        "results": result["results"],
        "see_more": result["see_more"],
        "search_query": result["search_query"],
        "messages": updated_messages,
    }


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/ask")
def ask():
    q = request.args.get("q")
    answer = run(q)
    return answer


@app.route("/chat", methods=["POST"])
def chat_endpoint():
    body = request.get_json(silent=True) or {}
    message = body.get("message") or body.get("q")
    if not message or not str(message).strip():
        return jsonify({"error": "message is required"}), 400

    messages = _normalize_messages(body.get("messages"))
    return jsonify(chat(str(message).strip(), messages))


if __name__ == "__main__":
    if os.getenv("debug"):
        app.run(debug=True)
    else:
        from waitress import serve

        serve(app, host="0.0.0.0", port=5005)
