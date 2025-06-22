import pytest
from pydantic import ValidationError

from src.api.models import QueryRequest, QueryResponse


def test_query_request_valid():
    request = QueryRequest(query="What is the weather today?")
    assert request.query == "What is the weather today?"


def test_query_request_empty_string():
    request = QueryRequest(query="")
    assert request.query == ""


def test_query_request_missing_query():
    with pytest.raises(ValidationError):
        QueryRequest()


def test_query_response_valid():
    response = QueryResponse(response="The weather is sunny today.")
    assert response.response == "The weather is sunny today."


def test_query_response_empty_string():
    response = QueryResponse(response="")
    assert response.response == ""


def test_query_response_missing_response():
    with pytest.raises(ValidationError):
        QueryResponse()


def test_query_request_json_serialization():
    request = QueryRequest(query="Test query")
    json_data = request.model_dump()
    assert json_data == {"query": "Test query"}


def test_query_response_json_serialization():
    response = QueryResponse(response="Test response")
    json_data = response.model_dump()
    assert json_data == {"response": "Test response"}
