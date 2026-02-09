import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from loguru import logger

default_model = "qwen3:8b"


@dataclass
class Config:
    verbose: bool
    log_file: Path | None
    models: list[str]
    context: str


def parse_args(argv: list[str] | None = None) -> Config:
    parser = argparse.ArgumentParser(
        prog="git-agent", description="CLI para revisión de cambios con LLM"
    )
    parser.add_argument(
        "context",
        nargs=argparse.REMAINDER,
        help="Contexto libre para el revisor (texto)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode")
    parser.add_argument("--log-file", type=str, help="Log file path")
    parser.add_argument(
        "--models", type=str, help="Comma-separated list of model names to compare"
    )

    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    models = [m.strip() for m in (args.models or "").split(",") if m.strip()]
    user_context = " ".join(args.context or [])

    if len(models) == 0:
        models.append(default_model)

    return Config(
        verbose=args.verbose,
        log_file=Path(args.log_file) if args.log_file else None,
        models=models,
        context=user_context,
    )


def setup_logger(verbose: bool = False, log_file: Path | None = None) -> None:
    logger.remove()
    level = "DEBUG" if verbose else "INFO"

    if not verbose:
        console_format = "<level>{message}</level>"
    else:
        console_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

    logger.add(
        sys.stderr,
        level=level,
        colorize=True,
        backtrace=verbose,
        diagnose=verbose,
        format=console_format,
    )
    if not log_file:
        return

    logger.add(
        log_file,
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        backtrace=False,
        diagnose=False,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )
