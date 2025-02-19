from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class SelectorDetector:
    def __init__(self, driver):
        self.driver = driver
        self.common_selectors = {
            'article': [
                'article', '.article', '.post', '.post-content', 
                'div[class*="article"]', 'div[class*="content"]',
                '.main-content',  # Added for Instructables
                '.step-body'      # Added for Instructables steps
            ],
            'title': [
                'h1', '.article-title', '.post-title', 
                'h1[class*="title"]', '[class*="headline"]',
                '.header-title'   # Added for Instructables
            ],
            'links': [
                'a[href*="article"]', 'a[href*="news"]', 
                '.article-link', '.post-link', 
                'a[class*="title"]', '[class*="article-card"]',
                '.ible-title'     # Added for Instructables
            ]
        }

    def detect_selectors(self, url):
        """Automatically detect selectors for a given website"""
        print(f"\nAnalyzing website: {url}")
        self.driver.get(url)
        time.sleep(3)  # Wait for dynamic content

        detected = {
            'article_selector': self.detect_article_selector(),
            'title_selector': self.detect_title_selector(),
            'link_selector': self.detect_link_selector()
        }

        # Verify with user
        return self.verify_selectors(detected)

    def detect_article_selector(self):
        """Detect the main article content selector"""
        for selector in self.common_selectors['article']:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements and len(elements[0].text) > 200:  # Likely article content
                    return selector
            except:
                continue
        return None

    def detect_title_selector(self):
        """Detect the article title selector"""
        for selector in self.common_selectors['title']:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements and len(elements[0].text) > 10:  # Likely a title
                    return selector
            except:
                continue
        return None

    def detect_link_selector(self):
        """Detect article link selector"""
        for selector in self.common_selectors['links']:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements and len(elements) > 3:  # Multiple article links
                    return selector
            except:
                continue
        return None

    def verify_selectors(self, detected):
        """Verify detected selectors with user"""
        print("\nDetected selectors:")
        
        for name, selector in detected.items():
            if selector:
                print(f"\n{name}:")
                print(f"Suggested: {selector}")
                
                # Show example content
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    preview = element.text[:100] + "..." if len(element.text) > 100 else element.text
                    print(f"Example content: {preview}")
                except:
                    print("Could not fetch example content")
                
                if not input("\nAccept this selector? (Y/n): ").lower().startswith('n'):
                    continue
                
                # Let user modify if needed
                new_selector = input("Enter alternative selector (or press Enter to skip): ").strip()
                if new_selector:
                    detected[name] = new_selector
            else:
                print(f"\nCould not detect {name}")
                detected[name] = input(f"Please enter {name} manually: ")

        return detected

    def test_selectors(self, selectors):
        """Test if selectors work properly"""
        try:
            # Test article selector
            article = self.driver.find_element(By.CSS_SELECTOR, selectors['article_selector'])
            if not article or len(article.text) < 100:
                print("Warning: Article selector might not be optimal")

            # Test title selector
            title = self.driver.find_element(By.CSS_SELECTOR, selectors['title_selector'])
            if not title or len(title.text) < 5:
                print("Warning: Title selector might not be optimal")

            # Test link selector
            links = self.driver.find_elements(By.CSS_SELECTOR, selectors['link_selector'])
            if not links or len(links) < 2:
                print("Warning: Link selector might not be optimal")

            return True
        except Exception as e:
            print(f"Error testing selectors: {e}")
            return False 