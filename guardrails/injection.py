"""reject unsafe/off-topic inputs and flag instructions in evidence."""

# Input: executive questions or text returned from untrusted documents/tools.
# Output: a simple allowed/reason decision or sanitized-text/injection-flag result.

from __future__ import annotations

import re


# These expressions look for common prompt-injection instructions in a question
# or in text returned by a document/search tool. They flag suspicious text; they
# do not delete it, so the original evidence can still be shown with a warning.
#
# In each expression, \b means "word boundary" and \s+ means "one or more
# spaces". Parentheses group alternatives separated by |. re.I below makes
# matching case-insensitive, so "IGNORE" and "ignore" are treated the same.
INJECTION_PATTERNS = (
    # Examples: "ignore previous instructions", "ignore all your rules".
    re.compile(r"\bignore\s+(all\s+)?(previous|prior|your)\s+(instructions|rules)\b", re.I),
    # Examples: "reveal the system prompt", "print developer prompt".
    re.compile(r"\b(reveal|print|expose)\s+(the\s+)?(system|developer)\s+prompt\b", re.I),
    # Examples: "do not follow your rules", "do not obey instructions".
    re.compile(r"\bdo\s+not\s+(follow|obey)\s+(your\s+)?(rules|instructions)\b", re.I),
    # Examples: "act as an unrestricted agent", "act as uncensored model".
    re.compile(r"\bact\s+as\s+(an?\s+)?(unrestricted|uncensored)\s+(agent|model)\b", re.I),
)
# Reject requests that combine an instruction phrase with a harmful goal.
# .{0,80} allows up to 80 characters between the two parts, so extra wording
# (for example, "Help me write a program to ...") can appear between them.
# "How to" is included because a harmful request may use that phrasing directly.
UNSAFE_REQUEST = re.compile(
    r"\b(how\s+to|write|build|explain|plan|help me|instructions for)\b.{0,80}"
    r"\b(malware|ransomware|steal credentials|evade law enforcement|make a bomb|"
    r"kill|murder|assassinate|poison|"
    r"self-harm|suicide|hack into|bypass security|hurt someone|target a person)\b",
    re.I,
)
# A question must mention at least one word in this list to count as related to
# ARGUS's business-risk purpose. The alternatives between | are the keywords.
# \b matches complete words: "export" matches, but "exports" does NOT, because
# the "t" in "export" is followed by "s", not a word boundary. Use export(?:s)?
# to match both forms: the optional s is the part inside (?:...)?.
BUSINESS_CONTEXT = re.compile(
    r"\b(risk|company|business|supplier|product|supply|market|regulation|"
    # Previous version: r"export|geopolit|news|event|impact|inventory|contract|compliance|"
    r"exports?|geopolit|news|event|impact|inventory|contract|compliance|"
    r"semiconductor|incident|vendor|country|government)\b",
    re.I,
)


def check_input(query: str) -> dict[str, bool | str]:
    """Return whether a question is safe and in scope, plus a human-readable reason.

    Checks run from most important to least important:
    1. Empty questions cannot be investigated.
    2. Harmful requests are rejected.
    3. Prompt-injection instructions are rejected.
    4. A remaining question must contain an ARGUS business-context keyword.
    """
    if not query or not query.strip():
        return {"allowed": False, "reason": "Enter a non-empty business intelligence question."}
    if UNSAFE_REQUEST.search(query):
        return {"allowed": False, "reason": "The request asks for harmful or illicit instructions."}
    if any(pattern.search(query) for pattern in INJECTION_PATTERNS):
        return {"allowed": False, "reason": "The request contains an instruction override attempt."}
    if not BUSINESS_CONTEXT.search(query):
        return {"allowed": False, "reason": "ARGUS accepts company, supplier, market, regulatory, and geopolitical risk questions."}
    return {"allowed": True, "reason": "Input is within the business intelligence scope."}


def sanitize_retrieved_text(text: str) -> dict[str, str | bool]:
    """Keep evidence text intact, but flag instructions embedded in that evidence.

    Retrieved documents are evidence, not commands for ARGUS to follow. Keeping
    the original words preserves citations while the flag tells later steps to
    treat suspicious content as untrusted.
    """
    # any(...) is true when at least one injection expression matches the text.
    flagged = any(pattern.search(text) for pattern in INJECTION_PATTERNS)
    return {"text": text, "flagged": flagged}
