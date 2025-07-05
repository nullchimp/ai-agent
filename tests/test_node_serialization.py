import uuid
from datetime import datetime, timezone

import pytest

from src.core.db.schemas import Node, EdgeType


class MockTestNode(Node):
    def __init__(self, name: str = "test", value: int = 42):
        super().__init__()
        self.name = name
        self.value = value


class MockNestedNode(Node):
    def __init__(self, test_node: MockTestNode = None):
        super().__init__()
        self.test_node = test_node or MockTestNode()


def test_node_to_dict_basic_types():
    node = MockTestNode("example", 123)
    result = node.to_dict()
    
    assert result["name"] == "example"
    assert result["value"] == 123
    assert isinstance(result["id"], str)
    assert isinstance(result["created_at"], str)
    assert isinstance(result["updated_at"], str)
    assert result["metadata"] == {}


def test_node_from_dict_basic_types():
    original = MockTestNode("example", 123)
    data = original.to_dict()
    restored = MockTestNode.from_dict(data)
    
    assert restored.name == original.name
    assert restored.value == original.value
    assert restored.id == original.id
    assert restored.created_at == original.created_at
    assert restored.updated_at == original.updated_at


def test_node_to_dict_with_nested_node():
    inner_node = MockTestNode("inner", 456)
    outer_node = MockNestedNode(inner_node)
    result = outer_node.to_dict()
    
    assert result["test_node"]["__class__"] == "MockTestNode"
    assert result["test_node"]["name"] == "inner"
    assert result["test_node"]["value"] == 456


def test_node_from_dict_with_nested_node():
    inner_node = MockTestNode("inner", 456)
    outer_node = MockNestedNode(inner_node)
    data = outer_node.to_dict()
    restored = MockNestedNode.from_dict(data)
    
    assert isinstance(restored.test_node, MockTestNode)
    assert restored.test_node.name == "inner"
    assert restored.test_node.value == 456


def test_node_serialization_roundtrip():
    original = MockNestedNode(MockTestNode("roundtrip", 999))
    data = original.to_dict()
    restored = MockNestedNode.from_dict(data)
    
    assert restored.test_node.name == original.test_node.name
    assert restored.test_node.value == original.test_node.value
    assert restored.test_node.id == original.test_node.id


def test_node_from_dict_with_polymorphism():
    original = MockTestNode("poly", 777)
    data = original.to_dict()
    data["__class__"] = "MockTestNode"
    
    restored = Node.from_dict(data)
    assert isinstance(restored, MockTestNode)
    assert restored.name == "poly"
    assert restored.value == 777


def test_node_from_dict_with_collections():
    node = MockTestNode()
    node.items = [MockTestNode("item1", 1), MockTestNode("item2", 2)]
    node.tags = {"tag1", "tag2"}
    node.config = {"key": MockTestNode("config", 100)}
    
    data = node.to_dict()
    restored = MockTestNode.from_dict(data)
    
    assert len(restored.items) == 2
    assert isinstance(restored.items[0], MockTestNode)
    assert restored.items[0].name == "item1"
    assert isinstance(restored.config["key"], MockTestNode)
    assert restored.config["key"].name == "config"


def test_load_from_class():
    node = Node.load_from_class("MockTestNode")
    assert isinstance(node, MockTestNode)
    assert node.name == "test"
    assert node.value == 42


def test_load_from_class_unknown():
    with pytest.raises(ValueError, match="Class UnknownClass not found in registry"):
        Node.load_from_class("UnknownClass")
