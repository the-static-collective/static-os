import importlib.util
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "config"
    / "includes.chroot"
    / "usr"
    / "local"
    / "bin"
    / "static-git"
)
SPEC = importlib.util.spec_from_file_location("static_git", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class GitBridgeUnitTests(unittest.TestCase):
    def test_refuses_embedded_https_credentials(self):
        with self.assertRaisesRegex(ValueError, "credentials"):
            MODULE.validate_remote("https://token:secret@github.com/example/repo.git")

    def test_accepts_https_and_ssh_remotes(self):
        self.assertEqual(
            MODULE.validate_remote("https://github.com/the-static-collective/static-os.git"),
            "https://github.com/the-static-collective/static-os.git",
        )
        self.assertEqual(
            MODULE.validate_remote("git@github.com:the-static-collective/static-os.git"),
            "git@github.com:the-static-collective/static-os.git",
        )

    def test_repo_must_stay_under_static_root(self):
        with tempfile.TemporaryDirectory() as home:
            with patch.dict(os.environ, {"HOME": home}):
                root = Path(home) / "static"
                root.mkdir()
                with self.assertRaisesRegex(ValueError, "under"):
                    MODULE.repo_path(str(Path(home) / "elsewhere"), must_exist=False)

    def test_explicit_paths_cannot_escape_repo(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory).resolve()
            with self.assertRaisesRegex(ValueError, "escapes"):
                MODULE.normalize_paths(repo, ["../secret"])


class GitBridgeIntegrationTests(unittest.TestCase):
    def git(self, cwd, *args, capture=False):
        result = subprocess.run(
            ["git", "-C", str(cwd), *args],
            check=True,
            text=True,
            stdout=subprocess.PIPE if capture else None,
        )
        return result.stdout.strip() if capture else ""

    def seed(self, base: Path):
        remote = base / "remote.git"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, stdout=subprocess.DEVNULL)
        seed = base / "seed"
        subprocess.run(["git", "clone", str(remote), str(seed)], check=True, stdout=subprocess.DEVNULL)
        self.git(seed, "config", "user.email", "test@example.invalid")
        self.git(seed, "config", "user.name", "Static Test")
        (seed / "hello.txt").write_text("one\n", encoding="utf-8")
        self.git(seed, "add", "hello.txt")
        self.git(seed, "commit", "-m", "seed")
        self.git(seed, "push", "-u", "origin", "HEAD")
        branch = self.git(seed, "branch", "--show-current", capture=True)
        return remote, seed, branch

    def test_receive_is_fast_forward_only_and_send_uses_existing_remote(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            remote, seed, branch = self.seed(base)
            home = base / "home"
            static = home / "static"
            static.mkdir(parents=True)
            local = static / "local"
            subprocess.run(["git", "clone", str(remote), str(local)], check=True, stdout=subprocess.DEVNULL)
            self.git(local, "config", "user.email", "test@example.invalid")
            self.git(local, "config", "user.name", "Static Test")

            (seed / "hello.txt").write_text("two\n", encoding="utf-8")
            self.git(seed, "add", "hello.txt")
            self.git(seed, "commit", "-m", "remote update")
            self.git(seed, "push")

            with patch.dict(os.environ, {"HOME": str(home)}):
                args = type("Args", (), {"repo": "local"})()
                MODULE.cmd_receive(args)
                self.assertEqual((local / "hello.txt").read_text(encoding="utf-8"), "two\n")

                (local / "out.txt").write_text("from static os\n", encoding="utf-8")
                commit_args = type(
                    "Args",
                    (),
                    {"repo": "local", "message": "outbound", "path": ["out.txt"]},
                )()
                MODULE.cmd_commit(commit_args)
                MODULE.cmd_send(args)

            self.git(seed, "pull", "--ff-only")
            self.assertEqual((seed / "out.txt").read_text(encoding="utf-8"), "from static os\n")


if __name__ == "__main__":
    unittest.main()
