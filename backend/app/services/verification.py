"""
Line-number verification for LLM-returned CodeIssues.

The LLM occasionally hallucinates line numbers — it says "line 42 has a SQL
injection" when line 42 is an import statement. verify_issues() cross-checks
every issue's line against the actual submitted code and stamps each with a
`verified` boolean that the frontend can surface to the user.
"""

import re

from app.schemas.review import CodeIssue

# Short tokens and universal programming keywords that appear on almost every
# line and are therefore useless for content-matching.
_STOP_TOKENS = {
    "and", "are", "as", "bool", "class", "const", "def", "dict", "elif",
    "else", "false", "for", "from", "function", "have", "if", "import",
    "in", "int", "is", "let", "list", "new", "none", "not", "null", "or",
    "pass", "private", "public", "return", "self", "static", "str", "that",
    "the", "this", "true", "type", "var", "void", "with",
}


def verify_issues(code: str, issues: list[CodeIssue]) -> list[CodeIssue]:
    """
    Cross-check LLM-returned line numbers against actual code.
    Returns issues with a `verified` field set.
    """
    lines = code.strip().split("\n")
    num_lines = len(lines)

    verified_issues = []
    for issue in issues:
        if issue.line is None:
            # General issue with no line reference — nothing to verify
            issue.verified = True
        elif issue.line < 1 or issue.line > num_lines:
            # Line number outside the submitted code — hallucinated
            issue.verified = False
            issue.original_line = issue.line
            issue.line = None
        else:
            # Line exists — check whether the issue description is plausibly
            # related to what actually appears on that line
            actual_line = lines[issue.line - 1]
            issue.verified = _content_matches(actual_line, issue)

        verified_issues.append(issue)

    return verified_issues


def _content_matches(actual_line: str, issue: CodeIssue) -> bool:
    """
    Heuristic: does the actual source line look related to the issue?

    Strategy:
    1. Extract meaningful identifier tokens from the code line.
    2. Check whether any of those tokens appear in the issue's description
       or suggestion text.

    A match means "plausibly related", not "definitely correct". A non-match
    means the LLM described something that has no lexical relationship to the
    line it cited — a strong signal of hallucination.

    Edge cases:
    - Blank lines always return False (nothing to match).
    - Lines with only symbols/numbers return True (benefit of the doubt —
      e.g., `x = 0` legitimately cited for an off-by-one bug).
    - Comment markers are stripped before tokenising so comment text is
      used for matching.
    """
    stripped = actual_line.strip()

    # Blank line — the LLM can't have a valid reason to cite it
    if not stripped:
        return False

    # Strip leading comment markers to expose the comment text
    for marker in ("#", "//", "/*", "* ", "*"):
        if stripped.startswith(marker):
            stripped = stripped[len(marker):].strip()
            break

    # Extract word-like tokens (identifiers): must start with a letter or
    # underscore so we skip pure numbers and operator sequences
    line_tokens = {
        t.lower()
        for t in re.findall(r'\b[a-zA-Z_]\w*\b', stripped)
        if len(t) >= 3 and t.lower() not in _STOP_TOKENS
    }

    if not line_tokens:
        # e.g. `x = 0`, `{`, `];` — only symbols/short names, can't verify
        return True

    issue_text = (issue.description + " " + issue.suggestion).lower()
    return any(token in issue_text for token in line_tokens)
