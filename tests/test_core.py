import pytest
from unittest.mock import Mock, patch, MagicMock
import asyncio
import datetime
from typing import Dict, Any

from core import (
    set_debug, 
    mainloop, 
    graceful_exit, 
    chatutil, 
    pretty_print, 
    recursive_unescape,
    complex_handler,
    colorize_text,
    colorize_json,
    prettify
)


class TestCoreUtilities:

    def test_set_debug(self):
        from core import DEBUG
        original_debug = DEBUG
        
        set_debug(True)
        from core import DEBUG as debug_after_true
        assert debug_after_true is True
        
        set_debug(False)
        from core import DEBUG as debug_after_false
        assert debug_after_false is False
        
        set_debug(original_debug)

    @pytest.mark.asyncio
    async def test_graceful_exit_async_success(self):
        @graceful_exit
        async def test_func():
            return "success"
        
        result = await test_func()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_graceful_exit_async_keyboard_interrupt(self, capsys):
        @graceful_exit
        async def test_func():
            raise KeyboardInterrupt()
        
        with pytest.raises(SystemExit):
            await test_func()
        
        captured = capsys.readouterr()
        assert "Bye!" in captured.out

    @pytest.mark.asyncio
    async def test_graceful_exit_async_exception(self, capsys):
        @graceful_exit
        async def test_func():
            raise ValueError("test error")
        
        result = await test_func()
        assert result is None
        
        captured = capsys.readouterr()
        assert "Error: test error" in captured.out

    def test_graceful_exit_sync_success(self):
        @graceful_exit
        def test_func():
            return "success"
        
        result = test_func()
        assert result == "success"

    def test_graceful_exit_sync_keyboard_interrupt(self, capsys):
        @graceful_exit
        def test_func():
            raise KeyboardInterrupt()
        
        with pytest.raises(SystemExit):
            test_func()
        
        captured = capsys.readouterr()
        assert "Bye!" in captured.out

    def test_graceful_exit_sync_exception(self, capsys):
        @graceful_exit
        def test_func():
            raise ValueError("test error")
        
        result = test_func()
        assert result is None
        
        captured = capsys.readouterr()
        assert "Error: test error" in captured.out

    @pytest.mark.asyncio
    async def test_mainloop_decorator(self):
        call_count = 0
        
        @mainloop
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count >= 3:
                raise KeyboardInterrupt()
            return f"call_{call_count}"
        
        with pytest.raises(KeyboardInterrupt):
            await test_func()
        
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_chatutil_decorator(self):
        with patch('builtins.input', return_value='test_input'):
            @chatutil("TestChat")
            async def test_func(user_input, other_arg):
                return f"Input: {user_input}, Other: {other_arg}"
            
            # The chatutil decorator doesn't return the result, it just calls the function
            result = await test_func("other_value")
            # Since the wrapper doesn't return anything, result should be None
            assert result is None

    def test_recursive_unescape_string(self):
        test_string = '{"key": "value"}'
        result = recursive_unescape(test_string)
        assert result == {"key": "value"}

    def test_recursive_unescape_dict(self):
        test_dict = {"nested": '{"inner": "value"}'}
        result = recursive_unescape(test_dict)
        assert result == {"nested": {"inner": "value"}}

    def test_recursive_unescape_list(self):
        test_list = ['{"key": "value"}', "plain_string"]
        result = recursive_unescape(test_list)
        assert result == [{"key": "value"}, "plain_string"]

    def test_recursive_unescape_datetime(self):
        test_datetime = datetime.datetime(2023, 1, 1, 12, 0, 0)
        result = recursive_unescape(test_datetime)
        assert result == "2023-01-01T12:00:00"

    def test_recursive_unescape_invalid_json(self):
        test_string = "not json"
        result = recursive_unescape(test_string)
        assert result == "not json"

    def test_complex_handler_with_dict_object(self):
        class TestObj:
            def __init__(self):
                self.attr1 = "value1"
                self.attr2 = {"nested": "value2"}
        
        obj = TestObj()
        result = complex_handler(obj)
        assert result == {"attr1": "value1", "attr2": {"nested": "value2"}}

    def test_complex_handler_without_dict(self):
        with pytest.raises(TypeError):
            complex_handler("string")

    def test_colorize_text_valid_color(self):
        result = colorize_text("test", "red")
        assert "test" in result
        assert "\033[31m" in result  # ANSI red color code

    def test_colorize_text_invalid_color(self):
        result = colorize_text("test", "invalid_color")
        assert "test" in result

    def test_colorize_json_with_colored_keys(self):
        test_json = '{\n  "messages": "value",\n  "content": "text"\n}'
        result = colorize_json(test_json)
        assert "messages" in result
        assert "content" in result

    @patch('core.colorize_json')
    @patch('core.recursive_unescape')
    def test_prettify_with_dict(self, mock_unescape, mock_colorize):
        mock_unescape.return_value = {"key": "value"}
        mock_colorize.return_value = "colored_json"
        
        data = {"key": "value"}
        result = prettify(data)
        
        mock_unescape.assert_called_once()
        mock_colorize.assert_called_once()
        assert result == "colored_json"

    @patch('core.colorize_json')
    @patch('core.recursive_unescape')
    def test_prettify_with_string(self, mock_unescape, mock_colorize):
        mock_unescape.return_value = "test_string"
        mock_colorize.return_value = "colored_string"
        
        data = "test_string"
        result = prettify(data)
        
        mock_unescape.assert_called_once()
        mock_colorize.assert_called_once()
        assert result == "colored_string"

    @patch('core.prettify')
    @patch('core.colorize_text')
    def test_pretty_print(self, mock_colorize, mock_prettify, capsys):
        mock_prettify.return_value = "prettified_data"
        mock_colorize.side_effect = lambda x, color: f"colored_{x}"
        
        pretty_print("TestName", "test_data", "red")
        
        captured = capsys.readouterr()
        assert "TestName" in captured.out
        assert "prettified_data" in captured.out
        mock_prettify.assert_called_once_with("test_data")

    @patch('core.prettify')
    def test_pretty_print_no_color(self, mock_prettify, capsys):
        mock_prettify.return_value = "prettified_data"
        
        pretty_print("TestName", "test_data")
        
        captured = capsys.readouterr()
        assert "TestName" in captured.out
        assert "prettified_data" in captured.out
