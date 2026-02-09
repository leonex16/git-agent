from abc import ABC, abstractmethod
from typing import Protocol

from git_agent.domain.models import CodeReviewResult, FileContext, GitDiff, LintScore, ReviewContext
from git_agent.domain.result import Result


class CodeReviewAgent(Protocol):
    def review_with_context(
        self, context: ReviewContext, user_context: str = ""
    ) -> CodeReviewResult:
        """Reviews the code based on the provided context."""
        pass


class GitProvider(ABC):
    @abstractmethod
    def get_diff(self, staged_only: bool = True) -> Result[GitDiff]:
        """
        Retrieves the git diff and basic file statistics.
        Returns a GitDiff object with diff and files_changed.
        """
        pass


class FSProvider(ABC):
    @abstractmethod
    def read_file(self, file_path: str, max_lines: int | None = None) -> Result[FileContext | None]:
        """Reads a file and returns its content context."""
        pass


class LinterProvider(ABC):
    @abstractmethod
    def run_linter(self, file_paths: list[str]) -> Result[LintScore]:
        """Runs linters on the specified files."""
        pass


class LLMProvider(ABC):
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.5,
        max_tokens: int = 2000,
    ) -> str:
        """Generates text using an LLM."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Checks if the LLM service is available."""
        pass
