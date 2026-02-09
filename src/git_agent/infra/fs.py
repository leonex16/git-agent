from pathlib import Path
from typing import cast

from loguru import logger

from git_agent.domain.models import FileContext
from git_agent.domain.ports import FSProvider
from git_agent.domain.result import Res, Result


class FSAdapter(FSProvider):
    def read_file(
        self, file_path: str, max_lines: int | None = None
    ) -> Result[FileContext | None]:
        try:
            path = Path(file_path)

            if not path.exists():
                return Res.err(f"File not found. Path: {file_path}")

            if self._is_ignored(file_path):
                logger.debug(f"Skipping ignored file: {path.name}")
                return Res.ok(cast(FileContext | None, None), "File ignored by policy")

            lines = path.read_text(encoding="utf-8").splitlines()

            if not lines:
                return Res.ok(cast(FileContext | None, None), "File is empty")

            max_lines = max_lines or len(lines)
            skipped_lines = len(lines) - max_lines
            lines = lines[:max_lines]

            if skipped_lines:
                lines.append(f"{skipped_lines} skipped lines")

            language = detect_language(file_path)
            data = FileContext(language=language, lines=lines)

            return Res.ok(
                cast(FileContext | None, data),
                f"Read file. {data.line_count} lines read, language: {data.language}",
            )
        except Exception as e:
            return Res.err(f"Error read {file_path}. Cause: {e!s}")

    def _is_ignored(self, file_path: str) -> bool:
        path = Path(file_path)
        return path.name in IGNORED_FILES or path.suffix in IGNORED_EXTENSIONS


LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "react",
    ".tsx": "react-typescript",
    ".kt": "kotlin",
    ".kts": "kotlin-script",
    ".dart": "dart",
    ".java": "java",
    ".rs": "rust",
    ".toml": "toml",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".md": "markdown",
    ".html": "html",
    ".css": "css",
    ".sh": "bash",
    ".bash": "bash",
}


def detect_language(r_file_path: str) -> str:
    extension = Path(r_file_path).suffix.lower()
    return LANGUAGE_MAP.get(extension, "unknown")


IGNORED_FILES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "uv.lock"}
IGNORED_EXTENSIONS = {".lock", ".svg", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".tar", ".gz"}


def read_file_context(
    r_file_path: str, max_lines: int | None = None
) -> Result[FileContext | None]:
    return FSAdapter().read_file(r_file_path, max_lines)
