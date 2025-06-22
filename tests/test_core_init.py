import asyncio
import json
import pytest
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime

from core import (
    set_debug, mainloop, graceful_exit, chatutil, 
    pretty_print, recursive_unescape, complex_handler,
    colorize_text, colorize_json, prettify
)


class TestCoreInit:
    def test_set_debug(self):
        import core
        original_debug = core.is_debug()
        
        set_debug(True)
        assert core.is_debug() is True
        
        set_debug(False)
        assert core.is_debug() is False
        
        # Restore original state
        set_debug(original_debug)

    @pytest.mark.asyncio
    async def test_mainloop_decorator(self):
        call_count = 0
        
        @mainloop
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count >= 3:
                raise KeyboardInterrupt()
        
        with pytest.raises(KeyboardInterrupt):
            await test_func()
        
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_graceful_exit_async_success(self):
        @graceful_exit
        async def test_func():
            return "success"
        
        result = await test_func()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_graceful_exit_async_keyboard_interrupt(self):
        with patch('builtins.print') as mock_print, \
             patch('builtins.exit') as mock_exit:
            
            @graceful_exit
            async def test_func():
                raise KeyboardInterrupt()
            
            await test_func()
            mock_print.assert_called_with("\nBye!")
            mock_exit.assert_called_with(0)

    @pytest.mark.asyncio
    async def test_graceful_exit_async_exception(self):
        with patch('builtins.print') as mock_print:
            
            @graceful_exit
            async def test_func():
                raise ValueError("test error")
            
            result = await test_func()
            assert result is None
            mock_print.assert_called_with("Error: test error")

    def test_graceful_exit_sync_success(self):
        @graceful_exit
        def test_func():
            return "success"
        
        result = test_func()
        assert result == "success"

    def test_graceful_exit_sync_keyboard_interrupt(self):
        with patch('builtins.print') as mock_print, \
             patch('builtins.exit') as mock_exit:
            
            @graceful_exit
            def test_func():
                raise KeyboardInterrupt()
            
            test_func()
            mock_print.assert_called_with("\nBye!")
            mock_exit.assert_called_with(0)

    def test_graceful_exit_sync_exception(self):
        with patch('builtins.print') as mock_print:
            
            @graceful_exit
            def test_func():
                raise ValueError("test error")
            
            result = test_func()
            assert result is None
            mock_print.assert_called_with("Error: test error")

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_chatutil_decorator(self):
        test_func_called = False
        received_input = None
        received_extra = None
        
        @chatutil("TestChat")
        async def test_func(user_input, extra_arg):
            nonlocal test_func_called, received_input, received_extra
            test_func_called = True
            received_input = user_input
            received_extra = extra_arg
        
        with patch('builtins.input', return_value="test input"):
            await test_func("extra_value")
        
        assert test_func_called
        assert received_input == "test input"
        assert received_extra == "extra_value"

    def test_pretty_print(self):
        with patch('builtins.print') as mock_print:
            pretty_print("Test", {"key": "value"})
            mock_print.assert_called()

    def test_recursive_unescape_string(self):
        result = recursive_unescape("simple string")
        assert result == "simple string"

    def test_recursive_unescape_json_string(self):
        json_str = '{"key": "value"}'
        result = recursive_unescape(json_str)
        assert result == {"key": "value"}

    def test_recursive_unescape_dict(self):
        data = {"key": '{"nested": "value"}'}
        result = recursive_unescape(data)
        assert result == {"key": {"nested": "value"}}

    def test_recursive_unescape_list(self):
        data = ['{"key": "value"}', "simple"]
        result = recursive_unescape(data)
        assert result == [{"key": "value"}, "simple"]

    def test_recursive_unescape_datetime(self):
        dt = datetime(2023, 1, 1, 12, 0, 0)
        result = recursive_unescape(dt)
        assert result == dt.isoformat()

    def test_complex_handler_with_dict(self):
        class TestObj:
            def __init__(self):
                self.attr = "value"
        
        obj = TestObj()
        result = complex_handler(obj)
        assert result == {"attr": "value"}

    def test_complex_handler_without_dict(self):
        obj = "string"
        with pytest.raises(TypeError):
            complex_handler(obj)

    def test_colorize_text(self):
        result = colorize_text("test", "red")
        assert "test" in result
        assert len(result) > len("test")  # Should contain color codes

    def test_colorize_json(self):
        json_str = '{\n  "key": "value"\n}'
        result = colorize_json(json_str)
        assert "key" in result
        assert "value" in result

    def test_prettify_with_dict(self):
        data = {"key": "value"}
        result = prettify(data)
        assert "key" in result

    def test_prettify_with_string(self):
        data = "simple string"
        result = prettify(data)
        assert "simple string" in result

    def test_prettify_with_complex_object(self):
        class TestObj:
            def __init__(self):
                self.attr = "value"
        
        obj = TestObj()
        result = prettify(obj)
        assert isinstance(result, str)
