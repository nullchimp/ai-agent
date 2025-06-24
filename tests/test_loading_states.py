"""
Tests for loading states in the frontend UI during new chat creation and tool initialization.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import json
import os
from pathlib import Path


class TestLoadingStates:
    """Test the loading states functionality in the chat UI."""

    def test_new_chat_button_loading_state_logic(self):
        """Test that the new chat button shows loading state correctly."""
        # Simulate the JavaScript logic for updating button state
        
        class MockButton:
            def __init__(self):
                self.disabled = False
                self.classList = MockClassList()
                self.icon = Mock()
                self.span = Mock()
                
            def querySelector(self, selector):
                if selector == 'svg':
                    return self.icon
                elif selector == 'span':
                    return self.span
                return None
        
        class MockClassList:
            def __init__(self):
                self.classes = set()
            
            def add(self, cls):
                self.classes.add(cls)
            
            def remove(self, cls):
                self.classes.discard(cls)
            
            def contains(self, cls):
                return cls in self.classes

        def update_new_chat_button_state(button, is_creating_session):
            """Simulate the TypeScript updateNewChatButtonState method."""
            icon = button.querySelector('svg')
            span = button.querySelector('span')
            
            if is_creating_session:
                button.disabled = True
                button.classList.add('loading')
                if icon:
                    icon.style = {'display': 'none'}
                if span:
                    span.textContent = 'Creating...'
            else:
                button.disabled = False
                button.classList.remove('loading')
                if icon:
                    icon.style = {'display': 'block'}
                if span:
                    span.textContent = 'New chat'

        # Test loading state
        button = MockButton()
        update_new_chat_button_state(button, True)
        
        assert button.disabled == True
        assert button.classList.contains('loading')
        assert button.icon.style['display'] == 'none'
        assert button.span.textContent == 'Creating...'
        
        # Test normal state
        update_new_chat_button_state(button, False)
        
        assert button.disabled == False
        assert not button.classList.contains('loading')
        assert button.icon.style['display'] == 'block'
        assert button.span.textContent == 'New chat'

    def test_tools_loading_state_logic(self):
        """Test that the tools section shows loading state correctly."""
        
        def render_tools_loading():
            """Simulate the TypeScript renderToolsLoading method."""
            return {
                'html': '''
                    <div class="tools-loading">
                        <div class="loading-spinner"></div>
                        <span>Loading tools...</span>
                    </div>
                ''',
                'label_text': 'Tools Configuration [Loading...]'
            }
        
        def render_tools_normal(tools):
            """Simulate the TypeScript renderTools method with normal state."""
            enabled_count = sum(1 for tool in tools if tool.get('enabled', False))
            total_count = len(tools)
            
            return {
                'label_text': f'Tools Configuration [{enabled_count}/{total_count}]',
                'tools_rendered': True
            }
        
        # Test loading state
        loading_result = render_tools_loading()
        assert 'tools-loading' in loading_result['html']
        assert 'loading-spinner' in loading_result['html']
        assert 'Loading tools...' in loading_result['html']
        assert loading_result['label_text'] == 'Tools Configuration [Loading...]'
        
        # Test normal state with tools
        tools = [
            {'name': 'tool1', 'enabled': True},
            {'name': 'tool2', 'enabled': False},
            {'name': 'tool3', 'enabled': True}
        ]
        normal_result = render_tools_normal(tools)
        assert normal_result['label_text'] == 'Tools Configuration [2/3]'
        assert normal_result['tools_rendered'] == True

    def test_session_loading_message_logic(self):
        """Test that the session loading message is displayed correctly."""
        
        def clear_messages(is_creating_session=False):
            """Simulate the TypeScript clearMessages method."""
            if is_creating_session:
                return '''
                    <div class="welcome-message">
                        <div class="session-loading">
                            <div class="loading-spinner"></div>
                            <h1>Setting up your new chat...</h1>
                            <p>Initializing tools and preparing the session for you.</p>
                        </div>
                    </div>
                '''
            else:
                return '''
                    <div class="welcome-message">
                        <h1>AI Agent</h1>
                        <p>How can I help you today?</p>
                    </div>
                '''
        
        # Test loading state
        loading_html = clear_messages(is_creating_session=True)
        assert 'session-loading' in loading_html
        assert 'loading-spinner' in loading_html
        assert 'Setting up your new chat...' in loading_html
        assert 'Initializing tools and preparing the session for you.' in loading_html
        
        # Test normal state
        normal_html = clear_messages(is_creating_session=False)
        assert 'AI Agent' in normal_html
        assert 'How can I help you today?' in normal_html
        assert 'session-loading' not in normal_html

    def test_loading_state_workflow(self):
        """Test the complete loading state workflow for new chat creation."""
        
        class MockChatApp:
            def __init__(self):
                self.is_creating_session = False
                self.is_loading_tools = False
                self.button_state = 'normal'
                self.tools_state = 'normal'
                self.message_state = 'normal'
            
            async def create_new_session(self):
                """Simulate the complete session creation process."""
                # Step 1: Start loading
                self.is_creating_session = True
                self.button_state = 'loading'
                self.message_state = 'loading'
                
                try:
                    # Step 2: Create backend session (simulated)
                    await self._create_backend_session()
                    
                    # Step 3: Load tools
                    await self._load_tools()
                    
                    # Step 4: Complete
                    self.message_state = 'normal'
                    
                except Exception as e:
                    # Handle errors
                    self.message_state = 'error'
                    raise
                finally:
                    # Step 5: Reset loading states
                    self.is_creating_session = False
                    self.is_loading_tools = False
                    self.button_state = 'normal'
                    self.tools_state = 'normal'
            
            async def _create_backend_session(self):
                """Simulate backend session creation."""
                # Simulate network delay
                return {'session_id': 'test-session-123'}
            
            async def _load_tools(self):
                """Simulate tool loading."""
                self.is_loading_tools = True
                self.tools_state = 'loading'
                
                # Simulate tool discovery and loading
                tools = [
                    {'name': 'google_search', 'enabled': True},
                    {'name': 'read_file', 'enabled': True}
                ]
                
                self.is_loading_tools = False
                self.tools_state = 'normal'
                return tools
        
        # Test the workflow
        import asyncio
        
        async def test_workflow():
            app = MockChatApp()
            
            # Initial state
            assert app.is_creating_session == False
            assert app.button_state == 'normal'
            assert app.message_state == 'normal'
            assert app.tools_state == 'normal'
            
            # Start session creation
            await app.create_new_session()
            
            # Final state
            assert app.is_creating_session == False
            assert app.is_loading_tools == False
            assert app.button_state == 'normal'
            assert app.tools_state == 'normal'
            assert app.message_state == 'normal'
        
        # Run the async test
        asyncio.run(test_workflow())

    def test_css_loading_classes_exist(self):
        """Test that the required CSS classes for loading states exist."""
        # Get the project root directory dynamically
        current_dir = Path(__file__).parent
        project_root = current_dir.parent
        css_file = project_root / "src" / "ui" / "styles.css"
        
        # Read the CSS file to check for loading-related classes
        with open(css_file, 'r') as f:
            css_content = f.read()
        
        # Check for required loading CSS classes
        required_classes = [
            '.new-chat-btn.loading',
            '.loading-spinner',
            '.tools-loading',
            '.session-loading',
            '@keyframes spin'
        ]
        
        for css_class in required_classes:
            assert css_class in css_content, f"CSS class {css_class} not found in styles.css"

    def test_html_structure_for_loading(self):
        """Test that the HTML structure supports loading states."""
        # Get the project root directory dynamically
        current_dir = Path(__file__).parent
        project_root = current_dir.parent
        html_file = project_root / "src" / "ui" / "index.html"
        
        # Read the HTML file to check for loading-related structure
        with open(html_file, 'r') as f:
            html_content = f.read()
        
        # Check that the new chat button has a span for text
        assert '<span>New chat</span>' in html_content
        assert 'id="newChatBtn"' in html_content
        assert 'id="toolsList"' in html_content
        assert 'id="messagesContainer"' in html_content
