import json
from datetime import datetime
from typing import Dict, Optional
import os
from models.website import Website, WebsitePattern

class PatternStorage:
    def __init__(self, storage_file: str = 'website_patterns.json'):
        self.storage_file = storage_file
        self.patterns = self._load_patterns()

    def _load_patterns(self) -> Dict:
        """Load saved patterns from file"""
        if os.path.exists(self.storage_file):
            with open(self.storage_file, 'r') as f:
                data = json.load(f)
                # Convert JSON to Website objects
                return {
                    domain: Website(
                        url=site_data['url'],
                        domain=domain,
                        patterns={
                            k: WebsitePattern(**v) for k, v in site_data['patterns'].items()
                        },
                        last_updated=datetime.fromisoformat(site_data['last_updated'])
                    )
                    for domain, site_data in data.items()
                }
        return {}

    def save_patterns(self):
        """Save patterns to file"""
        data = {
            domain: {
                'url': website.url,
                'patterns': {
                    k: {
                        'selector': v.selector,
                        'confidence': v.confidence,
                        'last_used': v.last_used.isoformat(),
                        'success_count': v.success_count,
                        'fail_count': v.fail_count
                    }
                    for k, v in website.patterns.items()
                },
                'last_updated': website.last_updated.isoformat()
            }
            for domain, website in self.patterns.items()
        }
        
        with open(self.storage_file, 'w') as f:
            json.dump(data, f, indent=4)

    def get_patterns(self, domain: str) -> Optional[Website]:
        """Get patterns for a specific domain"""
        return self.patterns.get(domain)

    def update_patterns(self, website: Website):
        """Update patterns for a website"""
        self.patterns[website.domain] = website
        self.save_patterns() 