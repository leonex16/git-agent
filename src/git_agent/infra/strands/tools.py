from __future__ import annotations

from strands import tool
from strands_tools import diagram, file_read, journal

from git_agent.infra.git import GitAdapter
from git_agent.infra.linter import LinterAdapter


@tool
def git_diff_tool():
    return GitAdapter().get_diff()


@tool
def linter_tool(r_file_paths: list[str]):
    return LinterAdapter().run_linter(r_file_paths)


Tools = [git_diff_tool, linter_tool, file_read, diagram, journal]
__all__ = ["Tools", "git_diff_tool", "linter_tool"]
