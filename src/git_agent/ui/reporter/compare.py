from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from git_agent.domain.models import ApprovalStatus, CodeReviewResult
from git_agent.ui.reporter.constants import (
    COLOR_ERROR,
    COLOR_NEUTRAL,
    COLOR_PRIMARY,
    COLOR_SUCCESS,
    COLOR_WARNING,
)
from git_agent.ui.reporter.review import ReviewReporter


class CompareReporter:
    def __init__(self, console: Console):
        self.console = console
        self.reviewer = ReviewReporter(console)

    def render_multi(
        self,
        results_by_model: dict[str, CodeReviewResult],
        durations: dict[str, float] | None = None,
    ):
        table = Table(
            title="Model Comparison",
            show_header=True,
            header_style=f"bold {COLOR_PRIMARY}",
            expand=True,
        )
        table.add_column("Model", width=22)
        table.add_column("Status", width=14)
        table.add_column("Critical", width=8)
        table.add_column("Warnings", width=9)
        table.add_column("Files", width=6)
        table.add_column("Languages", width=20)
        table.add_column("Time (s)", width=10)

        for model, result in results_by_model.items():
            status = result.approval_status.value
            critical = str(len(result.critical_bugs))
            warnings = str(len(result.warnings))
            files = str(result.files_reviewed)
            languages = ", ".join(result.languages_detected)
            time_cell = f"{durations.get(model, 0):.2f}" if durations else "-"
            row_style = {
                ApprovalStatus.Approved: COLOR_SUCCESS,
                ApprovalStatus.NeedsFixes: COLOR_WARNING,
                ApprovalStatus.Rejected: COLOR_ERROR,
            }.get(result.approval_status, COLOR_NEUTRAL)
            table.add_row(
                model,
                status,
                critical,
                warnings,
                files,
                languages,
                time_cell,
                style=row_style,
            )

        self.console.print(table)
        self.console.print("\n")

        min_panel_width = 50
        console_width = self.console.size.width

        num_cols = max(1, (console_width + 1) // (min_panel_width + 1))

        items = list(results_by_model.items())

        for i in range(0, len(items), num_cols):
            chunk = items[i : i + num_cols]

            row_table = Table(
                show_header=False,
                show_edge=False,
                box=None,
                expand=True,
                padding=(0, 1),
            )

            for _ in range(len(chunk)):
                row_table.add_column(ratio=1)

            row_panels = []
            for model, result in chunk:
                review_content = self.reviewer.build_review_group(result)
                border_color = {
                    ApprovalStatus.Approved: COLOR_SUCCESS,
                    ApprovalStatus.NeedsFixes: COLOR_WARNING,
                    ApprovalStatus.Rejected: COLOR_ERROR,
                }.get(result.approval_status, COLOR_NEUTRAL)

                panel = Panel(
                    review_content,
                    title=f"[bold]{model}[/]",
                    border_style=border_color,
                    padding=(1, 1),
                    expand=True,
                )
                row_panels.append(panel)

            row_table.add_row(*row_panels)
            self.console.print(row_table)
