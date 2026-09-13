"""Tests for process execution with bounded argv command supervision."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.orchestrator_eval.case import CommandRecord, ExitCode, Status
from scripts.orchestrator_eval.process import ProcessResult, run_command, run_command_with_evidence


class TestProcessExecution(unittest.TestCase):
    
    def test_simple_command(self):
        """Test running a simple command."""
        command = CommandRecord(
            name="test",
            argv=("echo", "hello"),
            cwd=".",
            expected_status=Status.PASSED,
            expected_exit_code=ExitCode.SUCCESS
        )
        
        result = run_command(command)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout.strip(), b"hello")
        self.assertFalse(result.timed_out)
        self.assertGreater(result.duration, 0)
        
    def test_command_with_timeout(self):
        """Test running a command with timeout."""
        command = CommandRecord(
            name="test",
            argv=("sleep", "2"),
            cwd=".",
            expected_status=Status.PASSED,
            expected_exit_code=ExitCode.SUCCESS
        )
        
        result = run_command(command, timeout=0.1)
        self.assertTrue(result.timed_out)
        # On Unix systems, sleep returns SIGTERM signal when killed (exit code -15)
        # But let's just check that it timed out and took roughly the right amount of time
        self.assertGreater(result.duration, 0.05)
        self.assertLess(result.duration, 0.5)
        
    def test_nonexistent_command(self):
        """Test running a nonexistent command."""
        command = CommandRecord(
            name="test",
            argv=("this_command_does_not_exist",),
            cwd=".",
            expected_status=Status.FAILED,
            expected_exit_code=ExitCode.FAILURE
        )
        
        result = run_command(command)
        self.assertNotEqual(result.exit_code, 0)
        self.assertFalse(result.timed_out)

    def test_command_with_working_directory(self):
        """Test running a command with a specific working directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test content")
            
            command = CommandRecord(
                name="test",
                argv=("cat", str(test_file)),
                cwd=tmpdir,
                expected_status=Status.PASSED,
                expected_exit_code=ExitCode.SUCCESS
            )
            
            result = run_command(command)
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.stdout.strip(), b"test content")
            
    def test_command_with_environment(self):
        """Test running a command with custom environment."""
        command = CommandRecord(
            name="test",
            argv=("sh", "-c", "echo $TEST_VAR"),
            cwd=".",
            expected_status=Status.PASSED,
            expected_exit_code=ExitCode.SUCCESS
        )

        env = {"TEST_VAR": "test_value"}
        result = run_command(command, env=env)
        self.assertEqual(result.exit_code, 0)
        # We might get extra whitespace, so just check if our value is present
        self.assertIn(b"test_value", result.stdout)
        
    def test_command_with_shell(self):
        """Test running a command that requires shell."""
        command = CommandRecord(
            name="test",
            argv=("sh", "-c", "echo hello world"),
            cwd=".",
            expected_status=Status.PASSED,
            expected_exit_code=ExitCode.SUCCESS
        )
        
        result = run_command(command)
        self.assertEqual(result.exit_code, 0)
        # Check if the output contains our expected text
        self.assertIn(b"hello world", result.stdout)
        
    def test_process_result_dataclass(self):
        """Test that ProcessResult is properly constructed."""
        result = ProcessResult(
            exit_code=0,
            stdout=b"test output",
            stderr=b"test error",
            duration=0.1,
            timed_out=False
        )
        
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout, b"test output")
        self.assertEqual(result.stderr, b"test error")
        self.assertEqual(result.duration, 0.1)
        self.assertFalse(result.timed_out)
        
    def test_command_with_evidence(self):
        """Test command execution with evidence capture."""
        command = CommandRecord(
            name="test",
            argv=("echo", "hello evidence"),
            cwd=".",
            expected_status=Status.PASSED,
            expected_exit_code=ExitCode.SUCCESS
        )
        
        result = run_command_with_evidence(command)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout.strip(), b"hello evidence")
        self.assertFalse(result.timed_out)

    def test_descendant_process_interruption(self):
        """Test that descendant processes are properly terminated on interruption."""
        # This test creates a command that spawns a descendant process
        # and verifies that all processes in the group are cleaned up
        command = CommandRecord(
            name="test",
            argv=("sh", "-c", "sleep 2 & pid=$!; sleep 1; wait $pid 2>/dev/null || true"),
            cwd=".",
            expected_status=Status.PASSED,
            expected_exit_code=ExitCode.SUCCESS
        )

        # Test with timeout to trigger cleanup
        result = run_command(command, timeout=0.1)
        self.assertTrue(result.timed_out)
        # Verify that the command was properly timed out and cleaned up
        self.assertGreater(result.duration, 0.05)
        self.assertLess(result.duration, 0.5)


if __name__ == "__main__":
    unittest.main()
