import subprocess
from collections import defaultdict

from git_agent.domain.models import LintScore, LintScoreIssue
from git_agent.domain.ports import LinterProvider
from git_agent.domain.result import Res, Result
from git_agent.infra.fs import detect_language


class LinterAdapter(LinterProvider):
    def run_linter(self, file_paths: list[str]) -> Result[LintScore]:
        all_issues: list[LintScoreIssue] = []
        by_language = defaultdict(list)
        linters_used: set[str] = set()

        for f in file_paths:
            file_issues = self._process_file(f)
            if not file_issues:
                continue

            all_issues.extend(file_issues)
            for issue in file_issues:
                linters_used.add(issue.linter)
                by_language[issue.language].append(issue)

        message_parts = []

        if linters_used:
            message_parts.append(f"✅ Linters: {', '.join(linters_used)}")

        message_parts.append(f"{len(all_issues)} issue(s)")

        data = LintScore(
            issues=all_issues, by_language=dict(by_language), linters_used=linters_used
        )

        return Res.ok(data, message=" | ".join(message_parts))

    def _process_file(self, r_file_path: str) -> list[LintScoreIssue]:
        linter_lang = detect_language(r_file_path)
        if linter_lang == "unknown":
            return []

        cmd_base = linter_commands.get(linter_lang)
        if not cmd_base:
            return []

        linter_cmd = [*cmd_base, r_file_path]
        linter_name = linter_cmd[0]

        try:
            result = subprocess.run(
                linter_cmd, capture_output=True, text=True, timeout=30
            )

            output = result.stderr.strip()
            if not output:
                return []

            return [
                LintScoreIssue(
                    file=r_file_path,
                    language=linter_lang,
                    linter=linter_name,
                    message=line.strip(),
                )
                for line in output.splitlines()
                if line.strip()
            ]

        except (FileNotFoundError, subprocess.TimeoutExpired):
            return [
                LintScoreIssue(
                    r_file_path, linter_lang, linter_name, "Linter timeout or not found"
                )
            ]
        except Exception as e:
            return [
                LintScoreIssue(r_file_path, linter_lang, linter_name, f"❌ Error: {e!s}")
            ]


linter_commands = {
    "python": ["ruff", "check"],
    "javascript": ["npx", "eslint"],
    "typescript": ["npx", "eslint"],
}
