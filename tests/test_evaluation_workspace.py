from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.orchestrator_eval.workspace import create_workspace, materialize_source_tree, prepare_workspace


class WorkspaceTests(unittest.TestCase):
    def git(self, args, cwd):
        return subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=True)

    def test_history_free_candidate_and_safe_preparation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source-repo"
            source.mkdir()
            self.git(["init", "--quiet"], source)
            (source / "README").write_text("pinned", encoding="utf-8")
            self.git(["add", "README"], source)
            self.git(["-c", "user.name=Test", "-c", "user.email=t@t", "commit", "-m", "one"], source)
            pinned = self.git(["rev-parse", "HEAD"], source).stdout.strip()
            workspace = create_workspace(source, pinned, root / "run")
            self.assertEqual(workspace.candidate.name, "candidate")
            self.assertEqual(self.git(["branch", "--show-current"], workspace.candidate).stdout.strip(), "eval/46-incorrect-name-resolution")
            self.assertEqual(self.git(["rev-list", "--count", "HEAD"], workspace.candidate).stdout.strip(), "1")
            config = root / "config"
            config.mkdir()
            (config / "settings.json").write_text("{}", encoding="utf-8")
            (config / "credentials.json").write_text("secret", encoding="utf-8")
            trace, auth = root / "trace", root / "auth"
            trace.write_text("", encoding="utf-8")
            auth.write_text("", encoding="utf-8")
            prepare_workspace(workspace, config, trace, auth)
            self.assertTrue((workspace.candidate / ".opencode" / "settings.json").exists())
            self.assertFalse((workspace.candidate / ".opencode" / "credentials.json").exists())
            self.assertTrue((workspace.candidate / ".opencode" / "trace").is_symlink())
            self.assertEqual(self.git(["status", "--porcelain"], workspace.candidate).stdout, "")


if __name__ == "__main__":
    unittest.main()
