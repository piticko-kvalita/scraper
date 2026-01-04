"""Comprehensive scraper for all AI training material types."""
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import re
import config
from models import ScrapedContent, get_session


class UniversalAIScraper:
    """Universal scraper for all types of AI training materials."""
    
    # All AI training material types
    MATERIAL_TYPES = {
        "text": "Text content for NLP/LLM training",
        "image": "Images for computer vision",
        "video": "Videos for video understanding AI",
        "audio": "Audio files for speech/music AI",
        "code": "Code for code generation AI",
        "dataset": "Structured datasets for ML",
        "pdf": "PDF documents for document AI",
        "table": "Tables for tabular data AI",
        "qa": "Question-Answer pairs for chatbots",
        "dialogue": "Conversations for dialogue AI",
        "transcript": "Text transcripts for NLU",
        "annotation": "Annotated data for supervised learning",
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": config.USER_AGENT})
    
    def scrape_all_materials(self, url: str) -> Dict:
        """
        Scrape ALL types of AI training materials from a URL.
        
        Args:
            url: URL to scrape
            
        Returns:
            Dictionary with all material types found
        """
        try:
            response = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Extract all material types
            materials = {
                "url": url,
                "title": soup.title.string if soup.title else url,
                "text": self._extract_text(soup),
                "images": self._extract_images(soup, url),
                "videos": self._extract_videos(soup),
                "audio": self._extract_audio(soup, url),
                "code": self._extract_code(soup),
                "datasets": self._extract_datasets(soup, url),
                "pdfs": self._extract_pdfs(soup, url),
                "tables": self._extract_tables(soup),
                "qa_pairs": self._extract_qa_pairs(soup),
                "dialogues": self._extract_dialogues(soup),
                "transcripts": self._extract_transcripts(soup),
                "annotations": self._extract_annotations(soup),
            }
            
            # Calculate richness score
            materials["richness_score"] = self._calculate_richness(materials)
            materials["material_types_found"] = self._get_found_types(materials)
            
            return materials
            
        except Exception as e:
            return {"error": f"Scraping failed: {str(e)}"}
    
    def _extract_text(self, soup: BeautifulSoup) -> Dict:
        """Extract text content."""
        # Get main content
        main_content = soup.find("main") or soup.find("article") or soup
        
        paragraphs = [p.get_text().strip() for p in main_content.find_all("p")]
        text_content = "\n\n".join(paragraphs)
        
        return {
            "content": text_content[:5000],  # Preview
            "full_length": len(text_content),
            "paragraph_count": len(paragraphs),
            "word_count": len(text_content.split()),
        }
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Extract images for computer vision AI."""
        images = []
        seen_urls = set()
        
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src")
            if not src:
                continue
            
            absolute_url = urljoin(base_url, src)
            if absolute_url in seen_urls:
                continue
            seen_urls.add(absolute_url)
            
            images.append({
                "url": absolute_url,
                "alt": img.get("alt", ""),
                "title": img.get("title", ""),
                "width": img.get("width"),
                "height": img.get("height"),
            })
        
        return images[:50]  # Increased limit
    
    def _extract_videos(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract videos for video understanding AI."""
        videos = []
        
        # Video tags
        for video in soup.find_all("video"):
            src = video.get("src")
            if src:
                videos.append({
                    "url": src,
                    "type": "video",
                    "duration": video.get("duration"),
                })
        
        # YouTube/Vimeo embeds
        for iframe in soup.find_all("iframe"):
            src = iframe.get("src", "")
            if src:
                try:
                    parsed = urlparse(src)
                    netloc = parsed.netloc.lower()
                    if netloc in ("www.youtube.com", "youtube.com", "youtu.be", "m.youtube.com", "vimeo.com", "player.vimeo.com"):
                        videos.append({
                            "url": src,
                            "type": "embed",
                            "platform": netloc,
                        })
                except Exception:
                    pass
        
        return videos[:20]
    
    def _extract_audio(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Extract audio files for speech/music AI training."""
        audio_files = []
        
        # Audio tags
        for audio in soup.find_all("audio"):
            src = audio.get("src")
            if src:
                audio_files.append({
                    "url": urljoin(base_url, src),
                    "type": "audio",
                    "format": audio.get("type", "unknown"),
                })
            
            # Source tags within audio
            for source in audio.find_all("source"):
                src = source.get("src")
                if src:
                    audio_files.append({
                        "url": urljoin(base_url, src),
                        "type": "audio",
                        "format": source.get("type", "unknown"),
                    })
        
        # Links to audio files
        for link in soup.find_all("a", href=True):
            href = link["href"].lower()
            if any(ext in href for ext in [".mp3", ".wav", ".ogg", ".m4a", ".flac"]):
                audio_files.append({
                    "url": urljoin(base_url, link["href"]),
                    "type": "audio_link",
                    "text": link.get_text().strip()[:100],
                })
        
        return audio_files[:20]
    
    def _extract_code(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract code snippets for code generation AI."""
        code_snippets = []
        
        for elem in soup.find_all(["pre", "code"]):
            code_text = elem.get_text().strip()
            if len(code_text) < 10:
                continue
            
            # Detect language
            language = "unknown"
            classes = " ".join(elem.get("class", [])).lower()
            
            # Common language patterns
            lang_patterns = {
                "python": ["python", "py"],
                "javascript": ["javascript", "js", "jsx"],
                "java": ["java"],
                "cpp": ["cpp", "c++"],
                "go": ["go", "golang"],
                "rust": ["rust"],
                "sql": ["sql"],
                "html": ["html"],
                "css": ["css"],
            }
            
            for lang, patterns in lang_patterns.items():
                if any(p in classes for p in patterns):
                    language = lang
                    break
            
            code_snippets.append({
                "code": code_text[:2000],
                "language": language,
                "line_count": len(code_text.split('\n')),
            })
        
        return code_snippets[:30]
    
    def _extract_datasets(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Extract links to datasets for ML training."""
        datasets = []
        
        # Look for dataset links
        for link in soup.find_all("a", href=True):
            href = link["href"].lower()
            text = link.get_text().lower()
            
            # Common dataset file formats
            if any(ext in href for ext in [".csv", ".json", ".xlsx", ".parquet", ".tsv", ".h5", ".hdf5"]):
                datasets.append({
                    "url": urljoin(base_url, link["href"]),
                    "type": "dataset_file",
                    "format": href.split(".")[-1],
                    "description": link.get_text().strip()[:200],
                })
            
            # Dataset keywords
            elif any(keyword in text for keyword in ["dataset", "data download", "training data", "test data"]):
                datasets.append({
                    "url": urljoin(base_url, link["href"]),
                    "type": "dataset_link",
                    "description": link.get_text().strip()[:200],
                })
        
        return datasets[:15]
    
    def _extract_pdfs(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Extract PDF documents for document AI training."""
        pdfs = []
        
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if ".pdf" in href.lower():
                pdfs.append({
                    "url": urljoin(base_url, href),
                    "title": link.get_text().strip()[:200],
                    "type": "pdf",
                })
        
        # PDF embeds
        for embed in soup.find_all("embed", src=True):
            if ".pdf" in embed["src"].lower():
                pdfs.append({
                    "url": urljoin(base_url, embed["src"]),
                    "title": embed.get("title", ""),
                    "type": "pdf_embed",
                })
        
        return pdfs[:15]
    
    def _extract_tables(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract tables for tabular data AI training."""
        tables = []
        
        for table in soup.find_all("table"):
            # Extract headers
            headers = []
            header_row = table.find("tr")
            if header_row:
                headers = [th.get_text().strip() for th in header_row.find_all(["th", "td"])]
            
            # Extract rows
            rows = []
            for tr in table.find_all("tr")[1:]:  # Skip header
                cells = [td.get_text().strip() for td in tr.find_all(["td", "th"])]
                if cells:
                    rows.append(cells)
            
            if rows:
                column_count = len(headers) if headers else (len(rows[0]) if rows[0] else 0)
                tables.append({
                    "headers": headers,
                    "rows": rows[:100],  # Limit rows
                    "row_count": len(rows),
                    "column_count": column_count,
                })
        
        return tables[:10]
    
    def _extract_qa_pairs(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract Q&A pairs for chatbot/assistant training."""
        qa_pairs = []
        
        # Look for FAQ sections
        for elem in soup.find_all(["div", "section"], class_=re.compile("faq|question|qa", re.I)):
            # Find questions and answers
            questions = elem.find_all(["h3", "h4", "h5", "dt", "div"], class_=re.compile("question", re.I))
            
            for q in questions:
                question_text = q.get_text().strip()
                # Find following answer
                answer = q.find_next_sibling()
                if answer:
                    answer_text = answer.get_text().strip()
                    if question_text and answer_text:
                        qa_pairs.append({
                            "question": question_text[:500],
                            "answer": answer_text[:1000],
                        })
        
        return qa_pairs[:20]
    
    def _extract_dialogues(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract conversation/dialogue data for dialogue AI."""
        dialogues = []
        
        # Look for chat/conversation patterns
        for elem in soup.find_all(["div", "section"], class_=re.compile("chat|conversation|message", re.I)):
            messages = []
            for msg in elem.find_all(["div", "p"], class_=re.compile("message|msg", re.I)):
                speaker = "unknown"
                # Try to find speaker
                speaker_elem = msg.find(["span", "strong"], class_=re.compile("user|author|speaker", re.I))
                if speaker_elem:
                    speaker = speaker_elem.get_text().strip()
                
                text = msg.get_text().strip()
                if text:
                    messages.append({
                        "speaker": speaker,
                        "text": text[:500],
                    })
            
            if len(messages) >= 2:  # At least 2 messages for dialogue
                dialogues.append({
                    "messages": messages[:20],
                    "turn_count": len(messages),
                })
        
        return dialogues[:10]
    
    def _extract_transcripts(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract transcripts for NLU training."""
        transcripts = []
        
        # Look for transcript sections
        for elem in soup.find_all(["div", "section"], class_=re.compile("transcript|captions", re.I)):
            text = elem.get_text().strip()
            if len(text) > 100:
                # Try to identify timestamps
                has_timestamps = bool(re.findall(r'\d{1,2}:\d{2}', text))
                
                transcripts.append({
                    "content": text[:5000],
                    "has_timestamps": has_timestamps,
                    "word_count": len(text.split()),
                })
        
        return transcripts[:5]
    
    def _extract_annotations(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract annotated/labeled data for supervised learning."""
        annotations = []
        
        # Look for data with labels/tags
        for elem in soup.find_all(["span", "div"], attrs={"data-label": True}):
            annotations.append({
                "content": elem.get_text().strip()[:500],
                "label": elem.get("data-label"),
                "type": "labeled_span",
            })
        
        # Look for tagged content
        for elem in soup.find_all(class_=re.compile("tag|label|category", re.I)):
            parent = elem.parent
            if parent:
                annotations.append({
                    "content": parent.get_text().strip()[:500],
                    "label": elem.get_text().strip(),
                    "type": "tagged_content",
                })
        
        return annotations[:20]
    
    def _calculate_richness(self, materials: Dict) -> float:
        """Calculate how rich the scraped materials are."""
        score = 0.0
        
        # Text
        if materials["text"]["word_count"] > 100:
            score += 1.0
        
        # Images
        if len(materials["images"]) > 0:
            score += min(len(materials["images"]) / 20.0, 1.0)
        
        # Videos
        if len(materials["videos"]) > 0:
            score += min(len(materials["videos"]) / 5.0, 1.0)
        
        # Audio
        if len(materials["audio"]) > 0:
            score += min(len(materials["audio"]) / 5.0, 1.0)
        
        # Code
        if len(materials["code"]) > 0:
            score += min(len(materials["code"]) / 10.0, 1.0)
        
        # Datasets
        if len(materials["datasets"]) > 0:
            score += 1.0
        
        # PDFs
        if len(materials["pdfs"]) > 0:
            score += min(len(materials["pdfs"]) / 5.0, 1.0)
        
        # Tables
        if len(materials["tables"]) > 0:
            score += min(len(materials["tables"]) / 5.0, 1.0)
        
        # Q&A
        if len(materials["qa_pairs"]) > 0:
            score += 1.0
        
        # Dialogues
        if len(materials["dialogues"]) > 0:
            score += 1.0
        
        # Transcripts
        if len(materials["transcripts"]) > 0:
            score += 1.0
        
        # Annotations
        if len(materials["annotations"]) > 0:
            score += 1.0
        
        return min(score / 12.0, 1.0)  # Normalize to 0-1
    
    def _get_found_types(self, materials: Dict) -> List[str]:
        """Get list of material types found."""
        found = []
        
        if materials["text"]["word_count"] > 50:
            found.append("text")
        if len(materials["images"]) > 0:
            found.append("image")
        if len(materials["videos"]) > 0:
            found.append("video")
        if len(materials["audio"]) > 0:
            found.append("audio")
        if len(materials["code"]) > 0:
            found.append("code")
        if len(materials["datasets"]) > 0:
            found.append("dataset")
        if len(materials["pdfs"]) > 0:
            found.append("pdf")
        if len(materials["tables"]) > 0:
            found.append("table")
        if len(materials["qa_pairs"]) > 0:
            found.append("qa")
        if len(materials["dialogues"]) > 0:
            found.append("dialogue")
        if len(materials["transcripts"]) > 0:
            found.append("transcript")
        if len(materials["annotations"]) > 0:
            found.append("annotation")
        
        return found
    
    def save_to_db(self, scrape_result: Dict, source_type: str = "universal_scraper") -> Dict:
        """Save universal scrape results to database."""
        if "error" in scrape_result:
            return {"success": False, "message": scrape_result["error"]}
        
        db_session = get_session()
        try:
            url = scrape_result["url"]
            existing = db_session.query(ScrapedContent).filter_by(url=url).first()
            
            # Determine primary content type
            types_found = scrape_result["material_types_found"]
            primary_type = types_found[0] if types_found else "text"
            
            # Consolidate all materials into JSON fields
            all_materials = {
                "text": scrape_result["text"],
                "audio": scrape_result["audio"],
                "datasets": scrape_result["datasets"],
                "pdfs": scrape_result["pdfs"],
                "tables": scrape_result["tables"],
                "qa_pairs": scrape_result["qa_pairs"],
                "dialogues": scrape_result["dialogues"],
                "transcripts": scrape_result["transcripts"],
                "annotations": scrape_result["annotations"],
            }
            
            if existing:
                existing.title = scrape_result["title"]
                existing.content = scrape_result["text"]["content"]
                existing.content_type = primary_type
                existing.images = [img["url"] for img in scrape_result["images"]]
                existing.videos = [vid["url"] for vid in scrape_result["videos"]]
                existing.code_snippets = scrape_result["code"]
                existing.word_count = scrape_result["text"]["word_count"]
                existing.quality_score = scrape_result["richness_score"]
                existing.source_type = source_type
                message = f"Updated with {len(types_found)} material types"
            else:
                content_obj = ScrapedContent(
                    url=url,
                    title=scrape_result["title"],
                    content=scrape_result["text"]["content"],
                    content_type=primary_type,
                    images=[img["url"] for img in scrape_result["images"]],
                    videos=[vid["url"] for vid in scrape_result["videos"]],
                    code_snippets=scrape_result["code"],
                    word_count=scrape_result["text"]["word_count"],
                    quality_score=scrape_result["richness_score"],
                    is_valid=True,
                    source_type=source_type,
                )
                db_session.add(content_obj)
                message = f"Saved with {len(types_found)} material types"
            
            db_session.commit()
            return {
                "success": True,
                "message": message,
                "data": {
                    "material_types": types_found,
                    "richness_score": scrape_result["richness_score"],
                }
            }
            
        except Exception as e:
            db_session.rollback()
            return {"success": False, "message": f"Database error: {str(e)}"}
        finally:
            db_session.close()


def get_universal_scraper() -> UniversalAIScraper:
    """Get universal AI scraper instance."""
    return UniversalAIScraper()
