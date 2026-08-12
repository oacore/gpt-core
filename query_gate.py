import re
from dataclasses import dataclass
from enum import Enum


class GateOutcome(Enum):
    SEARCH = "search"
    DECLINE = "decline"
    UNDECIDED = "undecided"
    FOLLOWUP = "followup"


@dataclass
class GateResult:
    outcome: GateOutcome
    reason: str
    source: str  # heuristic | model


GREETINGS = {
    "hi", "hello", "hey", "thanks", "thank you", "bye", "goodbye",
    "ok", "okay", "yes", "no", "cool", "nice", "great",
}

QUESTION_STARTERS = (
    "what", "why", "how", "when", "where", "who", "which",
    "is", "are", "was", "were", "does", "do", "did", "can", "could",
    "should", "would", "has", "have", "will",
)

RESEARCH_TERMS = {
    "research", "study", "studies", "paper", "papers", "article", "articles",
    "journal", "abstract", "literature", "meta-analysis", "systematic review",
    "evidence", "findings", "hypothesis", "methodology", "bibliometric",
    "peer-reviewed", "publication", "dataset", "clinical trial", "survey",
    "correlation", "causation", "impact", "effect", "effects", "analysis",
    "theory", "framework", "empirical", "scholarly", "academic", "scientific",
}

OFF_TOPIC_TERMS = {
    "recipe", "weather", "joke", "poem", "song lyrics", "football score",
    "movie review", "restaurant", "pizza", "bitcoin price",
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _word_count(text: str) -> int:
    return len(re.findall(r"[a-zA-Z']+", text))


def _alpha_ratio(text: str) -> float:
    if not text:
        return 0.0
    alpha = sum(c.isalpha() for c in text)
    return alpha / len(text)


def _has_research_signal(text: str) -> bool:
    words = set(re.findall(r"[a-zA-Z'-]+", text.lower()))
    if words & RESEARCH_TERMS:
        return True
    if "?" in text:
        return True
    first = words and next(iter(text.lower().split()), "")
    return first in QUESTION_STARTERS


def _is_greeting_only(text: str) -> bool:
    cleaned = re.sub(r"[^\w\s]", "", _normalize(text))
    return cleaned in GREETINGS


def _is_off_topic(text: str) -> bool:
    normalized = _normalize(text)
    return any(term in normalized for term in OFF_TOPIC_TERMS)


def _context_suggests_research(messages: list[dict]) -> bool:
    prior = " ".join(
        m.get("content", "") for m in messages[:-1]
        if m.get("role") in ("user", "assistant")
    ).lower()
    return bool(set(re.findall(r"[a-zA-Z'-]+", prior)) & RESEARCH_TERMS)


def heuristic_gate(message: str, messages: list[dict] | None = None) -> GateResult:
    messages = messages or []
    text = message.strip()

    if len(text) < 2:
        return GateResult(GateOutcome.DECLINE, "Message is too short.", "heuristic")

    if _alpha_ratio(text) < 0.5:
        return GateResult(GateOutcome.DECLINE, "Message does not look like a text query.", "heuristic")

    if _is_greeting_only(text):
        return GateResult(GateOutcome.DECLINE, "Greeting detected; no research question.", "heuristic")

    if _is_off_topic(text):
        return GateResult(GateOutcome.DECLINE, "Query appears off-topic for academic search.", "heuristic")

    if _word_count(text) >= 8 and _has_research_signal(text):
        return GateResult(GateOutcome.SEARCH, "Substantive research-style question.", "heuristic")

    if "?" in text and _word_count(text) >= 3:
        return GateResult(GateOutcome.SEARCH, "Direct question detected.", "heuristic")

    if _word_count(text) <= 2 and not _context_suggests_research(messages):
        return GateResult(GateOutcome.DECLINE, "Too brief to form a research query.", "heuristic")

    if _context_suggests_research(messages) and _word_count(text) >= 2:
        return GateResult(GateOutcome.FOLLOWUP, "Follow-up in an active research conversation.", "heuristic")

    first_word = _normalize(text).split()[0] if text.split() else ""
    if first_word in QUESTION_STARTERS and _word_count(text) >= 4:
        return GateResult(GateOutcome.SEARCH, "Question-shaped query with enough detail.", "heuristic")

    return GateResult(GateOutcome.UNDECIDED, "Query intent is unclear.", "heuristic")
