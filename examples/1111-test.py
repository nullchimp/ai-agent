from dotenv import load_dotenv
# Force reload of environment variables to avoid cached data
load_dotenv(override=True)

from core.db.schemas import Node

class MockTestNode2(Node):
    def __init__(self, name: str = "test2", value: int = 84):
        super().__init__()
        self.name = name
        self.value = value

class MockTestNode(Node):
    def __init__(self, name: str = "test", value: int = 42):
        super().__init__()
        self.name = name
        self.value = value
        self.test_node2 = MockTestNode2()

class MockNestedNode(Node):
    def __init__(self):
        super().__init__()
        self.test_node = MockTestNode()
        self.add_metadata(key1="value1", key2="value2")

def test_node_to_dict_basic_types(node: MockNestedNode = None) -> dict:
    result = node.to_dict()
    
    assert result["test_node"]["__class__"] == "MockTestNode"
    assert result["test_node"]["name"] == "test"
    assert result["test_node"]["value"] == 42
    assert result["test_node"]["test_node2"]["__class__"] == "MockTestNode2"
    assert result["test_node"]["test_node2"]["name"] == "test2"
    assert result["test_node"]["test_node2"]["value"] == 84
    assert isinstance(result["id"], str)
    assert isinstance(result["created_at"], str)
    assert isinstance(result["updated_at"], str)
    assert result["metadata"] == {"key1": "value1", "key2": "value2"}

    print(f"Node ID: {result}")

    return result

def test_node_from_dict_basic_types(result: dict):
    restored = Node.from_dict(result)
    
    assert isinstance(restored.test_node, MockTestNode)
    assert restored.test_node.name == "test"
    assert restored.test_node.value == 42
    assert isinstance(restored.test_node.test_node2, MockTestNode2)
    assert restored.test_node.test_node2.name == "test2"
    assert restored.test_node.test_node2.value == 84
    assert restored.metadata == {"key1": "value1", "key2": "value2"}

from core.db.connection_pool import get_connection_pool

pool = get_connection_pool()

with pool.get_connection() as db:
    n = MockNestedNode()
    test_node_to_dict_basic_types(n)
    db._execute(*n.create())
    b = Node.from_dict(db._fetch_by_id(n.id))
    test_node_to_dict_basic_types(b)