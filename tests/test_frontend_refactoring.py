import os
import subprocess
import sys


def test_service_modules_exist():
    """Test that the refactored service modules exist and can be built"""
    service_files = [
        'src/ui/apiService.ts',
        'src/ui/chatService.ts', 
        'src/ui/utils.ts'
    ]
    
    for file_path in service_files:
        assert os.path.exists(file_path), f"Service module {file_path} should exist"
    print("✓ All service modules exist")


def test_api_service_structure():
    """Test that ApiService has the expected structure"""
    with open('src/ui/apiService.ts', 'r') as f:
        content = f.read()
    
    expected_methods = [
        'callChatAPI',
        'createNewSession', 
        'verifySession',
        'deleteSession',
        'loadTools',
        'toggleTool',
        'toggleAllTools',
        'toggleSourceTools',
        'setDebugMode',
        'clearDebugEvents',
        'loadDebugEvents'
    ]
    
    for method in expected_methods:
        assert method in content, f"ApiService should have {method} method"
    print("✓ ApiService has all expected methods")


def test_chat_service_structure():
    """Test that ChatService has the expected structure"""
    with open('src/ui/chatService.ts', 'r') as f:
        content = f.read()
    
    expected_methods = [
        'getSessions',
        'getCurrentSession',
        'createSession',
        'deleteSession', 
        'updateSessionTitle',
        'addMessage',
        'clearMessages',
        'updateSessionBackendId',
        'updateDebugState',
        'validateMessage',
        'createMessage'
    ]
    
    for method in expected_methods:
        assert method in content, f"ChatService should have {method} method"
    print("✓ ChatService has all expected methods")


def test_utils_structure():
    """Test that Utils has the expected structure"""
    with open('src/ui/utils.ts', 'r') as f:
        content = f.read()
    
    expected_methods = [
        'escapeHtml',
        'generateId',
        'applyColorSchemeToData',
        'colorizeJsonData',
        'findRootColorMetadata'
    ]
    
    for method in expected_methods:
        assert method in content, f"Utils should have {method} method"
    print("✓ Utils has all expected methods")


def test_main_chat_imports_services():
    """Test that the main chat.ts file imports the service modules"""
    with open('src/ui/chat.ts', 'r') as f:
        content = f.read()
    
    # Check imports
    assert "import { ApiService }" in content, "chat.ts should import ApiService"
    assert "import { ChatService }" in content, "chat.ts should import ChatService" 
    assert "import { Utils }" in content, "chat.ts should import Utils"
    
    # Check service initialization
    assert "new ApiService()" in content, "chat.ts should initialize ApiService"
    assert "new ChatService()" in content, "chat.ts should initialize ChatService"
    print("✓ Main chat.ts imports and initializes services")


def test_typescript_compilation_succeeds():
    """Test that the refactored TypeScript code compiles successfully"""
    result = subprocess.run(['npm', 'run', 'ui:build'], 
                          capture_output=True, text=True)
    
    assert result.returncode == 0, f"TypeScript compilation failed: {result.stderr}"
    print("✓ TypeScript compilation succeeds")


def test_separation_of_concerns():
    """Test that the refactoring properly separated concerns"""
    with open('src/ui/chat.ts', 'r') as f:
        chat_content = f.read()
    
    # These should no longer be in the main chat file
    methods_that_should_be_removed = [
        'private generateId',
        'private saveChatHistory', 
        'private loadChatHistory',
        'private escapeHtml'
    ]
    
    for method in methods_that_should_be_removed:
        assert method not in chat_content, f"{method} should have been moved to a service"
    print("✓ Proper separation of concerns achieved")


def test_api_calls_use_service():
    """Test that API calls now go through the ApiService"""
    with open('src/ui/chat.ts', 'r') as f:
        content = f.read()
    
    # Should use service methods instead of direct fetch calls for these operations
    service_usage = [
        'this.apiService.callChatAPI',
        'this.apiService.createNewSession',
        'this.apiService.loadTools',
        'this.apiService.toggleTool'
    ]
    
    for usage in service_usage:
        assert usage in content, f"Should use {usage} instead of direct fetch"
    print("✓ API calls use ApiService")


def test_session_management_uses_service():
    """Test that session management uses ChatService"""
    with open('src/ui/chat.ts', 'r') as f:
        content = f.read()
    
    service_usage = [
        'this.chatService.getSessions',
        'this.chatService.createSession',
        'this.chatService.addMessage',
        'this.chatService.validateMessage'
    ]
    
    for usage in service_usage:
        assert usage in content, f"Should use {usage} for session management"
    print("✓ Session management uses ChatService")


def test_utility_functions_use_utils():
    """Test that utility functions use Utils class"""
    with open('src/ui/chat.ts', 'r') as f:
        content = f.read()
    
    # Should use Utils class for these operations
    utils_usage = [
        'Utils.escapeHtml'
    ]
    
    for usage in utils_usage:
        assert usage in content, f"Should use {usage} instead of local implementation"
    
    # Should NOT have local implementations of these
    local_implementations = [
        'private generateId(',
        'private escapeHtml('
    ]
    
    for impl in local_implementations:
        assert impl not in content, f"Should not have local implementation {impl}"
    
    print("✓ Utility functions use Utils class")


if __name__ == "__main__":
    try:
        test_service_modules_exist()
        test_api_service_structure()
        test_chat_service_structure()
        test_utils_structure()
        test_main_chat_imports_services()
        test_typescript_compilation_succeeds()
        test_separation_of_concerns()
        test_api_calls_use_service()
        test_session_management_uses_service()
        test_utility_functions_use_utils()
        
        print("\n🎉 All refactoring tests passed!")
        print("The frontend has been successfully refactored with proper separation of concerns.")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)