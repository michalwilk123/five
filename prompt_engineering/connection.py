import json
import os
import random
import time
from dataclasses import asdict, dataclass

import tqdm
from google import genai
from google.genai import types
from google.genai.errors import ServerError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

LITE_MODEL = "gemini-2.5-flash-lite-preview-06-17"
MEDIUM_MODEL = "gemini-2.5-flash-preview-05-20"
BIG_MODEL = "gemini-2.5-pro"


@dataclass
class LanguageModelQuery:
    system_prompt: str
    prompt: str
    model_name: str = LITE_MODEL


def prepare_prompt(prompt: str, config):
    config_dict = asdict(config)
    for key, value in config_dict.items():
        assert isinstance(value, str), f"Value {value} is not a string"

        prompt = prompt.replace("{{%s}}" % key, value)
    return prompt


def is_retryable_error(exception):
    """Check if the exception is retryable (rate limiting or server errors)"""
    if isinstance(exception, ServerError):
        # Retry on 503 (overloaded) and other server errors
        return exception.status_code >= 500 or exception.status_code == 429
    return False


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=60),
    retry=retry_if_exception_type((ServerError, ValueError, json.JSONDecodeError)),
    before_sleep=lambda retry_state: print(
        f"Retrying after error: {retry_state.outcome.exception()}. Attempt {retry_state.attempt_number}/5"
    ),
)
def _execute_prompt_internal(query: LanguageModelQuery, api_key: str | None = None):
    if api_key is None:
        api_key = os.getenv("GEMINI_API_KEY")

    client = genai.Client(
        api_key=api_key,
    )

    model = query.model_name
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=query.prompt),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            thinking_budget=0,
        ),
        response_mime_type="application/json",
        system_instruction=[types.Part.from_text(text=query.system_prompt)],
    )

    response = ""

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if not isinstance(chunk.text, str):
            continue

        response += chunk.text

    response = json.loads(response)

    return response


def execute_prompt(query: LanguageModelQuery, api_key: str | None = None):
    """
    Execute a prompt with retry logic for both API errors and JSON validation errors.
    """
    max_attempts = 5

    for attempt in range(max_attempts):
        try:
            response = _execute_prompt_internal(query, api_key)
            return response
        except Exception as e:
            if attempt < max_attempts - 1:
                print(
                    f"Error occurred, retrying... (attempt {attempt + 1}/{max_attempts})"
                )
                print(f"Error: {e}")
                time.sleep(random.uniform(3, 45))  # Random delay before retry
                continue
            else:
                print(f"Failed after {max_attempts} attempts")
                raise e
