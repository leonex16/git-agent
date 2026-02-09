# uv run main.py --models deepseek-r1:7b,llama3.1:8b,glm4:latest,mistral:latest,llama3.2:3b,gemma3:4b,qwen2.5:7b,qwen3:8b,phi3:3.8b,qwen2.5-coder:7b
# uv run main.py --models qwen3:8b,mistral-nemo:12b,qwen2.5-coder:7b
from __future__ import annotations

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from loguru import logger
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from git_agent.application.ollama_agent import OllamaCodeReviewAgent
from git_agent.application.services import ReviewService
from git_agent.config import parse_args, setup_logger
from git_agent.domain.models import CodeReviewResult, ReviewContext
from git_agent.infra.fs import FSAdapter
from git_agent.infra.git import GitAdapter
from git_agent.infra.linter import LinterAdapter
from git_agent.infra.strands.agent import StrandsCodeReviewAgent
from git_agent.ui.reporter import TerminalReporter

reporter = TerminalReporter()


@dataclass
class ModelRunResult:
    model: str
    review: CodeReviewResult
    duration_seconds: float


def _run_model_review(
    model: str, ctx: ReviewContext, uctx: str, service: ReviewService
) -> ModelRunResult:
    start = time.perf_counter()

    # llm_client = OllamaLLMProvider(model=model)
    # agent = OllamaCodeReviewAgent(model=model)
    agent = StrandsCodeReviewAgent(model=model)
    review = agent.review_with_context(ctx, uctx)

    duration = time.perf_counter() - start
    return ModelRunResult(model=model, review=review, duration_seconds=duration)


def main(argv: list[str] | None = None) -> int:
    config = parse_args(argv)
    user_context = config.context
    models = config.models

    setup_logger(verbose=config.verbose, log_file=config.log_file)

    fs_adapter = FSAdapter()
    git_adapter = GitAdapter()
    linter_adapter = LinterAdapter()

    review_service = ReviewService(
        git_provider=git_adapter, fs_provider=fs_adapter, linter_provider=linter_adapter
    )

    try:
        try:
            context: ReviewContext = review_service.gather_context()
        except ValueError as e:
            logger.error(f"Failed to gather review context: {e}")
            return 1
        except Exception as e:
            logger.error(f"Unexpected error gathering context: {e}")
            return 1

        logger.debug(f"User context {context}")
        logger.info(f"Running review across models: {', '.join(models)}")
        results_ordered: list[ModelRunResult | None] = [None] * len(models)

        with Progress(
            SpinnerColumn(spinner_name="point"),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            transient=True,
        ) as progress:
            model_tasks = {}

            for model in models:
                task_id = progress.add_task(f"[{model}] Starting...", total=None)
                model_tasks[model] = task_id

            with ThreadPoolExecutor(max_workers=min(4, len(models))) as executor:
                future_map = {}
                for idx, model in enumerate(models):
                    progress.update(
                        model_tasks[model], description=f"{model} - Thinking..."
                    )
                    future = executor.submit(
                        _run_model_review, model, context, user_context, review_service
                    )
                    future_map[future] = (idx, model)

                for future in as_completed(future_map):
                    idx, model = future_map[future]
                    try:
                        res = future.result()
                        results_ordered[idx] = res
                        progress.update(
                            model_tasks[model],
                            description=f"[{model}] Done",
                            completed=1,
                            total=1,
                        )
                    except Exception as e:
                        logger.exception(f"Model '{model}' failed: {e}")
                        progress.update(
                            model_tasks[model],
                            description=f"[{model}] Failed",
                            completed=1,
                            total=1,
                        )

        worst_exit = 0
        results_by_model: dict[str, CodeReviewResult] = {}
        durations_by_model: dict[str, float] = {}

        for res in results_ordered:
            if res is None:
                continue

            results_by_model[res.model] = res.review
            durations_by_model[res.model] = res.duration_seconds

            if res.review.approval_status.value == "rejected":
                worst_exit = max(worst_exit, 1)

        if len(models) > 1:
            reporter.render_multi(results_by_model, durations_by_model)
        else:
            model = models[0]
            reporter.render_model_header(
                model,
                duration_s=durations_by_model[model],
                status=results_by_model[model].approval_status,
            )
            reporter.render_review(results_by_model[model])

        if worst_exit:
            logger.warning("At least one model rejected the review")
            return worst_exit

        logger.success("All models approved or suggested minor adjustments")
        return 0
    except Exception as e:
        logger.error(f"Critical error in main process: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
