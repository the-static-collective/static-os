"""LAUNCHPAD-001: validate user-scope wrapper without package install/VM effects."""
from pathlib import Path
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/start-train.sh"

class LaunchpadTests(unittest.TestCase):
    def test_script_syntax_and_help(self):
        subprocess.run(["bash","-n",str(SCRIPT)],check=True)
        help_=subprocess.run(["bash",str(SCRIPT),"--help"],check=True,text=True,
                            capture_output=True).stdout
        self.assertIn("--start",help_)
        self.assertIn("--check",help_)
        self.assertIn("NOT as root",help_)

    def test_unknown_mode_refuses(self):
        result=subprocess.run(["bash",str(SCRIPT),"--format"],text=True,capture_output=True)
        self.assertEqual(result.returncode,2)
        self.assertIn("unknown launch mode",result.stderr)

    def test_no_privileged_or_destructive_command_in_script(self):
        content=SCRIPT.read_text(encoding="utf-8")
        for unexpected in ("sudo ", "mkfs", "dd if=", "lb build", "virsh destroy",
                           "git reset --hard", "git checkout -f", "curl | bash"):
            self.assertNotIn(unexpected,content)
        self.assertIn('if [[ "$(id -u)" -eq 0 ]]',content)
        self.assertIn('git -C "$WORKTREE" checkout --detach "$HOUSE_SHA"',content)

if __name__=="__main__": unittest.main()
