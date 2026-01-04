"""Enhanced export functionality for AI training data."""
import csv
import json
from io import StringIO, BytesIO
from typing import List, Dict, Optional
from models import get_session, ScrapedContent


class DataExporter:
    """Enhanced data export with multiple formats and filters."""
    
    def export_json(self, content_type: Optional[str] = None, 
                   min_quality: Optional[float] = None) -> bytes:
        """
        Export data as JSON with optional filtering.
        
        Args:
            content_type: Filter by content type (image, code, article, etc.)
            min_quality: Minimum quality score
            
        Returns:
            JSON data as bytes
        """
        data = self._get_filtered_content(content_type, min_quality)
        json_str = json.dumps(data, indent=2)
        return json_str.encode('utf-8')
    
    def export_csv(self, content_type: Optional[str] = None,
                  min_quality: Optional[float] = None) -> bytes:
        """
        Export data as CSV.
        
        Args:
            content_type: Filter by content type
            min_quality: Minimum quality score
            
        Returns:
            CSV data as bytes
        """
        data = self._get_filtered_content(content_type, min_quality)
        
        if not data:
            return b""
        
        output = StringIO()
        
        # Define CSV fields
        fieldnames = [
            'id', 'url', 'title', 'content_type', 'word_count',
            'quality_score', 'scraped_at', 'source_type', 
            'image_count', 'video_count', 'code_snippet_count'
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for item in data:
            row = {
                'id': item.get('id'),
                'url': item.get('url'),
                'title': item.get('title'),
                'content_type': item.get('content_type'),
                'word_count': item.get('word_count'),
                'quality_score': item.get('quality_score'),
                'scraped_at': item.get('scraped_at'),
                'source_type': item.get('source_type'),
                'image_count': len(item.get('images', [])),
                'video_count': len(item.get('videos', [])),
                'code_snippet_count': len(item.get('code_snippets', [])),
            }
            writer.writerow(row)
        
        return output.getvalue().encode('utf-8')
    
    def export_images_only(self, min_quality: Optional[float] = None) -> Dict:
        """
        Export only image URLs and metadata.
        
        Args:
            min_quality: Minimum quality score
            
        Returns:
            Dictionary with image data
        """
        db_session = get_session()
        try:
            query = db_session.query(ScrapedContent).filter(
                ScrapedContent.images.isnot(None)
            )
            
            if min_quality is not None:
                query = query.filter(ScrapedContent.quality_score >= min_quality)
            
            results = query.all()
            
            image_data = []
            for item in results:
                if item.images:
                    for img_url in item.images:
                        image_data.append({
                            "image_url": img_url,
                            "source_url": item.url,
                            "source_title": item.title,
                            "content_type": item.content_type,
                            "quality_score": item.quality_score,
                            "scraped_at": item.scraped_at.isoformat() if item.scraped_at else None
                        })
            
            return {
                "total_images": len(image_data),
                "images": image_data
            }
        finally:
            db_session.close()
    
    def export_code_only(self, language: Optional[str] = None,
                        min_quality: Optional[float] = None) -> Dict:
        """
        Export only code snippets.
        
        Args:
            language: Filter by programming language
            min_quality: Minimum quality score
            
        Returns:
            Dictionary with code data
        """
        db_session = get_session()
        try:
            query = db_session.query(ScrapedContent).filter(
                ScrapedContent.code_snippets.isnot(None)
            )
            
            if min_quality is not None:
                query = query.filter(ScrapedContent.quality_score >= min_quality)
            
            results = query.all()
            
            code_data = []
            for item in results:
                if item.code_snippets:
                    for snippet in item.code_snippets:
                        # Filter by language if specified
                        if language and snippet.get("language") != language:
                            continue
                        
                        code_data.append({
                            "code": snippet.get("code"),
                            "language": snippet.get("language"),
                            "source_url": item.url,
                            "source_title": item.title,
                            "quality_score": item.quality_score,
                            "scraped_at": item.scraped_at.isoformat() if item.scraped_at else None
                        })
            
            return {
                "total_snippets": len(code_data),
                "code_snippets": code_data
            }
        finally:
            db_session.close()
    
    def export_by_content_type(self) -> Dict:
        """
        Export data grouped by content type.
        
        Returns:
            Dictionary with data grouped by type
        """
        db_session = get_session()
        try:
            all_content = db_session.query(ScrapedContent).all()
            
            by_type = {}
            for item in all_content:
                content_type = item.content_type or "general"
                if content_type not in by_type:
                    by_type[content_type] = []
                
                by_type[content_type].append(item.to_dict())
            
            return {
                "total_types": len(by_type),
                "by_type": by_type,
                "summary": {
                    ctype: len(items) for ctype, items in by_type.items()
                }
            }
        finally:
            db_session.close()
    
    def export_training_dataset(self, content_type: Optional[str] = None) -> Dict:
        """
        Export data formatted for AI training.
        
        Args:
            content_type: Filter by content type
            
        Returns:
            Dictionary in training-ready format
        """
        data = self._get_filtered_content(content_type, min_quality=0.5)
        
        training_data = []
        for item in data:
            # Format based on content type
            if item.get('content_type') == 'image':
                # Image training format
                for img_url in item.get('images', []):
                    training_data.append({
                        "image_url": img_url,
                        "caption": item.get('title'),
                        "metadata": {
                            "source": item.get('url'),
                            "quality": item.get('quality_score')
                        }
                    })
            elif item.get('content_type') == 'code':
                # Code training format
                for snippet in item.get('code_snippets', []):
                    training_data.append({
                        "code": snippet.get('code'),
                        "language": snippet.get('language'),
                        "description": item.get('title'),
                        "metadata": {
                            "source": item.get('url'),
                            "quality": item.get('quality_score')
                        }
                    })
            else:
                # Text training format
                training_data.append({
                    "text": item.get('content'),
                    "title": item.get('title'),
                    "type": item.get('content_type'),
                    "metadata": {
                        "url": item.get('url'),
                        "word_count": item.get('word_count'),
                        "quality": item.get('quality_score')
                    }
                })
        
        return {
            "total_samples": len(training_data),
            "content_type": content_type or "all",
            "samples": training_data
        }
    
    def _get_filtered_content(self, content_type: Optional[str] = None,
                             min_quality: Optional[float] = None) -> List[Dict]:
        """Get filtered content from database."""
        db_session = get_session()
        try:
            query = db_session.query(ScrapedContent)
            
            if content_type:
                query = query.filter(ScrapedContent.content_type == content_type)
            
            if min_quality is not None:
                query = query.filter(ScrapedContent.quality_score >= min_quality)
            
            results = query.order_by(ScrapedContent.scraped_at.desc()).all()
            
            # Return full content (not preview)
            data = []
            for item in results:
                item_dict = item.to_dict()
                item_dict['content'] = item.content  # Full content
                data.append(item_dict)
            
            return data
        finally:
            db_session.close()


def get_exporter() -> DataExporter:
    """Get data exporter instance."""
    return DataExporter()
