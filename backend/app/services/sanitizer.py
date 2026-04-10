SUSPICIOUS_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?previous\s+instructions",
    r"(?i)ignore\s+(all\s+)?above",
    r"(?i)you\s+are\s+now",
    r"(?i)new\s+instructions?:",
    r"(?i)system\s*:",
    r"(?i)assistant\s*:",
    r"(?i)forget\s+(everything|all|your)",
    r"(?i)disregard\s+(all|previous|above)",
    r"(?i)override\s+(previous|system|all)",
    r"(?i)pretend\s+you\s+are",
    r"(?i)act\s+as\s+(if|a|an)",
    r"(?i)do\s+not\s+follow",
    r"(?i)jailbreak",
]

def sanitize_code_input(code: str) -> tuple[str, list[str]]:
    """
    Scan code for prompt injection patterns.
    Returns (sanitized_code, list_of_warnings).

    Does NOT modify the code — flags suspicious patterns
    so the LLM prompt can include a warning, and the
    request can be logged for review.
    """