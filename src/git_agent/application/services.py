from loguru import logger

from git_agent.domain.models import FileContext, ReviewContext
from git_agent.domain.ports import FSProvider, GitProvider, LinterProvider


class ReviewService:
    def __init__(
        self,
        git_provider: GitProvider,
        fs_provider: FSProvider,
        linter_provider: LinterProvider,
    ):
        self.git_provider = git_provider
        self.fs_provider = fs_provider
        self.linter_provider = linter_provider

    def gather_context(self) -> ReviewContext:
        logger.debug("Gathering context...")
        file_contents: dict[str, FileContext] = {}

        logger.debug("  Getting git diff...")
        diff_result = self.git_provider.get_diff()

        if not diff_result.success:
            raise ValueError(f"Cannot obtain git diff: {diff_result.message}")

        if not diff_result.value:
            raise ValueError("Git diff result is empty")

        files_changed = diff_result.value.files_changed
        files_changed_count = len(files_changed)

        logger.debug(f"{files_changed_count} modified file(s)")

        logger.debug("  Reading files content")

        for r_file_path in files_changed:
            file_content = self.fs_provider.read_file(r_file_path)

            if not file_content.success:
                logger.warning(f"Could not read {r_file_path}: {file_content.message}")
                continue

            if not file_content.value:
                continue

            file_contents[r_file_path] = file_content.value
            logger.debug(f"  Read {r_file_path}")

        logger.debug("  Running linters...")

        linter_result = self.linter_provider.run_linter(files_changed)

        if not linter_result.success:
            raise ValueError(f"Linter failed: {linter_result.message}")

        if not linter_result.value:
            raise ValueError("Linter result is empty")

        context = ReviewContext(
            diff=diff_result.value.diff,
            files_changed=files_changed,
            file_contents=file_contents,
            linter_results=linter_result.value,
        )

        return context
