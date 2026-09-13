"""CLI adapter for orchestrator evaluation cases."""

import argparse
from pathlib import Path
import sys

try:  # Support both ``python scripts/evaluate_orchestrator.py`` and ``-m``.
    from .orchestrator_eval.case import CaseError, load_case
except ImportError:  # pragma: no cover - exercised by direct script launch.
    from orchestrator_eval.case import CaseError, load_case


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="evaluate_orchestrator.py",
        description="Evaluate an OpenCode orchestrator case",
        allow_abbrev=False,
    )
    commands = parser.add_subparsers(dest="action")
    help_command = commands.add_parser("help", help="show help for a command", allow_abbrev=False)
    help_command.add_argument("topic", nargs="?", choices=("doctor", "run"))
    doctor = commands.add_parser("doctor", help="validate prerequisites and a case", allow_abbrev=False)
    doctor.add_argument("case")
    doctor.add_argument("--source-repo", required=True, type=Path)
    run = commands.add_parser("run", help="run a validated evaluation case", allow_abbrev=False)
    run.add_argument("case")
    run.add_argument("--source-repo", required=True, type=Path)
    run.add_argument("--output-root", type=Path)
    run.add_argument("--discard-raw", action="store_true")
    return parser


def main(argv=None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.action == "help":
        if args.topic:
            subparsers = next(action for action in parser._actions if isinstance(action, argparse._SubParsersAction))
            subparsers.choices[args.topic].print_help()
            return 0
        parser.print_help()
        return 0
    if args.action is None:
        parser.print_help(sys.stderr)
        return int(2)
    try:
        case = load_case(args.case, args.source_repo)
    except CaseError as error:
        print(f"error: {error}", file=sys.stderr)
        return int(2)
    if args.action == "doctor":
        print(f"ok: {case.case_id} ({len(case.commands)} command(s))")
        return 0
    # Execution is intentionally owned by the later evaluation ticket.  This
    # adapter validates the complete input contract without inventing a public
    # lifecycle interface.
    print(f"ready: {case.case_id} ({len(case.commands)} command(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
