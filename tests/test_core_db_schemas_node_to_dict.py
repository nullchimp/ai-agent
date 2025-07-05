import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Set, Tuple

import pytest

from src.core.db.schemas import EdgeType, Node


class MockEdgeType(Enum):
    TEST_EDGE = "TEST_EDGE"
    ANOTHER_EDGE = "ANOTHER_EDGE"


class MockNode(Node):
    def __init__(self, name: str = "test"):
        super().__init__()
        self.name = name


class NestedMockNode(Node):
    def __init__(self, value: int = 42):
        super().__init__()
        self.value = value
        self.nested_node = MockNode(f"nested_{value}")


class ComplexNode(Node):
    def __init__(self):
        super().__init__()
        self.string_value = "test_string"
        self.int_value = 123
        self.float_value = 45.67
        self.bool_value = True
        self.none_value = None
        self.datetime_value = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        self.uuid_value = uuid.uuid4()
        self.enum_value = MockEdgeType.TEST_EDGE
        self.edge_type_value = EdgeType.CHUNK_OF
        self.list_value = [1, 2, 3]
        self.dict_value = {"key1": "value1", "key2": "value2"}
        self.set_value = {1, 2, 3}
        self.tuple_value = (1, 2, 3)
        self.nested_node = MockNode("complex_nested")


def test_simple_node_to_dict():
    node = MockNode("simple")
    result = node.to_dict()
    
    assert isinstance(result, dict)
    assert result["name"] == "simple"
    assert "id" in result
    assert "created_at" in result
    assert "updated_at" in result
    assert "metadata" in result


def test_nested_single_node_to_dict():
    node = NestedMockNode(100)
    result = node.to_dict()
    
    assert result["value"] == 100
    assert isinstance(result["nested_node"], dict)
    assert result["nested_node"]["name"] == "nested_100"
    assert "id" in result["nested_node"]


def test_deeply_nested_nodes_to_dict():
    root_node = MockNode("root")
    level1_node = MockNode("level1")
    level2_node = MockNode("level2")
    level3_node = MockNode("level3")
    
    level2_node.child = level3_node
    level1_node.child = level2_node
    root_node.child = level1_node
    
    result = root_node.to_dict()
    
    assert result["name"] == "root"
    assert result["child"]["name"] == "level1"
    assert result["child"]["child"]["name"] == "level2"
    assert result["child"]["child"]["child"]["name"] == "level3"


def test_list_of_nodes_to_dict():
    parent_node = MockNode("parent")
    child_nodes = [MockNode(f"child_{i}") for i in range(3)]
    parent_node.children = child_nodes
    
    result = parent_node.to_dict()
    
    assert len(result["children"]) == 3
    for i, child_dict in enumerate(result["children"]):
        assert isinstance(child_dict, dict)
        assert child_dict["name"] == f"child_{i}"
        assert "id" in child_dict


def test_dict_with_node_values_to_dict():
    parent_node = MockNode("parent")
    node_dict = {
        "first": MockNode("first_node"),
        "second": MockNode("second_node"),
        "nested": {
            "inner": MockNode("inner_node")
        }
    }
    parent_node.node_mapping = node_dict
    
    result = parent_node.to_dict()
    
    assert isinstance(result["node_mapping"]["first"], dict)
    assert result["node_mapping"]["first"]["name"] == "first_node"
    assert isinstance(result["node_mapping"]["second"], dict)
    assert result["node_mapping"]["second"]["name"] == "second_node"
    assert isinstance(result["node_mapping"]["nested"]["inner"], dict)
    assert result["node_mapping"]["nested"]["inner"]["name"] == "inner_node"


def test_set_of_nodes_to_dict():
    parent_node = MockNode("parent")
    node_set = {MockNode("set_node_1"), MockNode("set_node_2")}
    parent_node.node_set = node_set
    
    # NOTE: This test demonstrates that sets containing nodes will fail
    # because Node.to_dict() returns dicts which are unhashable
    with pytest.raises(TypeError, match="unhashable type: 'dict'"):
        parent_node.to_dict()


def test_tuple_of_nodes_to_dict():
    parent_node = MockNode("parent")
    node_tuple = (MockNode("tuple_node_1"), MockNode("tuple_node_2"), "string_item")
    parent_node.node_tuple = node_tuple
    
    result = parent_node.to_dict()
    
    assert isinstance(result["node_tuple"], tuple)
    assert len(result["node_tuple"]) == 3
    assert isinstance(result["node_tuple"][0], dict)
    assert isinstance(result["node_tuple"][1], dict)
    assert result["node_tuple"][2] == "string_item"


def test_complex_nested_structure_to_dict():
    root_node = ComplexNode()
    nested_in_list = [MockNode("list_item_1"), {"key": MockNode("dict_in_list")}]
    root_node.complex_list = nested_in_list
    
    result = root_node.to_dict()
    
    assert result["string_value"] == "test_string"
    assert result["int_value"] == 123
    assert result["float_value"] == 45.67
    assert result["bool_value"] is True
    assert result["none_value"] is None
    assert isinstance(result["datetime_value"], str)
    assert isinstance(result["uuid_value"], str)
    assert result["enum_value"] == "TEST_EDGE"
    assert result["edge_type_value"] == "CHUNK_OF"
    assert result["list_value"] == [1, 2, 3]
    assert result["dict_value"] == {"key1": "value1", "key2": "value2"}
    assert isinstance(result["set_value"], set)
    assert result["tuple_value"] == (1, 2, 3)
    assert isinstance(result["nested_node"], dict)
    assert result["nested_node"]["name"] == "complex_nested"
    
    # Test complex nested list
    assert isinstance(result["complex_list"][0], dict)
    assert result["complex_list"][0]["name"] == "list_item_1"
    assert isinstance(result["complex_list"][1]["key"], dict)
    assert result["complex_list"][1]["key"]["name"] == "dict_in_list"


def test_circular_reference_nodes():
    node1 = MockNode("node1")
    node2 = MockNode("node2")
    node1.ref = node2
    node2.ref = node1
    
    # NOTE: This test demonstrates that circular references cause infinite recursion
    # The current implementation doesn't handle circular reference detection
    with pytest.raises(RecursionError):
        node1.to_dict()


def test_datetime_iso_format_in_nested_nodes():
    test_time = datetime(2025, 7, 5, 14, 30, 45, 123456, tzinfo=timezone.utc)
    node = MockNode("datetime_test")
    node.custom_datetime = test_time
    nested_node = MockNode("nested_datetime")
    nested_node.another_datetime = test_time
    node.nested = nested_node
    
    result = node.to_dict()
    
    assert result["custom_datetime"] == test_time.isoformat()
    assert result["nested"]["another_datetime"] == test_time.isoformat()


def test_uuid_string_conversion_in_nested_nodes():
    test_uuid = uuid.uuid4()
    node = MockNode("uuid_test")
    node.custom_uuid = test_uuid
    nested_node = MockNode("nested_uuid")
    nested_node.another_uuid = test_uuid
    node.nested = nested_node
    
    result = node.to_dict()
    
    assert result["custom_uuid"] == str(test_uuid)
    assert result["nested"]["another_uuid"] == str(test_uuid)


def test_enum_value_conversion_in_nested_nodes():
    node = MockNode("enum_test")
    node.test_enum = MockEdgeType.ANOTHER_EDGE
    node.edge_enum = EdgeType.FOLLOWS
    nested_node = MockNode("nested_enum")
    nested_node.nested_enum = EdgeType.REFERENCES
    node.nested = nested_node
    
    result = node.to_dict()
    
    assert result["test_enum"] == "ANOTHER_EDGE"
    assert result["edge_enum"] == "FOLLOWS"
    assert result["nested"]["nested_enum"] == "REFERENCES"


def test_mixed_collection_with_nodes():
    node = MockNode("collection_test")
    mixed_list = [
        MockNode("in_list"),
        42,
        "string",
        datetime(2025, 1, 1, tzinfo=timezone.utc),
        uuid.uuid4(),
        EdgeType.CHUNK_OF,
        {"nested_dict_node": MockNode("dict_nested")}
    ]
    node.mixed_collection = mixed_list
    
    result = node.to_dict()
    
    collection = result["mixed_collection"]
    assert isinstance(collection[0], dict)  # Node
    assert collection[0]["name"] == "in_list"
    assert collection[1] == 42  # int
    assert collection[2] == "string"  # string
    assert isinstance(collection[3], str)  # datetime -> ISO string
    assert isinstance(collection[4], str)  # UUID -> string
    assert collection[5] == "CHUNK_OF"  # Enum -> value
    assert isinstance(collection[6]["nested_dict_node"], dict)  # Nested node in dict


def test_empty_collections_with_nodes():
    node = MockNode("empty_test")
    node.empty_list = []
    node.empty_dict = {}
    node.empty_set = set()
    node.empty_tuple = ()
    
    result = node.to_dict()
    
    assert result["empty_list"] == []
    assert result["empty_dict"] == {}
    assert result["empty_set"] == set()
    assert result["empty_tuple"] == ()


def test_none_values_in_nested_structures():
    node = MockNode("none_test")
    node.list_with_nones = [None, MockNode("not_none"), None]
    node.dict_with_nones = {"none_key": None, "node_key": MockNode("dict_node")}
    
    result = node.to_dict()
    
    assert result["list_with_nones"][0] is None
    assert isinstance(result["list_with_nones"][1], dict)
    assert result["list_with_nones"][2] is None
    assert result["dict_with_nones"]["none_key"] is None
    assert isinstance(result["dict_with_nones"]["node_key"], dict)


def test_private_and_callable_attributes_excluded():
    node = MockNode("exclusion_test")
    node._private_attr = "should_be_excluded"
    node.__dunder_attr = "should_be_excluded"
    node.public_node = MockNode("should_be_included")
    
    def test_method():
        return "callable"
    
    node.test_method = test_method
    
    result = node.to_dict()
    
    assert "_private_attr" not in result
    assert "__dunder_attr" not in result
    assert "test_method" not in result
    assert isinstance(result["public_node"], dict)
    assert result["public_node"]["name"] == "should_be_included"


def test_node_with_metadata_containing_nodes():
    node = MockNode("metadata_test")
    metadata_node = MockNode("metadata_node")
    node.metadata = {
        "simple_key": "simple_value",
        "node_key": metadata_node,
        "nested_dict": {
            "inner_node": MockNode("inner_metadata_node")
        }
    }
    
    result = node.to_dict()
    
    assert result["metadata"]["simple_key"] == "simple_value"
    assert isinstance(result["metadata"]["node_key"], dict)
    assert result["metadata"]["node_key"]["name"] == "metadata_node"
    assert isinstance(result["metadata"]["nested_dict"]["inner_node"], dict)
    assert result["metadata"]["nested_dict"]["inner_node"]["name"] == "inner_metadata_node"


def test_large_nested_structure_performance():
    root_node = MockNode("performance_test")
    
    # Create a moderately deep structure to test performance
    current_level = root_node
    for i in range(10):
        next_node = MockNode(f"level_{i}")
        next_node.data_list = [MockNode(f"item_{i}_{j}") for j in range(5)]
        current_level.next_level = next_node
        current_level = next_node
    
    result = root_node.to_dict()
    
    # Verify structure is properly converted
    assert result["name"] == "performance_test"
    current_result = result
    for i in range(10):
        assert current_result["next_level"]["name"] == f"level_{i}"
        assert len(current_result["next_level"]["data_list"]) == 5
        for j in range(5):
            assert current_result["next_level"]["data_list"][j]["name"] == f"item_{i}_{j}"
        if i < 9:  # Don't go beyond the last level
            current_result = current_result["next_level"]
