"""Specialized scraper for code-focused AI training data."""
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import re
import config
from models import ScrapedContent, get_session


class CodeScraper:
    """Specialized scraper for extracting code for AI training."""
    
    # Common code-related HTML elements and classes
    CODE_SELECTORS = [
        "pre", "code", ".highlight", ".code-block", ".snippet",
        ".syntax", ".language-", "div[class*='code']"
    ]
    
    # Language indicators
    LANGUAGE_PATTERNS = {
        "python": ["python", "py"],
        "javascript": ["javascript", "js", "jsx"],
        "typescript": ["typescript", "ts", "tsx"],
        "java": ["java"],
        "cpp": ["cpp", "c++", "cxx"],
        "c": ["c"],
        "go": ["go", "golang"],
        "rust": ["rust", "rs"],
        "ruby": ["ruby", "rb"],
        "php": ["php"],
        "swift": ["swift"],
        "kotlin": ["kotlin", "kt"],
        "sql": ["sql"],
        "html": ["html", "htm"],
        "css": ["css"],
        "bash": ["bash", "shell", "sh"],
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": config.USER_AGENT})
    
    def scrape_code(self, url: str, min_snippets: int = 3) -> Dict:
        """
        Scrape a URL specifically for code content.
        
        Args:
            url: URL to scrape
            min_snippets: Minimum number of code snippets required
            
        Returns:
            Dictionary with code snippets and metadata
        """
        try:
            response = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Extract all code snippets
            code_snippets = self._extract_all_code(soup)
            
            # Categorize by language
            by_language = self._categorize_by_language(code_snippets)
            
            # Extract documentation/comments
            documentation = self._extract_documentation(soup)
            
            title = soup.title.string if soup.title else url
            
            # Get code context (surrounding text)
            code_contexts = self._extract_code_contexts(soup)
            
            return {
                "url": url,
                "title": title,
                "content_type": "code",
                "total_snippets": len(code_snippets),
                "code_snippets": code_snippets,
                "by_language": by_language,
                "documentation": documentation,
                "code_contexts": code_contexts,
                "meets_threshold": len(code_snippets) >= min_snippets,
            }
            
        except Exception as e:
            return {"error": f"Code scraping failed: {str(e)}"}
    
    def _extract_all_code(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract all code snippets with details."""
        code_snippets = []
        seen_code = set()
        
        for selector in self.CODE_SELECTORS:
            elements = soup.select(selector) if selector.startswith(('.', '[')) else soup.find_all(selector)
            
            for elem in elements:
                code_text = elem.get_text().strip()
                
                # Skip very short or duplicate code
                if len(code_text) < 20 or code_text in seen_code:
                    continue
                
                seen_code.add(code_text)
                
                # Detect language
                language = self._detect_language(elem, code_text)
                
                # Get line count
                line_count = len(code_text.split('\n'))
                
                snippet = {
                    "code": code_text,
                    "language": language,
                    "line_count": line_count,
                    "element_type": elem.name,
                    "classes": " ".join(elem.get("class", [])),
                }
                
                code_snippets.append(snippet)
        
        return code_snippets
    
    def _detect_language(self, elem, code_text: str) -> str:
        """Detect programming language from element or content."""
        # Check class names
        classes = " ".join(elem.get("class", [])).lower()
        
        for lang, patterns in self.LANGUAGE_PATTERNS.items():
            for pattern in patterns:
                if pattern in classes:
                    return lang
        
        # Check for language indicators in code
        if re.search(r'\bdef\s+\w+\s*\(', code_text):
            return "python"
        elif re.search(r'\b(function|const|let|var)\s+\w+', code_text):
            return "javascript"
        elif re.search(r'\bpublic\s+class\s+\w+', code_text):
            return "java"
        elif re.search(r'\b(SELECT|INSERT|UPDATE|DELETE)\s+', code_text, re.IGNORECASE):
            return "sql"
        elif re.search(r'<[a-z]+.*>', code_text):
            return "html"
        
        return "unknown"
    
    def _categorize_by_language(self, code_snippets: List[Dict]) -> Dict[str, List]:
        """Categorize code snippets by language."""
        by_language = {}
        
        for snippet in code_snippets:
            lang = snippet["language"]
            if lang not in by_language:
                by_language[lang] = []
            by_language[lang].append(snippet)
        
        return by_language
    
    def _extract_documentation(self, soup: BeautifulSoup) -> List[str]:
        """Extract documentation and comments."""
        docs = []
        
        # Look for documentation sections
        for elem in soup.find_all(["p", "div", "section"]):
            text = elem.get_text().strip()
            # Look for documentation-like text near code
            if any(keyword in text.lower() for keyword in ["example", "usage", "syntax", "parameter", "return"]):
                if len(text) > 20 and len(text) < 500:
                    docs.append(text)
        
        return docs[:10]  # Limit to 10 docs
    
    def _extract_code_contexts(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract text context around code blocks."""
        contexts = []
        
        for code_elem in soup.find_all(["pre", "code"]):
            # Get preceding text
            prev_text = ""
            prev_sibling = code_elem.find_previous_sibling()
            if prev_sibling:
                prev_text = prev_sibling.get_text().strip()[:200]
            
            # Get following text
            next_text = ""
            next_sibling = code_elem.find_next_sibling()
            if next_sibling:
                next_text = next_sibling.get_text().strip()[:200]
            
            if prev_text or next_text:
                contexts.append({
                    "before": prev_text,
                    "after": next_text,
                    "code_preview": code_elem.get_text().strip()[:100]
                })
        
        return contexts[:20]  # Limit contexts
    
    def save_to_db(self, scrape_result: Dict, source_type: str = "code_scraper") -> Dict:
        """Save code scrape results to database."""
        if "error" in scrape_result:
            return {"success": False, "message": scrape_result["error"]}
        
        if not scrape_result.get("meets_threshold", False):
            return {
                "success": False,
                "message": f"Not enough code snippets found ({scrape_result.get('total_snippets', 0)})"
            }
        
        db_session = get_session()
        try:
            url = scrape_result["url"]
            existing = db_session.query(ScrapedContent).filter_by(url=url).first()
            
            # Create content from documentation
            content = "\n\n".join(scrape_result.get("documentation", []))
            
            # Format code snippets
            code_snippets_formatted = []
            for snippet in scrape_result["code_snippets"]:
                code_snippets_formatted.append({
                    "code": snippet["code"][:1000],  # Limit length
                    "language": snippet["language"],
                    "line_count": snippet["line_count"]
                })
            
            if existing:
                existing.title = scrape_result["title"]
                existing.content = content
                existing.content_type = "code"
                existing.code_snippets = code_snippets_formatted
                existing.word_count = len(content.split())
                existing.quality_score = min(scrape_result["total_snippets"] / 10.0, 1.0)
                existing.source_type = source_type
                message = "Code content updated"
            else:
                content_obj = ScrapedContent(
                    url=url,
                    title=scrape_result["title"],
                    content=content,
                    content_type="code",
                    images=[],
                    videos=[],
                    code_snippets=code_snippets_formatted,
                    word_count=len(content.split()),
                    quality_score=min(scrape_result["total_snippets"] / 10.0, 1.0),
                    is_valid=True,
                    source_type=source_type,
                )
                db_session.add(content_obj)
                message = "Code content saved"
            
            db_session.commit()
            return {"success": True, "message": message, "data": scrape_result}
            
        except Exception as e:
            db_session.rollback()
            return {"success": False, "message": f"Database error: {str(e)}"}
        finally:
            db_session.close()


def get_code_scraper() -> CodeScraper:
    """Get code scraper instance."""
    return CodeScraper()
