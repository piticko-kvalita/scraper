"""Core scraper functionality for extracting AI training materials."""
import time
import re
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, List
import validators
import config
from models import ScrapedContent, get_session

class AIContentScraper:
    """Scraper for AI training materials."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": config.USER_AGENT})
    
    def scrape_url(self, url: str) -> Optional[Dict]:
        """
        Scrape content from a given URL.
        
        Args:
            url: The URL to scrape
            
        Returns:
            Dictionary with scraped content or None if failed
        """
        if not validators.url(url):
            return {"error": "Invalid URL"}
        
        try:
            response = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "lxml")
            
            # Extract title
            title = self._extract_title(soup)
            
            # Extract main content
            content = self._extract_content(soup)
            
            # Determine content type
            content_type = self._determine_content_type(url, soup)
            
            # Calculate word count
            word_count = len(content.split()) if content else 0
            
            return {
                "url": url,
                "title": title,
                "content": content,
                "content_type": content_type,
                "word_count": word_count,
            }
            
        except requests.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Scraping failed: {str(e)}"}
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        # Try multiple methods to get title
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        
        h1 = soup.find("h1")
        if h1:
            return h1.get_text().strip()
        
        return "Untitled"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from the page."""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Try to find main content area
        main_content = None
        
        # Look for common content containers
        for selector in ["main", "article", "#content", ".content", "#main", ".main"]:
            if selector.startswith("#") or selector.startswith("."):
                main_content = soup.select_one(selector)
            else:
                main_content = soup.find(selector)
            if main_content:
                break
        
        # If no main content found, use body
        if not main_content:
            main_content = soup.find("body")
        
        if not main_content:
            return ""
        
        # Extract text and clean it
        text = main_content.get_text(separator="\n", strip=True)
        
        # Clean up excessive whitespace
        text = re.sub(r"\n\s*\n", "\n\n", text)
        text = re.sub(r" +", " ", text)
        
        return text.strip()
    
    def _determine_content_type(self, url: str, soup: BeautifulSoup) -> str:
        """Determine the type of content."""
        url_lower = url.lower()
        
        if "tutorial" in url_lower or "guide" in url_lower:
            return "tutorial"
        elif "documentation" in url_lower or "docs" in url_lower:
            return "documentation"
        elif "blog" in url_lower or "article" in url_lower:
            return "article"
        elif "wiki" in url_lower:
            return "wiki"
        else:
            return "general"
    
    def scrape_and_save(self, url: str) -> Dict:
        """
        Scrape URL and save to database.
        
        Args:
            url: The URL to scrape
            
        Returns:
            Dictionary with status and message
        """
        # Scrape the content
        result = self.scrape_url(url)
        
        if "error" in result:
            return {"success": False, "message": result["error"]}
        
        # Save to database
        db_session = get_session()
        try:
            # Check if URL already exists
            existing = db_session.query(ScrapedContent).filter_by(url=url).first()
            
            if existing:
                # Update existing record
                existing.title = result["title"]
                existing.content = result["content"]
                existing.content_type = result["content_type"]
                existing.word_count = result["word_count"]
                message = "Content updated successfully"
            else:
                # Create new record
                content = ScrapedContent(
                    url=result["url"],
                    title=result["title"],
                    content=result["content"],
                    content_type=result["content_type"],
                    word_count=result["word_count"],
                )
                db_session.add(content)
                message = "Content scraped and saved successfully"
            
            db_session.commit()
            return {"success": True, "message": message, "data": result}
            
        except Exception as e:
            db_session.rollback()
            return {"success": False, "message": f"Database error: {str(e)}"}
        finally:
            db_session.close()
    
    def scrape_multiple(self, urls: List[str], delay: float = None) -> List[Dict]:
        """
        Scrape multiple URLs with rate limiting.
        
        Args:
            urls: List of URLs to scrape
            delay: Delay between requests (uses config default if None)
            
        Returns:
            List of results for each URL
        """
        if delay is None:
            delay = config.RATE_LIMIT_DELAY
        
        results = []
        for url in urls:
            result = self.scrape_and_save(url)
            results.append(result)
            
            # Rate limiting
            if url != urls[-1]:  # Don't delay after last URL
                time.sleep(delay)
        
        return results

def get_all_content() -> List[Dict]:
    """Get all scraped content from database."""
    db_session = get_session()
    try:
        contents = db_session.query(ScrapedContent).order_by(
            ScrapedContent.scraped_at.desc()
        ).all()
        return [content.to_dict() for content in contents]
    finally:
        db_session.close()

def get_content_by_id(content_id: int) -> Optional[Dict]:
    """Get specific content by ID."""
    db_session = get_session()
    try:
        content = db_session.query(ScrapedContent).filter_by(id=content_id).first()
        if content:
            result = content.to_dict()
            result["content"] = content.content  # Full content
            return result
        return None
    finally:
        db_session.close()

def delete_content(content_id: int) -> bool:
    """Delete content by ID."""
    db_session = get_session()
    try:
        content = db_session.query(ScrapedContent).filter_by(id=content_id).first()
        if content:
            db_session.delete(content)
            db_session.commit()
            return True
        return False
    finally:
        db_session.close()

def get_statistics() -> Dict:
    """Get scraping statistics."""
    db_session = get_session()
    try:
        total_items = db_session.query(ScrapedContent).count()
        total_words = db_session.query(ScrapedContent).with_entities(
            ScrapedContent.word_count
        ).all()
        word_count = sum(w[0] for w in total_words if w[0])
        
        # Content type distribution
        content_types = {}
        types = db_session.query(
            ScrapedContent.content_type, ScrapedContent.id
        ).all()
        
        for content_type, _ in types:
            content_types[content_type] = content_types.get(content_type, 0) + 1
        
        return {
            "total_items": total_items,
            "total_words": word_count,
            "content_types": content_types,
        }
    finally:
        db_session.close()
