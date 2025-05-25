import pytest
from unittest.mock import Mock, patch, AsyncMock
from dataclasses import dataclass

from src.tools.google_search import GoogleSearch


class TestGoogleSearch:
    
    @pytest.fixture
    def google_search_tool(self):
        return GoogleSearch()
    
    def test_name_property(self, google_search_tool):
        assert google_search_tool.name == "google_search"
    
    def test_description_property(self, google_search_tool):
        expected_description = "Search the web for relevant information."
        assert google_search_tool.description == expected_description
    
    def test_parameters_property(self, google_search_tool):
        parameters = google_search_tool.parameters
        
        assert parameters["type"] == "object"
        assert "properties" in parameters
        assert "query" in parameters["properties"]
        assert "num_results" in parameters["properties"]
        assert parameters["required"] == ["query"]
        
        # Check query parameter
        query_param = parameters["properties"]["query"]
        assert query_param["type"] == "string"
        assert "description" in query_param
        
        # Check num_results parameter
        num_results_param = parameters["properties"]["num_results"]
        assert num_results_param["type"] == "number"
        assert "description" in num_results_param
    
    @pytest.mark.asyncio
    async def test_run_success(self, google_search_tool):
        mock_results = Mock()
        mock_results.query = "test query"
        mock_results.total_results = 100
        mock_results.search_time = 0.25
        mock_results.formatted_count = "About 100 results"
        
        result1 = Mock()
        result1.__str__ = Mock(return_value="Result 1 (https://example1.com) - Snippet 1")
        
        result2 = Mock()
        result2.__str__ = Mock(return_value="Result 2 (https://example2.com) - Snippet 2")
        
        mock_results.results = [result1, result2]
        
        mock_service = Mock()
        mock_service.search.return_value = mock_results
        
        with patch('libs.search.service.Service') as mock_service_class:
            mock_service_class.create.return_value = mock_service
            
            result = await google_search_tool.run("test query", num_results=5)
            
            assert result["query"] == "test query"
            assert result["total_results"] == 100
            assert result["search_time"] == 0.25
            assert result["formatted_count"] == "About 100 results"
            assert len(result["results"]) == 2
            assert result["results"][0] == "Result 1 (https://example1.com) - Snippet 1"
            assert result["results"][1] == "Result 2 (https://example2.com) - Snippet 2"
            
            mock_service.search.assert_called_once_with("test query", 5)
    
    @pytest.mark.asyncio
    async def test_run_default_num_results(self, google_search_tool):
        mock_results = Mock()
        mock_results.query = "test query"
        mock_results.total_results = 50
        mock_results.search_time = 0.15
        mock_results.formatted_count = "About 50 results"
        mock_results.results = []
        
        mock_service = Mock()
        mock_service.search.return_value = mock_results
        
        with patch('libs.search.service.Service') as mock_service_class:
            mock_service_class.create.return_value = mock_service
            
            result = await google_search_tool.run("test query")
            
            # Should use default value of 5
            mock_service.search.assert_called_once_with("test query", 5)
    
    @pytest.mark.asyncio
    async def test_run_empty_results(self, google_search_tool):
        mock_results = Mock()
        mock_results.query = "no results query"
        mock_results.total_results = 0
        mock_results.search_time = 0.05
        mock_results.formatted_count = "0 results"
        mock_results.results = []
        
        mock_service = Mock()
        mock_service.search.return_value = mock_results
        
        with patch('libs.search.service.Service') as mock_service_class:
            mock_service_class.create.return_value = mock_service
            
            result = await google_search_tool.run("no results query", num_results=10)
            
            assert result["query"] == "no results query"
            assert result["total_results"] == 0
            assert result["search_time"] == 0.05
            assert result["formatted_count"] == "0 results"
            assert result["results"] == []
    
    @pytest.mark.asyncio
    async def test_run_service_error(self, google_search_tool):
        mock_service = Mock()
        mock_service.search.side_effect = Exception("Search service error")
        
        with patch('libs.search.service.Service') as mock_service_class:
            mock_service_class.create.return_value = mock_service
            
            with pytest.raises(Exception, match="Search service error"):
                await google_search_tool.run("error query")
    
    @pytest.mark.asyncio
    async def test_run_with_various_num_results(self, google_search_tool):
        mock_results = Mock()
        mock_results.query = "test"
        mock_results.total_results = 1000
        mock_results.search_time = 0.2
        mock_results.formatted_count = "About 1,000 results"
        mock_results.results = []
        
        mock_service = Mock()
        mock_service.search.return_value = mock_results
        
        with patch('libs.search.service.Service') as mock_service_class:
            mock_service_class.create.return_value = mock_service
            
            # Test with 1 result
            await google_search_tool.run("test", num_results=1)
            mock_service.search.assert_called_with("test", 1)
            
            # Test with 10 results (max)
            await google_search_tool.run("test", num_results=10)
            mock_service.search.assert_called_with("test", 10)
    
    @pytest.mark.asyncio
    async def test_run_formats_results_as_strings(self, google_search_tool):
        # Create mock result objects with __str__ method
        result1 = Mock()
        result1.__str__ = Mock(return_value="Formatted Result 1")
        
        result2 = Mock()
        result2.__str__ = Mock(return_value="Formatted Result 2")
        
        mock_results = Mock()
        mock_results.query = "format test"
        mock_results.total_results = 2
        mock_results.search_time = 0.1
        mock_results.formatted_count = "2 results"
        mock_results.results = [result1, result2]
        
        mock_service = Mock()
        mock_service.search.return_value = mock_results
        
        with patch('libs.search.service.Service') as mock_service_class:
            mock_service_class.create.return_value = mock_service
            
            result = await google_search_tool.run("format test")
            
            # Results should be converted to strings
            assert result["results"] == ["Formatted Result 1", "Formatted Result 2"]
            result1.__str__.assert_called_once()
            result2.__str__.assert_called_once()
    
    def test_tool_inheritance(self, google_search_tool):
        # Verify that GoogleSearch inherits from Tool
        from src.tools import Tool
        assert isinstance(google_search_tool, Tool)
    
    @pytest.mark.asyncio
    async def test_service_creation_called(self, google_search_tool):
        mock_results = Mock()
        mock_results.query = "test"
        mock_results.total_results = 0
        mock_results.search_time = 0.0
        mock_results.formatted_count = "0 results"
        mock_results.results = []
        
        mock_service = Mock()
        mock_service.search.return_value = mock_results
        
        with patch('libs.search.service.Service') as mock_service_class:
            mock_service_class.create.return_value = mock_service
            
            await google_search_tool.run("test")
            
            # Verify Service.create() was called
            mock_service_class.create.assert_called_once()
