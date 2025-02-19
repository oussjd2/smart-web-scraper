from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional
import logging

class WebsiteAnalyzer:
    def __init__(self, driver):
        self.driver = driver
        self.logger = logging.getLogger(__name__)

    def analyze_website_structure(self, url: str) -> Dict:
        """Analyze website structure and detect content patterns"""
        self.logger.info(f"Analyzing website structure: {url}")
        
        # Get page source
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Detect patterns
        content_patterns = self._detect_content_patterns(soup)
        nav_patterns = self._detect_navigation_patterns(soup)
        
        # Get best candidates
        selectors = {}
        
        # Find best article candidate
        if content_patterns['article_candidates']:
            best_article = max(content_patterns['article_candidates'], 
                             key=lambda x: x['score'])
            selectors['article'] = best_article['selector']
            
        # Find best title candidate
        if content_patterns['title_candidates']:
            selectors['title'] = content_patterns['title_candidates'][0]['selector']
            
        # Find link patterns
        link_patterns = [
            '.post-card-inline__title',  # Common news sites
            'a.title',                   # Common blog pattern
            'h2 a',                      # Common list pattern
            'article a',                 # Article links
            '.entry-title a',            # WordPress pattern
            'a[class*="title"]',         # Generic title links
            'a[class*="article"]',       # Generic article links
            '.ible-title'                # Instructables specific
        ]
        
        # Test each link pattern
        for pattern in link_patterns:
            try:
                links = soup.select(pattern)
                if links and len(links) > 2:  # At least 3 links
                    selectors['link_selector'] = pattern
                    break
            except:
                continue
                
        if 'link_selector' not in selectors:
            selectors['link_selector'] = 'a'  # Fallback to all links
            
        return {
            'selectors': selectors,
            'navigation': nav_patterns
        }

    def _detect_content_patterns(self, soup: BeautifulSoup) -> Dict:
        """Detect content patterns in the page"""
        patterns = {
            'article_candidates': [],
            'title_candidates': [],
            'link_patterns': []
        }

        # Find potential article containers
        for tag in soup.find_all(['article', 'div', 'section']):
            score = self._score_content_block(tag)
            if score > 0.5:  # Threshold for likely content
                patterns['article_candidates'].append({
                    'selector': self._get_unique_selector(tag),
                    'score': score,
                    'features': self._extract_block_features(tag)
                })

        # Find potential titles
        for tag in soup.find_all(['h1', 'h2', 'h3']):
            if self._is_likely_title(tag):
                patterns['title_candidates'].append({
                    'selector': self._get_unique_selector(tag),
                    'text': tag.get_text(strip=True),
                    'features': self._extract_title_features(tag)
                })

        return patterns

    def _score_content_block(self, tag) -> float:
        """Score a block based on how likely it is to be main content"""
        score = 0.0
        text = tag.get_text(strip=True)
        
        # Text length score
        if len(text) > 1000:
            score += 0.4
        elif len(text) > 500:
            score += 0.2

        # Structure score
        if tag.find_all(['p', 'img', 'ul', 'ol']):
            score += 0.3

        # Class/ID hints
        hints = ['content', 'article', 'post', 'entry']
        for attr in ['class', 'id']:
            if tag.get(attr):
                if any(hint in str(tag[attr]).lower() for hint in hints):
                    score += 0.2

        return min(score, 1.0)

    def _get_unique_selector(self, tag) -> str:
        """Generate a unique CSS selector for an element"""
        if tag.get('id'):
            return f"#{tag['id']}"
            
        classes = tag.get('class', [])
        if classes:
            return f"{tag.name}.{'.'.join(classes)}"
            
        # Generate path-based selector
        path = []
        parent = tag
        while parent and parent.name != '[document]':
            siblings = parent.find_previous_siblings(parent.name)
            if siblings:
                path.append(f"{parent.name}:nth-of-type({len(siblings) + 1})")
            else:
                path.append(parent.name)
            parent = parent.parent
            
        return ' > '.join(reversed(path))

    def verify_selectors(self, selectors: Dict) -> Dict:
        """Verify detected selectors work properly"""
        verified = {}
        
        for name, selector in selectors.items():
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    verified[name] = {
                        'selector': selector,
                        'sample': elements[0].text[:100],
                        'count': len(elements)
                    }
            except Exception as e:
                self.logger.warning(f"Failed to verify selector {selector}: {e}")
                
        return verified

    def learn_from_successful_scrape(self, url: str, successful_selectors: Dict):
        """Learn from successful scraping patterns"""
        # Implementation for pattern learning
        pass

    def _detect_navigation_patterns(self, soup: BeautifulSoup) -> Dict:
        """Detect navigation patterns in the page"""
        patterns = {
            'next_page': None,
            'pagination': None,
            'menu': None
        }
        
        # Find pagination
        for tag in soup.find_all(['a', 'button', 'div']):
            text = tag.get_text(strip=True).lower()
            if 'next' in text or '→' in text:
                patterns['next_page'] = self._get_unique_selector(tag)
            if any(x in text for x in ['page', 'previous', 'next']):
                patterns['pagination'] = self._get_unique_selector(tag.parent)
                
        return patterns

    def _identify_key_selectors(self, soup: BeautifulSoup) -> Dict:
        """Identify key selectors for the page"""
        content_patterns = self._detect_content_patterns(soup)
        nav_patterns = self._detect_navigation_patterns(soup)
        
        # Get best candidates
        selectors = {}
        if content_patterns['article_candidates']:
            best_article = max(content_patterns['article_candidates'], 
                             key=lambda x: x['score'])
            selectors['article'] = best_article['selector']
            
        if content_patterns['title_candidates']:
            selectors['title'] = content_patterns['title_candidates'][0]['selector']
            
        return {**selectors, **nav_patterns}

    def _is_likely_title(self, tag) -> bool:
        """Check if a tag is likely to be a title"""
        text = tag.get_text(strip=True)
        if not text:
            return False
            
        # Length check
        if len(text) < 10 or len(text) > 200:
            return False
            
        # Position check
        if tag.find_parent('article'):
            return True
            
        # Style check
        if tag.get('class'):
            classes = ' '.join(tag.get('class')).lower()
            if any(x in classes for x in ['title', 'heading', 'header']):
                return True
                
        return False

    def _extract_block_features(self, tag) -> Dict:
        """Extract features from a content block"""
        return {
            'text_length': len(tag.get_text(strip=True)),
            'has_paragraphs': bool(tag.find_all('p')),
            'has_images': bool(tag.find_all('img')),
            'has_links': bool(tag.find_all('a')),
            'depth': len(list(tag.parents))
        }

    def _extract_title_features(self, tag) -> Dict:
        """Extract features from a title element"""
        return {
            'text_length': len(tag.get_text(strip=True)),
            'tag_name': tag.name,
            'classes': tag.get('class', []),
            'is_header': bool(tag.find_parent('header'))
        } 