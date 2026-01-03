"""Specialized scraper for image-focused AI training data."""
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import config
from models import ScrapedContent, get_session


class ImageScraper:
    """Specialized scraper for extracting images for AI training."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": config.USER_AGENT})
    
    def scrape_images(self, url: str, min_images: int = 5) -> Dict:
        """
        Scrape a URL specifically for image content.
        
        Args:
            url: URL to scrape
            min_images: Minimum number of images required
            
        Returns:
            Dictionary with images and metadata
        """
        try:
            response = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Extract all images
            images = self._extract_all_images(soup, url)
            
            # Filter and categorize images
            categorized = self._categorize_images(images)
            
            # Extract image metadata
            image_metadata = self._extract_image_metadata(soup, images)
            
            title = soup.title.string if soup.title else url
            
            # Get alt text and captions
            alt_texts = self._extract_alt_texts(soup)
            
            return {
                "url": url,
                "title": title,
                "content_type": "image",
                "total_images": len(images),
                "images": images,
                "categorized_images": categorized,
                "image_metadata": image_metadata,
                "alt_texts": alt_texts,
                "meets_threshold": len(images) >= min_images,
            }
            
        except Exception as e:
            return {"error": f"Image scraping failed: {str(e)}"}
    
    def _extract_all_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Extract all images with details."""
        images = []
        seen_urls = set()
        
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
            if not src:
                continue
            
            # Convert to absolute URL
            absolute_url = urljoin(base_url, src)
            
            # Skip duplicates
            if absolute_url in seen_urls:
                continue
            seen_urls.add(absolute_url)
            
            # Get image attributes
            image_data = {
                "url": absolute_url,
                "alt": img.get("alt", ""),
                "title": img.get("title", ""),
                "width": img.get("width"),
                "height": img.get("height"),
                "class": " ".join(img.get("class", [])),
            }
            
            images.append(image_data)
        
        return images
    
    def _categorize_images(self, images: List[Dict]) -> Dict[str, List]:
        """Categorize images by type."""
        categories = {
            "large": [],      # Likely main content images
            "medium": [],     # Regular images
            "small": [],      # Icons, thumbnails
            "unknown": []     # No size info
        }
        
        for img in images:
            width = img.get("width")
            height = img.get("height")
            
            try:
                if width and height:
                    w = int(width) if isinstance(width, str) else width
                    h = int(height) if isinstance(height, str) else height
                    
                    if w >= 800 or h >= 600:
                        categories["large"].append(img)
                    elif w >= 300 or h >= 200:
                        categories["medium"].append(img)
                    else:
                        categories["small"].append(img)
                else:
                    categories["unknown"].append(img)
            except (ValueError, TypeError):
                categories["unknown"].append(img)
        
        return categories
    
    def _extract_image_metadata(self, soup: BeautifulSoup, images: List[Dict]) -> Dict:
        """Extract metadata about images."""
        return {
            "page_title": soup.title.string if soup.title else "",
            "meta_description": soup.find("meta", {"name": "description"}),
            "image_count": len(images),
            "has_gallery": bool(soup.find_all(["gallery", "figure"], limit=5)),
        }
    
    def _extract_alt_texts(self, soup: BeautifulSoup) -> List[str]:
        """Extract all alt texts for training."""
        alt_texts = []
        for img in soup.find_all("img"):
            alt = img.get("alt", "").strip()
            if alt and len(alt) > 3:  # Only meaningful alt text
                alt_texts.append(alt)
        return alt_texts
    
    def save_to_db(self, scrape_result: Dict, source_type: str = "image_scraper") -> Dict:
        """Save image scrape results to database."""
        if "error" in scrape_result:
            return {"success": False, "message": scrape_result["error"]}
        
        if not scrape_result.get("meets_threshold", False):
            return {
                "success": False,
                "message": f"Not enough images found ({scrape_result.get('total_images', 0)})"
            }
        
        db_session = get_session()
        try:
            url = scrape_result["url"]
            existing = db_session.query(ScrapedContent).filter_by(url=url).first()
            
            # Create content description from alt texts
            content = "\n".join(scrape_result.get("alt_texts", []))
            
            if existing:
                existing.title = scrape_result["title"]
                existing.content = content
                existing.content_type = "image"
                existing.images = [img["url"] for img in scrape_result["images"]]
                existing.word_count = len(content.split())
                existing.quality_score = min(scrape_result["total_images"] / 20.0, 1.0)
                existing.source_type = source_type
                message = "Image content updated"
            else:
                content_obj = ScrapedContent(
                    url=url,
                    title=scrape_result["title"],
                    content=content,
                    content_type="image",
                    images=[img["url"] for img in scrape_result["images"]],
                    videos=[],
                    code_snippets=[],
                    word_count=len(content.split()),
                    quality_score=min(scrape_result["total_images"] / 20.0, 1.0),
                    is_valid=True,
                    source_type=source_type,
                )
                db_session.add(content_obj)
                message = "Image content saved"
            
            db_session.commit()
            return {"success": True, "message": message, "data": scrape_result}
            
        except Exception as e:
            db_session.rollback()
            return {"success": False, "message": f"Database error: {str(e)}"}
        finally:
            db_session.close()


def get_image_scraper() -> ImageScraper:
    """Get image scraper instance."""
    return ImageScraper()
