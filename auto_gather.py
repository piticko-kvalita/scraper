"""Automatic gathering module for scheduled scraping of AI training materials."""
import time
import threading
from datetime import datetime, timedelta
from typing import List, Dict
import config
from scraper import AIContentScraper, get_all_content
from models import get_session, ScrapedContent

class AutoGatherer:
    """Automatic content gathering with scheduling."""
    
    # Default AI training material sources to automatically scrape
    DEFAULT_AUTO_SOURCES = [
        "https://en.wikipedia.org/wiki/Machine_learning",
        "https://en.wikipedia.org/wiki/Deep_learning",
        "https://en.wikipedia.org/wiki/Neural_network",
        "https://en.wikipedia.org/wiki/Computer_vision",
        "https://en.wikipedia.org/wiki/Natural_language_processing",
    ]
    
    def __init__(self, interval_hours: int = 24):
        """
        Initialize auto gatherer.
        
        Args:
            interval_hours: Hours between automatic scraping runs
        """
        self.interval_hours = interval_hours
        self.scraper = AIContentScraper()
        self.is_running = False
        self.thread = None
        self.sources = self.DEFAULT_AUTO_SOURCES.copy()
    
    def add_source(self, url: str):
        """Add a URL to the automatic gathering sources."""
        if url not in self.sources:
            self.sources.append(url)
    
    def remove_source(self, url: str):
        """Remove a URL from automatic gathering sources."""
        if url in self.sources:
            self.sources.remove(url)
    
    def get_sources(self) -> List[str]:
        """Get list of automatic gathering sources."""
        return self.sources.copy()
    
    def scrape_now(self) -> Dict:
        """Manually trigger automatic gathering."""
        print(f"[AutoGatherer] Starting manual scrape of {len(self.sources)} sources...")
        results = self.scraper.scrape_multiple(
            self.sources, 
            delay=config.RATE_LIMIT_DELAY,
            source_type="auto"
        )
        
        success_count = sum(1 for r in results if r.get("success", False))
        filtered_count = sum(
            1 for r in results 
            if not r.get("success", False) and "filtered" in r.get("message", "").lower()
        )
        
        print(f"[AutoGatherer] Completed: {success_count} successful, {filtered_count} filtered")
        
        return {
            "success": True,
            "scraped": success_count,
            "filtered": filtered_count,
            "total": len(results),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _run_scheduled(self):
        """Run scheduled scraping in background."""
        print(f"[AutoGatherer] Starting scheduled gathering (every {self.interval_hours} hours)")
        
        while self.is_running:
            try:
                # Run scraping
                self.scrape_now()
                
                # Wait for next interval
                if self.is_running:
                    sleep_seconds = self.interval_hours * 3600
                    print(f"[AutoGatherer] Next run in {self.interval_hours} hours")
                    
                    # Sleep in small intervals to allow stopping
                    for _ in range(int(sleep_seconds / 10)):
                        if not self.is_running:
                            break
                        time.sleep(10)
                    
            except Exception as e:
                print(f"[AutoGatherer] Error during scheduled run: {e}")
                time.sleep(60)  # Wait a minute before retrying
    
    def start(self):
        """Start automatic gathering in background thread."""
        if self.is_running:
            print("[AutoGatherer] Already running")
            return False
        
        self.is_running = True
        self.thread = threading.Thread(target=self._run_scheduled, daemon=True)
        self.thread.start()
        print("[AutoGatherer] Started")
        return True
    
    def stop(self):
        """Stop automatic gathering."""
        if not self.is_running:
            print("[AutoGatherer] Not running")
            return False
        
        print("[AutoGatherer] Stopping...")
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("[AutoGatherer] Stopped")
        return True
    
    def get_status(self) -> Dict:
        """Get current status of auto gatherer."""
        db_session = get_session()
        try:
            # Get stats for auto-scraped content
            auto_content = db_session.query(ScrapedContent).filter_by(
                source_type="auto"
            ).all()
            
            return {
                "is_running": self.is_running,
                "interval_hours": self.interval_hours,
                "sources_count": len(self.sources),
                "auto_scraped_count": len(auto_content),
                "sources": self.sources,
            }
        finally:
            db_session.close()


def discover_related_urls(base_urls: List[str], max_depth: int = 1) -> List[str]:
    """
    Discover related URLs from a set of base URLs.
    
    Args:
        base_urls: List of starting URLs
        max_depth: How many levels deep to follow links
        
    Returns:
        List of discovered URLs
    """
    discovered = set()
    scraper = AIContentScraper()
    
    for url in base_urls:
        try:
            response = scraper.session.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Find links with AI-related keywords
            ai_keywords = ['machine-learning', 'deep-learning', 'neural', 'ai', 'artificial-intelligence']
            
            for link in soup.find_all("a", href=True):
                href = link.get("href")
                if href:
                    from urllib.parse import urljoin
                    absolute_url = urljoin(url, href)
                    
                    # Check if URL contains AI keywords
                    if any(keyword in absolute_url.lower() for keyword in ai_keywords):
                        discovered.add(absolute_url)
            
            time.sleep(config.RATE_LIMIT_DELAY)
            
        except Exception as e:
            print(f"Error discovering URLs from {url}: {e}")
            continue
    
    return list(discovered)[:50]  # Limit to 50 discovered URLs


# Global auto gatherer instance
_auto_gatherer = None

def get_auto_gatherer(interval_hours: int = 24) -> AutoGatherer:
    """Get or create the global auto gatherer instance."""
    global _auto_gatherer
    if _auto_gatherer is None:
        _auto_gatherer = AutoGatherer(interval_hours)
    return _auto_gatherer
