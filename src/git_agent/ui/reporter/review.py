from loguru import logger
from rich.console import Console, Group, RenderableType
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from git_agent.domain.models import (
    ApprovalStatus,
    CodeIssue,
    CodeReviewResult,
    CommitMessage,
    StyleSuggestion,
)
from git_agent.ui.reporter.constants import (
    COLOR_DIM,
    COLOR_ERROR,
    COLOR_NEUTRAL,
    COLOR_PRIMARY,
    COLOR_SUCCESS,
    COLOR_WARNING,
)


class ReviewReporter:
    def __init__(self, console: Console):
        self.console = console

    def render_review(self, result: CodeReviewResult):
        logger.debug(result)
        group = self.build_review_group(result)
        self.console.print(group)

    def build_review_group(self, result: CodeReviewResult) -> Group:
        renderables: list[RenderableType] = []

        renderables.append(
            self._build_header(result.approval_status, result.files_reviewed)
        )

        renderables.append(
            Panel(Markdown(result.summary), title="Summary", border_style=COLOR_PRIMARY)
        )

        if result.critical_bugs:
            renderables.extend(
                self._build_issues("Critical Bugs", result.critical_bugs, COLOR_ERROR)
            )

        if result.warnings:
            renderables.extend(
                self._build_issues("Warnings", result.warnings, COLOR_WARNING)
            )

        if result.style_suggestions:
            renderables.append(self._build_style_table(result.style_suggestions))

        renderables.extend(self._build_commits(result.commit_proposals))

        if result.additional_notes:
            renderables.append(
                Panel(
                    result.additional_notes,
                    title="Additional Notes",
                    border_style=COLOR_DIM,
                )
            )

        return Group(*renderables)

    def _build_header(self, status: ApprovalStatus, files: int) -> Text:
        status_colors = {
            ApprovalStatus.Approved: COLOR_SUCCESS,
            ApprovalStatus.NeedsFixes: COLOR_WARNING,
            ApprovalStatus.Rejected: COLOR_ERROR,
        }
        color = status_colors.get(status, COLOR_NEUTRAL)
        return Text(
            f"\nSTATUS: {status.value.upper()} | Files reviewed: {files}",
            style=f"bold {color}",
        )

    def _build_issues(
        self, title: str, issues: list[CodeIssue], color: str
    ) -> list[RenderableType]:
        items = []
        items.append(Text(f"\n{title.upper()}", style=f"bold {color}"))
        for issue in issues:
            items.append(
                Text(f"• {issue.file}:{issue.line} - {issue.description}", style=color)
            )
            items.append(Text(f"  Suggestion: {issue.suggestion}", style="dim"))
            if issue.code_snippet:
                syntax = Syntax(
                    issue.code_snippet,
                    "python",
                    theme="monokai",
                    background_color="default",
                )
                items.append(Panel(syntax, border_style=COLOR_DIM))
        return items

    def _build_style_table(self, suggestions: list[StyleSuggestion]) -> Table:
        table = Table(
            title="Style Suggestions",
            show_header=True,
            header_style=f"bold {COLOR_PRIMARY}",
            expand=True,
        )
        table.add_column("Category", width=15)
        table.add_column("Location", width=20)
        table.add_column("Description")

        for s in suggestions:
            loc = f"{s.file}:{s.line}" if s.file else "General"
            table.add_row(s.category.value, loc, s.description)

        return table

    def _build_commits(self, commits: list[CommitMessage]) -> list[RenderableType]:
        items = []
        items.append(Text("\nCOMMIT PROPOSALS", style=f"bold {COLOR_PRIMARY}"))
        for i, commit in enumerate(commits, 1):
            formatted_message = commit.format()
            title = f"Option {i}"
            items.append(
                Panel(formatted_message, title=title, border_style=COLOR_PRIMARY)
            )
        return items

    def render_model_header(
        self,
        model: str,
        duration_s: float | None = None,
        status: ApprovalStatus | None = None,
    ):
        status_colors = {
            ApprovalStatus.Approved: COLOR_SUCCESS,
            ApprovalStatus.NeedsFixes: COLOR_WARNING,
            ApprovalStatus.Rejected: COLOR_ERROR,
        }
        border = COLOR_PRIMARY
        if status is not None:
            border = status_colors.get(status, COLOR_PRIMARY)
        body = f"Model: [bold]{model}[/]"
        if duration_s is not None:
            body += f"\nTime: {duration_s:.2f}s"
        if status is not None:
            body += f"\nStatus: [bold]{status.value}[/]"
        self.console.print(Panel(body, title="Model", border_style=border))
