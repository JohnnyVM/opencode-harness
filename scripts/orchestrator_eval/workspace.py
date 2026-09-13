"""Construction of isolated, history-free evaluation workspaces."""

from dataclasses import dataclass
import fnmatch
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
from typing import Callable, Iterable


class WorkspaceError(RuntimeError):
    pass


@dataclass(frozen=True)
class Workspace:
    root: Path
    origin: Path
    candidate: Path
    commit: str


def _git(args: list[str], cwd: Path | None = None, runner=subprocess.run) -> str:
    result = runner(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)
    if result.returncode:
        raise WorkspaceError((result.stderr or "git command failed").strip())
    return result.stdout.strip()


def _safe_members(members, destination: Path):
    destination = destination.resolve()
    for member in members:
        target = (destination / member.name).resolve()
        if os.path.commonpath((str(destination), str(target))) != str(destination):
            raise WorkspaceError("source archive contains an unsafe path")
        if member.issym() or member.islnk():
            # Symlinks in source are not allowed to escape the materialized tree.
            link_target = (target.parent / member.linkname).resolve()
            if os.path.commonpath((str(destination), str(link_target))) != str(destination):
                raise WorkspaceError("source archive contains an escaping symlink")
        yield member


def materialize_source_tree(source_repo: Path, commit: str, destination: Path, runner=subprocess.run) -> None:
    """Extract exactly ``commit`` without checkout, index, or source mutation."""
    destination.mkdir(parents=True, exist_ok=True)
    result = runner(["git", "archive", "--format=tar", commit], cwd=source_repo,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode:
        raise WorkspaceError(result.stderr.decode() if isinstance(result.stderr, bytes) else result.stderr)
    import io
    with tarfile.open(fileobj=io.BytesIO(result.stdout), mode="r:") as archive:
        archive.extractall(destination, members=_safe_members(archive, destination))


def create_workspace(source_repo: Path, pinned_commit: str, root: Path,
                     candidate_branch: str = "eval/46-incorrect-name-resolution",
                     runner=subprocess.run) -> Workspace:
    """Create a parentless source commit, local origin, and clean candidate clone."""
    root = Path(root).resolve()
    source_repo = Path(source_repo).resolve()
    root.mkdir(parents=True, exist_ok=True)
    source = root / "source"
    materialize_source_tree(Path(source_repo), pinned_commit, source, runner)
    _git(["init", "--quiet", "--initial-branch=main"], source, runner)
    _git(["add", "-A"], source, runner)
    tree = _git(["write-tree"], source, runner)
    commit = _git(["-c", "user.name=Evaluation", "-c", "user.email=evaluation@localhost",
                   "commit-tree", tree, "-m", "evaluation source"], source, runner)
    _git(["update-ref", "refs/heads/main", commit], source, runner)
    origin = root / "origin.git"
    _git(["clone", "--bare", str(source), str(origin)], root, runner)
    candidate = root / "candidate"
    _git(["clone", str(origin), str(candidate)], root, runner)
    _git(["switch", "--create", candidate_branch], candidate, runner)
    return Workspace(root, origin, candidate, commit)


def copy_opencode_configuration(source: Path, candidate: Path,
                                sensitive: Iterable[str] = ("**/*token*", "**/*password*", "**/*credential*",
                                                            "**/*secret*", "auth.json", "credentials.json")) -> None:
    """Copy config while omitting publication credentials and sensitive files."""
    source, candidate = Path(source), Path(candidate)
    if not source.exists():
        return
    for item in source.rglob("*"):
        relative = item.relative_to(source)
        if any(fnmatch.fnmatch(str(relative), pattern) or fnmatch.fnmatch(item.name, pattern) for pattern in sensitive):
            continue
        target = candidate / relative
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif not item.is_symlink():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def expose_trace_and_auth(candidate_config: Path, trace: Path, auth: Path) -> None:
    """Expose only runtime trace and auth through symlinks into copied config."""
    destination = Path(candidate_config)
    destination.mkdir(parents=True, exist_ok=True)
    for name, target in (("trace", trace), ("auth", auth)):
        link = destination / name
        if link.exists() or link.is_symlink():
            link.unlink() if link.is_file() or link.is_symlink() else shutil.rmtree(link)
        link.symlink_to(Path(target).resolve())


def prepare_workspace(workspace: Workspace, config_source: Path | None = None,
                      trace: Path | None = None, auth: Path | None = None) -> Workspace:
    # Evaluation-only files must not turn the candidate into a dirty checkout.
    exclude = workspace.candidate / ".git" / "info" / "exclude"
    with exclude.open("a", encoding="utf-8") as stream:
        stream.write("\n.opencode/\n")
    if config_source:
        copy_opencode_configuration(config_source, workspace.candidate / ".opencode")
    if trace and auth:
        expose_trace_and_auth(workspace.candidate / ".opencode", trace, auth)
    return workspace
