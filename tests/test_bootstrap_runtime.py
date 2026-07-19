from __future__ import annotations

import subprocess
import unittest
from unittest import mock

from _load import load_script

bootstrap = load_script("bootstrap_runtime")


class BootstrapRuntimeTests(unittest.TestCase):
    def test_supported_python_is_accepted(self):
        completed = subprocess.CompletedProcess([], 0, stdout="3.13.5\n", stderr="")
        with mock.patch.object(bootstrap.subprocess, "run", return_value=completed):
            self.assertEqual(bootstrap.inspect_python("python3"), (3, 13, 5))

    def test_unsupported_explicit_python_is_rejected(self):
        completed = subprocess.CompletedProcess([], 0, stdout="3.9.19\n", stderr="")
        with mock.patch.object(bootstrap.subprocess, "run", return_value=completed):
            with self.assertRaisesRegex(SystemExit, "needs Python 3.10-3.13"):
                bootstrap.inspect_python("python3")

    def test_unparseable_python_version_is_rejected(self):
        completed = subprocess.CompletedProcess([], 0, stdout="unknown\n", stderr="")
        with mock.patch.object(bootstrap.subprocess, "run", return_value=completed):
            with self.assertRaisesRegex(SystemExit, "Could not inspect"):
                bootstrap.inspect_python("python3")


if __name__ == "__main__":
    unittest.main()
