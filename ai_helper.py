"""AI-powered helper using OpenRouter API for intelligent scraping tasks."""
import requests
import json
from typing import List, Dict, Optional
import config

class AIHelper:
    """AI-powered assistant for scraping tasks using OpenRouter."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize AI Helper.
        
        Args:
            api_key: OpenRouter API key (uses config if not provided)
        """
        self.api_key = api_key or config.OPENROUTER_API_KEY
        self.api_url = config.OPENROUTER_API_URL
        self.model = config.OPENROUTER_MODEL
    
    def is_configured(self) -> bool:
        """Check if AI helper is properly configured."""
        return bool(self.api_key and self.api_key != "")
    
    def _call_ai(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        """
        Call OpenRouter API.
        
        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response
            
        Returns:
            AI response text or None if failed
        """
        if not self.is_configured():
            return None
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/piticko-kvalita/scraper",
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7,
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except Exception as e:
            print(f"AI API Error: {e}")
            return None
    
    def suggest_ai_urls(self, topic: str, count: int = 10) -> List[str]:
        """
        Use AI to suggest URLs for AI training materials on a topic.
        
        Args:
            topic: Topic to find materials for
            count: Number of URLs to suggest
            
        Returns:
            List of suggested URLs
        """
        if not self.is_configured():
            return []
        
        prompt = f"""You are helping build a dataset of AI training materials. 
Suggest {count} high-quality, reputable URLs about "{topic}" that would be good sources for AI training data.

Focus on:
- Wikipedia articles
- Academic resources
- Documentation sites
- Tutorial sites
- Research papers

Return ONLY a JSON array of URLs, no other text.
Example: ["https://example.com/page1", "https://example.com/page2"]
"""
        
        response = self._call_ai(prompt, max_tokens=500)
        if not response:
            return []
        
        try:
            # Extract JSON from response
            response = response.strip()
            if response.startswith("```"):
                # Remove markdown code blocks
                lines = response.split("\n")
                response = "\n".join(line for line in lines if not line.startswith("```"))
            
            urls = json.loads(response.strip())
            if isinstance(urls, list):
                return [url for url in urls if isinstance(url, str)]
        except Exception as e:
            print(f"Error parsing AI response: {e}")
        
        return []
    
    def is_quality_content(self, title: str, content_preview: str, url: str) -> Dict[str, any]:
        """
        Use AI to evaluate if content is high quality and relevant.
        
        Args:
            title: Content title
            content_preview: Preview of content (first 500 chars)
            url: Content URL
            
        Returns:
            Dict with is_quality (bool), reason (str), score (float)
        """
        if not self.is_configured():
            # Fallback to simple heuristic
            score = 0.5
            if len(content_preview) > 200:
                score += 0.2
            if any(word in title.lower() for word in ['ai', 'machine learning', 'deep learning']):
                score += 0.3
            return {
                "is_quality": score > 0.6,
                "reason": "Basic heuristic evaluation",
                "score": score
            }
        
        prompt = f"""Evaluate if this content is high-quality AI training material.

Title: {title}
URL: {url}
Content Preview: {content_preview[:300]}...

Respond with ONLY a JSON object:
{{
    "is_quality": true/false,
    "score": 0.0-1.0,
    "reason": "brief explanation"
}}
"""
        
        response = self._call_ai(prompt, max_tokens=200)
        if not response:
            return {"is_quality": True, "reason": "AI unavailable", "score": 0.5}
        
        try:
            # Extract JSON from response
            response = response.strip()
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join(line for line in lines if not line.startswith("```"))
            
            result = json.loads(response.strip())
            return {
                "is_quality": result.get("is_quality", True),
                "reason": result.get("reason", ""),
                "score": float(result.get("score", 0.5))
            }
        except Exception as e:
            print(f"Error parsing AI quality response: {e}")
            return {"is_quality": True, "reason": "Parse error", "score": 0.5}
    
    def extract_key_topics(self, content: str) -> List[str]:
        """
        Use AI to extract key topics from content.
        
        Args:
            content: Content text
            
        Returns:
            List of key topics
        """
        if not self.is_configured():
            # Fallback: simple keyword extraction
            common_topics = [
                'machine learning', 'deep learning', 'neural networks',
                'natural language processing', 'computer vision', 'reinforcement learning'
            ]
            return [topic for topic in common_topics if topic in content.lower()][:5]
        
        prompt = f"""Extract the key AI/ML topics from this content. Return ONLY a JSON array of topics.

Content: {content[:1000]}...

Return format: ["topic1", "topic2", "topic3"]
Maximum 5 topics.
"""
        
        response = self._call_ai(prompt, max_tokens=150)
        if not response:
            return []
        
        try:
            response = response.strip()
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join(line for line in lines if not line.startswith("```"))
            
            topics = json.loads(response.strip())
            if isinstance(topics, list):
                return [t for t in topics if isinstance(t, str)][:5]
        except Exception as e:
            print(f"Error parsing AI topics response: {e}")
        
        return []
    
    def suggest_related_queries(self, topic: str) -> List[str]:
        """
        Use AI to suggest related search queries.
        
        Args:
            topic: Base topic
            
        Returns:
            List of related queries
        """
        if not self.is_configured():
            return [
                f"{topic} tutorial",
                f"{topic} documentation",
                f"{topic} examples",
                f"{topic} research papers"
            ]
        
        prompt = f"""Suggest 5 related search queries for finding AI training materials about "{topic}".

Return ONLY a JSON array of search queries.
Example: ["query1", "query2", "query3"]
"""
        
        response = self._call_ai(prompt, max_tokens=200)
        if not response:
            return []
        
        try:
            response = response.strip()
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join(line for line in lines if not line.startswith("```"))
            
            queries = json.loads(response.strip())
            if isinstance(queries, list):
                return [q for q in queries if isinstance(q, str)][:5]
        except Exception as e:
            print(f"Error parsing AI queries response: {e}")
        
        return []
    
    def classify_content_type(self, title: str, url: str, content_preview: str) -> str:
        """
        Use AI to classify content type more accurately.
        
        Args:
            title: Content title
            url: Content URL
            content_preview: Preview of content
            
        Returns:
            Content type (article, tutorial, documentation, code, dataset, image, video, research)
        """
        if not self.is_configured():
            # Fallback to simple classification
            url_lower = url.lower()
            if 'tutorial' in url_lower:
                return 'tutorial'
            elif 'docs' in url_lower:
                return 'documentation'
            return 'article'
        
        prompt = f"""Classify this content into ONE category:
- article: Blog post or article
- tutorial: Step-by-step guide
- documentation: Technical documentation
- code: Code repository or examples
- dataset: Dataset or data resource
- research: Research paper
- image: Image collection
- video: Video content

Title: {title}
URL: {url}
Content: {content_preview[:200]}...

Respond with ONLY the category name, nothing else.
"""
        
        response = self._call_ai(prompt, max_tokens=50)
        if response:
            response = response.strip().lower()
            valid_types = ['article', 'tutorial', 'documentation', 'code', 'dataset', 'research', 'image', 'video']
            if response in valid_types:
                return response
        
        return 'article'


# Global AI helper instance
_ai_helper = None

def get_ai_helper(api_key: Optional[str] = None) -> AIHelper:
    """Get or create the global AI helper instance."""
    global _ai_helper
    if _ai_helper is None or api_key:
        _ai_helper = AIHelper(api_key)
    return _ai_helper
