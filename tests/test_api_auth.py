import os
import sys
from unittest.mock import patch

import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api.auth import get_api_key


def test_get_api_key_valid():
    with patch.dict(os.environ, {"API_KEY": "test-api-key"}):
        result = get_api_key("test-api-key")
        assert result == "test-api-key"


def test_get_api_key_missing():
    with pytest.raises(HTTPException) as exc_info:
        get_api_key(None)
    assert exc_info.value.status_code == 401
    assert "API key is required" in exc_info.value.detail


def test_get_api_key_invalid():
    with patch.dict(os.environ, {"API_KEY": "correct-key"}):
        with pytest.raises(HTTPException) as exc_info:
            get_api_key("wrong-key")
        assert exc_info.value.status_code == 401
        assert "Invalid API key" in exc_info.value.detail


def test_get_api_key_server_not_configured():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(HTTPException) as exc_info:
            get_api_key("any-key")
        assert exc_info.value.status_code == 500
        assert "API key not configured on server" in exc_info.value.detail
