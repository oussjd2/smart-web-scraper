from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class ContentExtractor:
    def __init__(self, driver):
        self.driver = driver
        self.logger = logging.getLogger(__name__)

    def extract_content(self, selectors: Dict[str, str]) -> Dict:
        """Extract content using provided selectors"""
        content = {}
        
        try:
            # Wait for main content
            if 'article' in selectors:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selectors['article']))
                )
            
            # Extract title
            if 'title' in selectors:
                title_elem = self.driver.find_element(By.CSS_SELECTOR, selectors['title'])
                content['title'] = title_elem.text.strip()
            
            # Extract main content
            if 'article' in selectors:
                article_elem = self.driver.find_element(By.CSS_SELECTOR, selectors['article'])
                content['content'] = article_elem.text.strip()
            
            # Extract metadata if available
            if 'date' in selectors:
                try:
                    date_elem = self.driver.find_element(By.CSS_SELECTOR, selectors['date'])
                    content['date'] = date_elem.get_attribute('datetime') or date_elem.text
                except:
                    self.logger.warning("Could not extract date")
            
            return content
            
        except Exception as e:
            self.logger.error(f"Error extracting content: {e}")
            return None 