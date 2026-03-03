from typing import Literal
from pydantic import BaseModel, Field

# Strict whitelist — prevents prompt injection via language field
SUPPORTED_LANGUAGES = Literal[
    "Python", "JavaScript", "TypeScript", "Java", "C++",
    "Go", "Rust", "SQL", "PHP", "C#", "Kotlin", "Swift", "Ruby"
]


class CodeRequest(BaseModel):
    code: str = Field(
        ...,
        description="The source code to be reviewed",
        min_length=1,
        max_length=8000
    )
    language: SUPPORTED_LANGUAGES = Field(
        default="Python",
        description="Programming language of the submitted code"
    )