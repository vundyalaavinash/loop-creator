from unittest.mock import MagicMock, patch
from loop_creator.adapters.devin import DevinAdapter
import pytest


def _mock_run(stdout: str, returncode: int = 0) -> MagicMock:
    m = MagicMock(); m.stdout = stdout; m.stderr = ""; m.returncode = returncode
    return m


def test_cli_call_returns_text():
    with patch("loop_creator.adapters.devin.shutil.which", return_value="/usr/bin/devin"), \
         patch("loop_creator.adapters.devin.subprocess.run", return_value=_mock_run("ok")):
        assert DevinAdapter().call("s", "u") == "ok"


def test_is_available_true_when_cli_found():
    with patch("loop_creator.adapters.devin.shutil.which", return_value="/usr/bin/devin"):
        assert DevinAdapter().is_available() is True


def test_is_available_true_when_api_key_set():
    with patch("loop_creator.adapters.devin.shutil.which", return_value=None):
        assert DevinAdapter(api_key="tok-123").is_available() is True


def test_is_available_false_when_neither():
    with patch("loop_creator.adapters.devin.shutil.which", return_value=None):
        assert DevinAdapter(api_key="").is_available() is False


def test_raises_when_neither_cli_nor_key():
    with patch("loop_creator.adapters.devin.shutil.which", return_value=None):
        with pytest.raises(RuntimeError, match="not available"):
            DevinAdapter(api_key="").call("s", "u")
