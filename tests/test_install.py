import contextlib
import io
import os
from pathlib import Path
import tempfile
import unittest

from scripts import install


class InstallerTests(unittest.TestCase):
    def make_source(self, root):
        source = Path(root) / "opencode"
        (source / "agents").mkdir(parents=True)
        (source / "skills" / "alpha").mkdir(parents=True)
        (source / "commands").mkdir(parents=True)
        (source / "opencode.jsonc").write_text("{}")
        (source / "agents" / "z.md").write_text("z")
        (source / "agents" / "ignore.txt").write_text("ignore")
        (source / "commands" / "a.md").write_text("a")
        (source / "skills" / "alpha" / "SKILL.md").write_text("alpha skill")
        return source

    def test_clean_install_creates_absolute_links(self):
        with tempfile.TemporaryDirectory() as temp:
            source = self.make_source(temp)
            home = Path(temp) / "home"
            self.assertEqual(install.install(source, home), 0)
            destination = home / ".config" / "opencode"
            expected = {
                destination / "opencode.jsonc": source / "opencode.jsonc",
                destination / "agents" / "z.md": source / "agents" / "z.md",
                destination / "skills" / "alpha": source / "skills" / "alpha",
                destination / "commands" / "a.md": source / "commands" / "a.md",
            }
            for path, target in expected.items():
                self.assertTrue(path.is_symlink())
                self.assertEqual(os.readlink(path), str(target.resolve()))

    def test_skill_directory_without_skill_file_is_ignored(self):
        with tempfile.TemporaryDirectory() as temp:
            source = self.make_source(temp)
            beta = source / "skills" / "beta"
            beta.mkdir()
            entries = install._entries(source)
            self.assertIn(source / "skills" / "alpha", dict(entries))
            self.assertNotIn(beta, dict(entries))

            home = Path(temp) / "home"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(install.install(source, home), 0)
            self.assertFalse((home / ".config" / "opencode" / "skills" / "beta").exists())

    def test_source_resolution_does_not_depend_on_cwd(self):
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as outside:
            old_cwd = os.getcwd()
            try:
                os.chdir(outside)
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    self.assertEqual(install.main(["--dry-run"], home=home), 0)
            finally:
                os.chdir(old_cwd)
            self.assertIn(str(install.source_root()), output.getvalue())

    def test_conflicts_are_skipped_and_other_links_continue(self):
        with tempfile.TemporaryDirectory() as temp:
            source = self.make_source(temp)
            home = Path(temp) / "home"
            destination = home / ".config" / "opencode"
            destination.mkdir(parents=True)
            (destination / "opencode.jsonc").write_text("keep")
            (destination / "agents").mkdir()
            (destination / "agents" / "z.md").mkdir()
            (destination / "skills").mkdir()
            os.symlink(source / "skills" / "alpha", destination / "skills" / "alpha")
            (destination / "commands").mkdir()
            os.symlink(destination / "commands" / "missing.md", destination / "commands" / "a.md")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(install.install(source, home), 0)
            self.assertEqual((destination / "opencode.jsonc").read_text(), "keep")
            self.assertTrue((destination / "agents" / "z.md").is_dir())
            self.assertTrue((destination / "skills" / "alpha").is_symlink())
            self.assertTrue((destination / "commands" / "a.md").is_symlink())
            self.assertIn("skip", output.getvalue().lower())

    def test_dry_run_does_not_write_and_rerun_skips(self):
        with tempfile.TemporaryDirectory() as temp:
            source = self.make_source(temp)
            home = Path(temp) / "home"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(install.install(source, home, dry_run=True), 0)
            self.assertFalse(home.exists())
            self.assertIn("link", output.getvalue().lower())
            self.assertEqual(install.install(source, home), 0)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(install.install(source, home), 0)
            self.assertGreaterEqual(output.getvalue().lower().count("skip"), 4)

    def test_invalid_arguments_are_nonzero(self):
        with self.assertRaises(SystemExit) as raised:
            install.main(["--not-an-option"])
        self.assertNotEqual(raised.exception.code, 0)

    def test_real_agent_enumeration_includes_cleaner(self):
        source = install.source_root() / "opencode"
        entries = dict(install._entries(source))
        cleaner = source / "agents" / "cleaner.md"
        self.assertIn(cleaner, entries)
        self.assertEqual(entries[cleaner], Path("agents") / "cleaner.md")

    def test_real_implement_command_is_discovered_and_linked(self):
        source = install.source_root() / "opencode"
        implement = source / "commands" / "implement.md"
        entries = dict(install._entries(source))
        self.assertEqual(entries[implement], Path("commands") / "implement.md")

        with tempfile.TemporaryDirectory() as home:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(install.install(source, home), 0)
            destination = Path(home) / ".config" / "opencode" / "commands" / "implement.md"
            self.assertTrue(destination.is_symlink())
            self.assertEqual(os.readlink(destination), str(implement.resolve()))


if __name__ == "__main__":
    unittest.main()
