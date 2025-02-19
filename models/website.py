from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class WebsitePattern:
    selector: str
    confidence: float
    last_used: datetime
    success_count: int
    fail_count: int

@dataclass
class Website:
    url: str
    domain: str
    patterns: Dict[str, WebsitePattern]
    last_updated: datetime
    
    def update_pattern_success(self, pattern_type: str, selector: str):
        if pattern_type in self.patterns:
            pattern = self.patterns[pattern_type]
            pattern.success_count += 1
            pattern.last_used = datetime.now()
    
    def update_pattern_failure(self, pattern_type: str, selector: str):
        if pattern_type in self.patterns:
            pattern = self.patterns[pattern_type]
            pattern.fail_count += 1 