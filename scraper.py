import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fpdf import FPDF
import time
import json
import os
from datetime import datetime
import urllib.request
from core.website_analyzer import WebsiteAnalyzer
from core.content_extractor import ContentExtractor
from utils.storage import PatternStorage
from models.website import Website, WebsitePattern
from urllib.parse import urlparse
import logging
from typing import Dict, Optional

class SmartScraper:
    def __init__(self):
        self.setup_logging()
        self.data_file = 'scraping_data.json'
        self.pdf_output_dir = 'scraped_articles'
        self.setup_directories()
        self.session_data = self.initialize_session_data()
        self.driver = self.setup_driver()
        self.analyzer = WebsiteAnalyzer(self.driver)
        self.extractor = ContentExtractor(self.driver)
        self.storage = PatternStorage()
        self.current_session = self.create_new_session()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def setup_driver(self):
        options = uc.ChromeOptions()
        options.headless = False
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        return uc.Chrome(options=options, version_main=133)

    def setup_directories(self):
        if not os.path.exists(self.pdf_output_dir):
            os.makedirs(self.pdf_output_dir)

    def initialize_session_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return {"sessions": {}}

    def create_new_session(self):
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.session_data["sessions"][session_id] = {
            "date": datetime.now().strftime('%Y-%m-%d'),
            "links": []
        }
        self.save_session_data()
        return session_id

    def save_session_data(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.session_data, f, indent=4)

    def run(self):
        try:
            while True:
                print("\nWeb Scraper Menu:")
                print("1. Manual Surf Mode")
                print("2. Auto Surf Mode")
                print("3. Scrape Single URL")
                print("4. Manage Links")
                print("5. Export Options")
                print("6. Exit")
                
                mode = input("\nChoose mode (1-6): ").strip()
                
                if mode == "6":
                    break
                    
                if mode in ["1", "2", "3"]:
                    url = input("Enter website URL to scrape: ").strip()
                    if not url.startswith(('http://', 'https://')):
                        url = 'https://' + url
                    
                    try:
                        print(f"\nNavigating to {url}")
                        self.driver.get(url)
                        time.sleep(3)  # Wait for page to load
                        
                        if mode == "1":
                            self.manual_surf_mode()
                        elif mode == "2":
                            self.auto_surf_mode()
                        elif mode == "3":
                            self.scrape_single_url(url)
                    except Exception as e:
                        print(f"Error accessing URL: {e}")
                        continue
                        
                elif mode == "4":
                    self.manage_links_menu()
                elif mode == "5":
                    self.export_menu()

        except Exception as e:
            print(f"Error in main loop: {e}")

    def manual_surf_mode(self, duration=120):
        """Manual surf mode where user clicks links"""
        print("\nStarting manual surf mode...")
        print("Instructions:")
        print("- Browser will open and you can click on articles")
        print("- Each clicked link will be saved automatically")
        print("- Links will open in new tabs")
        print(f"- Session will last {duration} seconds")
        input("Press Enter to start...")

        start_time = time.time()
        original_window = self.driver.current_window_handle
        
        while time.time() - start_time < duration:
            try:
                for handle in self.driver.window_handles:
                    if handle != original_window:
                        self.driver.switch_to.window(handle)
                        url = self.driver.current_url
                        content = self.scrape_content(url)
                        
                        if content:
                            self.add_to_session(url, content)
                            print(f"\nScraped: {content.get('title', 'No title')}")
                        
                        self.driver.close()
                        self.driver.switch_to.window(original_window)
                
                remaining = duration - (time.time() - start_time)
                print(f"\rTime remaining: {int(remaining)} seconds", end='')
                time.sleep(1)
                
            except Exception as e:
                print(f"\nError in manual surf: {e}")
                continue

    def auto_surf_mode(self, duration=120):
        """Auto surf mode that finds and scrapes content"""
        print(f"\nStarting auto surf mode for {duration} seconds...")
        start_time = time.time()
        
        try:
            # Initial analysis of the page
            analysis = self.analyzer.analyze_website_structure(self.driver.current_url)
            if not analysis or 'selectors' not in analysis:
                print("Could not detect article patterns on this page")
                return

            selectors = analysis['selectors']
            if 'link_selector' not in selectors:
                print("Could not detect article links on this page")
                return

            while time.time() - start_time < duration:
                try:
                    # Find article links
                    links = self.driver.find_elements(By.CSS_SELECTOR, selectors['link_selector'])
                    print(f"\nFound {len(links)} potential article links")
                    
                    for link in links[:5]:  # Process top 5 links
                        try:
                            url = link.get_attribute('href')
                            if url and url.startswith(('http://', 'https://')):
                                print(f"\nAnalyzing: {url}")
                                content = self.scrape_content(url)
                                if content:
                                    self.add_to_session(url, content)
                                    print(f"Scraped: {content.get('title', 'No title')}")
                                    print(f"Content length: {len(content.get('content', ''))}")
                        except Exception as e:
                            print(f"Error processing link: {e}")
                            continue
                    
                    # Try to find and click next page if available
                    if 'next_page' in analysis['navigation'] and analysis['navigation']['next_page']:
                        try:
                            next_button = self.driver.find_element(
                                By.CSS_SELECTOR, analysis['navigation']['next_page']
                            )
                            next_button.click()
                            time.sleep(3)
                        except:
                            print("\nNo more pages to process")
                            break
                    
                    remaining = duration - (time.time() - start_time)
                    print(f"\rTime remaining: {int(remaining)} seconds", end='')
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"\nError during scraping: {e}")
                    time.sleep(1)
                    
        except Exception as e:
            print(f"\nError in auto surf: {e}")

    def add_to_session(self, url: str, content: dict):
        """Add scraped content to current session"""
        self.session_data["sessions"][self.current_session]["links"].append({
            "url": url,
            "title": content.get('title', ''),
            "content": content.get('content', ''),
            "date": content.get('date', ''),
            "scraped_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        self.save_session_data()

    def manage_links_menu(self):
        """Submenu for managing links"""
        while True:
            print("\nManage Links Menu:")
            print("1. View All Sessions")
            print("2. View Links by Session")
            print("3. Start New Session")
            print("4. Back to Main Menu")
            
            choice = input("\nChoose option (1-4): ").strip()
            
            if choice == "1":
                self.view_sessions()
            elif choice == "2":
                self.view_session_links()
            elif choice == "3":
                self.current_session = self.create_new_session()
            elif choice == "4":
                break

    def export_menu(self):
        """Submenu for export options"""
        while True:
            print("\nExport Options:")
            print("1. Export All to Single PDF")
            print("2. Export Each Article to Separate PDFs")
            print("3. Export by Session")
            print("4. Back to Main Menu")
            
            choice = input("\nChoose option (1-4): ").strip()
            
            if choice == "1":
                self.export_to_pdf(single_file=True)
            elif choice == "2":
                self.export_to_pdf(single_file=False)
            elif choice == "3":
                self.view_sessions()
                session_id = input("Enter session ID to export: ")
                if session_id in self.session_data["sessions"]:
                    self.export_to_pdf(session_id=session_id)
                else:
                    print("Invalid session ID")
            elif choice == "4":
                break

    def export_to_pdf(self, session_id=None, single_file=False):
        """Export articles to PDF"""
        if single_file:
            pdf = FPDF()
            
        sessions_to_process = ([session_id] if session_id 
                             else list(self.session_data["sessions"].keys()))
        
        for sess_id in sessions_to_process:
            session = self.session_data["sessions"][sess_id]
            for link in session["links"]:
                try:
                    title = link["title"]
                    content = link["content"]
                    
                    if single_file:
                        pdf.add_page()
                        pdf.set_font('Arial', 'B', 16)
                        pdf.multi_cell(0, 10, txt=title)
                        pdf.ln(10)
                        pdf.set_font('Arial', size=12)
                        pdf.multi_cell(0, 10, txt=content)
                    else:
                        self.create_single_pdf(title, content)
                        
                except Exception as e:
                    print(f"Error exporting {link.get('url', 'unknown URL')}: {e}")
                    continue
        
        if single_file:
            filename = os.path.join(self.pdf_output_dir, "all_articles.pdf")
            pdf.output(filename, 'F')
            print(f"All articles exported to: {filename}")

    def create_single_pdf(self, title, content):
        """Create a single PDF file for an article"""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.multi_cell(0, 10, txt=title)
        pdf.ln(10)
        pdf.set_font('Arial', size=12)
        pdf.multi_cell(0, 10, txt=content)
        
        safe_title = "".join(x for x in title if x.isalnum() or x in (' ', '-', '_'))[:50]
        filename = os.path.join(self.pdf_output_dir, f"{safe_title}.pdf")
        pdf.output(filename, 'F')
        print(f"Saved to: {filename}")

    def view_sessions(self):
        """Display all sessions and their statistics"""
        print("\nAvailable Sessions:")
        for session_id, session in self.session_data["sessions"].items():
            print(f"\nSession ID: {session_id}")
            print(f"Date: {session['date']}")
            print(f"Total Links: {len(session['links'])}")
            print("-" * 50)

    def view_session_links(self):
        """View links in a specific session"""
        self.view_sessions()
        session_id = input("\nEnter session ID to view links: ")
        
        if session_id in self.session_data["sessions"]:
            session = self.session_data["sessions"][session_id]
            print(f"\nLinks in session {session_id}:")
            for i, link in enumerate(session["links"], 1):
                print(f"\n{i}. Title: {link['title']}")
                print(f"   URL: {link['url']}")
                print(f"   Scraped Date: {link['scraped_date']}")
        else:
            print("Invalid session ID")

    def analyze_website(self, url: str) -> Dict:
        """Analyze website and detect patterns"""
        domain = urlparse(url).netloc
        
        # Check if we have existing patterns
        existing = self.storage.get_patterns(domain)
        if existing and existing.last_updated > datetime.now().timestamp() - 86400:
            self.logger.info("Using existing patterns")
            return existing.patterns
            
        # Analyze website structure
        self.logger.info(f"Analyzing website: {url}")
        analysis = self.analyzer.analyze_website_structure(url)
        
        # Create new patterns
        patterns = {}
        for pattern_type, candidates in analysis['content_patterns'].items():
            if candidates:
                # Use the highest scoring candidate
                best_candidate = max(candidates, key=lambda x: x['score'])
                patterns[pattern_type] = WebsitePattern(
                    selector=best_candidate['selector'],
                    confidence=best_candidate['score'],
                    last_used=datetime.now(),
                    success_count=0,
                    fail_count=0
                )
        
        # Save patterns
        website = Website(
            url=url,
            domain=domain,
            patterns=patterns,
            last_updated=datetime.now()
        )
        self.storage.update_patterns(website)
        
        return patterns

    def scrape_content(self, url: str) -> Optional[Dict]:
        """Scrape content from a URL"""
        try:
            self.driver.get(url)
            time.sleep(2)  # Wait for page load
            
            analysis = self.analyzer.analyze_website_structure(url)
            if not analysis or 'selectors' not in analysis:
                print("Could not detect content structure")
                return None
                
            selectors = analysis['selectors']
            if 'article' not in selectors or 'title' not in selectors:
                print("Missing required selectors")
                return None
                
            content = self.extractor.extract_content(selectors)
            if content:
                # Update success patterns
                website = self.storage.get_patterns(urlparse(url).netloc)
                if website:
                    for pattern_type in selectors:
                        website.update_pattern_success(pattern_type, selectors[pattern_type])
                    self.storage.update_patterns(website)
                
                return content
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {e}")
            return None

    def scrape_single_url(self, url: str):
        """Scrape content from a single URL"""
        if not url:
            print("Please provide a valid URL")
            return
            
        try:
            print(f"\nAnalyzing and scraping: {url}")
            self.driver.get(url)
            content = self.scrape_content(url)
            
            if content:
                self.add_to_session(url, content)
                print(f"\nSuccessfully scraped:")
                print(f"Title: {content.get('title', 'No title')}")
                print(f"Content length: {len(content.get('content', ''))}")
            else:
                print("Failed to extract content")
                
        except Exception as e:
            print(f"Error scraping URL: {e}")

    def __del__(self):
        if hasattr(self, 'driver'):
            self.driver.quit()

if __name__ == "__main__":
    scraper = SmartScraper()
    scraper.run()
