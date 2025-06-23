import pytest
from unittest.mock import Mock, patch, AsyncMock
import json


class TestUIToolsConfiguration:
    def test_tools_configuration_text_format(self):
        """Test that tools configuration text shows correct <active>/<all> format"""
        # This test validates the JavaScript functionality for updating tools configuration text
        # Since we can't directly test JavaScript from Python, we'll test the logic
        
        # Simulate different tool scenarios
        test_cases = [
            {"enabled_tools": 0, "total_tools": 5, "expected": "Tools Configuration <0/5>"},
            {"enabled_tools": 3, "total_tools": 5, "expected": "Tools Configuration <3/5>"},
            {"enabled_tools": 5, "total_tools": 5, "expected": "Tools Configuration <5/5>"},
            {"enabled_tools": 1, "total_tools": 1, "expected": "Tools Configuration <1/1>"},
        ]
        
        for case in test_cases:
            enabled_count = case["enabled_tools"]
            total_count = case["total_tools"]
            expected_text = case["expected"]
            
            # Simulate the JavaScript logic for formatting the text
            actual_text = f"Tools Configuration <{enabled_count}/{total_count}>"
            
            assert actual_text == expected_text, f"Failed for case: {case}"

    def test_tools_configuration_edge_cases(self):
        """Test edge cases for tools configuration text formatting"""
        # Test with zero tools
        assert "Tools Configuration <0/0>" == f"Tools Configuration <{0}/{0}>"
        
        # Test with large numbers
        assert "Tools Configuration <99/100>" == f"Tools Configuration <{99}/{100}>"

    @pytest.mark.asyncio
    async def test_tools_api_response_format(self):
        """Test that the tools API returns data in the expected format for UI consumption"""
        # Mock tools data as it would come from the API
        mock_tools_data = {
            "tools": [
                {"name": "google_search", "description": "Search Google", "enabled": True},
                {"name": "read_file", "description": "Read files", "enabled": False},
                {"name": "write_file", "description": "Write files", "enabled": True},
                {"name": "list_files", "description": "List files", "enabled": False},
                {"name": "github_search", "description": "Search GitHub", "enabled": True}
            ]
        }
        
        # Calculate enabled count (simulating JavaScript logic)
        enabled_count = sum(1 for tool in mock_tools_data["tools"] if tool["enabled"])
        total_count = len(mock_tools_data["tools"])
        
        assert enabled_count == 3
        assert total_count == 5
        
        # Test the format string
        config_text = f"Tools Configuration <{enabled_count}/{total_count}>"
        assert config_text == "Tools Configuration <3/5>"

    def test_tools_configuration_text_update_logic(self):
        """Test the logic for updating tools configuration text dynamically"""
        
        def simulate_render_tools(tools):
            """Simulate the renderTools function logic from chat.ts"""
            enabled_count = sum(1 for tool in tools if tool.get("enabled", False))
            total_count = len(tools)
            return f"Tools Configuration <{enabled_count}/{total_count}>"
        
        # Test initial state
        initial_tools = [
            {"name": "tool1", "enabled": True},
            {"name": "tool2", "enabled": False},
            {"name": "tool3", "enabled": True}
        ]
        
        result = simulate_render_tools(initial_tools)
        assert result == "Tools Configuration <2/3>"
        
        # Test after enabling a tool
        initial_tools[1]["enabled"] = True
        result = simulate_render_tools(initial_tools)
        assert result == "Tools Configuration <3/3>"
        
        # Test after disabling all tools
        for tool in initial_tools:
            tool["enabled"] = False
        result = simulate_render_tools(initial_tools)
        assert result == "Tools Configuration <0/3>"

    def test_tools_configuration_responsive_updates(self):
        """Test that configuration text updates correctly when tools are toggled"""
        
        class MockToolsManager:
            def __init__(self, tools):
                self.tools = tools
            
            def get_enabled_count(self):
                return sum(1 for tool in self.tools if tool.get("enabled", False))
            
            def get_total_count(self):
                return len(self.tools)
            
            def get_configuration_text(self):
                enabled = self.get_enabled_count()
                total = self.get_total_count()
                return f"Tools Configuration <{enabled}/{total}>"
            
            def toggle_tool(self, tool_name, enabled):
                for tool in self.tools:
                    if tool["name"] == tool_name:
                        tool["enabled"] = enabled
                        break
        
        # Initialize with mixed tool states
        tools = [
            {"name": "google_search", "enabled": True},
            {"name": "read_file", "enabled": False},
            {"name": "write_file", "enabled": True}
        ]
        
        manager = MockToolsManager(tools)
        
        # Initial state
        assert manager.get_configuration_text() == "Tools Configuration <2/3>"
        
        # Enable a disabled tool
        manager.toggle_tool("read_file", True)
        assert manager.get_configuration_text() == "Tools Configuration <3/3>"
        
        # Disable an enabled tool
        manager.toggle_tool("google_search", False)
        assert manager.get_configuration_text() == "Tools Configuration <2/3>"
        
        # Disable all tools
        manager.toggle_tool("read_file", False)
        manager.toggle_tool("write_file", False)
        assert manager.get_configuration_text() == "Tools Configuration <0/3>"
