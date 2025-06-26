import pytest
from pathlib import Path
from unittest.mock import patch
import json
from fastapi.testclient import TestClient

# Add src to path to import api.app
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from api.app import create_app


def test_ui_files_exist():
    """Test that all required UI files exist"""
    ui_dir = Path(__file__).parent.parent / "src" / "ui"
    dist_dir = ui_dir / "dist"

    assert ui_dir.exists(), "UI directory should exist"
    assert (ui_dir / "index.html").exists(), "index.html should exist"
    assert (ui_dir / "styles.css").exists(), "styles.css should exist"
    assert (dist_dir / "chat.js").exists(), "chat.js should exist"
    
    # Check for new modular TypeScript structure
    assert (ui_dir / "types.ts").exists(), "types.ts should exist"
    assert (ui_dir / "ChatApp.ts").exists(), "ChatApp.ts should exist"
    assert (ui_dir / "ChatComponent.ts").exists(), "ChatComponent.ts should exist"
    assert (ui_dir / "SessionComponent.ts").exists(), "SessionComponent.ts should exist"
    assert (ui_dir / "ToolsComponent.ts").exists(), "ToolsComponent.ts should exist"
    assert (ui_dir / "DebugComponent.ts").exists(), "DebugComponent.ts should exist"


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
    """Test that TypeScript components exist and compile to proper structure"""
    ui_dir = Path(__file__).parent.parent / "src" / "ui"
    js_file = ui_dir / "dist" / "chat.js"

    # Check that TypeScript components exist
    assert (ui_dir / "types.ts").exists(), "Should have types.ts with interfaces"
    assert (ui_dir / "ChatApp.ts").exists(), "Should have ChatApp.ts"
    assert (ui_dir / "SessionComponent.ts").exists(), "Should have SessionComponent.ts"
    assert (ui_dir / "ToolsComponent.ts").exists(), "Should have ToolsComponent.ts"
    assert (ui_dir / "DebugComponent.ts").exists(), "Should have DebugComponent.ts"
    assert (ui_dir / "ChatComponent.ts").exists(), "Should have ChatComponent.ts"

    # Check types.ts structure
    types_content = (ui_dir / "types.ts").read_text()
    assert 'interface Message' in types_content, "Should define Message interface"
    assert 'interface ChatSession' in types_content, "Should define ChatSession interface"
    assert 'class EventEmitter' in types_content, "Should define EventEmitter class"

    # Check ChatApp.ts structure
    chatapp_content = (ui_dir / "ChatApp.ts").read_text()
    assert 'class ChatApp' in chatapp_content, "Should define ChatApp class"
    assert 'DOMContentLoaded' in chatapp_content, "Should set up initialization"

    # Check that JavaScript was compiled and bundled
    assert js_file.exists(), "JavaScript file should be compiled from TypeScript"
    
    js_content = js_file.read_text()
    assert 'EventEmitter' in js_content, "Should include EventEmitter"
    assert 'SessionComponent' in js_content, "Should include SessionComponent"
    assert 'ToolsComponent' in js_content, "Should include ToolsComponent"
    assert 'DebugComponent' in js_content, "Should include DebugComponent"
    assert 'ChatComponent' in js_content, "Should include ChatComponent"
    assert 'ChatApp' in js_content, "Should include ChatApp"


def test_api_serves_static_files():
    """Test that the FastAPI app serves the static UI files."""
    app = create_app()
    client = TestClient(app)

    # The app mounts static files from src/ui/dist.
    # We need to make sure those files exist for the test.
    dist_dir = Path(__file__).parent.parent / "src" / "ui" / "dist"
    
    # This test assumes `npm run ui:build` has been run.
    if not dist_dir.exists() or not (dist_dir / "index.html").exists():
        pytest.skip("UI files not built. Run 'npm run ui:build' before testing.")

    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

    response = client.get("/styles.css")
    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]

    response = client.get("/chat.js")
    assert response.status_code == 200
    assert "application/javascript" in response.headers["content-type"]


@patch("os.path.exists", return_value=False)
def test_api_does_not_serve_static_files_if_missing(mock_exists):
    """Test that the FastAPI app does not mount static files if the directory is missing."""
    app = create_app()
    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 404


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
    """Test that TypeScript defines proper chat functionality in components"""
    ui_dir = Path(__file__).parent.parent / "src" / "ui"
    
    # Check ChatComponent has message functionality
    chat_content = (ui_dir / "ChatComponent.ts").read_text()
    assert 'sendMessage' in chat_content, "Should have sendMessage method"
    assert 'displayMessage' in chat_content, "Should have displayMessage method"
    
    # Check SessionComponent has session management
    session_content = (ui_dir / "SessionComponent.ts").read_text()
    assert 'createNewSession' in session_content, "Should have session management"
    assert 'localStorage' in session_content, "Should persist chat history"
    
    # Check ToolsComponent has tool management
    tools_content = (ui_dir / "ToolsComponent.ts").read_text()
    assert 'loadTools' in tools_content, "Should have tool loading"
    assert 'toggleTool' in tools_content, "Should have tool toggling"
    
    # Check DebugComponent has debug functionality
    debug_content = (ui_dir / "DebugComponent.ts").read_text()
    assert 'loadDebugEvents' in debug_content, "Should have debug event loading"
    assert 'toggleDebugPanel' in debug_content, "Should have debug panel control"
    
    # Check compiled JavaScript has typing indicators
    js_file = ui_dir / "dist" / "chat.js"
    js_content = js_file.read_text()
    assert 'typing-indicator' in js_content or 'typingIndicator' in js_content, "Should show typing indicators"


def test_package_json_scripts():
    """Test that package.json has the required scripts"""
    package_file = Path(__file__).parent.parent / "package.json"

    if package_file.exists():
        content = json.loads(package_file.read_text())

        scripts = content.get('scripts', {})
        assert 'ui:build' in scripts, "Should have ui:build script"


def test_tool_highlighting_css():
    """Test that CSS contains proper styling for tool highlighting"""
    ui_dir = Path(__file__).parent.parent / "src" / "ui"
    css_file = ui_dir / "styles.css"

    content = css_file.read_text()

    # Check for tool-related CSS classes
    assert '.tool-item' in content, "Should have tool-item styling"
    assert '.tool-item.enabled' in content, "Should have enabled tool highlighting"
    assert '.tool-item.enabled:hover' in content, "Should have enabled tool hover state"
    
    # Check for light blue highlighting colors
    assert '#dbeafe' in content, "Should have light blue background for enabled tools"
    assert '#bfdbfe' in content, "Should have light blue border and hover states"
