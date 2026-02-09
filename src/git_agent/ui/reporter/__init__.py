from rich.console import Console

from .compare import CompareReporter
from .review import ReviewReporter


class TerminalReporter:
    def __init__(self):
        self.console = Console()
        self.reviewer = ReviewReporter(self.console)
        self.comparator = CompareReporter(self.console)

    def render_review(self, *args, **kwargs):
        self.reviewer.render_review(*args, **kwargs)

    def render_model_header(self, *args, **kwargs):
        self.reviewer.render_model_header(*args, **kwargs)

    def render_multi(self, *args, **kwargs):
        self.comparator.render_multi(*args, **kwargs)
