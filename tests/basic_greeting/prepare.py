"""Create a tiny repository with a passing baseline behavior."""

import os
from pathlib import Path
import subprocess


workspace = Path(os.environ["TEST_WORKSPACE"])
repository = workspace / "tmp"
repository.mkdir()
subprocess.run(["git", "init", "--initial-branch", "main"], cwd=repository, check=True)
subprocess.run(["git", "config", "user.name", "Lifecycle Test"], cwd=repository, check=True)
subprocess.run(["git", "config", "user.email", "lifecycle@example.test"], cwd=repository, check=True)
(repository / "greeting.py").write_text(
    "def greet(name):\n"
    "    return name\n"
)
(repository / "test_greeting.py").write_text(
    "import unittest\n\n"
    "from greeting import greet\n\n\n"
    "class GreetingTests(unittest.TestCase):\n"
    "    def test_greet_returns_name(self):\n"
    "        self.assertEqual(greet(\"Ada\"), \"Ada\")\n\n\n"
    "if __name__ == \"__main__\":\n"
    "    unittest.main()\n"
)
subprocess.run(["git", "add", "greeting.py", "test_greeting.py"], cwd=repository, check=True)
subprocess.run(["git", "commit", "-m", "Add greeting baseline"], cwd=repository, check=True)
subprocess.run(["git", "switch", "--create", "e2e/basic-greeting"], cwd=repository, check=True)
(repository / ".git" / "info" / "exclude").write_text(".scratch/\n.agent-trace/\n")
