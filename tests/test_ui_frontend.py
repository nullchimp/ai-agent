import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add src to path to import serve_ui
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from serve_ui import serve_ui


def test_ui_files_exist():
    """Test that all required UI files exist"""
    ui_dir = Path(__file__).parent.parent / "src" / "ui"
    dist_dir = ui_dir / "dist"

    assert ui_dir.exists(), "UI directory should exist"
    assert (ui_dir / "index.html").exists(), "index.html should exist"
    assert (ui_dir / "styles.css").exists(), "styles.css should exist"
    assert (dist_dir / "chat.js").exists(), "chat.js should exist"
    assert (ui_dir / "chat.ts").exists(), "chat.ts should exist"


def test_html_structure():
    """Test that HTML contains required elements"""
    ui_dir = Path(__file__).parent.parent / "src" / "ui"
    html_file = ui_dir / "index.html"

    content = html_file.read_text()

    # Check for essential elements
    assert '<div id="app">' in content, "Should have main app container"
    assert '<div class="sidebar">' in content, "Should have sidebar"
    assert '<div class="main-content">' in content, "Should have main content area"
    assert 'id="messageInput"' in content, "Should have message input"
    assert 'id="sendBtn"' in content, "Should have send button"
    assert 'chat.js' in content, "Should include JavaScript file"
    assert 'styles.css' in content, "Should include CSS file"


def test_css_contains_chatgpt_styling():
    """Test that CSS contains ChatGPT-like styling"""
    ui_dir = Path(__file__).parent.parent / "src" / "ui"
    css_file = ui_dir / "styles.css"

    content = css_file.read_text()

    # Check for key CSS classes and properties
    assert '.sidebar' in content, "Should have sidebar styling"
    assert '.message' in content, "Should have message styling"
    assert '.chat-container' in content, "Should have chat container styling"
    assert '.input-container' in content, "Should have input styling"
    assert '.typing-indicator' in content, "Should have typing indicator"
    assert 'flex' in content, "Should use flexbox layout"
    assert 'border-radius' in content, "Should have rounded corners"


def test_typescript_compiles():
    """Test that TypeScript file exists and has proper structure"""
    ui_dir = Path(__file__).parent.parent / "src" / "ui"
    ts_file = ui_dir / "chat.ts"
    js_file = ui_dir / "dist" / "chat.js"

    ts_content = ts_file.read_text()

    # Check TypeScript structure
    assert 'interface Message' in ts_content, "Should define Message interface"
    assert 'interface ChatSession' in ts_content, "Should define ChatSession interface"
    assert 'class ChatApp' in ts_content, "Should define ChatApp class"
    assert 'private apiBaseUrl' in ts_content, "Should have API configuration"
    assert 'addEventListener' in ts_content, "Should set up event listeners"

    # Check that JavaScript was compiled
    assert js_file.exists(), "JavaScript file should be compiled from TypeScript"


@patch('socketserver.TCPServer')
@patch('os.chdir')
def test_serve_ui_server_setup(mock_chdir, mock_tcpserver):
    """Test that UI server sets up correctly"""
    mock_server = MagicMock()
    mock_tcpserver.return_value.__enter__.return_value = mock_server

    # Mock the UI directory to exist
    with patch('pathlib.Path.exists', return_value=True):
        # This should not raise an exception
        try:
            serve_ui(8080)
        except KeyboardInterrupt:
            pass  # Expected when mocking server

    # Verify server setup
    mock_tcpserver.assert_called_once()
    mock_chdir.assert_called_once()


def test_serve_ui_handles_missing_directory():
    """Test that server handles missing UI directory gracefully"""
    with patch('pathlib.Path.exists', return_value=False):
        with pytest.raises(SystemExit):
            serve_ui(8080)


def test_javascript_api_integration():
    """Test that compiled JavaScript contains API integration code"""
    ui_dir = Path(__file__).parent.parent / "src" / "ui"
    js_file = ui_dir / "dist" / "chat.js"

    content = js_file.read_text()

    # Check for API-related functionality
    assert 'fetch(' in content, "Should have fetch API calls"
    assert 'POST' in content, "Should make POST requests"
    assert 'Content-Type' in content, "Should set content type"
    assert 'localhost:5555' in content, "Should have default API endpoint"


def test_ui_responsive_design():
    """Test that CSS includes responsive design elements"""
    ui_dir = Path(__file__).parent.parent / "src" / "ui"
    css_file = ui_dir / "styles.css"

    content = css_file.read_text()

    # Check for responsive design
    assert '@media' in content, "Should have media queries"
    assert 'max-width: 768px' in content or 'max-width:768px' in content, "Should have mobile breakpoint"
    assert 'viewport' in Path(ui_dir / "index.html").read_text(), "HTML should have viewport meta tag"


def test_chat_functionality_structure():
    """Test that TypeScript defines proper chat functionality"""
    ui_dir = Path(__file__).parent.parent / "src" / "ui"
    ts_file = ui_dir / "chat.ts"

    content = ts_file.read_text()

    # Check for essential methods
    assert 'sendMessage' in content, "Should have sendMessage method"
    assert 'displayMessage' in content, "Should have displayMessage method"
    assert 'createNewSession' in content, "Should have session management"
    assert 'localStorage' in content, "Should persist chat history"
    assert 'typing-indicator' in content or 'typingIndicator' in content, "Should show typing indicators"


def test_package_json_scripts():
    """Test that package.json has the required scripts"""
    package_file = Path(__file__).parent.parent / "package.json"

    if package_file.exists():
        import json
        content = json.loads(package_file.read_text())

        scripts = content.get('scripts', {})
        assert 'ui:build' in scripts, "Should have build-ui script"
        assert 'ui:serve' in scripts, "Should have serve-ui script"
