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
        (source / "contracts").mkdir(parents=True)
        (source / "scripts").mkdir(parents=True)
        (source / "opencode.jsonc").write_text("{}")
        (source / "agents" / "z.md").write_text("z")
        (source / "agents" / "ignore.txt").write_text("ignore")
        (source / "commands" / "a.md").write_text("a")
        (source / "contracts" / "package.md").write_text("contract")
        (source / "scripts" / "validate.py").write_text("validator")
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
                destination / "contracts" / "package.md": source / "contracts" / "package.md",
                destination / "scripts" / "validate.py": source / "scripts" / "validate.py",
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

    def test_real_conditional_agents_are_discovered_and_linked(self):
        """Test that the new conditional agents are discovered and linked by the installer."""
        source = install.source_root() / "opencode"
        test_investigation = source / "agents" / "test-investigation.md"
        code_pattern = source / "agents" / "code-pattern.md"
        
        # Check that both conditional agents exist
        self.assertTrue(test_investigation.exists(), "test-investigation.md should exist")
        self.assertTrue(code_pattern.exists(), "code-pattern.md should exist")
        
        # Check that they are enumerated by the installer
        entries = dict(install._entries(source))
        self.assertIn(test_investigation, entries)
        self.assertIn(code_pattern, entries)
        self.assertEqual(entries[test_investigation], Path("agents") / "test-investigation.md")
        self.assertEqual(entries[code_pattern], Path("agents") / "code-pattern.md")

        # Test that they get linked correctly during installation
        with tempfile.TemporaryDirectory() as home:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(install.install(source, home), 0)
            
            # Check that both agents are linked
            destination_test_investigation = Path(home) / ".config" / "opencode" / "agents" / "test-investigation.md"
            destination_code_pattern = Path(home) / ".config" / "opencode" / "agents" / "code-pattern.md"
            
            self.assertTrue(destination_test_investigation.is_symlink())
            self.assertTrue(destination_code_pattern.is_symlink())
            self.assertEqual(os.readlink(destination_test_investigation), str(test_investigation.resolve()))
            self.assertEqual(os.readlink(destination_code_pattern), str(code_pattern.resolve()))

    def test_real_contract_and_validator_are_discovered_and_linked(self):
        source = install.source_root() / "opencode"
        contract = source / "contracts" / "implementation-package.md"
        validator = source / "scripts" / "validate_implementation_package.py"
        entries = dict(install._entries(source))
        self.assertEqual(entries[contract], Path("contracts") / contract.name)
        self.assertEqual(entries[validator], Path("scripts") / validator.name)

        with tempfile.TemporaryDirectory() as home:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(install.install(source, home), 0)
            for item, folder in ((contract, "contracts"), (validator, "scripts")):
                destination = Path(home) / ".config" / "opencode" / folder / item.name
                self.assertTrue(destination.is_symlink())
                self.assertEqual(os.readlink(destination), str(item.resolve()))

    def test_implement_command_and_plugin_are_installed(self):
        source = install.source_root() / "opencode"
        command = source / "commands" / "implement.md"
        plugin = source / "plugins" / "implement.js"
        entries = dict(install._entries(source))
        self.assertEqual(entries[command], Path("commands") / command.name)
        self.assertEqual(entries[plugin], Path("plugins") / plugin.name)

        with tempfile.TemporaryDirectory() as home:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(install.install(source, home), 0)
            for item, folder in ((command, "commands"), (plugin, "plugins")):
                destination = Path(home) / ".config" / "opencode" / folder / item.name
                self.assertTrue(destination.is_symlink())
                self.assertEqual(os.readlink(destination), str(item.resolve()))


if __name__ == "__main__":
    unittest.main()
