import os
import json
import pytest
from unittest.mock import patch, mock_open
from tfe_tools.common import sanitize_path, tfe_token, get_requests_session, mod_dependencies, find_mod_source

def test_sanitize_path():
    assert sanitize_path("~/test") == os.path.abspath(os.path.expanduser("~/test"))
    assert sanitize_path("$HOME/test") == os.path.abspath(os.path.expandvars("$HOME/test"))
    assert sanitize_path("/test") == os.path.abspath("/test")

@patch("builtins.open", new_callable=mock_open, read_data='{"credentials": [{"terraform.corp.clover.com": {"token": "test_token"}}]}')
@patch("os.path.isfile", return_value=True)
def test_tfe_token(mock_isfile, mock_open):
    assert tfe_token("terraform.corp.clover.com", "~/test") == "test_token"

@patch("tfe_tools.common.sanitize_path", return_value="/test")
@patch("builtins.open", new_callable=mock_open, read_data='{"credentials": {"terraform.corp.clover.com": {"token": "test_token"}}}')
@patch("os.path.isfile", return_value=True)
def test_tfe_token_with_sanitize_path(mock_isfile, mock_open, mock_sanitize_path):
    assert tfe_token("terraform.corp.clover.com", "~/test") == "test_token"

@patch("tfe_tools.common.sanitize_path", return_value="/test")
@patch("builtins.open", new_callable=mock_open, read_data='{"credentials": {"terraform.corp.clover.com": {"token": "test_token"}}}')
@patch("os.path.isfile", return_value=False)
@patch("os.environ.get", return_value="test_token")
def test_tfe_token_with_env_var(mock_get, mock_isfile, mock_open, mock_sanitize_path):
    assert tfe_token("terraform.corp.clover.com", "~/test") == "test_token"

@patch("tfe_tools.common.tfe_token", return_value="test_token")
def test_get_requests_session(mock_tfe_token):
    session = get_requests_session()
    assert session.headers["Authorization"] == "Bearer test_token"
    assert session.headers["Content-Type"] == "application/vnd.api+json"

@patch("glob.glob", return_value=["test.tf"])
@patch("builtins.open", new_callable=mock_open, read_data='{"module": {"test_module": {"source": "test_source"}}}')
def test_mod_dependencies(mock_open, mock_glob):
    assert mod_dependencies("test_module") == {"test_module": "test_source"}

@patch("subprocess.Popen")
def test_find_mod_source(mock_popen):
    mock_popen.return_value.communicate.return_value = (json.dumps({"test": "test"}).encode("utf-8"), b"")
    assert find_mod_source("test_source") == {"test": "test"}
