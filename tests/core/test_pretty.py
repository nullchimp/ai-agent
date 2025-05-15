from colorama import Fore, Style
from core import colorize_text, colorize_json, prettify

def test_colorize_text():
    """Test the colorize_text function with different colors"""
    test_text = "Hello World"
    
    # Test with a known color
    red_text = colorize_text(test_text, "red")
    assert red_text == f"{Fore.RED}{test_text}{Style.RESET_ALL}"
    
    # Test with a color not in the color map
    custom_text = colorize_text(test_text, "nonexistent_color")
    assert custom_text == f"nonexistent_color{test_text}{Style.RESET_ALL}"

def test_colorize_json():
    """Test the colorize_json function with various JSON strings"""
    # Test with a simple JSON string
    simple_json = '{"message": "Hello", "role": "user"}'
    colorized = colorize_json(simple_json)
    
    # Verify that the keys were colorized
    assert "message" in colorized
    assert "role" in colorized
    
    # Test with multi-line JSON
    multi_line_json = '{\n"content": "test",\n"error": "none"\n}'
    colorized = colorize_json(multi_line_json)
    
    # Verify content was properly colorized
    assert "content" in colorized
    assert "error" in colorized
    
    # Test with a line that doesn't contain a key
    json_with_value = '{\n"key": [\n"value"\n]\n}'
    colorized = colorize_json(json_with_value)
    assert "value" in colorized

def test_prettify():
    """Test the prettify function with various inputs"""
    # Test with a dictionary
    test_dict = {"key": "value", "nested": {"inner": "data"}}
    result = prettify(test_dict)
    assert "key" in result
    assert "value" in result
    assert "nested" in result
    
    # Test with a string that's already JSON
    json_str = '{"message": "Hello"}'
    result = prettify(json_str)
    assert "message" in result
    assert "Hello" in result
    
    # Test with a complex object
    class TestObj:
        def __init__(self):
            self.name = "test"
            self.value = 123
    
    obj = TestObj()
    result = prettify(obj)
    assert "name" in result
    assert "test" in result
    assert "123" in result
    
    # Test with a non-serializable object that falls back to str()
    import datetime
    dt = datetime.datetime.now()
    result = prettify(dt)
    assert str(dt) in result or repr(dt) in result