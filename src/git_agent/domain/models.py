from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TypedDict

from pydantic import BaseModel, Field


@dataclass
class FileContext:
    language: str
    content: str
    line_count: int = field(init=False)

    def __init__(self, language: str, lines: list[str]):
        self.line_count = len(lines)
        self.language = language.title()
        self.content = "\n".join(lines)


class FileInfo(TypedDict):
    content: str
    language: str
    line_count: int


@dataclass
class LintScoreIssue:
    file: str
    language: str
    linter: str
    message: str


@dataclass
class LintScore:
    issues: list[LintScoreIssue]
    by_language: dict[str, list[LintScoreIssue]]
    linters_used: set[str]


@dataclass
class GitDiff:
    diff: str
    files_changed: list[str]


@dataclass
class ReviewContext:
    diff: str
    files_changed: list[str]
    file_contents: dict[str, FileContext]
    linter_results: LintScore


class SeverityLevel(str, Enum):
    Critical = "critical"
    Warning = "warning"
    Info = "info"


class ApprovalStatus(str, Enum):
    Approved = "approved"
    NeedsFixes = "needs_fixes"
    Rejected = "rejected"


class CommitType(str, Enum):
    Feat = "feat"
    Fix = "fix"
    Refactor = "refactor"
    Docs = "docs"
    Style = "style"
    Test = "test"
    Chore = "chore"
    Perf = "perf"


class StyleCategory(str, Enum):
    Naming = "naming"
    Structure = "structure"
    Documentation = "documentation"
    Complexity = "complexity"
    Duplication = "duplication"
    Formatting = "formatting"


class CodeIssue(BaseModel):
    file: str = Field()
    line: int = Field()
    severity: SeverityLevel = Field()
    description: str = Field()
    suggestion: str = Field()
    code_snippet: str | None = Field(default=None)


class StyleSuggestion(BaseModel):
    category: StyleCategory = Field()
    description: str = Field()
    file: str | None = Field(default=None)
    line: int | None = Field(default=None)
    example: str | None = Field(default=None)


class CommitMessage(BaseModel):
    type: CommitType = Field()
    scope: str = Field()
    description: str = Field()
    body: str | None = Field(default=None)
    breaking: bool = Field(default=False)
    footer: str | None = Field(default=None)
    files: list[str] = Field(default_factory=list)

    def format(self) -> str:
        first_line = f"{self.type.value}({self.scope}): {self.description}"
        parts = [first_line]

        if self.body:
            parts.append("")
            parts.append(self.body)

        if self.breaking:
            parts.append("")
            parts.append("BREAKING CHANGE: This introduces breaking changes")

        if self.footer:
            parts.append("")
            parts.append(self.footer)

        return "\n".join(parts)

    def commit_commands(self, chunk_size: int = 10) -> list[str]:
        """Generates git commit commands, handling large file lists by splitting them."""
        if not self.files:
            return [f'git commit -m "{self.format()}"']

        commands = []
        msg = self.format().replace('"', '\\"')

        # Split files into chunks to avoid command line length limits
        for i in range(0, len(self.files), chunk_size):
            chunk = self.files[i : i + chunk_size]
            files_str = " ".join(f'"{f}"' for f in chunk)

            # If it's the first chunk, create the commit
            if i == 0:
                commands.append(f'git add {files_str} && git commit -m "{msg}"')
            else:
                # For subsequent chunks, amend the commit (or just add and commit again if preferred,
                # but amending keeps it atomic-ish if we consider the PR context.
                # However, for simplicity/safety in CLI copy-paste, separate commits might be safer
                # or just adding to the previous one.
                # Let's stick to adding and amending to keep it as one logical commit if possible,
                # OR just returning multiple add commands and one commit?
                # The prompt requested "Prefer multiple commits when the file list is large".
                # So we should probably generate multiple commits if explicitly requested,
                # but here we are implementing the `commit_commands` method for a SINGLE CommitMessage object.
                # If a single CommitMessage has many files, it implies one logical change.
                # So `git add` in chunks + one `git commit` is the technical solution.
                pass

        # Simpler approach: One command with all files, assuming user shell handles it,
        # or just "git add <files>" then "git commit".
        # Let's return a list of commands: git add <files>... then git commit.

        cmds = []
        # Add files in chunks
        for i in range(0, len(self.files), chunk_size):
            chunk = self.files[i : i + chunk_size]
            files_str = " ".join(f'"{f}"' for f in chunk)
            cmds.append(f"git add {files_str}")

        cmds.append(f'git commit -m "{msg}"')
        return cmds


class CodeReviewResult(BaseModel):
    summary: str = Field()
    critical_bugs: list[CodeIssue] = Field(default_factory=list)
    warnings: list[CodeIssue] = Field(default_factory=list)
    style_suggestions: list[StyleSuggestion] = Field(default_factory=list)
    commit_proposals: list[CommitMessage] = Field()
    approval_status: ApprovalStatus = Field()
    files_reviewed: int = Field()
    languages_detected: list[str] = Field()
    additional_notes: str | None = Field(default=None)
