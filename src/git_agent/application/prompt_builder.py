from loguru import logger

from git_agent.domain.models import ReviewContext


class PromptBuilder:
    @staticmethod
    def build(context: ReviewContext, user_context: str) -> str:
        logger.debug("Building prompt...")
        parts: list[str] = []

        parts.append("# Request Code Review\n")
        if user_context.strip():
            parts.append(f"## User Context\n{user_context}\n")

        parts.append("## Git Changes (Diff)\n")
        parts.append("```diff")
        parts.append(context.diff)
        parts.append("```\n")

        files_to_read = [
            f for f in context.files_changed if f in context.file_contents
        ]
        parts.append(f"## File Content Context ({len(files_to_read)} files)\n")

        for filepath in files_to_read:
            info = context.file_contents[filepath]
            parts.append(f"### File: {filepath} ({info.language})")
            parts.append(
                "```text"
            )
            parts.append(PromptBuilder._format_file_with_lines(info.content))
            parts.append("```\n")

        if context.linter_results.issues:
            parts.append("## Linter Results (Automated Checks)\n")
            parts.append(f"Total Issues: {len(context.linter_results.issues)}\n")

            for lang, issues in context.linter_results.by_language.items():
                 parts.append(f"### {lang} Issues\n")
                 for issue in issues:
                     parts.append(f"- [{issue.linter}] {issue.file}: {issue.message}")
            parts.append("\n")
        else:
            parts.append("## Linter Results\n✅ No linter issues found.\n")

        return "\n".join(parts)

    @staticmethod
    def _format_file_with_lines(content: str) -> str:
        lines = content.splitlines()
        digits = len(str(len(lines)))
        formatted = []
        for i, line in enumerate(lines, 1):
            formatted.append(f"{i:>{digits}} | {line}")
        return "\n".join(formatted)
