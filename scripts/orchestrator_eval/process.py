"""Process execution with bounded argv command supervision."""

import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from .case import CommandRecord, ExitCode


@dataclass(frozen=True)
class ProcessResult:
    """Represents the result of a process execution."""
    exit_code: int
    stdout: bytes
    stderr: bytes
    duration: float
    timed_out: bool


def run_command(
    command: CommandRecord,
    cwd: Optional[Path] = None,
    env: Optional[dict] = None,
    timeout: Optional[float] = None,
) -> ProcessResult:
    """
    Execute a command with bounded argv supervision.

    Args:
        command: CommandRecord describing the command to run
        cwd: Working directory for the command (defaults to current)
        env: Environment variables for the command (defaults to current)
        timeout: Timeout in seconds (None for no timeout)

    Returns:
        ProcessResult with execution details

    Raises:
        ValueError: If command arguments are invalid
    """
    # Validate command arguments
    if not command.argv:
        raise ValueError("Command must have at least one argument")
    
    # Set up the command with proper environment and working directory
    cmd_args = list(command.argv)
    
    # Create process environment
    process_env = os.environ.copy() if env is None else env.copy()
    
    # Set up working directory
    process_cwd = Path.cwd() if cwd is None else cwd
    
    # Start timing
    start_time = time.time()
    
    process = None
    try:
        # Execute the command with process group management
        process = subprocess.Popen(
            cmd_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=process_cwd,
            env=process_env,
            preexec_fn=os.setsid,  # Create new process group
        )
        
        # Handle timeout if specified
        if timeout is not None:
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                timed_out = False
            except subprocess.TimeoutExpired:
                # Kill the entire process group to ensure cleanup
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    # Give it a moment to terminate gracefully
                    stdout, stderr = process.communicate(timeout=1)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't respond
                    try:
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    except ProcessLookupError:
                        pass  # Process already gone
                    stdout, stderr = process.communicate()
                timed_out = True
        else:
            stdout, stderr = process.communicate()
            timed_out = False
            
    except (KeyboardInterrupt, SystemExit):
        # Handle interruption and cleanup properly
        if process is not None:
            try:
                # Try graceful termination first
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                try:
                    process.communicate(timeout=1)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't respond
                    try:
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    except ProcessLookupError:
                        pass  # Process already gone
                    process.communicate()
            except Exception:
                # If cleanup fails, still re-raise original exception
                pass
        # Re-raise the original exception so caller can handle interruption properly
        raise

    except Exception as e:
        # If we encounter an exception during execution, capture it
        end_time = time.time()
        duration = end_time - start_time
        return ProcessResult(
            exit_code=1,
            stdout=b"",
            stderr=str(e).encode(),
            duration=duration,
            timed_out=False
        )
    
    end_time = time.time()
    duration = end_time - start_time
    
    return ProcessResult(
        exit_code=process.returncode,
        stdout=stdout,
        stderr=stderr,
        duration=duration,
        timed_out=timed_out
    )


def run_command_with_evidence(command: CommandRecord, cwd: Optional[Path] = None, env: Optional[dict] = None, timeout: Optional[float] = None) -> ProcessResult:
    """
    Execute a command with evidence capture and proper timeout/interruption handling.

    This version ensures that evidence is preserved even on timeout and that
    interruptions are handled correctly.

    Args:
        command: CommandRecord describing the command to run
        cwd: Working directory for the command (defaults to current)
        env: Environment variables for the command (defaults to current)
        timeout: Timeout in seconds (None for no timeout)

    Returns:
        ProcessResult with execution details
    """
    # Simply delegate to the main function for consistency
    return run_command(command, cwd, env, timeout)
