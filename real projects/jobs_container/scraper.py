"""
Web Scraper for Product Prices
This scraper needs specific Chrome and Selenium versions to work reliably
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import sys
from datetime import datetime


def setup_driver():
    """Configure Chrome driver with headless options"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def scrape_quotes():
    """Scrape quotes from a demo website"""
    driver = setup_driver()
    results = []
    
    try:
        print("Starting scraper...")
        driver.get("http://quotes.toscrape.com/")
        
        # Wait for quotes to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "quote"))
        )
        
        # Extract quotes
        quotes = driver.find_elements(By.CLASS_NAME, "quote")
        
        for quote in quotes[:5]:  # Get first 5 quotes
            text = quote.find_element(By.CLASS_NAME, "text").text
            author = quote.find_element(By.CLASS_NAME, "author").text
            
            results.append({
                "quote": text,
                "author": author,
                "scraped_at": datetime.now().isoformat()
            })
        
        print(f"Successfully scraped {len(results)} quotes")
        
    except Exception as e:
        print(f"Error during scraping: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        driver.quit()
    
    return results


def save_results(data, filename="results.json"):
    """Save scraped data to JSON file"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Results saved to {filename}")


if __name__ == "__main__":
    quotes = scrape_quotes()
    save_results(quotes)
    
    # Print summary
    print("\n=== Scraping Summary ===")
    print(f"Total quotes: {len(quotes)}")
    print(f"Authors: {', '.join(set(q['author'] for q in quotes))}")
