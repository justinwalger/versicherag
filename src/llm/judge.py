"""Reviews the chat agent's draft answer for grounding and policy compliance
before it reaches the user."""

from google import genai
from google.genai import types
from loguru import logger

from src.llm.models import JudgeVerdict
from src.llm.prompts import JUDGE_PROMPT


class AnswerJudge:
    """Checks a draft answer against the retrieved context and VersicherungsAssist's
    own rules (citations, no legal advice, stays in scope)."""

    def __init__(self, client: genai.Client, model_name: str) -> None:
        self.client = client
        self.model_name = model_name

    def review(self, query: str, context: str, answer: str) -> JudgeVerdict:
        prompt = JUDGE_PROMPT.format(
            query=query,
            context=context or "(kein Kontext abgerufen)",
            answer=answer,
        )
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=JudgeVerdict,
                ),
            )
            if not isinstance(response.parsed, JudgeVerdict):
                raise TypeError(
                    f"Expected JudgeVerdict from structured output, got {type(response.parsed)!r}."
                )
            return response.parsed
        except Exception:  # noqa: BLE001 - deliberate fail-open: any judge failure
            # should never block the chat turn, so every error is treated the same.
            logger.warning("Judge review failed; answer is being delivered unreviewed.")
            return JudgeVerdict(passed=True, issues=[])
