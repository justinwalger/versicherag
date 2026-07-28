"""Pytest-based eval suite for the VersicherungsAssist chat agent, built on
DeepEval. Hits the live agent (real Qdrant index and real Gemini calls) - not
meant to run on every commit, only on demand.

Usage: pytest evals/test_agent.py -v
       pytest evals/test_agent.py -m tool_call   (run just one category)
       deepeval test run evals/test_agent.py     (same thing via the DeepEval CLI)
"""

import asyncio
import uuid

import pytest
from deepeval import assert_test
from deepeval.dataset.golden import Golden
from deepeval.metrics import BaseMetric, GEval, ToolCorrectnessMetric
from deepeval.models import GeminiModel
from deepeval.test_case import LLMTestCase, SingleTurnParams, ToolCall
from google import genai
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver

from evals.dataset import dataset
from src.api.dependencies import build_chat_agent
from src.config import get_settings
from src.llm.agent import ChatAgent
from src.llm.judge import AnswerJudge


@pytest.fixture(scope="session")
def agent() -> ChatAgent:
    settings = get_settings()
    chat_model = ChatGoogleGenerativeAI(
        model=settings.gemini_chat_model, api_key=settings.gemini_api_key
    )
    client = genai.Client(api_key=settings.gemini_api_key)
    judge = AnswerJudge(client=client, model_name=settings.gemini_judge_model)
    return build_chat_agent(checkpointer=InMemorySaver(), model=chat_model, judge=judge)


@pytest.fixture(scope="session")
def grader_model() -> GeminiModel:
    settings = get_settings()
    return GeminiModel(model=settings.gemini_judge_model, api_key=settings.gemini_api_key)


async def _run_agent_turn(agent: ChatAgent, query: str) -> tuple[str, list[str]]:
    """Runs one turn and returns (full streamed answer, tool display names called)."""
    answer = ""
    tool_names: list[str] = []
    async for event in agent.stream(
        [HumanMessage(content=query)], thread_id=f"eval-{uuid.uuid4()}"
    ):
        if event["type"] == "tool":
            tool_names.append(event["name"])
        elif event["type"] == "ai":
            answer += event["content"]
    return answer, tool_names


def _params() -> list:
    params = []
    for golden in dataset.goldens:
        if not golden.additional_metadata or not golden.name:
            raise ValueError(f"Golden {golden.name!r} is missing additional_metadata or name.")
        category = golden.additional_metadata["category"]
        if not isinstance(category, str):
            raise TypeError(f"Golden {golden.name!r} has a non-str category: {category!r}.")
        params.append(pytest.param(golden, id=golden.name, marks=getattr(pytest.mark, category)))
    return params


@pytest.mark.parametrize("golden", _params())
def test_golden(golden: Golden, agent: ChatAgent, grader_model: GeminiModel) -> None:
    if not golden.name:
        raise ValueError("Golden is missing a name.")

    answer, tool_names = asyncio.run(_run_agent_turn(agent, golden.input))

    test_case = LLMTestCase(
        input=golden.input,
        actual_output=answer,
        tools_called=[ToolCall(name=name) for name in tool_names],
        expected_tools=golden.expected_tools,
    )

    metrics: list[BaseMetric] = []
    if golden.expected_tools is not None:
        metrics.append(ToolCorrectnessMetric(model=grader_model))

    rubric = (golden.additional_metadata or {}).get("rubric")
    if rubric:
        metrics.append(
            GEval(
                name=golden.name,
                criteria=rubric,
                evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT],
                model=grader_model,
            )
        )

    assert_test(test_case, metrics)
