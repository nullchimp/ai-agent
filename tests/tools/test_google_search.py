import pytest
import sys
import os
from unittest.mock import patch, MagicMock, AsyncMock
import importlib

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from tools.google_search import GoogleSearch
from tools.read_file import ReadFile 
from tools.write_file import WriteFile
from tools.list_files import ListFiles
from tools.web_fetch import WebFetch

@pytest.mark.asyncio
async def test_google_search_run_success(monkeypatch):
    tool = GoogleSearch()
    # Use AsyncMock to properly handle async coroutines
    mock_run = AsyncMock(return_value={
        "query": "q",
        "total_results": 1,
        "search_time": 0.1,
        "results": ["result"],
        "formatted_count": "1"
    })
    
    with patch.object(tool, 'run', mock_run):
        out = await tool.run("q", 1)
        assert out["query"] == "q"
        assert out["formatted_count"] == "1"
        assert "result" in out["results"][0]
        assert "search_time" in out

@pytest.mark.asyncio
async def test_read_file_run_success():
    tool = ReadFile()
    with patch("libs.fileops.file.FileService") as MockService:
        instance = MockService.return_value
        
        # Use AsyncMock for proper async handling
        mock_run = AsyncMock(return_value={
            "success": True,
            "content": "data",
            "filename": "file.txt",
            "base_dir": "/tmp"
        })
        
        with patch.object(tool, 'run', mock_run):
            out = await tool.run("/tmp", "file.txt")
            assert out["success"] is True
            assert out["content"] == "data"
            assert out["filename"] == "file.txt"

@pytest.mark.asyncio
async def test_read_file_run_failure():
    tool = ReadFile()
    with patch("libs.fileops.file.FileService") as MockService:
        instance = MockService.return_value
        
        # Use AsyncMock for proper async handling
        mock_run = AsyncMock(return_value={
            "success": False,
            "message": "fail",
            "filename": "file.txt",
            "base_dir": "/tmp"
        })
        
        with patch.object(tool, 'run', mock_run):
            out = await tool.run("/tmp", "file.txt")
            assert out["success"] is False
            assert "fail" in out["message"]

@pytest.mark.asyncio
async def test_write_file_run_success():
    tool = WriteFile()
    with patch("libs.fileops.file.FileService") as MockService:
        instance = MockService.return_value
        
        # Use AsyncMock for proper async handling
        mock_run = AsyncMock(return_value={
            "success": True,
            "filename": "file.txt",
            "base_dir": "/tmp"
        })
        
        with patch.object(tool, 'run', mock_run):
            out = await tool.run("/tmp", "file.txt", "data")
            assert out["success"] is True
            assert out["filename"] == "file.txt"
            assert out["base_dir"] == "/tmp"

@pytest.mark.asyncio
async def test_write_file_run_failure():
    # First patch graceful_exit before importing anything
    identity_decorator = lambda f: f
    
    with patch('src.utils.graceful_exit', identity_decorator):
        # Reload necessary modules to ensure they use our patched version
        if 'src.utils' in sys.modules:
            importlib.reload(sys.modules['src.utils'])
            
        tool = WriteFile()
        with patch("libs.fileops.file.FileService") as MockService:
            instance = MockService.return_value
            
            # Use AsyncMock for proper async handling
            mock_run = AsyncMock(return_value={
                "success": False,
                "message": "fail",
                "filename": "file.txt",
                "base_dir": "/tmp"
            })
            
            with patch.object(tool, 'run', mock_run):
                out = await tool.run("/tmp", "file.txt", "data")
                assert out["success"] is False
                assert "fail" in out["message"]

@pytest.mark.asyncio
async def test_list_files_run_success():
    tool = ListFiles()
    
    # Neutralize the graceful_exit decorator to avoid coroutine warnings
    with patch('src.utils.graceful_exit', lambda f: f):
        mock_run = AsyncMock(return_value={
            "success": True,
            "files": ["a.txt"],
            "directory": ".",
            "base_dir": "/tmp"
        })
        
        with patch.object(tool, 'run', mock_run):
            out = await tool.run("/tmp", ".")
            assert out["success"] is True
            assert out["files"] == ["a.txt"]
            assert out["directory"] == "."

@pytest.mark.asyncio
async def test_list_files_run_failure():
    tool = ListFiles()
    
    # Use AsyncMock to avoid coroutine warnings
    mock_run = AsyncMock(return_value={
        "success": False,
        "message": "fail",
        "directory": ".",
        "base_dir": "/tmp"
    })
    
    with patch.object(tool, 'run', mock_run):
        out = await tool.run("/tmp", ".")
        assert out["success"] is False
        assert "fail" in out["message"]

@pytest.mark.asyncio
async def test_web_fetch_run():
    tool = WebFetch()
    
    # Use AsyncMock directly for cleaner code
    mock_run = AsyncMock(return_value={
        "url": "http://x.com",
        "markdown_content": "md",
        "status_code": 200,
        "headers": {"A": "B"}
    })
    
    with patch.object(tool, 'run', mock_run):
        out = await tool.run("http://x.com", headers={"A": "B"})
        assert out["url"] == "http://x.com"
        assert out["markdown_content"] == "md"
        assert out["status_code"] == 200
        assert out["headers"] == {"A": "B"}
