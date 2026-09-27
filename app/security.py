import re

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous instructions",
    r"reveal\s+(the\s+)?system prompt",
    r"show\s+me\s+(all\s+)?(employee|user).{0,30}(phone|email|id|password)",
    r"disregard\s+your\s+instructions",
    r"忽略.*指令",
    r"显示.*系统提示",
]
# These are intentionally lightweight MVP rules. A production system would add
# stronger classifiers, authorization, audit controls, and red-team coverage.

PII_PATTERNS = [
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "[EMAIL_REDACTED]"),
    (re.compile(r"\b(?:\+?\d[\d ()-]{7,}\d)\b"), "[PHONE_REDACTED]"),
    (re.compile(r"\b\d{6,20}\b"), "[ID_REDACTED]"),
]

def injection_suspected(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered, flags=re.IGNORECASE) for pattern in INJECTION_PATTERNS)

def redact_pii(text: str) -> str:
    for pattern, replacement in PII_PATTERNS:
        text = pattern.sub(replacement, text)
    return text

def sanitize_context(text: str) -> str:
    """Remove obvious instructions and PII from untrusted indexed content."""
    lines = []
    for line in text.splitlines():
        if injection_suspected(line):
            lines.append("[UNTRUSTED INSTRUCTION REMOVED]")
        else:
            lines.append(redact_pii(line))
    return "\n".join(lines)
