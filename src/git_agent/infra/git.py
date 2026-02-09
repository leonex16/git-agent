import subprocess

from git_agent.domain.models import GitDiff
from git_agent.domain.ports import GitProvider
from git_agent.domain.result import Res, Result


class GitAdapter(GitProvider):
    def get_diff(self, staged_only: bool = True) -> Result[GitDiff]:
        try:
            git_diff_cmd = ["git", "diff", "--no-color", "--unified=0"]

            subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                check=True,
                capture_output=True,
            )

            if staged_only:
                git_diff_cmd.append("--staged")

            result = subprocess.run(git_diff_cmd, capture_output=True, text=True)
            diff = result.stdout

            if not diff.strip():
                files_changed = self._get_files_changed(staged_only)
                if not files_changed:
                    return Res.err("No changes detected")
            else:
                 files_changed = self._get_files_changed(staged_only)

            data = GitDiff(diff=diff, files_changed=files_changed)

            return Res.ok(data)
        except FileNotFoundError:
            return Res.err("Git not found")
        except subprocess.CalledProcessError:
             return Res.err("Not a git repository")
        except Exception as e:
            return Res.err(f"Unexpected error: {e!s}")

    def _get_files_changed(self, staged_only: bool) -> list[str]:
        cmd = ["git", "diff", "--name-only"]

        if staged_only:
            cmd.append("--staged")

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        files = result.stdout.strip().splitlines()
        return files
