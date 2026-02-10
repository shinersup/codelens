"""
LLM Service — the heart of CodeLens.
"""

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser

from app.config import settings
from app.schemas.review import ReviewResult
from app.services.cache import get_cached, set_cached, make_cache_key


class LLMService:
    """Handles all LLM interactions for code analysis."""

    def __init__(self):
        # Initialize the LLM client
        # temperature=0.2 means mostly deterministic (good for code analysis)
        # higher temperature = more creative/random responses
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.2,
            max_tokens=2000,
            api_key=settings.openai_api_key,
        )

        # This parser validates that the LLM's response matches ReviewResult
        # If the LLM returns malformed JSON, it raises an error instead of
        # passing garbage to the frontend
        self.review_parser = PydanticOutputParser(pydantic_object=ReviewResult)

    async def review_code(self, code: str, language: str) -> tuple[ReviewResult, bool]:
        """
        Analyze code for bugs, security issues, performance problems, and style.

        Returns:
            (ReviewResult, was_cached: bool)
        """
        # Step 1: Check cache
        cache_key = make_cache_key("review", code, language)
        cached = await get_cached(cache_key)
        if cached:
            return ReviewResult(**cached), True

        # Step 2: Build the prompt
        # The format_instructions tell the LLM exactly what JSON schema to follow
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

        # Step 3: Chain the prompt → LLM → parser
        # LangChain's | operator pipes output from one step to the next
        chain = prompt | self.llm | self.review_parser

        # Step 4: Call the LLM
        result = await chain.ainvoke({
            "code": code,
            "language": language,
            "format_instructions": self.review_parser.get_format_instructions(),
        })

        # Step 5: Cache the result (expires in 1 hour)
        await set_cached(cache_key, result.model_dump(), ttl=3600)

        return result, False

    async def explain_code(self, code: str, language: str) -> tuple[str, bool]:
        """
        Explain what code does in plain English.

        Returns:
            (explanation: str, was_cached: bool)
        """
        # Check cache
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

        # Cache it
        await set_cached(cache_key, {"explanation": explanation}, ttl=3600)

        return explanation, False

    async def suggest_refactor(self, code: str, language: str) -> tuple[str, bool]:
        """
        Suggest refactoring improvements with before/after examples.

        Returns:
            (suggestions: str, was_cached: bool)
        """
        # Check cache
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

        # Cache it
        await set_cached(cache_key, {"suggestions": suggestions}, ttl=3600)

        return suggestions, False


# Singleton instance used across the app
llm_service = LLMService()
