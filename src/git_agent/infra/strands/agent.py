from __future__ import annotations

from dataclasses import asdict, is_dataclass
import json
import os

from dotenv import load_dotenv
from loguru import logger
from strands import Agent
from strands.agent import AgentResult
from strands.models.ollama import OllamaModel

from git_agent.domain.models import CodeReviewResult
from git_agent.domain.ports import CodeReviewAgent
from git_agent.domain.prompts import SENIOR_DEV_PROMPT
from git_agent.infra.hooks.logging import LoggingHook
from git_agent.infra.serialization import EnhancedJSONEncoder
from git_agent.infra.strands.tools import Tools
from git_agent.domain.models import ReviewContext


class StrandsCodeReviewAgent(CodeReviewAgent):
    def __init__(self, model: str | None = None, ollama_host: str | None = None):
        load_dotenv()
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
        self.ollama_host = ollama_host or os.getenv(
            "OLLAMA_HOST", "http://localhost:11434"
        )

        self.ollama_model = OllamaModel(
            host=self.ollama_host,
            model_id=self.model,
            max_tokens=4096,
            temperature=0.2,
            top_p=0.9,
        )

        self.agent = Agent(
            name=self.__class__.__name__,
            system_prompt=SENIOR_DEV_PROMPT,
            tools=Tools,
            model=self.ollama_model,
            hooks=[LoggingHook()],
        )

    def review_with_context(
        self, context: ReviewContext, user_context: str = ""
    ) -> CodeReviewResult:
        message = (
            "Review the current code changes.\n\n"
            "Steps:\n"
            "1. Get the diff with get_git_diff\n"
            "2. Run the linter over modified files with run_linter\n"
            "3. If you need more context, read specific files with read_file_context\n"
            "4. Review the code changes and provide feedback.\n"
            "```json\n"
            + json.dumps(context, ensure_ascii=False, cls=EnhancedJSONEncoder)
            + "\n```"
        )

        if user_context:
            message += f"\n\nAdditional context: {user_context}"

        try:
            response = self.agent(
                prompt=message, structured_output_model=CodeReviewResult
            )
            review = self._parse_response(response)
            logger.success("Review completed")
            return review
        except Exception as e:
            logger.error(f"Error during review: {e}")
            raise

    def _parse_response(self, response: AgentResult) -> CodeReviewResult:
        content = response.message.get("content")[0]
        data = content.get("toolUse").get("input")
        logger.debug(response.message)
        logger.debug(response.structured_output)
        logger.debug(json.dumps(data, indent=2, ensure_ascii=False))

        try:
            return CodeReviewResult(**data)
        except Exception as e:
            raise ValueError(
                f"Response does not match schema: {e}\nData: {response}"
            ) from None


__all__ = ["StrandsCodeReviewAgent"]
