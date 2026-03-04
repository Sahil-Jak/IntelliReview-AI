import os
import json
import re
import logging

from openai import AsyncOpenAI
from dotenv import load_dotenv
from pydantic import ValidationError

from app.models.review_response import ReviewResponse

load_dotenv()

logger = logging.getLogger(__name__)

# GitHub token loaded but NEVER logged
_github_token = os.getenv("GITHUB_TOKEN")

client = AsyncOpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=_github_token
)

# ── PROMPT ─────────────────────────────────────────────────────────────────
# {language} and {code} are the only .format() placeholders.
# All literal braces in the JSON schema are doubled {{ }} to escape them.
# Code section uses single quotes to avoid any triple-quote collision.
PROMPT_TEMPLATE = (
    "You are an expert {language} code reviewer.\n\n"
    "Analyze the following {language} code carefully and respond ONLY with valid JSON.\n"
    "No markdown, no backticks, no extra text — pure JSON only.\n\n"
    "You MUST return ALL of the following fields with numeric scores (floats between 0 and 10):\n\n"
    "{{\n"
    '  "readability":      <float 0-10>,\n'
    '  "performance":      <float 0-10>,\n'
    '  "maintainability":  <float 0-10>,\n'
    '  "security":         <float 0-10>,\n'
    '  "best_practices":   <float 0-10>,\n'
    '  "overall_score":    <float 0-10>,\n'
    '  "issues":           "<string — describe all issues found, or \'No issues found.\'>",\n'
    '  "ai_explanation":   "<string — brief explanation of the overall code quality>",\n'
    '  "fixed_code":       "<string — corrected version of the code, or \'No fix needed.\'>"\n'
    "}}\n\n"
    "Rules:\n"
    "- All score fields MUST be numbers, not strings.\n"
    "- overall_score should reflect the weighted average of the 5 dimension scores.\n"
    "- Be specific and actionable in issues and ai_explanation.\n\n"
    "Code to review:\n"
    "{code}\n"
)

# Max characters sent to AI per file (token guard)
MAX_CODE_CHARS = 3000


def _sanitise_code(code: str) -> str:
    """
    Escape lone curly braces in user code before injecting into PROMPT_TEMPLATE.

    Problem: PROMPT_TEMPLATE uses str.format(), so any { or } in the code
    being reviewed is misread as a format placeholder — causing KeyError or
    a corrupted prompt that makes the model output non-JSON.

    Fix: replace { -> {{ and } -> }} so str.format() treats them as literals,
    and the model sees normal { } characters in the rendered prompt.
    """
    # Step 1: protect any pre-existing {{ }} doubles
    code = code.replace("{{", "\x00LEFT\x00").replace("}}", "\x00RIGHT\x00")
    # Step 2: escape all remaining single braces
    code = code.replace("{", "{{").replace("}", "}}")
    # Step 3: restore the pre-existing doubles
    code = code.replace("\x00LEFT\x00", "{{").replace("\x00RIGHT\x00", "}}")
    return code


async def analyze_code_with_fix(code: str, language: str = "Python") -> dict:
    """
    Send code to GitHub Models (GPT-4.1-nano) for multi-dimensional review.
    Returns validated dict with 6 scores + issues + explanation + fixed_code + token_usage.
    """
    truncated_code = code[:MAX_CODE_CHARS]

    # Sanitise braces so PROMPT_TEMPLATE.format() never trips on code
    # that contains { } characters (dicts, f-strings, templates, JSON, etc.)
    safe_code = _sanitise_code(truncated_code)

    try:
        prompt = PROMPT_TEMPLATE.format(language=language, code=safe_code)
    except KeyError as e:
        # Absolute last-resort fallback — build prompt without .format()
        logger.warning(f"Prompt .format() failed after sanitise — key: {e}. Using replace fallback.")
        prompt = (
            PROMPT_TEMPLATE
            .replace("{language}", language)
            .replace("{code}", truncated_code)
            .replace("{{", "{")
            .replace("}}", "}")
        )

    try:
        response = await client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            timeout=30  # prevent indefinite hang if API is slow
        )

        raw_output = response.choices[0].message.content.strip()

        # Log token usage — safe, no secrets
        token_usage = None
        if response.usage:
            token_usage = response.usage.total_tokens
            logger.info(
                f"Token usage — prompt: {response.usage.prompt_tokens}, "
                f"completion: {response.usage.completion_tokens}, "
                f"total: {response.usage.total_tokens}"
            )

        # Strip markdown code fences if model wraps its response in them
        raw_output = re.sub(r"```json|```", "", raw_output).strip()

        # Extract first complete JSON object from the response
        json_match = re.search(r"\{.*\}", raw_output, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON block found in model output.")

        parsed = json.loads(json_match.group(0))

        # Strict Pydantic validation — ensures all 6 scores present and numeric
        validated = ReviewResponse(**parsed)
        result = validated.model_dump()
        result["token_usage"] = token_usage
        return result

    except (json.JSONDecodeError, ValueError, ValidationError) as e:
        logger.warning(f"AI response parse/validation failed: {e}")
        return _fallback_response(str(e))

    except Exception as e:
        # Never expose raw exception — may contain API key details
        logger.error(f"GitHub Models API call failed: {type(e).__name__}")
        return _fallback_response(
            "GitHub Models API call failed — check GITHUB_TOKEN and network.",
            api_error=True
        )


def _fallback_response(detail: str, api_error: bool = False) -> dict:
    """Return a safe zero-score fallback when the AI call or parse fails."""
    issue_msg = (
        "GitHub Models API call failed — check GITHUB_TOKEN and network."
        if api_error
        else "Model did not return valid structured JSON."
    )
    return {
        "readability":     0.0,
        "performance":     0.0,
        "maintainability": 0.0,
        "security":        0.0,
        "best_practices":  0.0,
        "overall_score":   0.0,
        "issues":          issue_msg,
        "ai_explanation":  detail,
        "fixed_code":      "No fix generated.",
        "token_usage":     None,
    }