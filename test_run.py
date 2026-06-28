"""Unit tests for run.py"""
import unittest
from unittest.mock import patch, MagicMock
import sys
import os
from pathlib import Path

# Add project root to path to allow importing run
project_root = Path(__file__).parent
if not (project_root / "run.py").exists():
    project_root = project_root.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import run

class TestRun(unittest.TestCase):
    def setUp(self):
        # Patch dependencies in run.py
        self.mock_sys = patch('run.sys').start()
        self.mock_os = patch('run.os').start()
        self.mock_subprocess = patch('run.subprocess').start()
        self.mock_path_cls = patch('run.Path').start()
        
        # Setup common mock objects
        self.mock_project_root = MagicMock()
        self.mock_project_root.__str__.return_value = "/app"
        
        # Configure Path(__file__).parent.absolute() to return mock_project_root
        self.mock_path_instance = self.mock_path_cls.return_value
        self.mock_path_instance.parent.absolute.return_value = self.mock_project_root
        
        # Setup venv path mock (project_root / "venv")
        self.mock_venv_path = MagicMock()
        self.mock_project_root.__truediv__.return_value = self.mock_venv_path
        
        # Default sys configuration
        self.mock_sys.path = []
        self.mock_sys.platform = "linux"
        self.mock_sys.executable = "/usr/bin/python"
        
        # Make os.environ.copy return a real dict for testing modifications
        self.mock_os.environ.copy.return_value = {}
        
    def tearDown(self):
        patch.stopall()

    def test_setup_paths(self):
        """Test that project root is added to sys.path and CWD is set."""
        # Setup
        self.mock_venv_path.exists.return_value = False
        
        # Mock frontend.main import to prevent ImportError
        with patch.dict(sys.modules, {'frontend.main': MagicMock()}):
            run.main()
            
        # Verify
        self.assertIn("/app", self.mock_sys.path)
        self.mock_os.chdir.assert_called_with(self.mock_project_root)

    def test_venv_restart_linux(self):
        """Test restarting with venv python on Linux."""
        # Setup Linux environment
        self.mock_sys.platform = "linux"
        self.mock_sys.executable = "/usr/bin/python"
        
        # Setup venv exists
        self.mock_venv_path.exists.return_value = True
        
        # Setup python executable path in venv
        mock_python_exe = MagicMock()
        mock_python_exe.exists.return_value = True
        mock_python_exe.__str__.return_value = "/app/venv/bin/python"
        
        # Handle path construction: venv_path / "bin" / "python"
        mock_bin = MagicMock()
        def venv_div_side_effect(arg):
            if arg == "bin": return mock_bin
            return MagicMock()
        self.mock_venv_path.__truediv__.side_effect = venv_div_side_effect
        
        def bin_div_side_effect(arg):
            if arg == "python": return mock_python_exe
            return MagicMock()
        mock_bin.__truediv__.side_effect = bin_div_side_effect

        # Run
        run.main()
        
        # Verify subprocess.run called with correct args
        self.mock_subprocess.run.assert_called_once()
        args, kwargs = self.mock_subprocess.run.call_args
        self.assertEqual(args[0], ["/app/venv/bin/python", "frontend/main.py"])
        self.assertEqual(kwargs['cwd'], "/app")
        self.assertIn("PYTHONPATH", kwargs['env'])
        self.assertIn("QTWEBENGINE_CHROMIUM_FLAGS", kwargs['env'])

    def test_venv_restart_windows(self):
        """Test restarting with venv python on Windows."""
        # Setup Windows environment
        self.mock_sys.platform = "win32"
        self.mock_sys.executable = "C:\\System\\python.exe"
        
        self.mock_venv_path.exists.return_value = True
        
        mock_python_exe = MagicMock()
        mock_python_exe.exists.return_value = True
        mock_python_exe.__str__.return_value = "C:\\app\\venv\\Scripts\\python.exe"
        
        # Handle path construction: venv_path / "Scripts" / "python.exe"
        mock_scripts = MagicMock()
        def venv_div_side_effect(arg):
            if arg == "Scripts": return mock_scripts
            return MagicMock()
        self.mock_venv_path.__truediv__.side_effect = venv_div_side_effect
        
        def scripts_div_side_effect(arg):
            if arg == "python.exe": return mock_python_exe
            return MagicMock()
        mock_scripts.__truediv__.side_effect = scripts_div_side_effect

        # Run
        run.main()
        
        # Verify
        self.mock_subprocess.run.assert_called_once()
        args, _ = self.mock_subprocess.run.call_args
        self.assertEqual(args[0][0], "C:\\app\\venv\\Scripts\\python.exe")

    def test_already_in_venv(self):
        """Test running directly when already inside the venv."""
        self.mock_sys.platform = "linux"
        venv_python = "/app/venv/bin/python"
        self.mock_sys.executable = venv_python
        
        self.mock_venv_path.exists.return_value = True
        
        mock_python_exe = MagicMock()
        mock_python_exe.exists.return_value = True
        mock_python_exe.__str__.return_value = venv_python
        
        # Setup path traversal
        mock_bin = MagicMock()
        self.mock_venv_path.__truediv__.side_effect = lambda x: mock_bin if x == "bin" else MagicMock()
        mock_bin.__truediv__.side_effect = lambda x: mock_python_exe if x == "python" else MagicMock()
        
        # Mock frontend import
        mock_app_main = MagicMock()
        mock_module = MagicMock()
        mock_module.main = mock_app_main
        
        with patch.dict(sys.modules, {'frontend.main': mock_module}):
            run.main()
            
        # Verify we did NOT restart
        self.mock_subprocess.run.assert_not_called()
        # Verify we called app_main
        mock_app_main.assert_called_once()

    def test_import_error(self):
        """Test that ImportError causes system exit."""
        self.mock_venv_path.exists.return_value = False
        
        # Force ImportError for frontend.main
        original_import = __import__
        def import_mock(name, *args, **kwargs):
            if name.startswith('frontend'):
                raise ImportError("Mocked import error")
            return original_import(name, *args, **kwargs)
            
        with patch('builtins.__import__', side_effect=import_mock):
            run.main()
            
        # Verify sys.exit(1) was called
        self.mock_sys.exit.assert_called_with(1)

    def test_broken_venv(self):
        """Test that we don't restart if venv exists but python is missing."""
        self.mock_sys.platform = "linux"
        self.mock_venv_path.exists.return_value = True
        
        # Mock python exe not existing
        mock_python_exe = MagicMock()
        mock_python_exe.exists.return_value = False
        
        # Setup path traversal
        mock_bin = MagicMock()
        self.mock_venv_path.__truediv__.side_effect = lambda x: mock_bin if x == "bin" else MagicMock()
        mock_bin.__truediv__.side_effect = lambda x: mock_python_exe if x == "python" else MagicMock()
        
        # Mock frontend import
        with patch.dict(sys.modules, {'frontend.main': MagicMock()}):
            run.main()
            
        # Verify we did NOT restart
        self.mock_subprocess.run.assert_not_called()

if __name__ == '__main__':
    unittest.main()