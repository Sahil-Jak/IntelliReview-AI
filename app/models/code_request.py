"""
Request validation models for the IntelliReview AI review endpoint.

Enforces code length limits and restricts the language field
to a strict whitelist, preventing prompt injection attacks.
"""
from typing import Literal
from pydantic import BaseModel, Field

# Supported language whitelist — prevents prompt injection via language field
SUPPORTED_LANGUAGES = Literal[
    "Python", "JavaScript", "TypeScript", "Java", "C++",
    "Go", "Rust", "SQL", "PHP", "C#", "Kotlin", "Swift", "Ruby"
]


class CodeRequest(BaseModel):
    """
    Incoming request body for POST /review-code.

    Attributes:
        code:     The source code to be reviewed (1–8000 characters).
        language: Programming language from the supported whitelist.

    Example:
        {
            "code": "def hello():\\n    return 'world'",
            "language": "Python"
        }
    """

    code: str = Field(
        ...,
        description="The source code to be reviewed",
        min_length=1,
        max_length=8000,
        examples=["def hello():\n    return 'world'"]
    )
    language: SUPPORTED_LANGUAGES = Field(
        default="Python",
        description="Programming language of the submitted code"
    )