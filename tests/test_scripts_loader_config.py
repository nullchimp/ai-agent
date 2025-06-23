import pytest
from unittest.mock import Mock, patch
from scripts.loader_config import DOC_LOADER_CONFIGS, WEB_LOADER_CONFIGS, LoaderConfig, WebLoaderConfig


def test_loader_config_structure():
    assert len(DOC_LOADER_CONFIGS) >= 1
    assert all(isinstance(config, LoaderConfig) for config in DOC_LOADER_CONFIGS)
    
    first_config = DOC_LOADER_CONFIGS[0]
    assert first_config.path
    assert first_config.file_extensions
    assert first_config.uri_replacement


def test_web_loader_config_structure():
    assert len(WEB_LOADER_CONFIGS) >= 1
    assert all(isinstance(config, WebLoaderConfig) for config in WEB_LOADER_CONFIGS)
    
    first_config = WEB_LOADER_CONFIGS[0]
    assert first_config.url
    assert first_config.uri_replacement


def test_loader_config_uri_replacement():
    config = LoaderConfig(
        path="/test/path",
        file_extensions=['.md'],
        uri_replacement=("/old/path", "https://new.url")
    )
    
    assert config.uri_replacement[0] == "/old/path"
    assert config.uri_replacement[1] == "https://new.url"


def test_web_loader_config_uri_replacement():
    config = WebLoaderConfig(
        url="http://localhost:4000/test",
        uri_replacement=("http://localhost:4000", "https://docs.github.com")
    )
    
    assert config.uri_replacement[0] == "http://localhost:4000"
    assert config.uri_replacement[1] == "https://docs.github.com"


def test_doc_loader_config_validation():
    """Test that DOC_LOADER_CONFIGS has valid configuration for doc_loader.py logic"""
    from scripts.loader_config import DOC_LOADER_CONFIGS
    
    config = DOC_LOADER_CONFIGS[0]
    assert config.path == "/Users/nullchimp/Projects/customer-security-trust/FAQ"
    assert config.file_extensions == ['.md']
    assert config.uri_replacement is not None
    assert config.uri_replacement == (
        "/Users/nullchimp/Projects/customer-security-trust/FAQ", 
        "https://github.com/github/customer-security-trust/blob/main/FAQ"
    )
    
    # Test that the second config doesn't have URI replacement
    config2 = DOC_LOADER_CONFIGS[1]
    assert config2.path == "/Users/nullchimp/Projects/github-docs/content-copilot"
    assert config2.file_extensions == ['.md']
    assert config2.uri_replacement is None


def test_doc_loader_uri_replacement_logic():
    config = DOC_LOADER_CONFIGS[0]
    
    # Simulate source URI that would come from DocumentLoader
    mock_source_uri = "/Users/nullchimp/Projects/customer-security-trust/FAQ/security-faq.md"
    
    if config.uri_replacement:
        old_pattern, new_pattern = config.uri_replacement
        # This is the actual logic from doc_loader.py
        new_uri = mock_source_uri.replace(old_pattern, new_pattern)
        
        expected_uri = "https://github.com/github/customer-security-trust/blob/main/FAQ/security-faq.md"
        assert new_uri == expected_uri


def test_web_loader_uri_replacement_logic():
    config = WEB_LOADER_CONFIGS[0]
    
    # Simulate source URI that would come from WebLoader  
    mock_source_uri = "http://localhost:4000/en/enterprise-cloud@latest"
    mock_source_name = "some-page.md"
    
    if config.uri_replacement:
        old_pattern, new_pattern = config.uri_replacement
        # This is the actual logic from url_loader.py
        new_uri = f"{mock_source_uri.replace(old_pattern, new_pattern)}"
        
        expected_uri = "https://docs.github.com/en/enterprise-cloud@latest"
        assert new_uri == expected_uri


def test_config_has_expected_structure():
    # Test that we have the expected number of configs
    assert len(DOC_LOADER_CONFIGS) == 2
    assert len(WEB_LOADER_CONFIGS) == 1
    
    # Test first doc loader config (with URI replacement)
    first_doc_config = DOC_LOADER_CONFIGS[0]
    assert first_doc_config.uri_replacement is not None
    
    # Test second doc loader config (without URI replacement)
    second_doc_config = DOC_LOADER_CONFIGS[1]
    assert second_doc_config.path == "/Users/nullchimp/Projects/github-docs/content-copilot"
    assert second_doc_config.uri_replacement is None
    
    # Test web loader config
    web_config = WEB_LOADER_CONFIGS[0]
    assert web_config.url == "http://localhost:4000/en/enterprise-cloud@latest"
    assert web_config.uri_replacement is not None
