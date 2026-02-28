"""
LLM Service — the heart of CodeLens.

Supports MOCK_LLM=true mode for free testing without OpenAI API calls.
Set MOCK_LLM=true in your .env file to enable mock mode.
"""

from app.config import settings
from app.schemas.review import ReviewResult, CodeIssue
from app.services.cache import get_cached, set_cached, make_cache_key


# ============================================================
# MOCK SERVICE — realistic fake responses for free testing
# ============================================================

class MockLLMService:
    """Returns realistic fake responses without calling OpenAI."""

    async def review_code(self, code: str, language: str) -> tuple[ReviewResult, bool]:
        cache_key = make_cache_key("review", code, language)
        cached = await get_cached(cache_key)
        if cached:
            return ReviewResult(**cached), True

        lines = code.strip().split("\n")
        issues = []

        for i, line in enumerate(lines, 1):
            # Security issues
            if "eval(" in line or "exec(" in line:
                issues.append(CodeIssue(
                    line=i, severity="critical", category="security",
                    description="Use of eval()/exec() allows arbitrary code execution and is a major security risk",
                    suggestion="Use ast.literal_eval() for safe evaluation or refactor to avoid dynamic code execution entirely",
                ))
            if "os.system" in line:
                issues.append(CodeIssue(
                    line=i, severity="critical", category="security",
                    description="os.system() executes shell commands with potential command injection vulnerability",
                    suggestion="Use subprocess.run() with a list of arguments and shell=False instead of string interpolation",
                ))
            if "subprocess" in line and "shell=True" in line:
                issues.append(CodeIssue(
                    line=i, severity="critical", category="security",
                    description="subprocess with shell=True is vulnerable to shell injection attacks",
                    suggestion="Pass command as a list with shell=False: subprocess.run(['cmd', 'arg1', 'arg2'])",
                ))
            if "SELECT" in line and ("+" in line or "format" in line or "f'" in line or 'f"' in line):
                issues.append(CodeIssue(
                    line=i, severity="critical", category="security",
                    description="SQL query built with string concatenation/formatting — SQL injection vulnerability",
                    suggestion="Use parameterized queries with placeholders: cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
                ))
            if "password" in line.lower() and ("=" in line) and ("hash" not in line.lower()) and ("environ" not in line.lower()):
                issues.append(CodeIssue(
                    line=i, severity="warning", category="security",
                    description="Possible hardcoded or plaintext password detected",
                    suggestion="Use environment variables or a secrets manager for sensitive credentials",
                ))

            # Bug issues
            if "except:" in line and "Exception" not in line:
                issues.append(CodeIssue(
                    line=i, severity="warning", category="bug",
                    description="Bare except clause catches all exceptions including SystemExit and KeyboardInterrupt",
                    suggestion="Use 'except Exception:' or catch specific exception types",
                ))
            if "== None" in line or "!= None" in line:
                issues.append(CodeIssue(
                    line=i, severity="info", category="style",
                    description="Use 'is None' / 'is not None' instead of '== None' / '!= None'",
                    suggestion="Replace with 'is None' or 'is not None' for proper identity comparison",
                ))

            # Performance issues
            if "import *" in line:
                issues.append(CodeIssue(
                    line=i, severity="warning", category="performance",
                    description="Wildcard import loads all module symbols into namespace, increasing memory usage",
                    suggestion="Import only the specific names you need: 'from module import func1, func2'",
                ))
            if ".append(" in line and "for " in code and line.strip().startswith("for ") is False:
                # Heuristic: appending inside a loop pattern
                pass  # skip noisy false positives

            # Style issues
            if "TODO" in line or "FIXME" in line or "HACK" in line:
                issues.append(CodeIssue(
                    line=i, severity="info", category="style",
                    description="Unresolved comment marker found",
                    suggestion="Address or remove this marker before production deployment",
                ))
            if len(line) > 100:
                issues.append(CodeIssue(
                    line=i, severity="info", category="style",
                    description="Line exceeds 100 characters — reduces readability",
                    suggestion="Break this line into multiple lines or extract into a variable",
                ))

        # Add general suggestions if we found very few issues
        num_lines = len(lines)
        has_docstring = '"""' in code or "'''" in code or "/**" in code
        has_type_hints = "->" in code or ": str" in code or ": int" in code

        if not has_docstring and num_lines > 5:
            issues.append(CodeIssue(
                line=None, severity="info", category="style",
                description="No docstrings found — functions and classes should be documented",
                suggestion="Add docstrings to describe purpose, parameters, and return values",
            ))

        if language == "python" and not has_type_hints and num_lines > 3:
            issues.append(CodeIssue(
                line=None, severity="info", category="style",
                description="No type hints found in function signatures",
                suggestion="Add type hints for better IDE support and code documentation: def func(x: int) -> str:",
            ))

        # Calculate score
        critical_count = sum(1 for i in issues if i.severity == "critical")
        warning_count = sum(1 for i in issues if i.severity == "warning")
        info_count = sum(1 for i in issues if i.severity == "info")
        score = max(1, min(10, 10 - (critical_count * 3) - (warning_count * 1) - (info_count * 0)))

        # Build summary
        if critical_count > 0:
            summary = (
                f"Found {critical_count} critical issue{'s' if critical_count > 1 else ''} requiring immediate attention. "
                f"The code has significant security or reliability concerns that should be addressed before deployment."
            )
        elif warning_count > 0:
            summary = (
                f"Generally solid code with {warning_count} warning{'s' if warning_count > 1 else ''} worth addressing. "
                f"No critical issues found, but some improvements would make this more robust and maintainable."
            )
        else:
            summary = (
                "Clean, well-structured code with no major issues detected. "
                "Minor style suggestions are included for further polish."
            )

        result = ReviewResult(summary=summary, issues=issues, score=score)
        await set_cached(cache_key, result.model_dump(), ttl=3600)
        return result, False

    async def explain_code(self, code: str, language: str) -> tuple[str, bool]:
        cache_key = make_cache_key("explain", code, language)
        cached = await get_cached(cache_key)
        if cached:
            return cached["explanation"], True

        lines = code.strip().split("\n")
        num_lines = len(lines)

        # Detect code patterns for a smarter explanation
        has_functions = any(("def " in ln or "function " in ln or "func " in ln) for ln in lines)
        has_classes = any(("class " in ln) for ln in lines)
        has_loops = any(("for " in ln or "while " in ln) for ln in lines)
        has_imports = any(("import " in ln or "require(" in ln or "#include" in ln) for ln in lines)
        has_conditionals = any(("if " in ln or "else" in ln or "elif" in ln or "switch" in ln) for ln in lines)
        has_return = any(("return " in ln) for ln in lines)
        has_print = any(("print(" in ln or "console.log" in ln or "fmt.Print" in ln) for ln in lines)
        has_try = any(("try:" in ln or "try {" in ln) for ln in lines)

        # Extract function/class names
        func_names = []
        class_names = []
        for ln in lines:
            stripped = ln.strip()
            if stripped.startswith("def ") and "(" in stripped:
                func_names.append(stripped.split("(")[0].replace("def ", ""))
            elif stripped.startswith("class ") and (":" in stripped or "{" in stripped):
                class_names.append(stripped.split(":")[0].split("(")[0].replace("class ", "").strip())
            elif stripped.startswith("function ") and "(" in stripped:
                func_names.append(stripped.split("(")[0].replace("function ", ""))

        explanation = "## Overview\n\n"
        explanation += f"This is a **{num_lines}-line {language} snippet** that "

        if has_classes and has_functions:
            explanation += f"defines {len(class_names)} class{'es' if len(class_names) > 1 else ''} and {len(func_names)} function{'s' if len(func_names) > 1 else ''}.\n\n"
        elif has_classes:
            explanation += f"defines {len(class_names)} class{'es' if len(class_names) > 1 else ''}.\n\n"
        elif has_functions:
            explanation += f"defines {len(func_names)} function{'s' if len(func_names) > 1 else ''}.\n\n"
        else:
            explanation += "executes a sequence of operations.\n\n"

        explanation += "## Key Logic and Data Flow\n\n"

        if has_imports:
            explanation += "The code begins by importing its dependencies, setting up the necessary modules for the operations that follow.\n\n"

        if class_names:
            for name in class_names:
                explanation += f"**`{name}`** — This class encapsulates related data and behavior. "
            explanation += "It organizes the code into a reusable, logical unit.\n\n"

        if func_names:
            for name in func_names:
                explanation += f"- **`{name}()`** — "
                if has_return:
                    explanation += "Processes input and returns a computed result.\n"
                else:
                    explanation += "Performs an operation with side effects.\n"
            explanation += "\n"

        if has_loops:
            explanation += "The code uses **iteration** to process multiple items or repeat an operation. "
            if has_conditionals:
                explanation += "Within the loop, conditional logic determines how each item is handled.\n\n"
            else:
                explanation += "Each iteration performs the same operation on the next element.\n\n"

        if has_try:
            explanation += "**Error handling** is implemented with try/except blocks, ensuring the code fails gracefully rather than crashing on unexpected input.\n\n"

        if has_print:
            explanation += "Debug or output statements are used to display results to the console.\n\n"

        explanation += "## Notable Patterns\n\n"

        patterns = []
        if has_functions:
            patterns.append("**Modular design** — Logic is broken into named functions for reusability and readability")
        if has_classes:
            patterns.append("**Object-oriented approach** — Classes group related state and behavior together")
        if has_try:
            patterns.append("**Defensive programming** — Error handling prevents unexpected crashes")
        if has_loops and has_conditionals:
            patterns.append("**Filter/transform pattern** — Data is iterated over with conditional processing")
        if not patterns:
            patterns.append("**Procedural style** — The code executes top-to-bottom in a straightforward sequence")
            patterns.append("**Simplicity** — No unnecessary abstractions, keeping the logic easy to follow")

        for p in patterns:
            explanation += f"- {p}\n"

        explanation += f"\nOverall, this is a straightforward {language} implementation. "
        if num_lines > 20:
            explanation += "Given its length, consider adding comments or docstrings to improve maintainability."
        else:
            explanation += "The code is concise and should be easy to maintain."

        await set_cached(cache_key, {"explanation": explanation}, ttl=3600)
        return explanation, False

    async def suggest_refactor(self, code: str, language: str) -> tuple[str, bool]:
        cache_key = make_cache_key("refactor", code, language)
        cached = await get_cached(cache_key)
        if cached:
            return cached["suggestions"], True

        lines = code.strip().split("\n")
        suggestions = "## Refactoring Suggestions\n\n"
        suggestion_count = 0

        # Check for specific refactoring opportunities
        has_nested_ifs = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            indent = len(line) - len(line.lstrip())
            if ("if " in stripped) and indent >= 8:
                has_nested_ifs = True

        # Suggestion: Nested conditionals
        if has_nested_ifs:
            suggestion_count += 1
            suggestions += f"### {suggestion_count}. Flatten Nested Conditionals\n\n"
            suggestions += "**Issue:** Deeply nested if-statements reduce readability and increase cognitive complexity.\n\n"
            suggestions += "**Before:**\n```" + language + "\n"
            suggestions += "if condition_a:\n    if condition_b:\n        if condition_c:\n            do_something()\n"
            suggestions += "```\n\n**After:**\n```" + language + "\n"
            suggestions += "if not condition_a:\n    return\nif not condition_b:\n    return\nif condition_c:\n    do_something()\n"
            suggestions += "```\n\nUse early returns (guard clauses) to reduce nesting depth.\n\n"

        # Suggestion: Repeated code patterns
        line_counts = {}
        for line in lines:
            stripped = line.strip()
            if len(stripped) > 15 and not stripped.startswith("#") and not stripped.startswith("//"):
                line_counts[stripped] = line_counts.get(stripped, 0) + 1
        duplicates = {k: v for k, v in line_counts.items() if v > 1}

        if duplicates:
            suggestion_count += 1
            suggestions += f"### {suggestion_count}. Extract Repeated Code (DRY)\n\n"
            suggestions += "**Issue:** The same code appears multiple times. Duplicated logic is harder to maintain — fixing a bug in one place means fixing it everywhere.\n\n"
            suggestions += "**Suggestion:** Extract the repeated logic into a helper function:\n\n"
            suggestions += "```" + language + "\n"
            if language == "python":
                suggestions += "def shared_operation(param):\n    # extracted common logic here\n    pass\n"
            elif language in ("javascript", "typescript"):
                suggestions += "function sharedOperation(param) {\n  // extracted common logic here\n}\n"
            else:
                suggestions += "// Extract into a reusable function\n"
            suggestions += "```\n\n"

        # Suggestion: Long functions
        func_lengths = []
        current_func = None
        current_length = 0
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("def ") or stripped.startswith("function ") or stripped.startswith("func "):
                if current_func and current_length > 15:
                    func_lengths.append((current_func, current_length))
                current_func = stripped.split("(")[0].replace("def ", "").replace("function ", "").replace("func ", "")
                current_length = 0
            elif current_func:
                current_length += 1
        if current_func and current_length > 15:
            func_lengths.append((current_func, current_length))

        if func_lengths:
            suggestion_count += 1
            suggestions += f"### {suggestion_count}. Break Up Long Functions\n\n"
            for name, length in func_lengths:
                suggestions += f"**Issue:** `{name}()` is {length} lines long. Functions over ~15 lines are harder to test and reason about.\n\n"
            suggestions += "**Suggestion:** Identify logical sections within the function and extract each into a smaller, named function. Each function should do one thing well.\n\n"

        # Suggestion: Missing error handling
        has_try = any("try" in ln for ln in lines)
        has_file_ops = any(("open(" in ln or "read(" in ln or "write(" in ln) for ln in lines)
        has_network = any(("request" in ln.lower() or "fetch(" in ln or "http" in ln.lower()) for ln in lines)

        if (has_file_ops or has_network) and not has_try:
            suggestion_count += 1
            suggestions += f"### {suggestion_count}. Add Error Handling\n\n"
            suggestions += "**Issue:** The code performs I/O operations (file access or network requests) without error handling. These operations can fail due to missing files, network timeouts, or permission issues.\n\n"
            suggestions += "**Before:**\n```" + language + "\n"
            if has_file_ops:
                suggestions += 'data = open("file.txt").read()\n'
            else:
                suggestions += "response = requests.get(url)\n"
            suggestions += "```\n\n**After:**\n```" + language + "\n"
            if language == "python":
                suggestions += "try:\n"
                if has_file_ops:
                    suggestions += '    with open("file.txt") as f:\n        data = f.read()\nexcept FileNotFoundError:\n    logger.error("File not found")\n    data = default_value\n'
                else:
                    suggestions += "    response = requests.get(url, timeout=10)\n    response.raise_for_status()\nexcept requests.RequestException as e:\n    logger.error(f\"Request failed: {e}\")\n"
            else:
                suggestions += "// Wrap in try/catch with proper error handling\n"
            suggestions += "```\n\n"

        # Suggestion: Use modern language features
        has_old_format = "%" in code and ("'%" in code or '"%' in code)
        has_concatenation = any(("+ " in ln and ("'" in ln or '"' in ln)) for ln in lines)

        if language == "python" and (has_old_format or has_concatenation):
            suggestion_count += 1
            suggestions += f"### {suggestion_count}. Use Modern String Formatting\n\n"
            suggestions += "**Issue:** Using string concatenation or %-formatting is less readable than f-strings.\n\n"
            suggestions += '**Before:**\n```python\nmessage = "Hello " + name + ", you are " + str(age)\n```\n\n'
            suggestions += '**After:**\n```python\nmessage = f"Hello {name}, you are {age}"\n```\n\n'
            suggestions += "F-strings (Python 3.6+) are faster, more readable, and less error-prone.\n\n"

        # Always add a general best practice suggestion
        suggestion_count += 1
        suggestions += f"### {suggestion_count}. General Best Practices\n\n"

        best_practices = []
        has_constants = any(ln.strip() and ln.strip()[0].isupper() and "=" in ln and ln.strip().split("=")[0].strip().isupper() for ln in lines)
        has_magic_numbers = any(any(c.isdigit() for c in ln.split("#")[0]) and "range" not in ln and "enumerate" not in ln and "line" not in ln.lower() for ln in lines if ln.strip() and not ln.strip().startswith("#") and not ln.strip().startswith("//"))

        if has_magic_numbers and not has_constants:
            best_practices.append("**Extract magic numbers into named constants** for clarity: `MAX_RETRIES = 3` is more readable than a bare `3`")
        best_practices.append("**Add type hints** to function signatures for better IDE support and self-documenting code")
        best_practices.append("**Write unit tests** — if this code doesn't have tests yet, add them to prevent regressions")
        best_practices.append("**Keep functions pure where possible** — functions without side effects are easier to test and reason about")

        for bp in best_practices:
            suggestions += f"- {bp}\n"

        suggestions += "\nOverall, these refactoring suggestions would improve the code's **readability**, **maintainability**, and **robustness** without changing its core behavior."

        await set_cached(cache_key, {"suggestions": suggestions}, ttl=3600)
        return suggestions, False


# ============================================================
# REAL SERVICE — calls OpenAI via LangChain
# ============================================================

class RealLLMService:
    """Handles all LLM interactions for code analysis using OpenAI."""

    def __init__(self):
        from langchain_openai import ChatOpenAI
        from langchain.output_parsers import PydanticOutputParser

        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.2,
            max_tokens=2000,
            api_key=settings.openai_api_key,
        )
        self.review_parser = PydanticOutputParser(pydantic_object=ReviewResult)

    async def review_code(self, code: str, language: str) -> tuple[ReviewResult, bool]:
        from langchain.prompts import ChatPromptTemplate

        cache_key = make_cache_key("review", code, language)
        cached = await get_cached(cache_key)
        if cached:
            return ReviewResult(**cached), True

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are an expert code reviewer with deep knowledge of {language}. "
                "Analyze the following code for bugs, security vulnerabilities, "
                "performance issues, and style problems. Be specific about line numbers "
                "and provide actionable suggestions.\n\n{format_instructions}",
            ),
            (
                "human",
                "Review this {language} code:\n\n```{language}\n{code}\n```",
            ),
        ])

        chain = prompt | self.llm | self.review_parser

        result = await chain.ainvoke({
            "code": code,
            "language": language,
            "format_instructions": self.review_parser.get_format_instructions(),
        })

        await set_cached(cache_key, result.model_dump(), ttl=3600)
        return result, False

    async def explain_code(self, code: str, language: str) -> tuple[str, bool]:
        from langchain.prompts import ChatPromptTemplate

        cache_key = make_cache_key("explain", code, language)
        cached = await get_cached(cache_key)
        if cached:
            return cached["explanation"], True

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are a senior {language} developer explaining code to a junior. "
                "Provide a clear, structured explanation covering: "
                "1) Overall purpose, 2) Key logic and data flow, "
                "3) Notable patterns or techniques used. "
                "Keep it concise but thorough.",
            ),
            (
                "human",
                "Explain this {language} code:\n\n```{language}\n{code}\n```",
            ),
        ])

        chain = prompt | self.llm
        response = await chain.ainvoke({
            "code": code,
            "language": language,
        })

        explanation = response.content
        await set_cached(cache_key, {"explanation": explanation}, ttl=3600)
        return explanation, False

    async def suggest_refactor(self, code: str, language: str) -> tuple[str, bool]:
        from langchain.prompts import ChatPromptTemplate

        cache_key = make_cache_key("refactor", code, language)
        cached = await get_cached(cache_key)
        if cached:
            return cached["suggestions"], True

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are a senior {language} developer performing code refactoring. "
                "Analyze this code and suggest specific improvements. "
                "For each suggestion: 1) Explain the issue, "
                "2) Show the before code, 3) Show the after code. "
                "Focus on readability, performance, modern best practices, and DRY.",
            ),
            (
                "human",
                "Refactor this {language} code:\n\n```{language}\n{code}\n```",
            ),
        ])

        chain = prompt | self.llm
        response = await chain.ainvoke({
            "code": code,
            "language": language,
        })

        suggestions = response.content
        await set_cached(cache_key, {"suggestions": suggestions}, ttl=3600)
        return suggestions, False


# ============================================================
# SELECT SERVICE BASED ON CONFIG
# ============================================================

if settings.mock_llm:
    llm_service = MockLLMService()
    print("⚡ CodeLens running in MOCK MODE — no OpenAI calls will be made")
else:
    llm_service = RealLLMService()