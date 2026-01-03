"""Core scraper functionality for extracting AI training materials."""
import time
import re
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, List
from urllib.parse import urljoin, urlparse
import validators
import config
from models import ScrapedContent, get_session

class AIContentScraper:
    """Scraper for AI training materials."""
    
    # Spam keywords for filtering bad content
    SPAM_KEYWORDS = [
        'viagra', 'casino', 'lottery', 'click here now', 'buy now',
        'limited offer', 'act now', 'free money', 'earn $$$'
    ]
    
    # Minimum quality thresholds
    MIN_WORD_COUNT = 50
    MIN_QUALITY_SCORE = 0.3
    
    def __init__(self, use_ai: bool = False, ai_helper=None):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": config.USER_AGENT})
        self.use_ai = use_ai
        self.ai_helper = ai_helper
    
    def scrape_url(self, url: str, source_type: str = "manual") -> Optional[Dict]:
        """
        Scrape content from a given URL.
        
        Args:
            url: The URL to scrape
            source_type: Source type (manual, auto, scheduled)
            
        Returns:
            Dictionary with scraped content or None if failed
        """
        if not validators.url(url):
            return {"error": "Invalid URL"}
        
        try:
            response = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            # Try lxml parser first, fall back to html.parser
            try:
                soup = BeautifulSoup(response.content, "lxml")
            except Exception:
                soup = BeautifulSoup(response.content, "html.parser")
            
            # Extract title
            title = self._extract_title(soup)
            
            # Extract main content
            content = self._extract_content(soup)
            
            # Extract images
            images = self._extract_images(soup, url)
            
            # Extract videos
            videos = self._extract_videos(soup)
            
            # Extract code snippets
            code_snippets = self._extract_code(soup)
            
            # Determine content type
            content_type = self._determine_content_type(url, soup, images, videos, code_snippets)
            
            # Use AI to improve content type if available
            if self.use_ai and self.ai_helper and self.ai_helper.is_configured():
                ai_content_type = self.ai_helper.classify_content_type(title, url, content[:500])
                if ai_content_type:
                    content_type = ai_content_type
            
            # Calculate word count
            word_count = len(content.split()) if content else 0
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(
                content, title, word_count, images, code_snippets
            )
            
            # Use AI for enhanced quality checking if available
            if self.use_ai and self.ai_helper and self.ai_helper.is_configured():
                ai_quality = self.ai_helper.is_quality_content(title, content[:500], url)
                if ai_quality.get("score"):
                    # Blend AI score with heuristic score
                    quality_score = (quality_score + ai_quality["score"]) / 2
            
            # Check if content is valid (not spam/low quality)
            is_valid = self._validate_content(content, quality_score, word_count)
            
            return {
                "url": url,
                "title": title,
                "content": content,
                "content_type": content_type,
                "word_count": word_count,
                "images": images,
                "videos": videos,
                "code_snippets": code_snippets,
                "quality_score": quality_score,
                "is_valid": is_valid,
                "source_type": source_type,
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
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract image URLs from the page."""
        images = []
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src")
            if src:
                # Convert relative URLs to absolute
                absolute_url = urljoin(base_url, src)
                # Filter out tracking pixels and small images
                if self._is_valid_image_url(absolute_url):
                    images.append(absolute_url)
        return images[:20]  # Limit to 20 images
    
    def _is_valid_image_url(self, url: str) -> bool:
        """Check if image URL is valid (not tracking pixel, etc.)."""
        # Filter out common tracking pixels and invalid images
        invalid_patterns = ['tracking', 'pixel', '1x1', 'beacon', 'analytics']
        url_lower = url.lower()
        
        # Check file extension
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
        has_valid_ext = any(url_lower.endswith(ext) for ext in valid_extensions)
        
        # Check for invalid patterns
        has_invalid = any(pattern in url_lower for pattern in invalid_patterns)
        
        return has_valid_ext and not has_invalid
    
    def _extract_videos(self, soup: BeautifulSoup) -> List[str]:
        """Extract video URLs from the page."""
        videos = []
        
        # Extract video tags
        for video in soup.find_all("video"):
            src = video.get("src")
            if src:
                videos.append(src)
        
        # Extract YouTube embeds
        for iframe in soup.find_all("iframe"):
            src = iframe.get("src", "")
            if src:
                # Properly validate YouTube URLs
                from urllib.parse import urlparse
                try:
                    parsed = urlparse(src)
                    # Check if domain ends with youtube.com or is youtu.be
                    if (parsed.netloc.endswith("youtube.com") or 
                        parsed.netloc == "youtu.be" or
                        parsed.netloc.endswith(".youtube.com")):
                        videos.append(src)
                except Exception:
                    pass
        
        return videos[:10]  # Limit to 10 videos
    
    def _extract_code(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract code snippets from the page."""
        code_snippets = []
        
        # Find code blocks
        for code in soup.find_all(["code", "pre"]):
            code_text = code.get_text().strip()
            if len(code_text) > 20:  # Only include substantial code blocks
                # Try to detect language
                language = "unknown"
                classes = code.get("class", [])
                for cls in classes:
                    if isinstance(cls, str):
                        if "language-" in cls:
                            language = cls.replace("language-", "")
                        elif "lang-" in cls:
                            language = cls.replace("lang-", "")
                
                code_snippets.append({
                    "code": code_text[:500],  # Limit length
                    "language": language
                })
        
        return code_snippets[:10]  # Limit to 10 snippets
    
    def _determine_content_type(self, url: str, soup: BeautifulSoup, 
                                images: List, videos: List, code_snippets: List) -> str:
        """Determine the type of content."""
        url_lower = url.lower()
        
        # Check for specific content types based on media
        if len(images) > 5 and len(code_snippets) == 0:
            return "image"
        elif len(videos) > 0:
            return "video"
        elif len(code_snippets) > 3:
            return "code"
        elif "dataset" in url_lower or "data" in url_lower:
            return "dataset"
        elif "tutorial" in url_lower or "guide" in url_lower:
            return "tutorial"
        elif "documentation" in url_lower or "docs" in url_lower:
            return "documentation"
        elif "blog" in url_lower or "article" in url_lower:
            return "article"
        elif "wiki" in url_lower:
            return "wiki"
        else:
            return "general"
    
    def _calculate_quality_score(self, content: str, title: str, word_count: int,
                                 images: List, code_snippets: List) -> float:
        """Calculate quality score for content (0.0 to 1.0)."""
        score = 0.0
        
        # Word count score (up to 0.3)
        if word_count >= 500:
            score += 0.3
        elif word_count >= 200:
            score += 0.2
        elif word_count >= 50:
            score += 0.1
        
        # Title quality (up to 0.2)
        if title and title != "Untitled":
            if len(title) > 10:
                score += 0.2
            else:
                score += 0.1
        
        # Content structure (up to 0.2)
        if content:
            # Check for paragraphs
            paragraphs = content.split("\n\n")
            if len(paragraphs) >= 3:
                score += 0.2
            elif len(paragraphs) >= 1:
                score += 0.1
        
        # Media richness (up to 0.2)
        if len(images) > 0 or len(code_snippets) > 0:
            score += 0.1
        if len(images) >= 3 or len(code_snippets) >= 2:
            score += 0.1
        
        # AI-related content (up to 0.1)
        ai_keywords = ['machine learning', 'deep learning', 'neural network', 
                      'artificial intelligence', 'ai', 'ml', 'nlp', 'computer vision']
        content_lower = content.lower() if content else ""
        ai_mentions = sum(1 for keyword in ai_keywords if keyword in content_lower)
        if ai_mentions > 0:
            score += 0.1
        
        return min(score, 1.0)
    
    def _validate_content(self, content: str, quality_score: float, word_count: int) -> bool:
        """Validate content quality and filter spam."""
        # Check minimum word count
        if word_count < self.MIN_WORD_COUNT:
            return False
        
        # Check quality score
        if quality_score < self.MIN_QUALITY_SCORE:
            return False
        
        # Check for spam keywords
        if content:
            content_lower = content.lower()
            spam_count = sum(1 for keyword in self.SPAM_KEYWORDS if keyword in content_lower)
            if spam_count >= 2:  # Allow 1 spam keyword, but not more
                return False
        
        return True
    
    def scrape_and_save(self, url: str, source_type: str = "manual") -> Dict:
        """
        Scrape URL and save to database.
        
        Args:
            url: The URL to scrape
            source_type: Source type (manual, auto, scheduled)
            
        Returns:
            Dictionary with status and message
        """
        # Scrape the content
        result = self.scrape_url(url, source_type)
        
        if "error" in result:
            return {"success": False, "message": result["error"]}
        
        # Check if content is valid
        if not result.get("is_valid", True):
            return {
                "success": False, 
                "message": f"Content filtered (low quality or spam). Quality score: {result.get('quality_score', 0):.2f}"
            }
        
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
                existing.images = result.get("images", [])
                existing.videos = result.get("videos", [])
                existing.code_snippets = result.get("code_snippets", [])
                existing.quality_score = result.get("quality_score", 0.0)
                existing.is_valid = result.get("is_valid", True)
                existing.source_type = source_type
                message = "Content updated successfully"
            else:
                # Create new record
                content = ScrapedContent(
                    url=result["url"],
                    title=result["title"],
                    content=result["content"],
                    content_type=result["content_type"],
                    word_count=result["word_count"],
                    images=result.get("images", []),
                    videos=result.get("videos", []),
                    code_snippets=result.get("code_snippets", []),
                    quality_score=result.get("quality_score", 0.0),
                    is_valid=result.get("is_valid", True),
                    source_type=source_type,
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
    
    def scrape_multiple(self, urls: List[str], delay: float = None, source_type: str = "manual") -> List[Dict]:
        """
        Scrape multiple URLs with rate limiting.
        
        Args:
            urls: List of URLs to scrape
            delay: Delay between requests (uses config default if None)
            source_type: Source type (manual, auto, scheduled)
            
        Returns:
            List of results for each URL
        """
        if delay is None:
            delay = config.RATE_LIMIT_DELAY
        
        results = []
        for url in urls:
            result = self.scrape_and_save(url, source_type)
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
