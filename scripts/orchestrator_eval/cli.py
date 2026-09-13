"""Command-line adapter for the versioned evaluation case model."""

import argparse
from pathlib import Path
import sys

from .case import CaseError
from .harness import doctor_case, run_evaluation


def parser() -> argparse.ArgumentParser:
    command_parser = argparse.ArgumentParser(
        prog="evaluate_orchestrator.py",
        description="Evaluate an OpenCode orchestrator case",
        allow_abbrev=False,
    )
    commands = command_parser.add_subparsers(dest="action")
    help_command = commands.add_parser(
        "help", help="show help for a command", allow_abbrev=False
    )
    help_command.add_argument("topic", nargs="?", choices=("doctor", "run"))

    doctor = commands.add_parser("doctor", help="validate prerequisites and a case", allow_abbrev=False)
    doctor.add_argument("case")
    doctor.add_argument("--source-repo", required=True, type=Path)

    run = commands.add_parser("run", help="run a validated evaluation case", allow_abbrev=False)
    run.add_argument("case")
    run.add_argument("--source-repo", required=True, type=Path)
    run.add_argument("--output-root", type=Path)
    run.add_argument("--discard-raw", action="store_true")
    return command_parser


def main(argv=None) -> int:
    command_parser = parser()
    args = command_parser.parse_args(argv)
    if args.action == "help":
        if args.topic:
            subparsers = next(
                action for action in command_parser._actions
                if isinstance(action, argparse._SubParsersAction)
            )
            subparsers.choices[args.topic].print_help()
        else:
            command_parser.print_help()
        return 0
    if args.action is None:
        command_parser.print_help(sys.stderr)
        return 2
    try:
        case, doctor_report = doctor_case(args.case, args.source_repo)
    except CaseError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if args.action == "doctor":
        if not doctor_report.ok:
            for check in doctor_report.failed:
                print(f"failed: {check.name}: {check.detail}", file=sys.stderr)
            return 2
        print(f"ok: {case.case_id} ({len(case.commands)} command(s))")
        return 0
    else:
        result = run_evaluation(case, args.source_repo, output_root=args.output_root,
                                discard_raw=args.discard_raw)
        print(f"{result.outcome}: {case.case_id}")
        return result.exit_code
