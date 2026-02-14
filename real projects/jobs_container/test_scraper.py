"""
Unit tests for the web scraper
Run with: pytest test_scraper.py
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from scraper import setup_driver, scrape_quotes, save_results
import json


def test_setup_driver():
    """Test that driver is configured with correct options"""
    with patch('scraper.webdriver.Chrome') as mock_chrome:
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        driver = setup_driver()
        
        # Verify Chrome was called
        mock_chrome.assert_called_once()
        assert driver == mock_driver


def test_save_results(tmp_path):
    """Test that results are saved correctly to JSON"""
    test_data = [
        {"quote": "Test quote", "author": "Test Author", "scraped_at": "2024-01-01"}
    ]
    
    output_file = tmp_path / "test_results.json"
    save_results(test_data, str(output_file))
    
    # Verify file was created
    assert output_file.exists()
    
    # Verify content is correct
    with open(output_file) as f:
        loaded_data = json.load(f)
    
    assert loaded_data == test_data


@patch('scraper.webdriver.Chrome')
def test_scrape_quotes_success(mock_chrome):
    """Test successful scraping"""
    # Mock the driver and web elements
    mock_driver = MagicMock()
    mock_chrome.return_value = mock_driver
    
    # Mock quote elements
    mock_quote = MagicMock()
    mock_text = MagicMock()
    mock_text.text = "Life is what happens when you're busy making other plans."
    mock_author = MagicMock()
    mock_author.text = "John Lennon"
    
    mock_quote.find_element.side_effect = lambda by, value: mock_text if "text" in value else mock_author
    mock_driver.find_elements.return_value = [mock_quote]
    
    # Run scraper
    results = scrape_quotes()
    
    # Assertions
    assert len(results) == 1
    assert results[0]["author"] == "John Lennon"
    assert "Life is what happens" in results[0]["quote"]
    assert "scraped_at" in results[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
