import json

from loguru import logger

from git_agent.application.prompt_builder import PromptBuilder
from git_agent.domain.models import CodeReviewResult, ReviewContext
from git_agent.domain.ports import CodeReviewAgent
from git_agent.domain.prompts import SENIOR_DEV_PROMPT
from git_agent.infra.ollama_llm_provider import OllamaLLMProvider


class OllamaCodeReviewAgent(CodeReviewAgent):
    def __init__(self, model: str, ollama_host: str = "http://localhost:11434"):
        self.llm_provider = OllamaLLMProvider(host=ollama_host, model=model)

        if not self.llm_provider.is_available():
            logger.warning("LLM Provider is not available during initialization.")

    def review_with_context(
        self, context: ReviewContext, user_context: str = ""
    ) -> CodeReviewResult:
        logger.debug(f"Reviewing {len(context.files_changed)} files...")

        prompt = PromptBuilder.build(context, user_context)

        try:
            llm_response = self.llm_provider.generate(
                prompt=prompt, system=SENIOR_DEV_PROMPT
            )
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise

        review = self._parse_llm_response(llm_response)

        review.files_reviewed = len(context.files_changed)
        review.languages_detected = list(
            {info.language for info in context.file_contents.values()}
        )

        return review

    def _parse_llm_response(self, raw_response: str) -> CodeReviewResult:
        logger.debug("Parsing LLM response...")

        try:
            data = json.loads(raw_response)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from model: {e!s}")
            raise ValueError(f"Model did not return valid JSON: {e}") from None

        try:
            review = CodeReviewResult(**data)
            return review
        except Exception as e:
            logger.error(f"Schema validation error: {e!s}")
            raise
